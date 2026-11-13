"""Mostra o texto de algumas páginas de um documento do índice.

Uso: python3 scripts/ler_paginas.py ID INICIO [FIM]   (no máximo 3 páginas por vez)
"""
import sys

from comum import carregar_config, conectar


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    doc, inicio = int(sys.argv[1]), int(sys.argv[2])
    fim = min(int(sys.argv[3]) if len(sys.argv) > 3 else inicio, inicio + 2)
    con = conectar(carregar_config())
    d = con.execute("SELECT titulo, caminho, sensivel FROM documentos WHERE id = ?", (doc,)).fetchone()
    if not d:
        sys.exit("Documento não encontrado.")
    if d["sensivel"]:
        sys.exit("Documento sensível: o texto não está no índice.")
    print(f"{d['titulo'] or '(sem título)'}\n{d['caminho']}\n")
    for p in con.execute("SELECT pagina, texto FROM paginas WHERE documento_id = ? AND pagina BETWEEN ? AND ? "
                         "ORDER BY pagina", (doc, inicio, fim)):
        print(f"--- página {p['pagina']} ---\n{(p['texto'] or '').strip()}\n")


if __name__ == "__main__":
    main()
