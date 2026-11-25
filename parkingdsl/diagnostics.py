from dataclasses import dataclass


@dataclass(frozen=True)
class Position:
    line: int
    column: int


class DSLError(Exception):
    def __init__(self, phase: str, code: str, message: str, position: Position):
        self.phase, self.code = phase, code
        self.message, self.position = message, position
        super().__init__(str(self))

    def __str__(self):
        return (f'Erro {self.phase} [{self.code}] na linha {self.position.line}, '
                f'coluna {self.position.column}: {self.message}')

    def as_dict(self):
        return dict(phase=self.phase, code=self.code, message=self.message,
                    line=self.position.line, column=self.position.column)
