# Roteiro de apresentação e estudo

## Demonstração sugerida: 8 a 10 minutos

**0:00-1:00 - Problema e objetivo.** Explique que comandos de estacionamento precisam de sintaxe e regras de estado. O objetivo é implementar uma DSL pequena para estudar processamento de linguagens; não se trata de um produto com sensores ou inteligência artificial.

**1:00-2:00 - Sintaxe.** Abra `examples/01_ciclo_completo.dsl`. Mostre as cinco palavras iniciais de comando, as categorias e as placas entre aspas. Explique por que `liberar` e `saida` são operações distintas.

**2:00-3:30 - Pipeline.** Execute:

```console
python main.py examples/01_ciclo_completo.dsl --tokens
python main.py examples/01_ciclo_completo.dsl --ast
```

Mostre um token com posição e um nó Estacionar. Explique que o parser apenas monta a estrutura; ele não modifica vagas. A primeira palavra de cada comando determina qual produção reconhecer.

**3:30-4:30 - Execução válida.** Execute:

```console
python main.py examples/01_ciclo_completo.dsl --trace --verify
python main.py examples/02_ocupacao.dsl
```

No primeiro, mostre sete comandos aceitos, três vagas livres e ninguém presente. No segundo, mostre os três veículos estacionados em categorias distintas. Categoria é atributo da vaga, sem verificação de credencial.

**4:30-6:00 - Erros bem definidos.** Execute:

```console
python main.py examples/04_erro_ocupada.dsl --trace --verify
python main.py examples/05_erro_sintatico.dsl
python main.py examples/06_erro_lexico.dsl
```

No exemplo 04, indique E005 na linha 6, coluna 1, e A1 ainda ocupada pelo primeiro veículo. O segundo veículo entrou, mas não conseguiu estacionar. A liberação posterior não executou. Nos exemplos 05 e 06, nenhuma operação executa: erros estruturais são detectados antes da interpretação.

**6:00-7:00 - Evidências.** Execute `python run_tests.py`. Explique os grupos e abra `results/test_results.json`. Mostre que testes de erros comparam fase, código, posição e estado. O teste de modelo compara sequências com um oráculo independente.

**7:00-8:30 - Resultados e limites.** Mostre as tabelas do relatório, obtidas com cinco aquecimentos e 30 medições por tamanho. Diferencie mediana de p95. Mostre que a comparação de concisão teve a mesma quantidade de linhas; não apresente esse resultado como ganho de legibilidade. Finalize com limitações reais e uma evolução possível, como persistência, que exigiria nova especificação e novos testes.

## Perguntas que você precisa saber responder

**O que torna isso uma DSL?** É uma linguagem externa limitada a um domínio, com vocabulário e regras próprios, e não um conjunto de instruções Python.

**Por que usar Python?** Permite implementar explicitamente lexer, parser, AST e interpretador com biblioteca padrão, reduzindo dependências para execução e avaliação.

**Qual a diferença entre token e nó de AST?** Token representa um elemento reconhecido no texto; nó representa uma operação completa com seus argumentos.

**Por que `premium` causa erro sintático?** A produção `tipo` enumera apenas comum, pcd e idoso. A palavra é um ID léxico válido, mas não é uma categoria válida na posição esperada.

**Qual a diferença entre liberar e sair?** Liberar remove a associação com a vaga; sair remove o veículo do conjunto de presentes. Sair com vaga ocupada é proibido.

**Como impedir duas vagas para o mesmo veículo?** O índice inverso permite verificar em custo médio constante se o veículo já está estacionado, e os invariantes conferem sua correspondência com a ocupação.

**Um erro desfaz o estacionamento inteiro?** Erro léxico ou sintático impede toda execução. Erro semântico preserva o prefixo válido e não aplica o comando que falhou nem os posteriores.

**Todos os testes passarem prova corretude?** Não. É evidência para a bateria executada, reforçada pelo modelo independente. Não é prova formal nem teste em um estacionamento real.

**O parser usa autômato de pilha?** É um parser escrito como funções que reconhecem as produções. Não há bloco aninhado ou expressão recursiva na gramática atual; não há necessidade de pilha crescente para reconhecer esta DSL. A arquitetura em etapas não torna a linguagem necessariamente não regular.

**Por que não medir com `--verify`?** A verificação global percorre o estado depois de cada comando e acrescenta custo de depuração. O benchmark mantém as pré-condições semânticas ativas e confere os invariantes ao final, fora do intervalo medido.

**Há inteligência artificial?** Não. O termo inteligente veio do domínio do artigo. Este protótipo trata a camada lógica de comandos, sem sensores, aprendizado de máquina ou reconhecimento de placas.

## Checklist antes de apresentar

- Extraia o ZIP; não execute arquivos ainda dentro dele.
- Confira Python 3.10+ e rode os testes no computador da apresentação.
- Execute os exemplos válidos e os inválidos; reconheça os erros esperados.
- Saiba localizar lexer.py, parser.py, semantic.py e interpreter.py.
- Leia o relatório e explique o significado dos resultados, sem decorar números.
- Confira o enunciado do professor para nome de arquivos, forma de envio e eventuais requisitos extras.
