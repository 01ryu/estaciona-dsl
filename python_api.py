"""Suporte explícito para o cenário equivalente em Python; usa as mesmas regras."""
from parkingdsl.ast_nodes import DeclararVaga, Entrada, Estacionar, Liberar, Saida
from parkingdsl.diagnostics import Position
from parkingdsl.interpreter import Interpreter


class Parking:
    def __init__(self, name):
        self.machine = Interpreter(verify=True)
        self.machine.name = name

    def declare(self, space, category):
        if category not in ('comum', 'pcd', 'idoso'):
            raise ValueError('Categoria inválida')
        self.machine.step(DeclararVaga(Position(1, 1), space, category))

    def enter(self, plate):
        self.machine.step(Entrada(Position(1, 1), plate))

    def park(self, plate, space):
        self.machine.step(Estacionar(Position(1, 1), plate, space))

    def release(self, space):
        self.machine.step(Liberar(Position(1, 1), space))

    def leave(self, plate):
        self.machine.step(Saida(Position(1, 1), plate))
