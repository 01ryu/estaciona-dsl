# Decisões técnicas e relação com a disciplina

## 1. Linguagem e reconhecimento

A DSL é externa: sua sintaxe não é Python e os arquivos usam extensão `.dsl`. É interpretada por caminhamento de uma árvore sintática abstrata. Não gera código de máquina, bytecode ou código Python. Um erro de domínio não é confundido com falha de reconhecimento da gramática.

As regras léxicas para identificadores e veículos são regulares. Um autômato conceitual para ID começa em q0, exige uma letra ASCII para ir a q1 e permanece em q1 ao ler letra, dígito ou sublinhado. q1 é aceitador. Após reconhecer o lexema inteiro, o lexer consulta o conjunto de palavras reservadas, impedindo que `vagaExtra` se torne `vaga` seguido de `Extra`.

Para PLACA, o autômato exige uma aspa de abertura, exatamente sete transições com caracteres de `[A-Z0-9]` e uma aspa final. O código faz uma varredura limitada ao literal e usa uma expressão regular com correspondência completa. Símbolos fora das classes aceitas, quantidade incorreta e aspas sem fechamento têm diagnósticos distintos.

O lexer não precisa de pilha. A gramática agora admite blocos recursivos: o parser usa sua pilha de chamadas para reconhecer o aninhamento. A EBNF abstrata permite profundidade arbitrária; a implementação limita a 32 blocos para controlar recursos. Não se deve confundir a gramática abstrata com a linguagem efetivamente limitada pela implementação.

## 2. Por que não há retrocesso no parser

Os conjuntos FIRST das alternativas de comando são disjuntos:

| Produção | FIRST |
| --- | --- |
| declaracao | vaga |
| entrada | entrada |
| estacionar | estacionar |
| liberar | liberar |
| saida | saida |
| definicao | definir |
| bloco | bloco |

Cada comando é escolhido com um token de antecipação. Depois de cada comando, o parser aceita outro início de comando ou `}`; EOF antes de `}` sinaliza ausência do delimitador. A repetição usa laço, e não recursão proporcional à quantidade de comandos. A pilha cresce com a profundidade dos blocos, não com o número de comandos irmãos.

## 3. Tipos, símbolos e semântica dinâmica

`symbols.py` implementa uma pilha de dicionários. Cada símbolo contém nome, tipo (`veiculo` ou `vaga`), valor, caminho de escopo e linha de declaração. A busca vai do escopo interno ao externo. `definir` exige tipo do valor igual à anotação. Operações de presença exigem `veiculo`; destinos exigem `vaga`. Declarações físicas alimentam a tabela global. Aliases são imutáveis e não aceitam referências futuras.

O bloco empilha um ambiente e o remove em `finally`, inclusive se ocorrer erro. Uma declaração local pode sombrear uma global; ao sair, a global volta a ser visível. O registro de declarações permanece disponível para a interface, com marcação de escopos encerrados. O estado físico do estacionamento é global e não é revertido ao sair do bloco. Validações são feitas antes de cada comando, não em uma passagem estática integral.


Reconhecer `estacionar "ABC1234" em A1` não prova que A1 foi declarada nem que o veículo está presente. Essas propriedades dependem da história de execução. Declarações não são antecipadas: uma vaga declarada depois de um uso não torna válido o uso anterior.

Representação: V = categorias por vaga; P = conjunto de veículos presentes; O = veículo por vaga ocupada; I = vaga por veículo. Os invariantes são domínio de O contido em V, imagem de O contida em P, O injetiva e I igual à relação inversa de O. A política de saída exige liberação prévia. Não há liberação implícita.

`semantic.validate` apenas consulta o estado. `Interpreter.step` só aplica efeitos quando a validação retorna sem erro; os dois sentidos da ocupação são atualizados no mesmo comando. O programa não expõe operações simultâneas. A garantia de atomicidade é relativa às falhas semânticas previstas, não a qualquer interrupção externa do processo.

