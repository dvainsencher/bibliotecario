# Bibliotecário

> Projeto de exemplo, feito para um treinamento sobre o uso de IA na pesquisa. Serve para aprender e adaptar, não como ferramenta pronta. Use numa cópia dos seus arquivos e confira os resultados.

Organiza uma biblioteca pessoal de arquivos e cria uma busca por documento e por trecho, com o Claude Code e um índice SQLite.

## Primeiro uso

1. Baixe o projeto: `git clone https://github.com/dvainsencher/bibliotecario.git ~/projetos-ia/bibliotecario`. Evite as pastas Documentos e Mesa: o iCloud costuma sincronizá-las, e o índice não se dá bem com pasta sincronizada.
2. Copie a configuração: `cp config.exemplo.json config.json` e ajuste os caminhos.
3. Escreva as suas tags em `.claude/skills/organizar/tags.md`.
4. Troque SEU NOME no `CLAUDE.md`.
5. Abra a pasta na aba Code do app do Claude e peça: "Use a skill organizar no modo lote".

## O que tem aqui

- `CLAUDE.md`: regras fixas que o Claude Code lê ao abrir a pasta.
- `config.exemplo.json`: modelo dos caminhos (o seu `config.json` não vai para o git).
- `esquema.sql`: estrutura do índice.
- `.claude/skills/organizar` e `.claude/skills/buscar`: as skills.
- `.claude/agents/classificador.md`: subagente que classifica lotes com o Haiku.
- `scripts/`: programas em Python 3, só com a biblioteca padrão.
- `testes/`: teste completo com uma amostra falsa.
- `notas/`: suas anotações.

## Requisitos

macOS ou Linux, Python 3.9 ou mais novo, `pdftotext` (no Mac: `brew install poppler`) e SQLite com FTS5 (já vem no Mac).

## Testar

`python3 testes/rodar_teste.py` cria uma amostra falsa numa pasta temporária, roda o fluxo inteiro e confere o resultado. Não toca nos seus arquivos.
