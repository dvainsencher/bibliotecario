---
name: preparar
description: Prepara o bibliotecário para o primeiro uso e resolve problemas de instalação. Use quando eu pedir para preparar, instalar ou configurar, ou quando a verificação ao abrir a pasta mostrar algo faltando.
---
Você ajuda uma pessoa que não é da área técnica a deixar o bibliotecário pronto. Vá um passo por vez, em frases curtas, e confirme cada passo antes do próximo.

1. Rode python3 scripts/verificar.py e mostre o resultado em poucas linhas.
2. Resolva cada item que falta, nesta ordem:
   - Python antigo ou ausente: peça para a pessoa abrir o Terminal e colar xcode-select --install. Espere ela dizer que terminou.
   - pdftotext: se o comando brew existir, rode brew install poppler (peça licença antes). Se não existir, explique que o Homebrew é um instalador de programas, peça para ela abrir https://brew.sh, copiar o comando da página no Terminal e avisar quando terminar. Depois rode brew install poppler.
   - config.json: copie config.exemplo.json para config.json. Pergunte quais pastas têm os arquivos bagunçados (origens) e onde quer a biblioteca organizada (acervo). Sugira ~/Documents/Amostra para começar e ~/Documents/Biblioteca para o acervo. Grave os caminhos e confira que as pastas de origem existem.
3. Cuide dos avisos:
   - Tags: pergunte os temas da pesquisa e proponha de 15 a 30 tags curtas, em minúsculas, sem acentos. Mostre a lista, ajuste com a pessoa e grave em .claude/skills/organizar/tags.md, mantendo o cabeçalho e apagando a linha "Lista de exemplo".
   - Nome: pergunte o nome e troque SEU NOME no CLAUDE.md.
4. Rode python3 testes/rodar_teste.py. Ele usa uma amostra falsa e não toca nos arquivos dela. Se terminar com "Tudo certo.", diga que está pronto.
5. Termine dizendo o próximo passo: pedir "use a skill organizar no modo lote".

Regras
- Nunca apague nem mova arquivos da pessoa. Esta skill só instala programas e edita config.json, tags.md e CLAUDE.md.
- Não use sudo. Se algo pedir senha, é a pessoa que digita no Terminal, nunca você.
- Se um comando falhar duas vezes, pare, mostre a mensagem de erro e sugira mandar uma captura de tela no grupo.
