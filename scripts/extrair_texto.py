"""Extrai o texto de cada documento, página por página, para o índice.

Pula sensíveis e duplicados. PDF com pdftotext, uma página por vez. .docx pelas marcas de página
que o Word grava; sem elas, em blocos de parágrafos. .txt e .md em blocos de linhas.
Uso: python3 scripts/extrair_texto.py
"""
from comum import carregar_config, conectar, paginas_do_arquivo

MINIMO_CARACTERES = 200  # abaixo disso o documento é tratado como sem texto (escaneado)


def main():
    cfg = carregar_config()
    con = conectar(cfg)
    docs = con.execute(
        """SELECT d.id, d.caminho FROM documentos d
           WHERE d.situacao NOT IN ('sensivel', 'duplicata')
             AND NOT EXISTS (SELECT 1 FROM paginas p WHERE p.documento_id = d.id)""").fetchall()
    com_texto = sem_texto = 0
    for d in docs:
        paginas, paginado = paginas_do_arquivo(d["caminho"])
        total = sum(len(texto.strip()) for texto, _ in paginas)
        for n, (texto, linha_inicial) in enumerate(paginas, start=1):
            con.execute("INSERT INTO paginas (documento_id, pagina, texto, linha_inicial) VALUES (?, ?, ?, ?)",
                        (d["id"], n, texto, linha_inicial))
        tem = 1 if total >= MINIMO_CARACTERES else 0
        con.execute("UPDATE documentos SET paginas_total = ?, tem_texto = ?, paginado = ? WHERE id = ?",
                    (len(paginas), tem, 1 if paginado else 0, d["id"]))
        if tem:
            com_texto += 1
        else:
            sem_texto += 1
            print(f"Sem texto (escaneado?): {d['caminho']}")
        con.commit()
    print(f"Documentos processados: {len(docs)}  com texto: {com_texto}  sem texto: {sem_texto}")


if __name__ == "__main__":
    main()
