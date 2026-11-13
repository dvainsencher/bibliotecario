# Bibliotecário

> Projeto de exemplo, feito para um treinamento sobre o uso de IA na pesquisa. Serve para aprender e adaptar, não como ferramenta pronta. Use numa cópia dos seus arquivos e confira os resultados.

Organiza uma biblioteca pessoal de arquivos e cria uma busca por documento e por trecho, com o Claude Code e uma indexação em SQLite.

## Primeiro uso

Tudo acontece no Terminal (no Mac: Aplicativos, Utilitários, Terminal).

1. Instale o Claude Code, se ainda não tiver: `curl -fsSL https://claude.ai/install.sh | bash`. Feche e abra o Terminal e confira com `claude --version`. É preciso o plano Pro ou maior.
2. Baixe o projeto: `git clone https://github.com/dvainsencher/bibliotecario.git ~/projetos-ia/bibliotecario`. Evite as pastas Documentos e Mesa: o iCloud costuma sincronizá-las, e a indexação não se dá bem com pasta sincronizada.
3. Entre na pasta e abra o Claude Code: `cd ~/projetos-ia/bibliotecario` e depois `claude`. Na primeira vez, ele abre o navegador para você entrar na sua conta.
4. Peça: "Use a skill preparar". Ela confere o que falta (Python, pdftotext, configuração), ajuda a instalar, cria o `config.json`, escreve as suas tags e roda o teste.
5. Depois peça: "Use a skill organizar no modo lote".

Para começar, a configuração usa a amostra de treino `exemplo/` como origem e organiza o acervo em `biblioteca/`, dentro do projeto. Quando for usar com os seus arquivos, troque as origens pelas suas pastas e, se quiser, ponha o acervo em outro lugar (fora de pasta sincronizada). Caminho relativo no `config.json` vale a partir da pasta do projeto.

Se preferir fazer a preparação à mão: copie `config.exemplo.json` para `config.json` e ajuste os caminhos, escreva as suas tags em `.claude/skills/organizar/tags.md` (apagando a linha "Lista de exemplo"), troque SEU NOME no `CLAUDE.md` e rode `python3 scripts/verificar.py`.

## Como foi construído

[CONSTRUCAO.md](CONSTRUCAO.md) refaz a construção deste projeto do ponto de vista de quem pesquisa: começa por um pedido ingênuo, passa pela busca e chega ao projeto completo, com os pedidos de cada etapa. Para treinar, use a amostra `exemplo/` e confira o resultado em [gabarito/](gabarito/README.md).

## O acervo é do bibliotecário

Depois da primeira organização, o bibliotecário é dono da pasta do acervo. Não mova, não renomeie e não apague nada nela pelo Finder: peça ao Claude Code. Arquivo novo entra pela pasta `_entrada/` do acervo, e a skill organizar no modo entrada cuida dele.

Se algo mudar por fora, o índice deixa de bater com as pastas. Ao abrir o projeto, a verificação avisa "acervo alterado fora do bibliotecário" e sugere a skill organizar, que reencontra o que foi renomeado ou movido, classifica o que chegou sem registro e confere o resto.

## O que tem aqui

- `CLAUDE.md`: regras fixas que o Claude Code lê ao abrir a pasta.
- `CONSTRUCAO.md`: como o projeto foi construído, etapa por etapa.
- `config.exemplo.json`: modelo dos caminhos (o seu `config.json` não vai para o git).
- `esquema.sql`: estrutura do índice.
- `.claude/skills/preparar`, `.claude/skills/organizar` e `.claude/skills/buscar`: as skills.
- `.claude/settings.json`: hook que roda `scripts/verificar.py --curto` ao abrir a pasta e avisa o que falta.
- `.claude/agents/classificador.md`: subagente que classifica lotes com o Haiku.
- `scripts/`: programas em Python 3, só com a biblioteca padrão.
- `exemplo/`: amostra bagunçada para treinar. Não ponha arquivos seus aqui: esta pasta vai para o git.
- `gabarito/`: o que é cada arquivo da amostra, de onde veio e as buscas com resposta conhecida. Fica fora de `exemplo/` para não entrar na indexação.
- `testes/`: teste completo com uma amostra falsa.
- `notas/`: suas anotações.

## Requisitos

macOS ou Linux, Python 3.9 ou mais novo, `pdftotext` (no Mac: `brew install poppler`) e SQLite com FTS5 (já vem no Mac).

## Testar

`python3 testes/rodar_teste.py` cria uma amostra falsa numa pasta temporária, roda o fluxo inteiro e confere o resultado. Não toca nos seus arquivos.

## Licença

MIT (veja o arquivo LICENSE). Pode usar, copiar e adaptar, mantendo o aviso de licença.
