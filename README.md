# EstacionamentoDSL

Implementação do projeto **Uma Linguagem Específica de Domínio para Gerenciamento de Estacionamentos Inteligentes**, baseada no artigo fornecido. Equipe indicada no artigo: Ryan Augusto Dias, Luiz Augusto Curtolo de Souza e Bruno Barroso dos Santos; Engenharia de Computação, FHO.

O programa interpreta arquivos `.dsl` em português, constrói uma AST e executa cinco operações com validação de estado, aliases tipados e blocos com escopo léxico. Os resultados experimentais em `results/` são medições realizadas nesta entrega. O relatório PDF explica implementação, evidências e apresentação.

## Interface gráfica

No Windows, abra **ABRIR_INTERFACE.bat** com dois cliques. Ou execute `python gui.py` dentro da pasta do projeto. O navegador abre em `http://127.0.0.1:8765`. Mantenha o terminal aberto; Ctrl+C encerra o servidor. Se a porta estiver ocupada, use `python gui.py --port 8766`.

O Studio é um painel local: editor, exemplos, abrir/salvar `.dsl`, mapa de vagas, veículos, registro, tokens, AST e símbolos. Clique em **Executar** depois de editar. Cada execução começa com estado vazio. Não há banco de dados nem sessão persistente; salve seu código em arquivo. O painel usa o mesmo interpretador Python do terminal, não uma simulação em JavaScript. Limites do painel: 64 KiB de fonte e 6.000 tokens. Para benchmarks maiores, use a CLI.

## Comece por aqui

1. Extraia o ZIP inteiro.
2. Abra um terminal dentro da pasta `EstacionamentoDSL`.
3. Confira `python --version`: requer **Python 3.10 ou superior**.
4. Execute os comandos abaixo. Não precisa instalar pacotes com pip.

```console
python main.py examples/01_ciclo_completo.dsl --trace --verify
python main.py examples/02_ocupacao.dsl --trace
python main.py examples/04_erro_ocupada.dsl --trace --verify
python run_tests.py
```

No Windows, se o executável se chamar `py`, substitua `python` por `py -3`. O arquivo `DEMONSTRAR.bat` executa os principais cenários e os testes, com pausas para acompanhar.

O terceiro exemplo deve terminar com erro **E005, linha 6, coluna 1**. Isso demonstra uma rejeição correta; a vaga A1 permanece com ABC1234, e DEF5678 continua presente sem vaga. O comando `liberar A1` posterior não executa.

## A linguagem em um exemplo

```text
estacionamento Central {
vaga A1 comum
vaga A2 pcd
vaga A3 idoso
entrada "ABC1234"
estacionar "ABC1234" em A1
liberar A1
saida "ABC1234"
}
```

O estado final contém três vagas livres e nenhum veículo presente. `liberar` remove a associação veículo-vaga, mas mantém a presença. `saida` exige liberação anterior.

| Comando | Pré-condição | Efeito |
| --- | --- | --- |
| `vaga A1 comum` | A1 ainda não declarada | Cria vaga livre |
| `entrada "ABC1234"` | Veículo ausente | Registra presença |
| `estacionar "ABC1234" em A1` | Vaga declarada e livre; veículo presente e sem vaga | Associa veículo à vaga |
| `liberar A1` | Vaga ocupada | Libera vaga, mantendo presença |
| `saida "ABC1234"` | Veículo presente, sem vaga | Remove presença |

Categorias aceitas: `comum`, `pcd`, `idoso`. São atributos; esta versão não representa credenciais de condutores. Não há validação de elegibilidade para as categorias.

Identificadores seguem `[A-Za-z][A-Za-z0-9_]*`; palavras reservadas não podem ser nomes. Veículos usam exatamente sete letras maiúsculas ou dígitos entre aspas duplas. É um identificador sintético, não uma validação de placas brasileiras. A linguagem distingue maiúsculas e minúsculas. Aceita espaços, tabulações e quebras de linha; não aceita comentários, ponto e vírgula ou escapes. O programa deve conter pelo menos um comando; blocos locais podem ser vazios.

