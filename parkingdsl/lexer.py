"""Analisador léxico manual; posições em caracteres, começando em 1."""
import re
from dataclasses import dataclass
from .diagnostics import DSLError, Position

KEYWORDS = frozenset(('estacionamento', 'vaga', 'comum', 'pcd', 'idoso',
                      'entrada', 'estacionar', 'em', 'liberar', 'saida'))
ID = re.compile(r'[A-Za-z][A-Za-z0-9_]*')
PLATE = re.compile(r'[A-Z0-9]{7}')


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    position: Position


def tokenize(source: str) -> list[Token]:
    tokens = []
    i, line, column = 0, 1, 1
    # A API aceita os mesmos finais de linha que a leitura universal de arquivos.
    source = source.replace('\r\n', '\n').replace('\r', '\n')
    while i < len(source):
        char = source[i]
        pos = Position(line, column)
        if char in ' \t\n':
            if char == '\n':
                line, column = line + 1, 1
            else:
                column += 1
            i += 1
            continue
        if char in '{}':
            tokens.append(Token(char, char, pos))
            i, column = i + 1, column + 1
            continue
        if char == '"':
            end = i + 1
            while end < len(source) and source[end] not in '"\n':
                end += 1
            if end == len(source) or source[end] == '\n':
                raise DSLError('léxico', 'L002', 'Literal sem aspas de fechamento na mesma linha.', pos)
            value = source[i + 1:end]
            if not PLATE.fullmatch(value):
                raise DSLError('léxico', 'L003', 'Veículo deve ter exatamente 7 letras maiúsculas ou dígitos.', pos)
            tokens.append(Token('PLACA', value, pos))
            column += end - i + 1
            i = end + 1
            continue
        match = ID.match(source, i)
        if match:
            value = match.group()
            tokens.append(Token(value if value in KEYWORDS else 'ID', value, pos))
            i, column = match.end(), column + len(value)
            continue
        raise DSLError('léxico', 'L001', f'Caractere não permitido: {char!r}.', pos)
    tokens.append(Token('EOF', '', Position(line, column)))
    return tokens
