# Como este projeto foi construído

Este guia refaz a construção do bibliotecário do ponto de vista de quem pesquisa. Começa com um pedido ingênuo, passa pela busca e chega ao projeto completo. Cada etapa traz o pedido, o que observar na resposta e o que aquela etapa virou no projeto.

Os pedidos são pontos de partida. Escreva o seu com as suas palavras, compare com o daqui e ajuste. Quem conhece o problema é você.

Para treinar, use a amostra `exemplo/`, que vem no projeto. As respostas certas estão em [gabarito/](gabarito/README.md).

## Antes de começar: o Claude Code no Terminal

1. Instale, se ainda não tiver: `curl -fsSL https://claude.ai/install.sh | bash`. Feche e abra o Terminal e confira com `claude --version`.
2. Crie uma pasta vazia para o seu projeto e entre nela: `mkdir -p ~/projetos-ia/minha-biblioteca` e `cd ~/projetos-ia/minha-biblioteca`.
3. Copie a amostra para lá, para trabalhar sobre uma cópia: `cp -R ~/projetos-ia/bibliotecario/exemplo ~/projetos-ia/minha-biblioteca/amostra` (depois de baixar o bibliotecário com `git clone`, como no README).
4. Abra o Claude Code: `claude`. Na primeira vez, ele abre o navegador para você entrar na conta. Entre com a conta do Pro, não com uma chave de API.
5. Para não ter cobrança surpresa: no claude.ai, Settings, Usage, deixe desligada a opção "Usage credits". Desligada, quando o limite do Pro acaba, o Claude Code espera o limite renovar em vez de cobrar.

O básico dentro do Claude Code:

| Para | Faça |
|---|---|
| Entrar no modo Plan (ele planeja e não mexe em nada) | Shift+Tab até aparecer "plan mode" |
| Interromper o que ele está fazendo | Esc |
| Começar uma conversa nova | `/clear` |
| Ver quanto do limite do plano você usou | `/usage` |
| Sair | `/exit` |

## Etapa 0: a abordagem ingênua

Pedidos:

```
Organize os arquivos da pasta amostra.
```

```
Onde está o fichamento em que eu anotei que, para as elites, o Brasil era
uma nação sem povo?
```

O que observar:

- Ele mostrou um plano antes de mexer? Moveu ou renomeou sem perguntar?
- Inventou autor, título ou página?
- Abriu os arquivos inteiros para responder? Funciona com 40 arquivos. Com 2.000, gasta o limite do plano e erra mais.
- Semana que vem, ele começa do zero: nada ficou registrado.

O que virou no projeto: nada. Esta etapa mostra por que as outras existem. De longe, "organiza minha pasta" parece um pedido só. São vários problemas juntos.

## Etapa 1: configurar o projeto

O `CLAUDE.md` é um arquivo de texto que o Claude Code lê toda vez que abre a pasta. Ali ficam quem você é, o que o projeto faz, onde estão as coisas e as regras que não mudam. Sem ele, cada conversa começa do zero.

Pedido:

```
Esta pasta vai ser um projeto para organizar e buscar na minha biblioteca
de pesquisa. Sou [sua área e o tema da sua pesquisa]. Escreva um CLAUDE.md
curto com: quem eu sou, o que o projeto faz, onde estão os arquivos (a
pasta amostra, por enquanto) e as regras que valem sempre: nunca apagar
arquivos, nunca alterar a pasta de origem, mostrar o plano antes de mudar
qualquer arquivo e não ler documentos pessoais (RG, extratos, contratos,
entrevistas). Responda em português, com frases curtas.
```

O que observar: leia o `CLAUDE.md` que ele escreveu. Corrija o que não for você. Ele vai obedecer a esse arquivo.

O que virou no projeto: o [CLAUDE.md](CLAUDE.md) do bibliotecário.

## Etapa 2: definir o problema

Descreva o problema, não a solução. O pedido não fala em banco de dados, hash nem script: a técnica é ele quem propõe. Você define o que entra, o que sai e como saber que funcionou, e confere o plano.

Use o modo Plan (Shift+Tab).

Pedido:

