"""Mostra o texto de algumas páginas de um documento do índice.

Uso: python3 scripts/ler_paginas.py ID INICIO [FIM]   (no máximo 3 páginas por vez)
INICIO e FIM são os números que a busca mostra em "mais contexto". Em .txt, .md e .docx sem
marcas de página, cada número é um bloco, e o cabeçalho diz que linhas ou parágrafos ele cobre.
"""
import sys

from comum import carregar_config, conectar, contar_vazias


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    doc, inicio = int(sys.argv[1]), int(sys.argv[2])
    fim = min(int(sys.argv[3]) if len(sys.argv) > 3 else inicio, inicio + 2)
    con = conectar(carregar_config())
    d = con.execute("SELECT titulo, caminho, sensivel, extensao, paginado FROM documentos WHERE id = ?",
                    (doc,)).fetchone()
    if not d:
        sys.exit("Documento não encontrado.")
    if d["sensivel"]:
        sys.exit("Documento sensível: o texto não está no índice.")
    print(f"{d['titulo'] or '(sem título)'}\n{d['caminho']}\n")
    unidade = "parágrafos" if d["extensao"] == ".docx" else "linhas"
    for p in con.execute("SELECT pagina, texto, linha_inicial FROM paginas WHERE documento_id = ? "
                         "AND pagina BETWEEN ? AND ? ORDER BY pagina", (doc, inicio, fim)):
        texto = p["texto"] or ""
        if d["paginado"]:
            cabecalho = f"página {p['pagina']}"
        else:
            vazias = contar_vazias(d["extensao"])
            total = len([l for l in texto.split("\n") if vazias or l.strip()])
            primeira = p["linha_inicial"] or 1
            cabecalho = f"{unidade} {primeira} a {primeira + max(total, 1) - 1}"
        print(f"--- {cabecalho} ---\n{texto.strip()}\n")


if __name__ == "__main__":
    main()
