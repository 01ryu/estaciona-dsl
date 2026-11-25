"""Interpretação por caminhamento da AST; cada comando é validado antes da mutação."""
from dataclasses import dataclass
from .ast_nodes import DeclararVaga, Entrada, Estacionar, Liberar, Saida
from .lexer import tokenize
from .parser import Parser
from .semantic import State, validate


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

    def run(self, program):
        # Uma instância representa uma execução. A API rejeita reúso acidental.
        if self.name:
            raise RuntimeError('Crie um Interpreter novo para cada execução.')
        self.name = program.name
        for command in program.commands:
            self.step(command)
        return self.state

    def step(self, command):
        validate(command, self.state)
        state = self.state
        if isinstance(command, DeclararVaga):
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
        pos = command.position
        self.events.append(Event(len(self.events) + 1, type(command).__name__, description, pos.line, pos.column))


def execute(source, *, verify=False):
    program = Parser(tokenize(source)).parse()
    interpreter = Interpreter(verify=verify)
    interpreter.run(program)
    return interpreter
