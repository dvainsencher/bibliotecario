"""Copia (modo lote) ou move (modo entrada) os documentos classificados para o acervo.

Regras:
  confiança >= 0,8           -> pasta do tipo, com o nome sugerido
  confiança entre 0,5 e 0,8  -> _revisar/, com o nome sugerido
  confiança < 0,5 ou sem texto -> _revisar/, com o nome original
  sensível                   -> não sai do lugar (só aparece na lista)
  duplicata                  -> lote: não é copiada; entrada: vai para _revisar/
Nunca apaga nada. Cada cópia ou movimento vira uma linha na tabela movimentos.

Uso:
  python3 scripts/aplicar.py --simular           # só mostra o plano (sempre rode antes)
  python3 scripts/aplicar.py                     # modo lote: copia das pastas de origem
  python3 scripts/aplicar.py --entrada [--simular]  # modo entrada: move o que está em _entrada/
"""
import shutil
import sys
from pathlib import Path

from comum import PASTAS, agora, carregar_config, conectar


def destino_livre(caminho):
    caminho = Path(caminho)
    n = 2
    candidato = caminho
    while candidato.exists():
        candidato = caminho.with_name(f"{caminho.stem}_{n}{caminho.suffix}")
        n += 1
    return candidato


def main():
    simular = "--simular" in sys.argv
    entrada = "--entrada" in sys.argv
    cfg = carregar_config()
    con = conectar(cfg)
    acervo = Path(cfg["acervo"])
    pasta_entrada = str(acervo / "_entrada") + "/"
    todos = {r["id"]: r for r in con.execute("SELECT * FROM documentos")}
    docs = [d for d in todos.values() if d["situacao"] in ("novo", "duplicata", "sensivel")]
    docs.sort(key=lambda d: d["id"])
    if entrada:
        docs = [d for d in docs if d["caminho"].startswith(pasta_entrada)]
    else:
        docs = [d for d in docs if not d["caminho"].startswith(str(acervo) + "/")]
    plano, sensiveis, pulados = [], [], []
    for d in docs:
        if d["situacao"] == "sensivel":
            sensiveis.append(d)
            continue
        if d["situacao"] == "duplicata":
            if entrada:
                plano.append((d, acervo / "_revisar" / d["nome_original"], "revisar", d["motivo"]))
            else:
                pulados.append(d)
            continue
        conf = d["confianca"] if d["confianca"] is not None else 0
        if not d["tem_texto"]:
            plano.append((d, acervo / "_revisar" / d["nome_original"], "revisar", "sem texto"))
        elif d["classificado_por"] is None:
            continue  # ainda não classificado
        elif conf >= 0.8:
            pasta = PASTAS.get(d["tipo"] or "outro", "Outros")
            plano.append((d, acervo / pasta / (d["nome_sugerido"] + d["extensao"]), "ok", None))
        elif conf >= 0.5:
            plano.append((d, acervo / "_revisar" / (d["nome_sugerido"] + d["extensao"]), "revisar",
                          d["motivo"] or f"confiança {conf:.2f}"))
        else:
            plano.append((d, acervo / "_revisar" / d["nome_original"], "revisar",
                          d["motivo"] or f"confiança {conf:.2f}"))

    destinos = {d["id"]: dest for d, dest, _, _ in plano}
    if simular:
        relatorio(plano, destinos, pulados, sensiveis, todos, acervo, entrada, feito=False)
        print("Simulação: nada foi copiado nem movido.")
        return

    operacao = "move" if entrada else "copia"
    rodada = agora()
    for d, dest, sit, motivo in plano:
        dest = destino_livre(dest)
        destinos[d["id"]] = dest
        dest.parent.mkdir(parents=True, exist_ok=True)
        if entrada:
            shutil.move(d["caminho"], dest)
        else:
            shutil.copy2(d["caminho"], dest)
        con.execute(
            "INSERT INTO movimentos (documento_id, sha256, origem, destino, operacao, motivo, feito_em) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (d["id"], d["sha256"], d["caminho"], str(dest), operacao, motivo, rodada))
        con.execute("UPDATE documentos SET caminho = ?, caminho_origem = ?, situacao = ? WHERE id = ?",
                    (str(dest), d["caminho"], sit if d["situacao"] != "duplicata" else "duplicata", d["id"]))
        con.commit()
    relatorio(plano, destinos, pulados, sensiveis, todos, acervo, entrada, feito=True)
    print(f"Rodada registrada em movimentos como {rodada}.")


def principal_de(d, todos):
    """Segue duplicata_de até o documento que não é duplicata (um duplicado pode apontar para outro)."""
    vistos = set()
    while d["situacao"] == "duplicata" and d["duplicata_de"] in todos and d["duplicata_de"] not in vistos:
        vistos.add(d["id"])
        d = todos[d["duplicata_de"]]
    return d


def onde_esta(principal, destinos, acervo, feito):
    def curto(caminho):
        caminho = Path(caminho)
        return str(caminho.relative_to(acervo)) if acervo in caminho.parents else str(caminho)
    if principal["situacao"] == "sensivel":
        return "que é sensível e fica onde está"
    if principal["id"] in destinos:
        return f"{'que foi' if feito else 'que vai'} para {curto(destinos[principal['id']])}"
    return f"que está em {curto(principal['caminho'])}"


def relatorio(plano, destinos, pulados, sensiveis, todos, acervo, entrada, feito):
    verbo = ("movido(s)" if entrada else "copiado(s)") if feito else ("mover" if entrada else "copiar")
    print(f"{'Feito' if feito else 'Plano'} ({len(plano)} arquivo(s) {'' if feito else 'para '}{verbo}):")
    for d, _, _, motivo in plano:
        extra = f"  [{motivo}]" if motivo else ""
        # Sem motivo próprio, o motivo de ir para _revisar/ já é a confiança: não repete
        mostra_conf = d["confianca"] is not None and not (motivo or "").startswith("confiança")
        conf = f"  (confiança {d['confianca']:.2f})" if mostra_conf else ""
        print(f"  {d['nome_original']}  ->  {destinos[d['id']].relative_to(acervo)}{conf}{extra}")
    duplicados = pulados + [d for d, _, _, _ in plano if d["situacao"] == "duplicata"]
    if duplicados:
        if entrada:
            print(f"Duplicados ({len(duplicados)}): o documento já está no acervo; a cópia nova vai para "
                  "_revisar/ para você decidir.")
        else:
            print(f"Duplicados ({len(duplicados)}): só uma cópia de cada documento entra no acervo.")
        ids_pulados = {d["id"] for d in pulados}
        for d in duplicados:
            p = principal_de(d, todos)
            if d["id"] in ids_pulados:
                fica = f"Esta cópia fica só na origem: {d['caminho']}"
            else:
                fica = f"Esta cópia {'foi' if feito else 'vai'} para _revisar/."
            if p["id"] == d["id"]:
                print(f"  {d['nome_original']} está marcado como duplicata, mas o original não está mais no "
                      f"índice. {fica}")
                continue
            print(f"  {d['nome_original']} é cópia de {p['nome_original']} ({d['motivo']}), "
                  f"{onde_esta(p, destinos, acervo, feito)}. {fica}")
    if sensiveis:
        print(f"Sensíveis que ficam onde estão (decida se tira da área liberada): {len(sensiveis)}")
        for d in sensiveis:
            print(f"  {d['caminho']}  ({d['motivo']})")


if __name__ == "__main__":
    main()
