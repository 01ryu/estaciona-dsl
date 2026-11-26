# APRESENTACAO: executa a AST | resolve nomes | valida comandos | altera estado | eventos

"""Interpretação por caminhamento da AST; cada comando é validado antes da mutação."""
# replace cria uma cópia de um nó imutável com os nomes resolvidos, preservando a AST.
from dataclasses import dataclass, replace
from .ast_nodes import DeclararVaga, Entrada, Estacionar, Liberar, Saida
from .lexer import tokenize
from .parser import Parser
from .semantic import State, validate
from .ast_nodes import Binding, Block
from .symbols import SymbolTable
from .diagnostics import DSLError


@dataclass(frozen=True)
# Cada evento registra um comando aceito, sua descrição e a posição no arquivo.
class Event:
    number: int
    operation: str
    description: str
    line: int
    column: int


# Etapa 3: percorre a AST, resolve nomes, confere regras e aplica efeitos no estado.
class Interpreter:
    def __init__(self, verify=False):
        self.state = State()
        self.events = []
        self.name = ''
        self.verify = verify
        self.symbols = SymbolTable()

    def run(self, program):
        # Uma instância representa uma execução. A API rejeita reúso acidental.
        if self.name:
            raise RuntimeError('Crie um Interpreter novo para cada execução.')
        self.name = program.name
        for command in program.commands:
            self.step(command)
        return self.state

    # Executa um nó. Tipos e referências são verificados antes de cada operação,
    # não em uma passagem estática completa anterior à execução.
    def step(self, command):
        if isinstance(command, Block):
            self.symbols.push()
            try:
                for child in command.commands:
                    self.step(child)
            # Mesmo quando um comando falha, o escopo local deve ser removido.
            # Isso não reverte operações anteriores aceitas no estacionamento.
            finally:
                self.symbols.pop()
            return
        # Uma definição cria um alias imutável; não registra entrada nem ocupa vaga.
        if isinstance(command, Binding):
            self.symbols.available(command.name, command.position)
            kind, value = self.symbols.expression(command.value, command.position)
            self.symbols.expect(kind, command.declared_type, command.position)
            self.symbols.declare(command.name, kind, value, command.position)
            self.record(command, f'{command.name}: {kind} = {value} ({self.symbols.scopes[-1]}).')
            return
        if isinstance(command, DeclararVaga):
            if len(self.symbols.frames) != 1:
                raise DSLError('semântico', 'T004', 'Declare vagas físicas no escopo global; use aliases locais nos blocos.', command.position)
        if isinstance(command, (Entrada, Estacionar, Saida)):
            command = replace(command, plate=self.symbols.vehicle(command.plate, command.position))
        if isinstance(command, (Estacionar, Liberar)):
            command = replace(command, space=self.symbols.space(command.space, command.position))
        # Barreira de validação: falhas previstas interrompem antes da mutação deste comando.
        validate(command, self.state)
        state = self.state
        if isinstance(command, DeclararVaga):
            self.symbols.available(command.space, command.position)
            self.symbols.declare(command.space, 'vaga', command.space, command.position)
            state.spaces[command.space] = command.category
            description = f'Vaga {command.space} declarada ({command.category}).'
        elif isinstance(command, Entrada):
            state.present.add(command.plate)
            description = f'Entrada de {command.plate}.'
        # Atualiza os dois sentidos da relação: vaga -> veículo e veículo -> vaga.
        elif isinstance(command, Estacionar):
            state.occupied[command.space] = command.plate
            state.vehicle_space[command.plate] = command.space
            description = f'{command.plate} estacionado em {command.space}.'
        # Liberação desfaz a associação nos dois índices, mas mantém o veículo presente.
        elif isinstance(command, Liberar):
            plate = state.occupied.pop(command.space)
            del state.vehicle_space[plate]
            description = f'Vaga {command.space} liberada; {plate} permanece presente.'
        elif isinstance(command, Saida):
            state.present.remove(command.plate)
            description = f'Saída de {command.plate}.'
        if self.verify:
            state.check_invariants()
        self.record(command, description)

    # Somente comandos aceitos entram no registro; o comando rejeitado não gera evento.
    def record(self, command, description):
        pos = command.position
        self.events.append(Event(len(self.events) + 1, type(command).__name__, description, pos.line, pos.column))


# Atalho de programação que reúne texto -> tokens -> AST -> execução.
def execute(source, *, verify=False):
    program = Parser(tokenize(source)).parse()
    interpreter = Interpreter(verify=verify)
    interpreter.run(program)
    return interpreter
