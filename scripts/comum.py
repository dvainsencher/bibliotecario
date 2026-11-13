"""Funções comuns aos scripts da biblioteca. Python 3.9 ou mais novo, só biblioteca padrão."""
import datetime
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import unicodedata
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Pasta do acervo para cada tipo de documento
PASTAS = {
    "artigo": "Artigos",
    "livro": "Livros-e-capitulos",
    "capitulo": "Livros-e-capitulos",
    "tese": "Teses-e-dissertacoes",
    "fichamento": "Fichamentos",
    "politica": "Documentos-de-politica",
    "noticia": "Noticias",
    "dados": "Dados-e-planilhas",
    "outro": "Outros",
}

# Termos que marcam um arquivo como sensível pelo nome ou pela pasta (sem abrir o arquivo)
SENSIVEIS = [
    "rg", "cpf", "cnh", "passaporte", "extrato", "fatura", "boleto", "irpf", "imposto",
    "holerite", "contracheque", "contrato", "laudo", "exame", "receita medica",
    "atestado", "prontuario", "entrevista", "tcle", "consentimento", "senha",
]

EXTENSOES = {".pdf", ".docx", ".txt", ".md"}
PALAVRAS_POR_BLOCO = 400


def carregar_config():
    caminho = Path(os.environ.get("BIBLIOTECA_CONFIG", RAIZ / "config.json"))
    if not caminho.exists():
        sys.exit(f"Não achei {caminho}. Copie config.exemplo.json para config.json e ajuste os caminhos.")
    cfg = json.loads(caminho.read_text(encoding="utf-8"))
    base = caminho.parent
    cfg["origens"] = [str(Path(p).expanduser()) for p in cfg.get("origens", [])]
    cfg["acervo"] = str(Path(cfg["acervo"]).expanduser())
    indice = Path(cfg.get("indice", "indice/biblioteca.db")).expanduser()
    cfg["indice"] = str(indice if indice.is_absolute() else base / indice)
    lotes = Path(cfg.get("lotes", "indice/lotes")).expanduser()
    cfg["lotes"] = str(lotes if lotes.is_absolute() else base / lotes)
    return cfg


def conectar(cfg):
    Path(cfg["indice"]).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(cfg["indice"])
    con.row_factory = sqlite3.Row
    con.executescript((RAIZ / "esquema.sql").read_text(encoding="utf-8"))
    return con


def agora():
    return datetime.datetime.now().isoformat(timespec="seconds")


def sha256(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def sem_acentos(texto):
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c))


def normalizar(texto):
    """Minúsculas, sem acentos, só letras e números separados por espaço."""
    texto = sem_acentos(texto or "").lower()
    return re.sub(r"[^a-z0-9]+", " ", texto).strip()


def parece_sensivel(caminho):
    alvo = " " + normalizar(str(caminho)) + " "
    for termo in SENSIVEIS:
        # casa no começo de palavra: "entrevista" pega "entrevistas", "rg" não pega "org"
        if " " + termo in alvo:
            return termo
    return None


def nome_seguro(nome, limite=80):
    """Sem acentos, sem espaços, sem caracteres proibidos, no máximo `limite` caracteres."""
    nome = sem_acentos(nome or "").strip()
    nome = re.sub(r"\s+", "-", nome)
    nome = re.sub(r"[^A-Za-z0-9_.\-]", "", nome)
    nome = re.sub(r"-{2,}", "-", nome).strip("-_.")
    return nome[:limite] or "sem-nome"


def paginas_do_arquivo(caminho):
    """Devolve a lista de textos, um por página (PDF) ou por bloco de ~400 palavras (outros)."""
    ext = Path(caminho).suffix.lower()
    if ext == ".pdf":
        try:
            saida = subprocess.run(
                ["pdftotext", "-enc", "UTF-8", str(caminho), "-"],
                capture_output=True, check=True,
            ).stdout.decode("utf-8", errors="replace")
        except FileNotFoundError:
            sys.exit("pdftotext não encontrado. No Mac: brew install poppler")
        except subprocess.CalledProcessError:
            return []
        paginas = saida.split("\f")
        if paginas and not paginas[-1].strip():
            paginas = paginas[:-1]
        return paginas
    if ext == ".docx":
        texto = texto_docx(caminho)
    else:
        texto = Path(caminho).read_text(encoding="utf-8", errors="replace")
    palavras = texto.split()
    return [" ".join(palavras[i:i + PALAVRAS_POR_BLOCO])
            for i in range(0, len(palavras), PALAVRAS_POR_BLOCO)] or [""]


def texto_docx(caminho):
    """Lê o texto de um .docx sem programas externos (o .docx é um zip com XML dentro)."""
    try:
        with zipfile.ZipFile(caminho) as z:
            xml = z.read("word/document.xml").decode("utf-8", errors="replace")
    except (zipfile.BadZipFile, KeyError):
        return ""
    xml = re.sub(r"</w:p>", "\n", xml)
    xml = re.sub(r"<w:tab/>", " ", xml)
    texto = re.sub(r"<[^>]+>", "", xml)
    for a, b in (("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&apos;", "'")):
        texto = texto.replace(a, b)
    return texto


def ler_tags():
    arquivo = RAIZ / ".claude" / "skills" / "organizar" / "tags.md"
    tags = set()
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha.startswith("- "):
            tags.add(linha[2:].strip().lower())
    return tags
