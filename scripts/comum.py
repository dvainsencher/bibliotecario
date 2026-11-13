"""Funções comuns aos scripts da biblioteca. Python 3.9 ou mais novo, só biblioteca padrão."""
import datetime
import hashlib
import json
import os
import re
import shutil
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
    "rg", "cpf", "cnh", "passaporte", "extrato", "fatura", "boleto", "irpf",
    "holerite", "contracheque", "contrato", "laudo", "receita medica",
    "atestado", "prontuario", "entrevista", "tcle", "consentimento", "senha",
]

EXTENSOES = {".pdf", ".docx", ".txt", ".md"}
PALAVRAS_POR_BLOCO = 400


def resolver(valor, base):
    """Caminho do config.json: ~ expandido; relativo vale a partir da pasta do config.json, não da pasta atual."""
    p = Path(valor).expanduser()
    return p if p.is_absolute() else Path(base) / p


def carregar_config():
    caminho = Path(os.environ.get("BIBLIOTECA_CONFIG", RAIZ / "config.json"))
    if not caminho.exists():
        sys.exit(f"Não achei {caminho}. Copie config.exemplo.json para config.json e ajuste os caminhos.")
    cfg = json.loads(caminho.read_text(encoding="utf-8"))
    base = caminho.parent
    cfg["origens"] = [str(resolver(p, base)) for p in cfg.get("origens", [])]
    cfg["acervo"] = str(resolver(cfg["acervo"], base))
    cfg["indice"] = str(resolver(cfg.get("indice", "indice/biblioteca.db"), base))
    cfg["lotes"] = str(resolver(cfg.get("lotes", "indice/lotes"), base))
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


def achar_pdftotext():
    """Caminho do pdftotext, ou None. O app do Claude no Mac nem sempre herda o PATH do Terminal,
    por isso também procura nas pastas onde o Homebrew instala (Apple Silicon e Intel)."""
    for candidato in (shutil.which("pdftotext"), "/opt/homebrew/bin/pdftotext", "/usr/local/bin/pdftotext"):
        if candidato and Path(candidato).exists():
            return candidato
    return None


def paginas_do_arquivo(caminho):
    """Devolve (blocos, paginado).

    blocos: lista de (texto, linha_inicial), um por página ou por bloco de ~400 palavras.
    paginado: True quando cada bloco é uma página de verdade (PDF, ou .docx com as marcas do Word).
    - PDF: uma página por bloco, como o pdftotext separa.
    - .docx: um parágrafo por linha. Com as marcas do Word, um bloco por página; sem elas,
      blocos de parágrafos, e linha_inicial é o número do primeiro parágrafo.
    - .txt e .md: blocos de linhas inteiras, e linha_inicial é a linha do arquivo onde o bloco começa.
    """
    ext = Path(caminho).suffix.lower()
    if ext == ".pdf":
        programa = achar_pdftotext()
        if not programa:
            sys.exit("pdftotext não encontrado. No Mac: brew install poppler")
        try:
            saida = subprocess.run(
                [programa, "-enc", "UTF-8", str(caminho), "-"],
                capture_output=True, check=True,
            ).stdout.decode("utf-8", errors="replace")
        except PermissionError:
            sys.exit(f"Sem permissão para rodar {programa}. Reinstale com: brew reinstall poppler")
        except subprocess.CalledProcessError:
            return [], True
        paginas = saida.split("\f")
        if paginas and not paginas[-1].strip():
            paginas = paginas[:-1]
        return [(p, 1) for p in paginas], True
    if ext == ".docx":
        paginas, paginado = paginas_docx(caminho)
        if paginado:
            return [("\n".join(p), 1) for p in paginas], True
        return agrupar([par for p in paginas for par in p], contar_vazias=False), False
    texto = Path(caminho).read_text(encoding="utf-8", errors="replace")
    # split("\n") e não splitlines(): splitlines também quebra em \f e outros, e a contagem
    # deixaria de bater com a numeração de linhas do editor
    linhas = texto.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    return agrupar(linhas, contar_vazias=True), False


def agrupar(linhas, contar_vazias):
    """Junta linhas inteiras em blocos de ~PALAVRAS_POR_BLOCO palavras, guardando onde cada bloco começa."""
    blocos, atual, palavras, inicio, numero = [], [], 0, 1, 0
    for linha in linhas:
        if contar_vazias or linha.strip():
            numero += 1
        if not atual:
            inicio = numero
        atual.append(linha)
        palavras += len(linha.split())
        if palavras >= PALAVRAS_POR_BLOCO:
            blocos.append(("\n".join(atual), inicio))
            atual, palavras = [], 0
    if atual:
        blocos.append(("\n".join(atual), inicio))
    return blocos or [("", 1)]