## Tipos e escopos

```text
estacionamento Campus {
  vaga A1 comum
  definir cliente: veiculo = "ABC1234"
  definir destino: vaga = A1
  entrada cliente
  bloco {
    definir cliente: veiculo = "DEF5678"
    entrada cliente
  }
  estacionar cliente em destino
}
```

`definir` cria um alias imutável, do tipo `veiculo` ou `vaga`. A tabela armazena nome, tipo, valor, escopo e linha. A consulta começa no bloco atual e segue para os externos. Nomes locais podem sombrear nomes externos; sair do bloco restaura a visibilidade anterior, mas não desfaz operações no estacionamento. Referências futuras e duplicidade no mesmo escopo são rejeitadas. Vagas físicas são declaradas somente no escopo global. Limite: 32 blocos aninhados.

A verificação de tipos ocorre sequencialmente, antes de executar cada comando, junto à resolução de nomes. Não é uma passagem estática completa anterior à execução. Erros T001 (tipo), T002 (nome), T003 (duplicidade) e T004 (vaga física local) preservam o prefixo aceito. S004 indica anotação inválida e S005 excesso de aninhamento.

## Opções de execução

```console
python -m parkingdsl examples/01_ciclo_completo.dsl --tokens
python -m parkingdsl examples/01_ciclo_completo.dsl --ast
python -m parkingdsl examples/04_erro_ocupada.dsl --json
python -m parkingdsl examples/03_realocacao.dsl --trace --verify
```

`--tokens` e `--ast` inspecionam etapas e não executam o programa. `--json` produz estado, eventos e erro estruturados. `--trace` mostra o registro dos comandos aceitos; `--verify` verifica invariantes após cada comando. Os diagnósticos usam posições iniciadas em 1. Para erro semântico, a posição é o início do comando; erros léxicos apontam o caractere ou aspa inicial e erros sintáticos apontam o token inesperado. Tabulação conta como um caractere e aparece como um espaço na linha do diagnóstico.

| Código de saída | Significado |
| --- | --- |
| 0 | Execução ou inspeção concluída |
| 1 | Erro da linguagem |
| 2 | Falha de leitura do arquivo ou uso incorreto da CLI |

Arquivo UTF-8, com ou sem BOM; leitura universal de finais de linha. Estado final e JSON ordenam vagas de forma determinística, por ordem lexicográfica: A10 pode preceder A2.

## Arquitetura

```text
arquivo .dsl -> lexer -> tokens -> parser -> AST completa
                                              |
                                              v
                              pré-condições semânticas
                                              |
                                              v
                            interpretador -> estado/eventos
```

| Arquivo | Responsabilidade |
| --- | --- |
| `parkingdsl/lexer.py` | Tokenização manual e posições |
| `parkingdsl/parser.py` | Parser descendente recursivo |
| `parkingdsl/ast_nodes.py` | Nós imutáveis da árvore |
| `parkingdsl/symbols.py` | Tabela de símbolos, tipos e escopos |
| `parkingdsl/service.py` | Resultado estruturado para o painel |
| `gui.py` e `web/` | Servidor HTTP local e interface |
| `parkingdsl/semantic.py` | Estado e validações sem mutação |
| `parkingdsl/interpreter.py` | Caminhamento da AST e efeitos |
| `parkingdsl/diagnostics.py` | Diagnósticos estruturados |
| `parkingdsl/main.py` | Leitura, argumentos e saída |
| `docs/gramatica.ebnf` | Gramática e convenções léxicas |
| `tests/test_project.py` | Testes unitários, integrados e de modelo |
| `benchmark.py` | Geração de carga e medição |
| `compare_concision.py` | Comparação limitada de tamanho de scripts |

A tokenização e o parsing completos acontecem antes da execução. Erros nessas etapas deixam o estado vazio. Cada comando passa por todas as suas pré-condições antes de alterar o estado. Uma falha semântica preserva comandos anteriores e interrompe os posteriores; não há transação global nem rollback integral. A atomicidade aqui se refere a rejeições das regras do domínio, não a falhas de hardware ou falta de memória.

