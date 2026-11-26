# GUIA DE FALA PARA APRESENTACAO / TREINO
# O service.py faz a ponte entre a interface gráfica e o interpretador.
#
# Quando você clica em Executar, acontece este caminho:
# 1. A interface envia o código para o servidor em gui.py.
# 2. O servidor chama o service.py.
# 3. Ele encaminha o texto ao lexer, que gera os tokens.
# 4. Chama o parser, que monta a árvore sintática.
# 5. Chama o interpretador, que executa os comandos.
# 6. Organiza os resultados para a interface mostrar: vagas, veículos, eventos, tokens, árvore, símbolos e possíveis erros.
#
# Ele também limita o tamanho do código recebido e inicia cada execução com um estacionamento vazio.
#
# PARA FALAR AO PROFESSOR:
# O service.py centraliza o processamento solicitado pela interface. Ele conecta as etapas de análise e execução e organiza os resultados para serem enviados à tela em JSON. Assim, a interface utiliza o mesmo interpretador que usamos no terminal.
#
# PALAVRAS-CHAVE: ponte com a interface -> organiza as etapas -> devolve resultados.

"""Fachada compartilhada da interface; sempre usa o lexer, parser e interpretador reais."""
from dataclasses import asdict, is_dataclass
from .diagnostics import DSLError
from .lexer import tokenize
from .parser import Parser
from .interpreter import Interpreter

MAX_SOURCE_BYTES = 65536
MAX_TOKENS = 6000


# Converte recursivamente nós e sequências em dados JSON para inspecionar a AST.
def ast_json(value):
    if is_dataclass(value):
        return dict(node=type(value).__name__, **{
            name: ast_json(getattr(value, name)) for name in value.__dataclass_fields__})
    if isinstance(value, (tuple, list)):
        return [ast_json(item) for item in value]
    return value


# Ponto de ligação com a interface: recebe apenas texto DSL e cria estado novo.
# Não usa eval/exec e não executa código Python digitado no editor.
def run_source(source):
    if not isinstance(source, str):
        raise ValueError('O código deve ser texto.')
    if len(source.encode('utf-8')) > MAX_SOURCE_BYTES:
        raise ValueError('O painel aceita arquivos de até 64 KiB.')
    source = source.lstrip('\ufeff')
    # Uma máquina por solicitação impede que o estado vaze entre execuções.
    machine = Interpreter(verify=True)
    tokens, ast, error = [], None, None
    try:
        tokens = tokenize(source)
        if len(tokens) > MAX_TOKENS:
            raise ValueError('O painel aceita até 6.000 tokens por execução. Use o terminal para cargas maiores.')
        ast = Parser(tokens).parse()
        machine.run(ast)
    # Uma rejeição da DSL é um resultado esperado, com diagnóstico e estado parcial.
    except DSLError as exc:
        error = exc.as_dict()
    return dict(status='interrompido' if error else 'sucesso', name=machine.name,
                state=machine.state.snapshot(), events=[asdict(e) for e in machine.events],
                accepted_commands=len(machine.events), error=error,
                tokens=[asdict(t) for t in tokens], ast=ast_json(ast),
                symbols=machine.symbols.snapshot())