## 4. Fluxo de erros

| Fase | Momento | Estado observável |
| --- | --- | --- |
| Léxica | Antes da AST | Vazio |
| Sintática | Antes da interpretação | Vazio |
| Semântica | Antes da mutação do comando | Prefixo válido preservado |

Mensagens preservam fase, código, linha e coluna. O registro de eventos contém somente operações aceitas. O arquivo de exemplo 04 deve resultar em E005 (6:1), quatro comandos aceitos e A1 ocupada por ABC1234. A liberação na linha seguinte não executa. No exemplo 05, a ausência de `em` é S001 (4:22), e nem mesmo a declaração anterior é executada.

## 5. Custo e limitações das estimativas

Se N é o número de caracteres, T de tokens e C de comandos, a tokenização faz uma varredura O(N), e o parsing tem custo O(T). Cada literal é percorrido até seu delimitador, sem buscas repetidas pelo restante do arquivo. Cada pré-condição e atualização tem custo médio O(1) para chaves curtas em dicionários/conjuntos Python; identificadores arbitrariamente longos também têm custo de leitura e hashing proporcional ao tamanho. Não se afirma pior caso constante para tabelas hash.

Com `--verify` desativado, a interpretação tem custo médio O(C), mais o armazenamento das strings e eventos. O programa mantém tokens, AST, estado e eventos em memória: o consumo cresce com a entrada e o número de comandos. O código não faz streaming. A saída ordenada acrescenta O(V log V + P log P) e está fora do benchmark. `--verify` percorre o estado após cada comando e pode elevar o custo agregado para O(C*(V+P)); é uma opção de depuração, explicitamente separada da medição normal.

## 6. Matriz de rastreabilidade com o artigo

| Compromisso do artigo | Implementação | Evidência |
| --- | --- | --- |
| Léxico manual e posições | lexer.py | LexicalTests |
| Parser descendente e AST completa | parser.py e ast_nodes.py | SyntaxTests e IntegrationTests |
| Cinco comandos | interpreter.py | ValidTests e SemanticTests |
| Categorias enumeradas | parser.py | test_invalid_category_is_syntax_error |
| Índice inverso | semantic.py | test_vehicle_in_two_spaces e test_inverse_index_detection |
| Preservação do estado parcial | interpreter.py | test_run_stops_and_preserves_partial_state |
| Nenhum efeito por erro estrutural | main.py | test_syntax_failure_has_zero_effects e test_lexical_failure_has_zero_effects |
| Diagnóstico ordenado | semantic.py | test_diagnostic_priority |
| Ensaios 10/100/1000, 5+30 | benchmark.py | benchmark.json e benchmark.csv |
| Concisão com infraestrutura explícita | compare_concision.py | concision.json |

O identificador SHA-256 de revisão mede os módulos de produção e o script de benchmark. Os testes e a documentação não integram esse hash; o manifesto SHA256SUMS.txt identifica os arquivos de toda a entrega. O artigo revisado inclui a comparação com ParkLang (DOI 10.5220/0014399800004058), uma linguagem de modelagem arquitetural de estacionamentos, distinta desta DSL executável.

## 7. Interface e separação de responsabilidades

`gui.py` usa HTTP da biblioteca padrão, escuta apenas em 127.0.0.1 e serve três arquivos locais. `web/app.js` envia o texto para `/api/run`. `service.run_source` cria um interpretador por chamada e retorna tokens, AST, símbolos, eventos e estado. Nenhum código Python do editor é executado. O frontend usa `textContent` para exibir valores e erros. Há limites de entrada, validação de Host/Origin e caminhos estáticos permitidos. Não há autenticação, hospedagem pública ou persistência.

A interface conserva o resultado anterior enquanto você edita e indica que uma nova execução é necessária. O benchmark mede somente o núcleo, sem HTTP, DOM ou verificação global por comando; os tempos não representam latência do painel.
