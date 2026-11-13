"""Teste completo do fluxo da biblioteca com uma amostra falsa, numa pasta temporária.

Não toca nos seus arquivos nem no seu índice. Uso: python3 testes/rodar_teste.py
O subagente classificador é simulado: lê os metadados escritos na própria amostra.
"""
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SCRIPTS = RAIZ / "scripts"
LONGO = ("Este paragrafo existe para que a pagina tenha texto suficiente para ser considerada util "
         "pelo seletor de paginas. ") * 12


# ---------- amostra falsa ----------

def pdf(caminho, paginas):
    """PDF mínimo, uma página por item de `paginas` (texto com quebras de linha)."""
    objs = ["<< /Type /Catalog /Pages 2 0 R >>", None,
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"]
    kids = []
    for texto in paginas:
        linhas = []
        for linha in texto.split("\n"):
            while len(linha) > 90:
                corte = linha.rfind(" ", 0, 90)
                corte = corte if corte > 0 else 90
                linhas.append(linha[:corte])
                linha = linha[corte:].lstrip()
            linhas.append(linha)
        corpo = "BT /F1 10 Tf 40 800 Td 13 TL\n" + "".join(
            "(" + l.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") + ") '\n" for l in linhas) + "ET"
        stream = corpo.encode("cp1252", errors="replace")
        objs.append(("stream", stream))
        n_conteudo = len(objs)
        objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                    f"/Resources << /Font << /F1 3 0 R >> >> /Contents {n_conteudo} 0 R >>")
        kids.append(len(objs))
    objs[1] = f"<< /Type /Pages /Kids [{' '.join(f'{k} 0 R' for k in kids)}] /Count {len(kids)} >>"
    saida, offsets = bytearray(b"%PDF-1.4\n"), []
    for i, o in enumerate(objs, start=1):
        offsets.append(len(saida))
        if isinstance(o, tuple):
            saida += f"{i} 0 obj\n<< /Length {len(o[1])} >>\nstream\n".encode() + o[1] + b"\nendstream\nendobj\n"
        else:
            saida += f"{i} 0 obj\n{o}\nendobj\n".encode("latin-1")
    xref = len(saida)
    saida += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        saida += f"{off:010d} 00000 n \n".encode()
    saida += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    Path(caminho).write_bytes(bytes(saida))


PAGINA = "<<nova pagina>>"  # na lista de parágrafos do docx: o próximo parágrafo começa uma página
MANUAL = "<<quebra manual>>"  # quebra de página que a pessoa inseriu (Ctrl+Enter)


def docx(caminho, paragrafos, paginas_app=None):
    """.docx mínimo. PAGINA na lista grava a marca que o Word deixa onde a página começou."""
    corpo, marca = "", ""
    for p in paragrafos:
        if p == PAGINA:
            marca += "<w:lastRenderedPageBreak/>"
            continue
        if p == MANUAL:
            marca += '<w:br w:type="page"/>'
            continue
        corpo += f'<w:p w:rsidR="00A1"><w:pPr><w:jc w:val="both"/></w:pPr><w:r>{marca}<w:t xml:space="preserve">{p}</w:t></w:r></w:p>'
        marca = ""
    xml = ('<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/'
           f'wordprocessingml/2006/main"><w:body>{corpo}</w:body></w:document>')
    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(caminho, "w") as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/'
                   'package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/></Types>')
        z.writestr("word/document.xml", xml)
        if paginas_app is not None:
            z.writestr("docProps/app.xml", f"<Properties><Pages>{paginas_app}</Pages></Properties>")


def meta(titulo, autor, ano, tipo, conf=0.9, doi=None, tags=("fascismo",)):
    return (f"META|{json.dumps({'titulo': titulo, 'autor': autor, 'ano': ano, 'tipo': tipo, 'conf': conf, 'doi': doi, 'tags': list(tags)})}")


