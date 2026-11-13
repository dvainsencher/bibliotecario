"""Acha o mesmo documento em arquivos diferentes: mesmo DOI, ou mesmo título, primeiro autor e ano.

Fica o maior arquivo. Os outros viram duplicata. Casos parecidos mas não iguais são só listados,
para o modelo ou você decidirem.
Uso: python3 scripts/duplicados_conteudo.py [--simular]
"""
import sys
from collections import defaultdict
from difflib import SequenceMatcher

from comum import carregar_config, conectar, normalizar


def chave_titulo(d):
    autor = normalizar((d["autores"] or "").split(";")[0]).split(" ")
    return (normalizar(d["titulo"]), autor[-1] if autor else "", d["ano"] or "")


def main():
    simular = "--simular" in sys.argv
    cfg = carregar_config()
    con = conectar(cfg)
    docs = con.execute(
        """SELECT id, caminho, tamanho, titulo, autores, ano, doi FROM documentos
           WHERE classificado_por IS NOT NULL AND situacao NOT IN ('duplicata', 'sensivel')""").fetchall()
    grupos = defaultdict(list)
    for d in docs:
        if d["doi"]:
            grupos[("doi", d["doi"].lower().strip())].append(d)
        elif d["titulo"]:
            grupos[("titulo",) + chave_titulo(d)].append(d)
    marcados = 0
    for chave, membros in grupos.items():
        if len(membros) < 2:
            continue
        membros.sort(key=lambda d: -(d["tamanho"] or 0))
        principal = membros[0]
        motivo = "mesmo DOI" if chave[0] == "doi" else "mesmo título, autor e ano"
        for d in membros[1:]:
            print(f"Duplicata ({motivo}): {d['caminho']}  ->  principal: {principal['caminho']}")
            if not simular:
                con.execute("UPDATE documentos SET situacao = 'duplicata', motivo = ?, duplicata_de = ? WHERE id = ?",
                            (motivo, principal["id"], d["id"]))
            marcados += 1
    # Títulos muito parecidos (não iguais): só lista
    vistos = [d for d in docs if d["titulo"]]
    for i, a in enumerate(vistos):
        for b in vistos[i + 1:]:
            ta, tb = normalizar(a["titulo"]), normalizar(b["titulo"])
            if ta != tb and SequenceMatcher(None, ta, tb).ratio() > 0.9:
                print(f"Parecidos, confira: {a['caminho']}  |  {b['caminho']}")
    if not simular:
        con.commit()
    print(f"Duplicatas por conteúdo: {marcados}" + (" (simulação, nada mudou)" if simular else ""))


if __name__ == "__main__":
    main()