```
Tenho uma amostra de uns 190 arquivos da minha biblioteca na pasta amostra:
PDFs, .docx, notícias, planilhas e fichamentos, com nomes ruins
(IMG_2024.pdf, download.pdf), cópias repetidas e coisas fora do lugar.
Perco tempo para achar um documento e, mais ainda, um trecho que lembro
mais ou menos.

Quero:
1. achar um documento por autor, ano ou tema;
2. achar um trecho que lembro, com o arquivo e a página, para citar;
3. depois, ter nomes e pastas padronizados.

Regras: não mexa na pasta original e não apague nada. Antes de mudar
qualquer arquivo, mostre o plano. Documentos pessoais não podem ser lidos.
Vou usar isso muitas vezes e o acervo vai crescer para milhares de arquivos.

Como vou saber que funcionou: estas buscas, com a resposta que já sei:
- o fichamento em que as elites viam o Brasil como uma nação sem povo;
- o trecho de Adorno em que o fascista é uma mistura de barbeiro de bairro
  e King Kong;
- o que tenho sobre a política externa do governo Dilma;
- quantas cópias tenho de "Brazilian Political Institutions".

Não faça nada ainda. Pergunte o que não ficou claro e proponha como
resolveria, em passos, dizendo onde usaria IA e onde usaria um programa.
```

O que observar:

- O plano deve ler cada arquivo uma vez com um programa, guardar o texto com a página e buscar nesse texto guardado. Se ele propuser abrir os arquivos a cada pergunta, pergunte: "como isso funciona com 2.000 arquivos?".
- Ele separou o trabalho mecânico (listar, achar duplicados, extrair texto) do semântico (entender do que trata cada documento)?
- Responda às perguntas dele. Elas mostram o que faltou no seu pedido.

Por que indexar num banco e não buscar direto nos arquivos:

- **O contexto ficaria gigante.** Buscar nos arquivos obriga a ler tudo de novo a cada pergunta. Gasta o limite e o modelo presta menos atenção em texto longo.
- **A busca seria menos precisa.** PDF, .docx, HTML e texto se leem de jeitos diferentes. Buscas como "estas duas palavras perto uma da outra" ou "variações da frase que lembro" pedem um texto já extraído e organizado.
- **Ler uma vez, consultar muitas.** Na indexação, cada arquivo é lido uma vez, e o texto fica guardado com a página. Cada busca consulta só isso, rápido e sempre igual.

O que virou no projeto: [esquema.sql](esquema.sql), com as tabelas de documentos, páginas e movimentos.

## Etapa 3: indexação

Pedido, depois de aprovar o plano:

```
Pode fazer a indexação. No fim, me diga quantos arquivos encontrou, quantos
são cópias idênticas, quantos não têm texto e quantos você marcou como
pessoais, sem abrir esses.
```

O que observar: confira os números com o [gabarito](gabarito/README.md). Olhe a lista de pessoais. Tem artigo marcado como pessoal só por estar numa pasta chamada `Contratos`? Tem apólice de seguro que passou? O teste mostra o erro antes de você confiar.

O que virou no projeto: `scripts/inventario.py` (lista, hash, duplicados idênticos, sensíveis pelo nome) e `scripts/extrair_texto.py` (texto por página).

## Etapa 4: busca

Pedido:

```
Busque na indexação, sem abrir os arquivos: em que fichamento eu anotei
que, para as elites, o Brasil era uma nação sem povo? Quero o arquivo, a
página e o trecho literal. Tente variações da frase. Se não achar, diga
que não achou e o que tentou.
```

Repita com as outras buscas do gabarito.

O que observar:

- O trecho veio literal? Abra o arquivo e confira a página de pelo menos um resultado. A IA inventa com a mesma confiança com que acerta.
- A frase lembrada nem sempre é a do texto. Você lembra "barbeiro de bairro", e a tradução diz "barbeiro suburbano". A busca exata não acha nada. Por isso o pedido manda tentar variações, como as duas palavras mais raras perto uma da outra.
- Quantas buscas acertaram? Anote o placar.
- Quando errou, foi porque o arquivo não estava na indexação (sensível, tipo não lido) ou porque a busca não achou?

O que virou no projeto: `scripts/buscar.py` e `scripts/ler_paginas.py`.

## Etapa 5: virar ferramenta

Pedido:

```
Essa busca funcionou. Transforme numa skill buscar, com o passo a passo
que usamos e as regras: sempre consultar a indexação, nunca abrir o
arquivo inteiro, até 4 tentativas com variações, responder com caminho,
página e trecho literal, e dizer quando não achar.
```

