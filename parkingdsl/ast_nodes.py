"""Árvore sintática abstrata com posição do início de cada comando."""
from dataclasses import dataclass
from .diagnostics import Position


@dataclass(frozen=True)
class DeclararVaga:
    position: Position
    space: str
    category: str


@dataclass(frozen=True)
class Entrada:
    position: Position
    plate: str


@dataclass(frozen=True)
class Estacionar:
    position: Position
    plate: str
    space: str


@dataclass(frozen=True)
class Liberar:
    position: Position
    space: str


@dataclass(frozen=True)
class Saida:
    position: Position
    plate: str


Command = DeclararVaga | Entrada | Estacionar | Liberar | Saida


@dataclass(frozen=True)
class Program:
    name: str
    commands: tuple[Command, ...]
