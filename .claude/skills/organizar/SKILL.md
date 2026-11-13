---
name: organizar
description: Organiza a biblioteca de pesquisa. Use para montar o índice e organizar o acervo existente (modo lote) ou para processar arquivos novos na pasta _entrada/ (modo entrada).
---
Você organiza a minha biblioteca de pesquisa. Os caminhos estão em config.json. Os scripts estão em scripts/ e fazem o trabalho mecânico. Você só decide o que é semântico e conversa comigo.

Regras que valem sempre
- Nunca apague arquivos. Nunca altere as pastas de origem.
- Não abra PDFs nem documentos diretamente. Tudo o que você precisa ler está no índice ou nos lotes.
- Antes de copiar ou mover, rode o aplicar.py com --simular, mostre o plano e espere eu dizer "pode aplicar".
- Documentos sensíveis ficam fora: não leia, não classifique, só liste.

Modo lote (acervo existente)
1. python3 scripts/inventario.py
2. python3 scripts/extrair_texto.py
3. python3 scripts/selecionar_paginas.py --lote 10
4. Para cada arquivo indice/lotes/lote_NNN.json criado agora, chame o subagente classificador com o caminho do lote. Ele escreve lote_NNN_resposta.jsonl.
5. python3 scripts/gravar_classificacao.py indice/lotes/lote_NNN_resposta.jsonl --modelo haiku
6. python3 scripts/duplicados_conteudo.py --simular. Se houver pares "parecidos", leia os dois resumos no índice e me diga se são o mesmo documento. Depois rode sem --simular.
7. python3 scripts/aplicar.py --simular e me mostre o plano resumido: quantos vão para cada pasta, quantos para _revisar/ e por quê, quantos duplicados e sensíveis. Mostre 10 nomes novos de exemplo, com a confiança. Para os duplicados, repita o aviso do plano: só uma cópia entra no acervo, e diga para onde foi a principal.
8. Só depois de "pode aplicar": python3 scripts/aplicar.py
9. Termine com python3 scripts/estado.py e um resumo em poucas linhas.

Modo entrada (arquivos novos em _entrada/)
Os mesmos passos, com inventario.py --entrada no passo 1 e aplicar.py --entrada nos passos 7 e 8. No modo entrada os arquivos são movidos, não copiados. Duplicado vai para _revisar/.

Para desfazer a última rodada: python3 scripts/desfazer.py --simular, mostre, e depois sem --simular.

Para lotes muito grandes, processe no máximo 10 lotes por vez e pergunte antes de continuar. O limite de uso do plano é por período.