def gerar_amostra(origem):
    m_adorno = meta("Teoria freudiana e o padrão da propaganda fascista", "Theodor Adorno", "1951", "artigo",
                    doi="10.1000/adorno.1951")
    capa = "Revista de Estudos Críticos\nVolume 3"
    artigo = [capa, "Resumo\n" + m_adorno + "\nO artigo discute a propaganda fascista. " + LONGO,
              "Introdução\nA análise segue.\nO conceito de pseudoindividualizacao aparece nesta linha.\n" + LONGO]
    pdf(origem / "artigos" / "Adorno_teoria.pdf", artigo)
    (origem / "Downloads").mkdir(parents=True)
    shutil.copy2(origem / "artigos" / "Adorno_teoria.pdf", origem / "Downloads" / "download (1).pdf")
    pdf(origem / "Downloads" / "download.pdf", ["Baixado do portal X\n" + capa] + artigo[1:])
    m_ms = meta("Plano nacional de saúde da mulher", "Ministério da Saúde", "2023", "politica",
                tags=("saude", "politicas publicas", "genero"))
    pdf(origem / "politicas" / "plano_ms.pdf",
        ["Ministério da Saúde", "Resumo\n" + m_ms + "\nMetas para a saúde da mulher. " + LONGO,
         "Capítulo 2\nPúblico-alvo e metas. " + LONGO, "Anexo\n" + LONGO])
    m_fich = meta("Fichamento de Adorno sobre propaganda fascista", "Theodor Adorno", "1951", "fichamento")
    docx(origem / "fichamentos" / "fichamento adorno.docx",
         [m_fich, "Fichamento do texto de Adorno.", LONGO, PAGINA, "Segunda página do fichamento.",
          "Para Adorno, o fascista é uma mistura de barbeiro de bairro e King Kong.", LONGO], paginas_app=2)
    pdf(origem / "pessoal" / "RG_digitalizado.pdf", ["Documento de identidade"])
    pdf(origem / "Downloads" / "scan_001.pdf", [""])
    (origem / "notas.txt").write_text(
        meta("Notas soltas de leitura", "Anônimo", None, "outro", conf=0.6, tags=()) + "\n\nSegunda linha em branco acima.\n"
        "Aqui se fala de heteronomia.\n" + LONGO, encoding="utf-8")
    (origem / "Entrevistas").mkdir()
    (origem / "Entrevistas" / "participante_03.txt").write_text("Transcrição com nome real.", encoding="utf-8")
    (origem / "foto.jpg").write_bytes(b"nao e texto")


# ---------- subagente simulado ----------

def classificar_lote(lote):
    saida = Path(str(lote).replace(".json", "_resposta.jsonl"))
    linhas = []
    for d in json.loads(Path(lote).read_text(encoding="utf-8")):
        texto = " ".join(p["texto"] for p in d["paginas"])
        achou = re.search(r"META\|(\{.*?\})", texto.replace("\n", " "))
        m = json.loads(achou.group(1)) if achou else {"titulo": None, "autor": None, "ano": None,
                                                      "tipo": "outro", "conf": 0.3, "doi": None, "tags": []}
        sobrenome = (m["autor"] or "sd").split()[-1]
        palavras = [w for w in (m["titulo"] or "sem titulo").split() if w.lower() not in ("o", "a", "de", "da", "e")][:6]
        prefixo = "Fichamento_" if m["tipo"] == "fichamento" else ""
        if m["tipo"] == "politica":
            sobrenome = "MS"
        linhas.append(json.dumps({
            "id": d["id"], "tipo": m["tipo"], "titulo": m["titulo"], "autores": [m["autor"]], "ano": m["ano"],
            "fonte": None, "doi": m["doi"], "idioma": "pt", "tags": m["tags"] + ["tag-inventada"],
            "resumo": "Resumo simulado.", "sensivel": False, "confianca": m["conf"],
            "nome_sugerido": f"{prefixo}{sobrenome}_{m['ano'] or 'sd'}_{'-'.join(palavras)}",
            "motivo_baixa_confianca": None if m["conf"] >= 0.8 else "autor e ano incertos"}, ensure_ascii=False))
    saida.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return saida


# ---------- execução ----------

def rodar(env, *args):
    r = subprocess.run([sys.executable, str(SCRIPTS / args[0])] + list(args[1:]),
                       env=env, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout, r.stderr)
        raise SystemExit(f"FALHOU: {' '.join(args)}")
    return r.stdout


falhas = []


