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
import unicodedata
from pathlib import Path

# Antes de importar o resto: num Python antigo, a mensagem sai clara em vez de um erro de sintaxe
if sys.version_info < (3, 9):
    print("Bibliotecário: este Python é antigo demais (precisa do 3.9 ou mais novo). "
          "No Mac, rode no Terminal: xcode-select --install. Depois peça: use a skill preparar.")
    sys.exit(1)

from comum import EXTENSOES, RAIZ, achar_pdftotext, arquivo_tags, carregar_config, ler_tags  # noqa: E402

OK, AVISO, FALTA = "ok", "aviso", "falta"
ACERVO_ALTERADO = "acervo alterado fora do bibliotecário"


def checar():
    """Devolve a lista de (estado, item, o que fazer)."""
    versao = sys.version_info
    itens = [(OK, f"Python {versao.major}.{versao.minor}", "")]

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
        itens += checar_config(config)
        itens += checar_acervo()

    tags_md = arquivo_tags()
    if not tags_md.exists():
        itens.append((FALTA, "tags.md", "lista de tags não encontrada: recupere com git checkout .claude/skills/organizar/tags.md"))
    elif "Lista de exemplo" in tags_md.read_text(encoding="utf-8", errors="replace"):
        itens.append((AVISO, "tags de exemplo", "escreva as tags da sua pesquisa em .claude/skills/organizar/tags.md"))
    else:
        n = len(ler_tags())
        estado = OK if 15 <= n <= 30 else AVISO
        itens.append((estado, f"{n} tags", "" if estado == OK else "o ideal é ter de 15 a 30 tags"))

    claude_md = RAIZ / "CLAUDE.md"
    if claude_md.exists() and "SEU NOME" in claude_md.read_text(encoding="utf-8", errors="replace"):
        itens.append((AVISO, "nome no CLAUDE.md", "troque SEU NOME pelo seu nome no CLAUDE.md"))

    # Hoje o projeto só usa a biblioteca padrão. Se um dia houver requirements.txt, ele pede o venv.
    requisitos = RAIZ / "requirements.txt"
    if requisitos.exists() and not (RAIZ / ".venv").is_dir():
        itens.append((FALTA, "bibliotecas Python", "rode: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"))
    return itens


def checar_config(config):
    """Itens sobre o config.json: formato e pastas de origem."""
    formato = "o formato de config.json não está certo: compare com config.exemplo.json"
    try:
        cfg = json.loads(config.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return [(FALTA, "config.json", formato)]
    if not isinstance(cfg, dict):
        return [(FALTA, "config.json", formato)]
    origens = cfg.get("origens", [])
    if not isinstance(origens, list) or not all(isinstance(o, str) for o in origens):
        return [(FALTA, "config.json", 'origens precisa ser uma lista de pastas, como ["exemplo"] ou ["~/Documents/Amostra"]')]
    itens = [(OK, "config.json", "")]
    for origem in origens:
        caminho = Path(origem).expanduser()
        if (caminho if caminho.is_absolute() else config.parent / caminho).is_dir():
            itens.append((OK, f"pasta de origem {origem}", ""))
        else:
            itens.append((FALTA, f"pasta de origem {origem}", "a pasta não existe: corrija o caminho em config.json"))
    return itens


def checar_acervo():
    """Confere se o acervo bate com o índice. O acervo é do bibliotecário: mudança feita à mão vira aviso.

    Fica de fora o que ainda não é do acervo (_entrada/), o que o desfazer guardou (_revisar/_desfeitos/)
    e os arquivos ocultos do sistema (.DS_Store e afins).
    Só conta os tipos que o inventário indexa. Os caminhos são comparados em NFC, porque o Mac pode
    devolver o nome com acento em outra forma Unicode que a gravada no índice.
    """
    try:
        cfg = carregar_config()
        acervo, indice = Path(cfg["acervo"]), Path(cfg["indice"])
    except (SystemExit, AttributeError, KeyError, TypeError, ValueError, OSError):
        return []  # config.json com problema já aparece como 'falta' em checar_config
    if not acervo.is_dir() or not indice.is_file():
        return []  # ainda não houve a primeira organização
    try:
        with sqlite3.connect(f"{indice.as_uri()}?mode=ro", uri=True) as con:
            registrados = {nfc(r[0]) for r in con.execute("SELECT caminho FROM documentos")}
    except sqlite3.Error as erro:
        return [(AVISO, "não consegui conferir o acervo",
                 f"o índice não abriu ({erro}): rode python3 scripts/estado.py para ver o problema")]
    no_disco = {}  # caminho em NFC -> conta para 'sem registro'
    fora = (acervo / "_entrada", acervo / "_revisar" / "_desfeitos")
    for p in acervo.rglob("*"):
        partes = p.relative_to(acervo).parts
        if p.suffix.lower() in EXTENSOES and not any(parte.startswith(".") for parte in partes) and p.is_file():
            no_disco[nfc(str(p))] = not any(f in p.parents for f in fora)
    dentro = nfc(str(acervo) + os.sep)
    sumidos = {c for c in registrados if c.startswith(dentro)} - set(no_disco)
    sem_registro = {c for c, conta in no_disco.items() if conta} - registrados
    if not sumidos and not sem_registro:
        return [(OK, "acervo confere com o índice", "")]
    return [(AVISO, ACERVO_ALTERADO,
             f"{len(sem_registro)} arquivo(s) sem registro e {len(sumidos)} caminho(s) que sumiram. "
             "Peça: use a skill organizar para reclassificar e verificar")]


def nfc(texto):
    return unicodedata.normalize("NFC", texto)


def main():
    curto = "--curto" in sys.argv
    itens = checar()
    problemas = [i for i in itens if i[0] != OK]
    if curto:
        if problemas:
            so_acervo = all(i[1] == ACERVO_ALTERADO for i in problemas)
            skill = "organizar" if so_acervo else "preparar"
            print(f"Bibliotecário: {len(problemas)} item(ns) pedem atenção antes de usar. Peça: use a skill {skill}.")
            for estado, item, fazer in problemas:
                print(f"  {estado}: {item}: {fazer}")
    else:
        for estado, item, fazer in itens:
            print(f"  {estado:<5} {item}" + (f": {fazer}" if fazer else ""))
        print("Tudo pronto." if not problemas else "Peça ao Claude: use a skill preparar.")
    sys.exit(1 if any(i[0] == FALTA for i in itens) else 0)


if __name__ == "__main__":
    main()
