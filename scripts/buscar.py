"""Busca no índice, por documento ou por trecho. Só leitura.

Uso:
  python3 scripts/buscar.py documentos "consulta" [--tipo T] [--ano-de A] [--ano-ate A] [--limite N]
  python3 scripts/buscar.py paginas "consulta" [--doc ID] [--limite N]

Sintaxe da consulta (FTS5): palavras soltas (todas precisam aparecer), "frase exata", OR,
NEAR(palavra1 palavra2, 10), prefixo com asterisco (fascis*). Acentos não importam.

No modo paginas, cada resultado diz onde está o trecho: página e linha no PDF, página e parágrafo
no .docx salvo pelo Word, só o parágrafo no .docx sem marcas de página, só a linha no .txt e no .md.
"""
import re
import sqlite3
import sys

from comum import carregar_config, conectar, contar_vazias, descrever_local, numero_da_linha


def opcao(nome, padrao=None):
    return sys.argv[sys.argv.index(nome) + 1] if nome in sys.argv else padrao


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("documentos", "paginas"):
        sys.exit(__doc__)
    modo, consulta = sys.argv[1], sys.argv[2]
    limite = int(opcao("--limite", 10))
    con = conectar(carregar_config())
    try:
        if modo == "documentos":
            sql = """SELECT d.id, d.titulo, d.autores, d.ano, d.tipo, d.caminho, d.situacao,
                            snippet(documentos_fts, -1, '[', ']', ' ... ', 12) AS trecho
                     FROM documentos_fts JOIN documentos d ON d.id = documentos_fts.rowid
                     WHERE documentos_fts MATCH ? AND d.sensivel = 0"""
            params = [consulta]
            if opcao("--tipo"):
                sql += " AND d.tipo = ?"
                params.append(opcao("--tipo"))
            if opcao("--ano-de"):
                sql += " AND d.ano >= ?"
                params.append(opcao("--ano-de"))
            if opcao("--ano-ate"):
                sql += " AND d.ano <= ?"
                params.append(opcao("--ano-ate"))
            sql += " ORDER BY bm25(documentos_fts) LIMIT ?"
            linhas = con.execute(sql, params + [limite]).fetchall()
            for r in linhas:
                dup = "  (duplicata)" if r["situacao"] == "duplicata" else ""
                print(f"[{r['id']}] {r['titulo'] or '(sem título)'} | {r['autores'] or '?'} | {r['ano'] or 'sd'}"
                      f" | {r['tipo'] or '?'}{dup}\n     {r['caminho']}\n     {r['trecho']}")
        else:
            sql = """SELECT d.id, d.titulo, d.caminho, d.extensao, d.paginado, p.pagina, p.linha_inicial, p.texto,
                            snippet(paginas_fts, 0, '[', ']', ' ... ', 30) AS trecho,
                            snippet(paginas_fts, 0, char(2), char(3), '', 64) AS marcado
                     FROM paginas_fts JOIN paginas p ON p.id = paginas_fts.rowid
                     JOIN documentos d ON d.id = p.documento_id
                     WHERE paginas_fts MATCH ? AND d.sensivel = 0 AND d.situacao != 'duplicata'"""
            params = [consulta]
            if opcao("--doc"):
                sql += " AND d.id = ?"
                params.append(int(opcao("--doc")))
            sql += " ORDER BY bm25(paginas_fts) LIMIT ?"
            linhas = con.execute(sql, params + [limite]).fetchall()
            for r in linhas:
                # O primeiro termo que casou indica a linha (ou o parágrafo) dentro da página
                termo = re.search("\x02(.*?)\x03", r["marcado"] or "")
                n = numero_da_linha(r["texto"] or "", termo.group(1), contar_vazias(r["extensao"])) if termo else None
                local = descrever_local(r["extensao"], r["paginado"], r["pagina"], r["linha_inicial"], n)
                print(f"[{r['id']}] {r['titulo'] or '(sem título)'} | {local}\n"
                      f"     {r['caminho']}\n     {' '.join(r['trecho'].split())}\n"
                      f"     mais contexto: python3 scripts/ler_paginas.py {r['id']} {r['pagina']}")
    except sqlite3.OperationalError as e:
        sys.exit(f"Consulta inválida ({e}). Use aspas para frases e evite caracteres como : ( ) soltos.")
    if not linhas:
        print("Nada encontrado.")


if __name__ == "__main__":
    main()