O estado usa `spaces` (V), `present` (P), `occupied` (O) e `vehicle_space` (índice inverso). Mantém `dom(O) ⊆ dom(V)`, `im(O) ⊆ P`, injetividade de O e equivalência do índice inverso. `--verify` confere tudo após cada instrução aceita; fica desabilitado no benchmark para não acrescentar uma varredura global a cada comando.

## Testes e reprodução dos experimentos

```console
python run_tests.py
python benchmark.py
python compare_concision.py
```

Os testes incluem 21 métodos de tipos/escopos/serviço e 10 de HTTP. O primeiro comando grava `results/test_results.json`, com resultados individuais e por família. Os 81 métodos incluem subcasos; esse número não conta cada subcaso como um teste independente. Um teste adicional de modelo usa 10 sementes fixas e 120 tentativas de operação por semente, comparando cada operação válida gerada com um modelo independente baseado em lista e busca linear.

O benchmark padrão realiza cinco aquecimentos e 30 repetições para cada tamanho (10, 100 e 1.000 vagas), sempre com estado novo. Cada vaga recebe um ciclo de cinco comandos; mede lexer, parser, interpretador e total, em milissegundos. A medição exclui geração, leitura, impressão, descarte final dos objetos e conferência global dos invariantes. Inclui criação de estado e registro de eventos dentro da interpretação. O coletor de lixo padrão permanece habilitado. O p95 usa nearest-rank. As repetições brutas e os dados do equipamento ficam em `results/benchmark.json`, com resumo em CSV e SHA-256 da implementação medida.

Execute medições isoladamente, sem rodar testes ao mesmo tempo. Resultados variam com máquina, Python e carga do sistema. Os tempos não são prova de desempenho assintótico nem comparação com sistemas comerciais. `results/concision.json` compara três pares fixos: ciclo completo, ocupação e realocação, conta linhas e caracteres sob formatação fixa e informa o tamanho da infraestrutura separadamente. O suporte Python depende do mesmo núcleo; não é um concorrente independente nem estudo de usabilidade.

## Diagnósticos

| Código | Regra |
| --- | --- |
| L001 | Caractere não permitido |
| L002 | Aspas não fechadas na mesma linha |
| L003 | Identificador de veículo fora do padrão |
| S001 | Token esperado ausente ou trocado |
| S002 | Comando esperado |
| S003 | Categoria inválida |
| E001 | Declaração duplicada |
| E002 | Vaga inexistente ou ainda não declarada |
| E003 | Entrada duplicada |
| E004 | Veículo ausente |
| E005 | Vaga ocupada |
| E006 | Veículo já ocupa outra vaga |
| E007 | Tentativa de liberar vaga livre |
| E008 | Saída sem liberação prévia |

Em `estacionar`, a ordem fixa é: existência da vaga, presença do veículo, disponibilidade da vaga e ausência de outra vaga para o veículo. A categoria `premium`, por exemplo, é erro sintático S003, não erro de ocupação. Em `liberar`, uma vaga inexistente recebe E002 antes da verificação de ocupação; isso refina o diagnóstico sem mudar a pré-condição do artigo.

## Material de estudo e entrega

- `docs/ARQUITETURA.md`: relação com Teoria da Computação, escolhas e complexidade.
- `docs/APRESENTACAO.md`: demonstração e perguntas de defesa.
- `Relatorio_Projeto_EstacionamentoDSL.pdf`: relatório com resultados observados e guia.
- `results/`: evidências reproduzíveis e saídas de demonstração.

O escopo é acadêmico e sequencial, com estado em memória. Cobrança, reservas, sensores, IA, persistência e concorrência ficaram fora da versão proposta no artigo. A implementação não precisa de conexão à internet. A gramática, os exemplos, os testes e os scripts de medição acompanham o código para permitir avaliação e alterações. Use o roteiro para compreender as decisões e praticar a execução antes de apresentar.