MARCA_WORD = "<w:lastRenderedPageBreak/>"
QUEBRA_MANUAL = r'<w:br\b[^>]*w:type="page"[^>]*/>'
PECA_DOCX = r'(<w:p[\s>])|(</w:p>)|({quebra})|(<w:tab/>)|<w:t(?:\s[^>]*)?>([^<]*)</w:t>'
ENTIDADES = (("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&apos;", "'"), ("&amp;", "&"))


def paginas_docx(caminho):
    """Lê um .docx sem programas externos (é um zip com XML dentro).

    Devolve (paginas, paginado): paginas é uma lista de páginas, cada uma uma lista de parágrafos
    não vazios. O Word grava <w:lastRenderedPageBreak/> onde cada página começava da última vez que
    o arquivo foi aberto, inclusive depois das quebras manuais. Por isso, quando há marcas do Word,
    só elas contam; as quebras manuais (<w:br w:type="page"/>) só contam num arquivo sem nenhuma
    marca do Word. Página sem texto (só imagem, ou em branco) continua contando, para a numeração
    bater com a do Word. Um parágrafo que atravessa a página vira dois: o fim dele é o primeiro
    parágrafo da página seguinte, como a pessoa conta olhando a página.
    Sem marca nenhuma não há como saber a página: o documento todo fica numa página só, com
    paginado False, a não ser que o próprio Word diga (em docProps/app.xml) que ele tem uma página.
    """
    try:
        with zipfile.ZipFile(caminho) as z:
            xml = z.read("word/document.xml").decode("utf-8", errors="replace")
            try:
                app = z.read("docProps/app.xml").decode("utf-8", errors="replace")
            except KeyError:
                app = ""
    except (zipfile.BadZipFile, KeyError):
        return [[]], False
    paginas, atual = [[]], ""

    def fecha_paragrafo():
        nonlocal atual
        texto = atual.strip()
        for a, b in ENTIDADES:
            texto = texto.replace(a, b)
        if texto:
            paginas[-1].append(texto)
        atual = ""

    quebra = re.escape(MARCA_WORD) if MARCA_WORD in xml else QUEBRA_MANUAL
    for m in re.finditer(PECA_DOCX.format(quebra=quebra), xml):
        abre, fecha, nova_pagina, tab, texto = m.groups()
        if abre or fecha:
            fecha_paragrafo()
        elif nova_pagina:
            fecha_paragrafo()
            paginas.append([])
        elif tab:
            atual += " "
        elif texto is not None:
            atual += texto
    fecha_paragrafo()
    if paginas and not paginas[-1] and len(paginas) > 1:
        paginas.pop()
    total = re.search(r"<Pages>(\d+)</Pages>", app)
    paginado = len(paginas) > 1 or (total is not None and total.group(1) == "1")
    return paginas, paginado


def numero_da_linha(texto, termo, contar_vazias, antes=""):
    """Posição (a partir de 1) da linha onde está o termo, ou None.

    `antes` são as palavras que vêm logo antes do termo no trecho mostrado pela busca. Com elas,
    a linha é a da ocorrência mostrada, mesmo que a frase quebre de linha, e não a primeira
    ocorrência da palavra na página. Se o contexto não for achado, vale a primeira ocorrência.
    """
    termo = normalizar(termo)
    if not termo:
        return None
    contadas = [l for l in texto.split("\n") if contar_vazias or l.strip()]
    # Texto corrido da página, guardando onde cada linha começa
    corrido, inicios = " ", []
    for linha in contadas:
        inicios.append(len(corrido))
        corrido += normalizar(linha) + " "
    for alvo in (normalizar(antes + " " + termo), termo):
        pos = corrido.find(" " + alvo + " ")
        if pos >= 0:
            pos += len(alvo) - len(termo) + 1  # onde começa o termo
            return max(i for i, ini in enumerate(inicios, start=1) if ini <= pos)
    return None


def descrever_local(extensao, paginado, pagina, linha_inicial, n=None):
    """Como dizer onde está um trecho: 'página 3, linha 8', 'página 2, parágrafo 4', 'parágrafo 14' ou 'linha 120'."""
    unidade = "parágrafo" if extensao == ".docx" else "linha"
    if paginado:
        return f"página {pagina}" + (f", {unidade} {n}" if n else "")
    inicio = linha_inicial or 1
    return f"{unidade} {inicio + n - 1}" if n else f"{unidade} {inicio} em diante"


def contar_vazias(extensao):
    """Em .txt e .md a linha vazia conta (é como o editor numera); no PDF e no .docx, não."""
    return extensao in (".txt", ".md")


def arquivo_tags():
    """tags.md da skill organizar. BIBLIOTECA_TAGS troca o arquivo (o teste usa a lista de exemplo)."""
    return Path(os.environ.get("BIBLIOTECA_TAGS", RAIZ / ".claude" / "skills" / "organizar" / "tags.md"))


def ler_tags():
    arquivo = arquivo_tags()
    tags = set()
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha.startswith("- "):
            tags.add(linha[2:].strip().lower())
    return tags
