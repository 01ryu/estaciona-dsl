"""Tabela de símbolos tipados, resolução léxica e escopos de aliases imutáveis."""
from dataclasses import asdict, dataclass
from .ast_nodes import Reference
from .diagnostics import DSLError


@dataclass(frozen=True)
class Symbol:
    name: str
    type: str
    value: str
    scope: str
    line: int


class SymbolTable:
    def __init__(self):
        self.frames = [{}]
        self.scopes = ['global']
        self.declarations = []
        self.counter = 0

    def push(self):
        self.counter += 1
        self.frames.append({})
        self.scopes.append(f'{self.scopes[-1]}/bloco{self.counter}')

    def pop(self):
        self.frames.pop()
        self.scopes.pop()

    def find(self, name):
        for frame in reversed(self.frames):
            if name in frame:
                return frame[name]
        return None

    def require(self, name, position):
        symbol = self.find(name)
        if symbol is None:
            raise DSLError('semântico', 'T002', f'Símbolo {name} não declarado neste escopo.', position)
        return symbol

    def available(self, name, position):
        if name in self.frames[-1]:
            raise DSLError('semântico', 'T003', f'Símbolo {name} já declarado neste escopo.', position)

    def declare(self, name, kind, value, position):
        self.available(name, position)
        symbol = Symbol(name, kind, value, self.scopes[-1], position.line)
        self.frames[-1][name] = symbol
        self.declarations.append(symbol)
        return symbol

    def expression(self, value, position):
        if isinstance(value, Reference):
            symbol = self.require(value.name, position)
            return symbol.type, symbol.value
        return 'veiculo', value

    def expect(self, actual, expected, position):
        if actual != expected:
            raise DSLError('semântico', 'T001', f'Tipo incompatível: esperado {expected}; recebido {actual}.', position)

    def vehicle(self, operand, position):
        kind, value = self.expression(operand, position)
        self.expect(kind, 'veiculo', position)
        return value

    def space(self, name, position):
        symbol = self.find(name)
        if symbol is None:
            # A regra de domínio mantém E002 para a vaga física inexistente.
            return name
        self.expect(symbol.type, 'vaga', position)
        return symbol.value

    def snapshot(self):
        active = {id(s) for frame in self.frames for s in frame.values()}
        return [dict(asdict(s), active=id(s) in active) for s in self.declarations]
