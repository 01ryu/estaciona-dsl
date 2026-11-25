"""Parser descendente recursivo, sem execução ou alterações de estado."""
from .lexer import Token
from .diagnostics import DSLError
from .ast_nodes import Program, DeclararVaga, Entrada, Estacionar, Liberar, Saida
from .ast_nodes import Reference, Binding, Block


# Etapa 2: consome tokens segundo a gramática e monta a AST (árvore sintática).
# O parser verifica a estrutura; não modifica o estacionamento.
class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens, self.index = tokens, 0
        self.depth = 0

    @property
    def current(self):
        return self.tokens[self.index]

    # Exige um token específico. Se estiver correto, avança; caso contrário, gera S001.
    def expect(self, kind):
        token = self.current
        if token.kind != kind:
            found = token.value or 'fim do arquivo'
            raise DSLError('sintático', 'S001', f'Esperado {kind!r}; encontrado {found!r}.', token.position)
        self.index += 1
        return token

    # Reconhece o programa externo: estacionamento NOME { comandos } e fim de arquivo.
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

    # A primeira palavra determina o tipo do comando; não é preciso tentar e voltar.
    def command(self):
        token = self.current
        # Recursão: um bloco contém outros comandos, inclusive blocos.
        # O limite de profundidade evita consumir a pilha de chamadas sem controle.
        if token.kind == 'bloco':
            self.expect('bloco')
            self.expect('{')
            if self.depth >= 32:
                raise DSLError('sintático', 'S005', 'Limite de 32 blocos aninhados.', token.position)
            self.depth += 1
            commands = []
            while self.current.kind not in ('}', 'EOF'):
                commands.append(self.command())
            self.expect('}')
            self.depth -= 1
            return Block(token.position, tuple(commands))
        # Lê nome, anotação de tipo e valor; a compatibilidade do tipo será checada na execução.
        if token.kind == 'definir':
            self.expect('definir')
            name = self.expect('ID').value
            self.expect(':')
            kind = self.current
            if kind.kind not in ('veiculo', 'vaga'):
                raise DSLError('sintático', 'S004', 'Tipo deve ser veiculo ou vaga.', kind.position)
            self.expect(kind.kind)
            self.expect('=')
            return Binding(token.position, name, kind.value, self.operand())
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
            return Entrada(token.position, self.operand())
        if token.kind == 'estacionar':
            self.expect('estacionar')
            plate = self.operand()
            self.expect('em')
            return Estacionar(token.position, plate, self.expect('ID').value)
        if token.kind == 'liberar':
            self.expect('liberar')
            return Liberar(token.position, self.expect('ID').value)
        if token.kind == 'saida':
            self.expect('saida')
            return Saida(token.position, self.operand())
        raise DSLError('sintático', 'S002', 'Esperado comando de estacionamento, definir ou bloco.', token.position)

    # Distingue um literal entre aspas de uma referência a um nome da tabela de símbolos.
    def operand(self):
        if self.current.kind == 'ID':
            return Reference(self.expect('ID').value)
        return self.expect('PLACA').value
