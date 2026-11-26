# APRESENTACAO: analise lexica | texto -> tokens | palavras reservadas | linha e coluna

"""Analisador léxico manual; posições em caracteres, começando em 1."""
# re é a biblioteca padrão de expressões regulares; dataclass cria classes de dados.
# O ponto em .diagnostics indica um módulo do próprio pacote parkingdsl.
import re
from dataclasses import dataclass
from .diagnostics import DSLError, Position

# Palavras reservadas têm significado na gramática e não podem ser nomes de vagas.
KEYWORDS = frozenset(('estacionamento', 'vaga', 'comum', 'pcd', 'idoso',
                      'entrada', 'estacionar', 'em', 'liberar', 'saida',
                      'definir', 'veiculo', 'bloco'))
# ID começa com letra; PLATE exige sete letras maiúsculas ou dígitos.
# PLATE representa um identificador sintético, não a legislação de placas brasileiras.
ID = re.compile(r'[A-Za-z][A-Za-z0-9_]*')
PLATE = re.compile(r'[A-Z0-9]{7}')


# Um token guarda categoria, texto reconhecido e posição. frozen impede reatribuir campos.
@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    position: Position


# Etapa 1: transforma o texto em tokens. Ainda não cria vagas nem executa comandos.
def tokenize(source: str) -> list[Token]:
    tokens = []
    i, line, column = 0, 1, 1
    # A API aceita os mesmos finais de linha que a leitura universal de arquivos.
    source = source.replace('\r\n', '\n').replace('\r', '\n')
    while i < len(source):
        char = source[i]
        pos = Position(line, column)
        # Espaços são ignorados, mas linha e coluna continuam contando para apontar erros.
        if char in ' \t\n':
            if char == '\n':
                line, column = line + 1, 1
            else:
                column += 1
            i += 1
            continue
        if char in '{}:=':
            tokens.append(Token(char, char, pos))
            i, column = i + 1, column + 1
            continue
        # Aspas iniciam um literal de veículo: procura o fechamento e valida o conteúdo.
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
        # Reconhece o nome completo antes de consultar palavras reservadas.
        # vagaExtra é um ID único, não a palavra vaga seguida de Extra.
        match = ID.match(source, i)
        if match:
            value = match.group()
            tokens.append(Token(value if value in KEYWORDS else 'ID', value, pos))
            i, column = match.end(), column + len(value)
            continue
        raise DSLError('léxico', 'L001', f'Caractere não permitido: {char!r}.', pos)
    # EOF marca o fim da entrada e ajuda o parser a detectar programas incompletos.
    tokens.append(Token('EOF', '', Position(line, column)))
    return tokens
