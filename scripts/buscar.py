"""Busca no índice, por documento ou por trecho. Só leitura.

Uso:
  python3 scripts/buscar.py documentos "consulta" [--tipo T] [--ano-de A] [--ano-ate A] [--limite N]
  python3 scripts/buscar.py paginas "consulta" [--doc ID] [--limite N]

Sintaxe da consulta (FTS5): palavras soltas (todas precisam aparecer), "frase exata", OR,
NEAR(palavra1 palavra2, 10), prefixo com asterisco (fascis*). Acentos não importam.
"""
import sqlite3
import sys

from comum import carregar_config, conectar


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
            sql = """SELECT d.id, d.titulo, d.caminho, p.pagina,
                            snippet(paginas_fts, 0, '[', ']', ' ... ', 30) AS trecho
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
                print(f"[{r['id']}] {r['titulo'] or '(sem título)'} | página {r['pagina']}\n"
                      f"     {r['caminho']}\n     {' '.join(r['trecho'].split())}")
    except sqlite3.OperationalError as e:
        sys.exit(f"Consulta inválida ({e}). Use aspas para frases e evite caracteres como : ( ) soltos.")
    if not linhas:
        print("Nada encontrado.")


if __name__ == "__main__":
    main()
