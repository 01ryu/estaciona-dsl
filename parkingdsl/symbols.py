"""Tabela de símbolos tipados, resolução léxica e escopos de aliases imutáveis."""
from dataclasses import asdict, dataclass
from .ast_nodes import Reference
from .diagnostics import DSLError


@dataclass(frozen=True)
# Ficha de um nome: tipo, valor, ambiente e linha em que foi declarado.
class Symbol:
    name: str
    type: str
    value: str
    scope: str
    line: int


# Tabela de símbolos é diferente do estado físico das vagas.
# Ela responde: o que este nome significa e em qual escopo pode ser usado?
class SymbolTable:
    def __init__(self):
        # A primeira tabela é global; as próximas representam blocos locais empilhados.
        self.frames = [{}]
        self.scopes = ['global']
        self.declarations = []
        self.counter = 0

    # Entrar em um bloco cria um ambiente vazio com um identificador próprio.
    def push(self):
        self.counter += 1
        self.frames.append({})
        self.scopes.append(f'{self.scopes[-1]}/bloco{self.counter}')

    # Sair do bloco remove seus nomes visíveis, mas não desfaz entradas e ocupações.
    def pop(self):
        self.frames.pop()
        self.scopes.pop()

    # Busca de dentro para fora: um nome local pode sombrear o mesmo nome global.
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

    # Só proíbe duplicidade no ambiente atual; permite sombreamento em outro bloco.
    def available(self, name, position):
        if name in self.frames[-1]:
            raise DSLError('semântico', 'T003', f'Símbolo {name} já declarado neste escopo.', position)

    # Registra o símbolo no ambiente atual e guarda histórico para a interface.
    def declare(self, name, kind, value, position):
        self.available(name, position)
        symbol = Symbol(name, kind, value, self.scopes[-1], position.line)
        self.frames[-1][name] = symbol
        self.declarations.append(symbol)
        return symbol

    # Uma referência exige consulta; um literal já reconhecido pelo parser é veiculo.
    def expression(self, value, position):
        if isinstance(value, Reference):
            symbol = self.require(value.name, position)
            return symbol.type, symbol.value
        return 'veiculo', value

    # Checagem de tipos: não converte automaticamente vaga para veiculo, ou vice-versa.
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

    # Converte declarações em dados para a interface e indica quais escopos ainda existem.
    def snapshot(self):
        active = {id(s) for frame in self.frames for s in frame.values()}
        return [dict(asdict(s), active=id(s) in active) for s in self.declarations]
