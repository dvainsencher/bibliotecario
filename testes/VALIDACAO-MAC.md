# Validar o bibliotecário em outras versões de Mac

Não precisa de um Mac. O GitHub Actions tem Macs de verdade (Apple Silicon e Intel) e roda `python3 testes/rodar_teste.py` neles.

## Rodar o mesmo teste para uma versão específica

1. No GitHub, abra a aba Actions, workflow "Teste", botão "Run workflow".
2. Preencha:
   - runner: a máquina mais próxima da do participante (tabela abaixo).
   - python: a versão do Python do participante (por exemplo 3.9 ou 3.12). Vazio usa o Python da máquina.
3. O job "Personalizado" mostra macOS, arquitetura, Python, pdftotext, SQLite com FTS5 e o resultado. Deve terminar com "Tudo certo."

Pela linha de comando:

```
gh workflow run teste.yml -f runner=macos-15-intel -f python=3.9
gh run list --workflow teste.yml --limit 3
```

## Qual runner usar

| Mac do participante | runner |
|---|---|
| Apple Silicon (M1 ou mais novo), macOS 14 | macos-14 |
| Apple Silicon, macOS 15 | macos-15 |
| Apple Silicon, macOS 26 | macos-26 |
| Intel, qualquer macOS | macos-15-intel |
| Linux (referência) | ubuntu-latest |

Limites: o GitHub só oferece versões recentes de macOS. Um Mac Intel com macOS 13 ou 14 é testado em macOS 15 Intel: a arquitetura é a mesma, o sistema não. Quem tiver macOS 12 ou mais velho não roda o Claude Code (precisa do macOS 13).

## Estado da validação

- Feito: teste passa em macos-latest (Apple Silicon), macos-15-intel e ubuntu-latest, com o Python que vem na máquina (3.14 e 3.15) e poppler do Homebrew.
- Feito: teste passa em macos-15-intel (macOS 15.7, x86_64) com Python 3.9.25, o mais antigo suportado.
- Pendente: versões reais dos Macs e do Python dos participantes. Quando chegarem, rodar o passo acima com cada combinação e registrar o resultado na tabela.

| Participante | macOS | Chip | Python | runner usado | Resultado |
|---|---|---|---|---|---|
| Hugo | | | | | |
| Stephanie | | | | | |
| Ana Flavia | | | | | |