O que observar: leia o `SKILL.md` que ele criou. Na próxima conversa, peça só "busque o trecho da nação sem povo" e veja se ele usa a skill.

Esta é a virada: a IA deixa de ser só assistente e vira criadora de ferramenta. O programa que ela escreveu roda de graça e sempre igual. A IA entra só no que pede julgamento. Gasta menos e você reutiliza.

O que virou no projeto: [.claude/skills/buscar/SKILL.md](.claude/skills/buscar/SKILL.md).

## Etapa 6: classificar e dar nome

Pedido (modo Plan):

```
Agora quero nomes e pastas padronizados. Para cada documento que não é
pessoal nem cópia, descubra pelo conteúdo o tipo, o autor, o ano, o título
e de 1 a 6 temas de uma lista que vou te dar. O nome segue o padrão
Sobrenome_Ano_Titulo-curto, sem acentos. As pastas são poucas, por tipo de
documento (artigos, fichamentos, notícias...), e os temas viram etiquetas,
não pastas. O que for duvidoso vai para uma pasta _revisar. Use um modelo
barato, em lotes, lendo só as primeiras páginas úteis de cada documento.
Me mostre o plano de nomes e pastas antes de copiar qualquer coisa, e só
copie quando eu disser "pode aplicar". Registre cada cópia.
```

O que observar:

- Leia 10 nomes propostos antes de aprovar. Confira a lista de `_revisar`.
- Os pessoais que passaram na etapa 3 foram pegos agora, pelo conteúdo?

Por que pastas por tipo e não por tema: toda pasta é uma classificação hierárquica, e cada arquivo mora num lugar só. Um artigo sobre política de saúde da mulher é de saúde, de gênero e de políticas públicas ao mesmo tempo. Qualquer pasta que você escolher esconde o arquivo de quem procura pelo outro tema, e as fronteiras mudam com a pesquisa. O tipo do documento tem uma resposta só e não muda. Tema vira etiqueta, que pode ser várias, e a busca resolve o resto.

O que virou no projeto: `scripts/selecionar_paginas.py`, o subagente [classificador](.claude/agents/classificador.md) (Haiku), `scripts/gravar_classificacao.py`, `scripts/duplicados_conteudo.py`, `scripts/aplicar.py` e `scripts/desfazer.py`.

## Etapa 7: rotina de entrada e preparação

Perguntas que aparecem depois da primeira organização:

- **Como incluo um arquivo novo?** Pela pasta `_entrada/` do acervo, com a mesma rotina da etapa 6, só para os arquivos novos.
- **Como apago um arquivo?** Evite. Arquivo duvidoso vai para `_revisar/`. Se errou uma rodada, desfaça.
- **E se eu mexer pelo Finder?** A indexação deixa de bater com as pastas. Uma verificação ao abrir a pasta compara as duas e avisa.

Pedido:

```
Transforme a organização numa skill organizar com dois modos: lote, para o
acervo existente, e entrada, para arquivos novos na pasta _entrada. Crie
também uma verificação que rode toda vez que eu abrir esta pasta e me avise
se falta algo instalado ou se alguém mexeu no acervo por fora.
```

O que virou no projeto: [.claude/skills/organizar/SKILL.md](.claude/skills/organizar/SKILL.md), `scripts/verificar.py`, o hook em [.claude/settings.json](.claude/settings.json) e a skill [preparar](.claude/skills/preparar/SKILL.md), que deixa o projeto pronto para quem baixa pela primeira vez.

## Resumo: de cada etapa para o projeto

| Etapa | Virou |
|---|---|
| 1. Configurar o projeto | `CLAUDE.md` |
| 2. Definir o problema | `esquema.sql` |
| 3. Indexação | `inventario.py`, `extrair_texto.py` |
| 4. Busca | `buscar.py`, `ler_paginas.py` |
| 5. Virar ferramenta | skill buscar |
| 6. Classificar e dar nome | `selecionar_paginas.py`, subagente classificador, `gravar_classificacao.py`, `duplicados_conteudo.py`, `aplicar.py`, `desfazer.py` |
| 7. Entrada e preparação | skill organizar, `verificar.py`, hook, skill preparar |

O projeto pronto não saiu de um pedido. Saiu de vários, cada um testado contra respostas conhecidas e corrigido antes do próximo.
