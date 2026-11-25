# Ordem sugerida para explicar o código

1. main.py: inicia a versão de terminal.
2. parkingdsl/main.py: lê o arquivo e organiza o pipeline.
3. parkingdsl/lexer.py: transforma texto em tokens com posição.
4. parkingdsl/parser.py e ast_nodes.py: verificam a estrutura e constroem a AST.
5. parkingdsl/symbols.py: resolve nomes, tipos e escopos.
6. parkingdsl/semantic.py: define estado e pré-condições.
7. parkingdsl/interpreter.py: valida, aplica efeitos e registra eventos.
8. parkingdsl/diagnostics.py: organiza mensagens de erro.
9. gui.py e parkingdsl/service.py: ligam o navegador ao mesmo interpretador.
10. web/index.html, app.css e app.js: estrutura, aparência e interação.
11. run_tests.py, benchmark.py e compare_concision.py: testes e avaliação.

Os comentários explicam responsabilidades, bibliotecas e decisões sem alterar o comportamento.

## Rastreabilidade dos experimentos

O artigo e os resultados de benchmark/concisão correspondem à versão funcional do commit 31496d7c2236518b1cf2cffb818e52afa2bb60b9, anterior aos comentários didáticos. Seu hash e contagem de linhas físicas são mantidos como evidências daquela medição. A versão comentada tem mais linhas e outro hash de arquivos, mas preserva a árvore de sintaxe Python executável, conferida nesta revisão. SHA256SUMS.txt identifica os arquivos atuais. Comentários não constituem uma nova medição de desempenho.
