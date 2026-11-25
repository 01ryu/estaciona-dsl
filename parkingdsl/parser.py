"""Parser descendente recursivo, sem execução ou alterações de estado."""
from .lexer import Token
from .diagnostics import DSLError
from .ast_nodes import Program, DeclararVaga, Entrada, Estacionar, Liberar, Saida


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens, self.index = tokens, 0

    @property
    def current(self):
        return self.tokens[self.index]

    def expect(self, kind):
        token = self.current
        if token.kind != kind:
            found = token.value or 'fim do arquivo'
            raise DSLError('sintático', 'S001', f'Esperado {kind!r}; encontrado {found!r}.', token.position)
        self.index += 1
        return token

    def parse(self):
        self.expect('estacionamento')
        name = self.expect('ID').value
        self.expect('{')
        commands = [self.command()]  # A gramática exige pelo menos um comando.
        while self.current.kind not in ('}', 'EOF'):
            commands.append(self.command())
        self.expect('}')
        self.expect('EOF')
        return Program(name, tuple(commands))

    def command(self):
        token = self.current
        if token.kind == 'vaga':
            self.expect('vaga')
            space = self.expect('ID').value
            category = self.current
            if category.kind not in ('comum', 'pcd', 'idoso'):
                raise DSLError('sintático', 'S003', 'Categoria deve ser comum, pcd ou idoso.', category.position)
            self.expect(category.kind)
            return DeclararVaga(token.position, space, category.value)
        if token.kind == 'entrada':
            self.expect('entrada')
            return Entrada(token.position, self.expect('PLACA').value)
        if token.kind == 'estacionar':
            self.expect('estacionar')
            plate = self.expect('PLACA').value
            self.expect('em')
            return Estacionar(token.position, plate, self.expect('ID').value)
        if token.kind == 'liberar':
            self.expect('liberar')
            return Liberar(token.position, self.expect('ID').value)
        if token.kind == 'saida':
            self.expect('saida')
            return Saida(token.position, self.expect('PLACA').value)
        raise DSLError('sintático', 'S002', 'Esperado um comando: vaga, entrada, estacionar, liberar ou saida.', token.position)
