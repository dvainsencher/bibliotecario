"""Monta lotes para o subagente classificador, com até 3 páginas úteis de cada documento.

Pula páginas com menos de 800 caracteres e começa no Resumo ou Abstract, se houver.
Teto de 16 mil caracteres por documento.
Uso: python3 scripts/selecionar_paginas.py [--lote 10]
Saída: arquivos indice/lotes/lote_NNN.json
"""
import json
import sys
from pathlib import Path

from comum import carregar_config, conectar, normalizar

MIN_PAGINA = 800
MAX_PAGINAS = 3
MAX_CARACTERES = 16000


def escolher(paginas):
    inicio = 0
    for i, p in enumerate(paginas[:6]):
        n = " " + normalizar(p["texto"][:3000]) + " "
        if " resumo " in n or " abstract " in n:
            inicio = i
            break
    uteis = [p for p in paginas[inicio:] if len(p["texto"].strip()) >= MIN_PAGINA]
    if not uteis:
        uteis = [p for p in paginas if p["texto"].strip()]
    escolhidas, total = [], 0
    for p in uteis[:MAX_PAGINAS]:
        texto = p["texto"].strip()[: MAX_CARACTERES - total]
        if not texto:
            break
        escolhidas.append({"pagina": p["pagina"], "texto": texto})
        total += len(texto)
    return escolhidas


def main():
    tamanho = 10
    if "--lote" in sys.argv:
        tamanho = int(sys.argv[sys.argv.index("--lote") + 1])
    cfg = carregar_config()
    con = conectar(cfg)
    pasta = Path(cfg["lotes"])
    pasta.mkdir(parents=True, exist_ok=True)
    docs = con.execute(
        """SELECT id, nome_original, extensao, paginas_total FROM documentos
           WHERE situacao = 'novo' AND tem_texto = 1 AND classificado_por IS NULL ORDER BY id""").fetchall()
    numero = len(list(pasta.glob("lote_*.json"))) + 1
    criados = []
    for i in range(0, len(docs), tamanho):
        lote = []
        for d in docs[i:i + tamanho]:
            paginas = [dict(r) for r in con.execute(
                "SELECT pagina, texto FROM paginas WHERE documento_id = ? ORDER BY pagina", (d["id"],))]
            for p in paginas:
                p["texto"] = p["texto"] or ""
            lote.append({"id": d["id"], "nome_original": d["nome_original"], "extensao": d["extensao"],
                         "paginas_total": d["paginas_total"], "paginas": escolher(paginas)})
        arquivo = pasta / f"lote_{numero:03d}.json"
        arquivo.write_text(json.dumps(lote, ensure_ascii=False, indent=1), encoding="utf-8")
        criados.append(arquivo)
        numero += 1
    sem_texto = con.execute(
        "SELECT COUNT(*) FROM documentos WHERE situacao = 'novo' AND tem_texto = 0").fetchone()[0]
    print(f"Documentos para classificar: {len(docs)} em {len(criados)} lote(s)")
    for c in criados:
        print(f"  {c}")
    if sem_texto:
        print(f"Sem texto, vão para _revisar/ com o nome original: {sem_texto}")


if __name__ == "__main__":
    main()
