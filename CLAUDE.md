Este projeto (bibliotecário) organiza e indexa a biblioteca de pesquisa de SEU NOME.

Caminhos: em config.json (pastas de origem, acervo organizado e índice). Copie de config.exemplo.json na primeira vez.
Índice: caminho em config.json (padrão indice/biblioteca.db), com o esquema de esquema.sql.
Skills: organizar (montar o índice e organizar) e buscar (achar documentos e trechos).

Regras
- Nunca apague arquivos. Nunca altere as pastas de origem.
- Antes de copiar, renomear ou mover, mostre o plano e espere eu dizer "pode aplicar".
- Registre toda cópia, renomeação ou movimento na tabela movimentos (os scripts já fazem isso).
- Não abra arquivos marcados como sensíveis.
- Não leia PDFs inteiros: consulte o índice.
- Scripts em Python 3, só com a biblioteca padrão, em scripts/. Texto de PDF com pdftotext; .docx é lido pelo próprio Python.
- Responda em português, com frases curtas.
