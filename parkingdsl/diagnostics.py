# APRESENTACAO: erros da DSL | fase, codigo e mensagem | linha e coluna

from dataclasses import dataclass


@dataclass(frozen=True)
# Posições começam em 1 para corresponder às linhas vistas pelo usuário.
class Position:
    line: int
    column: int


# Exceção da linguagem: separa fase, código, mensagem e localização.
# Permite à CLI e ao painel mostrar o mesmo diagnóstico de formas diferentes.
class DSLError(Exception):
    def __init__(self, phase: str, code: str, message: str, position: Position):
        self.phase, self.code = phase, code
        self.message, self.position = message, position
        super().__init__(str(self))

    def __str__(self):
        return (f'Erro {self.phase} [{self.code}] na linha {self.position.line}, '
                f'coluna {self.position.column}: {self.message}')

    # Dicionário serializável em JSON, usado no painel e nos testes.
    def as_dict(self):
        return dict(phase=self.phase, code=self.code, message=self.message,
                    line=self.position.line, column=self.position.column)
