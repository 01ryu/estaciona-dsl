# Conferência do enunciado - revisão 25/11/2026

| Pedido | Evidência na entrega |
| --- | --- |
| DSL executável, compilador ou interpretador | main.py, parkingdsl, dez exemplos .dsl |
| Fundamentação em artigos, mínimo quatro e ao menos um sobre DSL | Seis artigos científicos no artigo; Mernik e van Deursen estão na lista sugerida |
| Comparação com linguagem do domínio | ParkLang: modelagem arquitetural versus execução de operações |
| Justificar DSL versus linguagem geral | Introdução, comparação de três pares de scripts e custo de infraestrutura |
| Gramática e processamento | docs/gramatica.ebnf, lexer, parser e AST |
| Tipos, símbolos e escopo | symbols.py, Binding/Block, 21 métodos de tipos/serviço |
| Testes e avaliação | 81 métodos, modelo independente e benchmark de três tamanhos |
| Artigo IEEE Conference | docs/Artigo.tex usa IEEEtran; PDF compilado |
| Manual e repositório | README, APRESENTACAO, ARQUITETURA e referência GitHub no artigo |
| Demonstração funcional | CLI e Studio local com tokens, AST, mapa e símbolos |

As ressalvas de implementação e documentação foram tratadas. A avaliação continua limitada: três cenários de concisão não são um estudo de usabilidade; benchmark do núcleo não mede a interface nem estacionamentos reais. Tipagem é verificada comando a comando, não em uma passagem estática completa. A avaliação e nota finais pertencem ao professor.
