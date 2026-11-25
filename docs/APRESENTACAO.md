# Apresentação da versão 2.0

## Roteiro de 8 a 10 minutos

1. Abra ABRIR_INTERFACE.bat. Explique que o navegador é a interface de um interpretador Python local.
2. Selecione 01 · Ciclo completo, carregue e execute. Mostre as vagas livres ao final e a diferença entre liberar e sair.
3. Abra Tokens: palavras e literais viraram unidades com linha e coluna. Em lexer.py, mostre tokenize e as expressões de ID/PLACA.
4. Abra Árvore sintática. Em parser.py, mostre parse, command e operand. O parser reconhece a ordem e cria dataclasses, sem executar.
5. Carregue 08 · Tipos e escopos. Antes de executar, explique que cliente global é ABC1234 e cliente local é DEF5678. Execute: B2 fica ocupada por DEF5678; ABC1234 sai.
6. Abra Símbolos e escopos. Mostre nome, tipo, valor e os aliases do bloco encerrado. Em symbols.py, mostre find (busca interna para externa) e expect (igualdade de tipos).
7. Em interpreter.py, mostre step: resolve referências, valida, altera estado e registra evento. No bloco, finally garante remoção do escopo.
8. Execute 09 · Erro de tipo e 10 · Erro de escopo. Explique T001 e T002. Depois, 04 erro ocupada: E005 preserva o prefixo válido.
9. Mostre run_tests.py e results/test_results.json: 81 métodos passaram. Subcasos não são contados como métodos adicionais.
10. Termine com limites: simulação acadêmica, memória, sem cobrança, sensores, persistência ou estudo com usuários.

## Perguntas de código

**Isso é um compilador?** É um interpretador: constrói uma AST e a percorre para executar. Não gera código de máquina.

**Por que uma DSL?** O vocabulário concentra operações e regras do domínio, eliminando parte da sintaxe geral dos scripts. Há custo de desenvolver a linguagem; não comprovamos maior facilidade de aprendizagem.

**O que é import?** Traz um módulo, classe ou função para o arquivo. dataclass gera a estrutura dos nós; re reconhece padrões; http.server atende a interface; os imports com ponto são do próprio pacote parkingdsl.

**O que é AST?** Uma árvore de objetos que registra a estrutura do programa sem depender de sua formatação. Cada comando tem posição para diagnóstico.

**Tabela de símbolos é igual ao estacionamento?** Não. A tabela resolve nomes, tipos e escopos. O estado guarda vagas, presença e ocupação. Um alias local pode sumir enquanto o carro continua estacionado.

**Tipos são verificados antes de tudo?** Não. O parsing completo vem primeiro; a resolução e checagem de tipos acontecem antes de cada comando durante a interpretação.

**Por que liberar e sair são diferentes?** Liberar remove a associação à vaga; sair remove a presença. Saída de carro ainda estacionado é rejeitada.

**Como impede carro em duas vagas?** occupied associa vaga ao veículo e vehicle_space faz o inverso. As pré-condições recusam conflitos e check_invariants confere as relações.

**Qual biblioteca da interface?** HTML, CSS e JavaScript sem framework. O servidor é http.server da biblioteca padrão do Python. fetch conecta o botão ao interpretador, sem reimplementar a DSL em JavaScript.

**Em quais artigos se baseia?** Mernik et al. e van Deursen et al. fundamentam DSLs. Lin et al. e Geng/Cassandras contextualizam estacionamento. DomainBuilder é comparação de implementação. ParkLang é comparação direta no domínio, voltada à arquitetura, enquanto este projeto executa operações.

**O experimento prova que é melhor?** Não. Há testes, tempos em uma máquina e contagem de três pares de scripts. Não há experimento com usuários. O modelo independente dos testes é diferente do adaptador usado na comparação de concisão.
