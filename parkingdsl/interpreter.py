"""Interpretação por caminhamento da AST; cada comando é validado antes da mutação."""
from dataclasses import dataclass, replace
from .ast_nodes import DeclararVaga, Entrada, Estacionar, Liberar, Saida
from .lexer import tokenize
from .parser import Parser
from .semantic import State, validate
from .ast_nodes import Binding, Block
from .symbols import SymbolTable
from .diagnostics import DSLError


@dataclass(frozen=True)
class Event:
    number: int
    operation: str
    description: str
    line: int
    column: int


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

    def step(self, command):
        if isinstance(command, Block):
            self.symbols.push()
            try:
                for child in command.commands:
                    self.step(child)
            finally:
                self.symbols.pop()
            return
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
        elif isinstance(command, Estacionar):
            state.occupied[command.space] = command.plate
            state.vehicle_space[command.plate] = command.space
            description = f'{command.plate} estacionado em {command.space}.'
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

    def record(self, command, description):
        pos = command.position
        self.events.append(Event(len(self.events) + 1, type(command).__name__, description, pos.line, pos.column))


def execute(source, *, verify=False):
    program = Parser(tokenize(source)).parse()
    interpreter = Interpreter(verify=verify)
    interpreter.run(program)
    return interpreter
