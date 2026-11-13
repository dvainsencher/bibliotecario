# Gabarito da amostra

`exemplo/` é uma pasta bagunçada de propósito, para treinar sem usar os seus arquivos. São 191 arquivos: artigos, fichamento, notícias, receitas, imagens, planilhas, documentos pessoais falsos, duplicados e lixo, espalhados por pastas com nomes que não ajudam. A origem de cada arquivo está em [FONTES.md](FONTES.md). Este gabarito fica fora de `exemplo/` para não entrar na indexação: senão, a busca acharia as respostas aqui.

Não ponha arquivos seus nesta pasta. Ela vai para o git. Os seus ficam em outra pasta de origem, indicada no `config.json`.

## Buscas com resposta conhecida

Use estas buscas para saber se a sua solução funciona. Os locais são os que a skill buscar mostra.

| Pergunta | Resposta |
|---|---|
| Em que fichamento eu anotei que, para as elites, o Brasil era uma nação sem povo? | `Documentos/leituras/fich questao racial.docx`, página 2, parágrafo 1. A citação original está em `misc/A questao racial na politica brasileira os ultimos quinze an.pdf`, página 4, linha 12 (Guimarães, 2001). |
| O que eu tenho sobre a política externa do governo Dilma? | `Receitas/por revisar/Balanco da politica externa de Dilma Rousseff perspectivas f.pdf` (Saraiva). Está numa pasta de receitas. |
| Quantas cópias eu tenho de "Brazilian Political Institutions: an Inconclusive Debate"? | Duas, idênticas, em `misc/`. |
| Onde está o artigo sobre raça e política de assistência social na psicologia? | `Contratos/por revisar/abr/IMG_20241116_4816.pdf` (Oliveira, 2019). Pegadinha: veja abaixo. |
| Tem documento pessoal misturado com os artigos? | Sim. Por exemplo, `Artigos/docx/dez/Apolice de seguro.pdf` e `Artigos/ciência política/final/Nota fiscal de servico 2017.pdf`. |

## O que o teste costuma revelar

- **Sensível pelo nome da pasta erra para os dois lados.** Quatro artigos da SciELO estão dentro de `Contratos/` e são marcados como sensíveis só por isso: o texto deles não entra na indexação, e o artigo de raça e assistência social some da busca. Já a apólice de seguro e a nota fiscal passam, porque o nome não tem nenhum termo da lista. Quem acerta esses casos é a classificação pelo conteúdo, e a sua revisão da lista de sensíveis.
- **Nem todo tipo de arquivo entra.** A indexação lê PDF, .docx, .txt e .md. Notícias salvas em HTML, planilhas, apresentações e imagens ficam de fora (81 arquivos). Se isso importa para você, é um pedido de melhoria.
- **Duplicado nem sempre é idêntico.** A amostra tem cópias idênticas (`(1)`, `- Copia`) e cópias truncadas, que têm outro conteúdo e não aparecem como duplicadas pelo hash.
- **Nome e pasta mentem.** Artigo em `Receitas/`, partitura em `Artigos/`, `IMG_...pdf` que é artigo. Por isso a classificação usa o conteúdo.