def confere(cond, msg):
    print(("  ok    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


def main():
    tmp = Path(tempfile.mkdtemp(prefix="teste_biblioteca_"))
    origem, acervo = tmp / "Amostra", tmp / "Biblioteca"
    origem.mkdir()
    gerar_amostra(origem)
    cfg = tmp / "config.json"
    cfg.write_text(json.dumps({"origens": [str(origem)], "acervo": str(acervo),
                               "indice": str(tmp / "biblioteca.db"), "lotes": str(tmp / "lotes")}))
    # O teste usa a lista de tags de exemplo, para não depender das tags que você escreveu
    tags = tmp / "tags.md"
    tags.write_text("Lista de exemplo: apague esta linha quando escrever as suas tags.\n" + "".join(
        f"- {t}\n" for t in ("metodologia", "politicas publicas", "saude", "genero", "estado", "empresariado",
                              "fascismo", "democracia")), encoding="utf-8")
    env = dict(os.environ, BIBLIOTECA_CONFIG=str(cfg), BIBLIOTECA_TAGS=str(tags))
    antes = sorted(str(p) for p in origem.rglob("*"))

    print("0. Verificação do ambiente")
    r = subprocess.run([sys.executable, str(SCRIPTS / "verificar.py")], env=env, capture_output=True, text=True)
    confere(r.returncode == 0 and re.search(r"^\s*ok\s+pdftotext", r.stdout, re.M)
            and re.search(r"^\s*ok\s+busca textual", r.stdout, re.M),
            "a verificação passa com pdftotext, FTS5 e config.json")
    confere("tags de exemplo" in r.stdout, "a verificação avisa que as tags ainda são as de exemplo")
    r = subprocess.run([sys.executable, str(SCRIPTS / "verificar.py"), "--curto"],
                       env=dict(env, BIBLIOTECA_CONFIG=str(tmp / "nao_existe.json")), capture_output=True, text=True)
    confere(r.returncode == 1 and "config.json" in r.stdout and "skill preparar" in r.stdout,
            "sem config.json, a verificação curta falha e indica a skill preparar")
    ruim = tmp / "config_ruim.json"
    for conteudo, esperado in (('{"origens": "~/uma/pasta"}', "origens precisa ser uma lista"),
                               ("[1, 2]", "formato de config.json"),
                               ('{"origens": ["/nao/existe/mesmo"]}', "a pasta não existe"),
                               ("{ruim", "formato de config.json")):
        ruim.write_text(conteudo, encoding="utf-8")
        r = subprocess.run([sys.executable, str(SCRIPTS / "verificar.py"), "--curto"],
                           env=dict(env, BIBLIOTECA_CONFIG=str(ruim)), capture_output=True, text=True)
        confere(r.returncode == 1 and not r.stderr and esperado in r.stdout,
                f"config.json com problema ({conteudo}) vira 'falta', sem erro de Python")
    r = subprocess.run([sys.executable, str(SCRIPTS / "verificar.py")],
                       env=dict(env, BIBLIOTECA_TAGS=str(tmp / "sumiu.md")), capture_output=True, text=True)
    confere(not r.stderr and "lista de tags não encontrada" in r.stdout, "tags.md apagado vira 'falta', sem erro de Python")

    print("1. Inventário")
    out = rodar(env, "inventario.py")
    confere("Arquivos novos no índice: 9" in out, "9 arquivos de texto entram no índice (a foto fica de fora)")
    confere("duplicados idênticos: 1" in out, "1 duplicado idêntico")
    confere("sensíveis pelo nome (texto não será lido): 2" in out, "2 sensíveis pelo nome ou pasta")

    print("2. Texto")
    out = rodar(env, "extrair_texto.py")
    confere("com texto: 5" in out and "sem texto: 1" in out, "5 com texto, 1 escaneado sem texto")

    print("3. Busca por trecho antes de classificar")
    out = rodar(env, "buscar.py", "paginas", 'NEAR(barbeiro "king kong", 30)')
    confere("fichamento adorno.docx" in out and "King Kong" in out, "acha o trecho do King Kong no fichamento")
    confere("página 2, parágrafo 2" in out, "no .docx com marcas do Word, indica página e parágrafo")
    achou = re.search(r"ler_paginas\.py (\d+) (\d+)", out)
    confere(bool(achou), "a busca diz como ler o trecho com ler_paginas.py")
    if achou:
        out = rodar(env, "ler_paginas.py", achou.group(1), achou.group(2))
        confere("--- página 2 ---" in out and "King Kong" in out, "ler_paginas mostra a página do Word")
    out = rodar(env, "buscar.py", "paginas", "pseudoindividualizacao")
    confere("página 3, linha 3" in out, "no PDF, indica página e linha")
    out = rodar(env, "buscar.py", "paginas", "heteronomia")
    confere("linha 4" in out and "página" not in out, "no .txt, indica só a linha")
    with sqlite3.connect(str(tmp / "biblioteca.db")) as con:
        sem_data = con.execute("SELECT COUNT(*) FROM documentos WHERE modificado_em IS NULL").fetchone()[0]
    confere(sem_data == 0, "o inventário grava a data de modificação de cada arquivo")

    print("4. Lotes e classificação")
    out = rodar(env, "selecionar_paginas.py", "--lote", "10")
    confere("Documentos para classificar: 5 em 1 lote(s)" in out, "5 documentos em 1 lote")
    lote = json.loads((tmp / "lotes" / "lote_001.json").read_text(encoding="utf-8"))
    artigo = next(d for d in lote if d["nome_original"] in ("Adorno_teoria.pdf", "download (1).pdf"))
    confere(artigo["paginas"][0]["pagina"] == 2, "o seletor pula a capa e começa no Resumo")
    resposta = classificar_lote(tmp / "lotes" / "lote_001.json")
    out = rodar(env, "gravar_classificacao.py", str(resposta))
    confere("Classificações gravadas: 5" in out, "5 classificações gravadas")
    confere("tag-inventada" in out, "tag fora da lista é descartada com aviso")

    print("5. Duplicados por conteúdo")
    out = rodar(env, "duplicados_conteudo.py")
    confere("Duplicatas por conteúdo: 1" in out, "o mesmo artigo de outra fonte vira duplicata pelo DOI")

    print("6. Plano e cópia")
    out = rodar(env, "aplicar.py", "--simular")
    confere(not acervo.exists(), "a simulação não cria nada")
    confere("(confiança 0.90)" in out, "o plano mostra a confiança de cada item")
    aviso = [l for l in out.splitlines() if "Adorno_teoria.pdf é cópia de" in l]
    confere(bool(aviso) and "Artigos/Adorno_1951_" in aviso[0],
            "o plano avisa para onde foi a cópia principal de um duplicado")
    out = rodar(env, "aplicar.py")
    nomes = sorted(str(p.relative_to(acervo)) for p in acervo.rglob("*") if p.is_file())
    print("     acervo:", nomes)
    confere(any(n.startswith("Artigos/Adorno_1951_") for n in nomes), "artigo vai para Artigos/ com o nome novo")
    confere(any(n.startswith("Documentos-de-politica/MS_2023_") for n in nomes), "política vai para Documentos-de-politica/")
    confere(any(n.startswith("Fichamentos/Fichamento_Adorno_1951") for n in nomes), "fichamento vai para Fichamentos/")
    confere("_revisar/scan_001.pdf" in nomes, "escaneado vai para _revisar/ com o nome original")
    confere(any(n.startswith("_revisar/Anonimo_sd_") for n in nomes), "confiança 0,6 vai para _revisar/ com o nome sugerido")
    confere(len(nomes) == 5, "5 arquivos copiados (duplicatas e sensíveis ficam de fora)")
    confere(sorted(str(p) for p in origem.rglob("*")) == antes, "a pasta de origem não mudou")
    out = rodar(env, "inventario.py")
    confere("Arquivos novos no índice: 0" in out, "rodar o inventário de novo depois de aplicar não duplica nada")

    print("7. Busca por documento")
    out = rodar(env, "buscar.py", "documentos", "propaganda fascista")
    confere("Biblioteca/Artigos/" in out, "a busca devolve o caminho novo")
    out = rodar(env, "buscar.py", "documentos", "saude", "--tipo", "politica")
    confere("Plano nacional" in out, "filtro por tipo funciona, sem diferença de acento")

    print("8. Desfazer")
    rodar(env, "desfazer.py")
    restantes = [p for p in acervo.rglob("*") if p.is_file() and "_desfeitos" not in str(p)]
    confere(not restantes, "as cópias vão para _revisar/_desfeitos/")
    rodar(env, "aplicar.py")
    confere((acervo / "Artigos").exists(), "aplicar de novo funciona depois de desfazer")

    print("9. Rotina de entrada")
    (acervo / "_entrada").mkdir(exist_ok=True)
    pdf(acervo / "_entrada" / "artigo_novo.pdf",
        ["Capa", "Resumo\n" + meta("Empresários e democracia no Brasil", "Ana Souza", "2020", "artigo",
                                    tags=("empresariado", "democracia")) + "\n" + LONGO])
    shutil.copy2(origem / "politicas" / "plano_ms.pdf", acervo / "_entrada" / "copia do plano.pdf")
    docx(acervo / "_entrada" / "nota do google docs.docx",
         [meta("Nota sem paginas", "Ana Souza", "2021", "outro"), "Um.", "Aqui esta a palavra ornitorrinco.", LONGO])
    rodar(env, "inventario.py", "--entrada")
    rodar(env, "extrair_texto.py")
    rodar(env, "selecionar_paginas.py")
    resposta = classificar_lote(tmp / "lotes" / "lote_002.json")
    rodar(env, "gravar_classificacao.py", str(resposta))
    out = rodar(env, "buscar.py", "paginas", "ornitorrinco")
    confere("parágrafo 3" in out and "página" not in out, "docx sem marcas do Word indica só o parágrafo")
    achou = re.search(r"ler_paginas\.py (\d+) (\d+)", out)
    if achou:
        out = rodar(env, "ler_paginas.py", achou.group(1), achou.group(2))
        confere("--- parágrafos 1 a 4 ---" in out, "ler_paginas diz que parágrafos o bloco cobre")
    rodar(env, "aplicar.py", "--entrada")
    confere(any(p.name.startswith("Souza_2020_") for p in (acervo / "Artigos").iterdir()), "artigo novo entra em Artigos/")
    confere((acervo / "_revisar" / "copia do plano.pdf").exists(), "cópia de um documento que já existe vai para _revisar/")
    confere(not any((acervo / "_entrada").iterdir()), "_entrada/ fica vazia")

    print("10. Estado")
    out = rodar(env, "estado.py")
    confere("Sensíveis (texto fora do índice):" in out and "participante_03" in out, "estado lista os sensíveis")

    print("11. Arquivo que mudou de lugar fora do bibliotecário")
    artigo_novo = next((acervo / "Artigos").glob("Souza_2020_*"))
    artigo_novo.rename(artigo_novo.with_name("renomeado_a_mao.pdf"))
    out = rodar(env, "inventario.py")
    confere("Caminhos no índice que não existem mais: 1" in out and artigo_novo.name in out,
            "o inventário lista caminhos que sumiram")
    out = rodar(env, "inventario.py", str(acervo))
    confere("Reencontrados em outro lugar: 1" in out and "Arquivos novos no índice: 0" in out,
            "reescanear o acervo acha o arquivo renomeado, sem criar duplicata")
    out = rodar(env, "buscar.py", "documentos", "empresarios")
    confere("renomeado_a_mao.pdf" in out, "a busca devolve o caminho novo do arquivo renomeado")
    out = rodar(env, "inventario.py")
    confere("não existem mais" not in out, "nenhum caminho sumido depois de reencontrar")

    print("12. Funções de apoio")
    sys.path.insert(0, str(SCRIPTS))
    import comum
    confere(comum.parece_sensivel("Revista_Exame_2020.pdf") is None, "'Exame' no nome não marca como sensível")
    confere(comum.parece_sensivel("imposto sobre fortunas.pdf") is None, "'imposto' no nome não marca como sensível")
    confere(comum.parece_sensivel("pessoal/IRPF 2023.pdf") == "irpf", "IRPF continua sensível")
    sem_marca = tmp / "sem_marca.docx"
    docx(sem_marca, ["Um.", "", "Dois.", "Tres."])
    paginas, paginado = comum.paginas_do_arquivo(sem_marca)
    confere(not paginado and paginas[0] == ("Um.\nDois.\nTres.", 1), "docx sem marcas vira parágrafos, sem página")
    uma = tmp / "uma_pagina.docx"
    docx(uma, ["Um.", "Dois."], paginas_app=1)
    confere(comum.paginas_do_arquivo(uma)[1], "docx de uma página salvo pelo Word conta como paginado")
    manual = tmp / "manual.docx"
    docx(manual, ["Um.", MANUAL, "Dois."])
    confere(comum.paginas_docx(manual) == ([["Um."], ["Dois."]], True), "quebra manual de página conta")
    ambas = tmp / "ambas.docx"
    docx(ambas, ["Um.", MANUAL, PAGINA, "Dois."])
    confere(comum.paginas_docx(ambas)[0] == [["Um."], ["Dois."]], "quebra manual e marca do Word não contam duas vezes")
    branca = tmp / "branca.docx"
    docx(branca, ["Um.", PAGINA, "", PAGINA, "Tres."])
    confere(comum.paginas_docx(branca)[0] == [["Um."], [], ["Tres."]], "página sem texto não some da contagem")
    txt = tmp / "com_quebra.txt"
    txt.write_text("um\fainda um\ndois\r\ntres", encoding="utf-8")
    texto, inicio = comum.paginas_do_arquivo(txt)[0][0]
    confere(comum.numero_da_linha(texto, "tres", True) == 3, "no .txt, a numeração de linhas é a do editor")
    pagina = "o fascismo aparece aqui\noutra linha\nmas o fascismo de verdade"
    confere(comum.numero_da_linha(pagina, "fascismo", False, antes="mas o") == 3,
            "a linha é a da ocorrência mostrada no trecho, não a primeira da página")

    print()
    if falhas:
        print(f"{len(falhas)} falha(s). Pasta do teste: {tmp}")
        sys.exit(1)
    shutil.rmtree(tmp)
    print("Tudo certo.")


if __name__ == "__main__":
    main()
