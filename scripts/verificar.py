"""Confere se o computador e o projeto estão prontos para usar o bibliotecário.

Uso:
  python3 scripts/verificar.py          # mostra cada item (ok, aviso ou falta)
  python3 scripts/verificar.py --curto  # só mostra o que precisa de atenção (usado ao abrir a pasta)
Sai com código 1 se faltar algo que impede rodar os scripts. Avisos não impedem.
"""
import json
import os
import sqlite3
import sys
from pathlib import Path

from comum import RAIZ, achar_pdftotext, ler_tags

OK, AVISO, FALTA = "ok", "aviso", "falta"


def checar():
    """Devolve a lista de (estado, item, o que fazer)."""
    itens = []
    versao = sys.version_info
    if versao >= (3, 9):
        itens.append((OK, f"Python {versao.major}.{versao.minor}", ""))
    else:
        itens.append((FALTA, f"Python {versao.major}.{versao.minor}",
                      "é preciso o Python 3.9 ou mais novo: rode xcode-select --install no Terminal"))

    if achar_pdftotext():
        itens.append((OK, "pdftotext", ""))
    else:
        itens.append((FALTA, "pdftotext", "rode no Terminal: brew install poppler (sem Homebrew, veja https://brew.sh)"))

    try:
        sqlite3.connect(":memory:").execute("CREATE VIRTUAL TABLE t USING fts5(x)")
        itens.append((OK, "busca textual (FTS5)", ""))
    except sqlite3.OperationalError:
        itens.append((FALTA, "busca textual (FTS5)", "o SQLite deste Python não tem FTS5: use o python3 do Mac"))

    config = Path(os.environ.get("BIBLIOTECA_CONFIG", RAIZ / "config.json"))
    if not config.exists():
        itens.append((FALTA, "config.json", "copie config.exemplo.json para config.json e ajuste os caminhos"))
    else:
        try:
            cfg = json.loads(config.read_text(encoding="utf-8"))
            itens.append((OK, "config.json", ""))
            for origem in cfg.get("origens", []):
                if Path(origem).expanduser().is_dir():
                    itens.append((OK, f"pasta de origem {origem}", ""))
                else:
                    itens.append((FALTA, f"pasta de origem {origem}", "a pasta não existe: corrija o caminho em config.json"))
        except (json.JSONDecodeError, AttributeError):
            itens.append((FALTA, "config.json", "o arquivo não é um JSON válido: compare com config.exemplo.json"))

    tags_md = RAIZ / ".claude" / "skills" / "organizar" / "tags.md"
    if "Lista de exemplo" in tags_md.read_text(encoding="utf-8"):
        itens.append((AVISO, "tags de exemplo", "escreva as tags da sua pesquisa em .claude/skills/organizar/tags.md"))
    else:
        n = len(ler_tags())
        estado = OK if 15 <= n <= 30 else AVISO
        itens.append((estado, f"{n} tags", "" if estado == OK else "o ideal é ter de 15 a 30 tags"))

    if "SEU NOME" in (RAIZ / "CLAUDE.md").read_text(encoding="utf-8"):
        itens.append((AVISO, "nome no CLAUDE.md", "troque SEU NOME pelo seu nome no CLAUDE.md"))

    requisitos = RAIZ / "requirements.txt"
    if requisitos.exists() and not (RAIZ / ".venv").is_dir():
        itens.append((FALTA, "bibliotecas Python", "rode: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"))
    return itens


def main():
    curto = "--curto" in sys.argv
    itens = checar()
    problemas = [i for i in itens if i[0] != OK]
    if curto:
        if problemas:
            print(f"Bibliotecário: {len(problemas)} item(ns) pedem atenção antes de usar. Peça: use a skill preparar.")
            for estado, item, fazer in problemas:
                print(f"  {estado}: {item}: {fazer}")
    else:
        for estado, item, fazer in itens:
            print(f"  {estado:<5} {item}" + (f": {fazer}" if fazer else ""))
        print("Tudo pronto." if not problemas else "Peça ao Claude: use a skill preparar.")
    sys.exit(1 if any(i[0] == FALTA for i in itens) else 0)


if __name__ == "__main__":
    main()
