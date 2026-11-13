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
    docs = con.execute(
        "SELECT * FROM documentos WHERE situacao IN ('novo', 'duplicata', 'sensivel') ORDER BY id").fetchall()
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

    operacao = "move" if entrada else "copia"
    print(f"Plano ({'mover' if entrada else 'copiar'} {len(plano)} arquivo(s)):")
    for d, dest, sit, motivo in plano:
        extra = f"  [{motivo}]" if motivo else ""
        print(f"  {d['nome_original']}  ->  {dest.relative_to(acervo)}{extra}")
    if pulados:
        print(f"Duplicatas que não serão copiadas: {len(pulados)}")
        for d in pulados:
            print(f"  {d['caminho']}  ({d['motivo']})")
    if sensiveis:
        print(f"Sensíveis que ficam onde estão (decida se tira da área liberada): {len(sensiveis)}")
        for d in sensiveis:
            print(f"  {d['caminho']}  ({d['motivo']})")
    if simular:
        print("Simulação: nada foi copiado nem movido.")
        return

    rodada = agora()
    for d, dest, sit, motivo in plano:
        dest = destino_livre(dest)
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
    print(f"Feito: {len(plano)} arquivo(s). Rodada registrada em movimentos como {rodada}.")


if __name__ == "__main__":
    main()
