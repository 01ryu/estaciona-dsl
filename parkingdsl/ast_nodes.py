"""Árvore sintática abstrata com posição do início de cada comando."""
from dataclasses import dataclass
from .diagnostics import Position


@dataclass(frozen=True)
class Reference:
    name: str


@dataclass(frozen=True)
class Binding:
    position: Position
    name: str
    declared_type: str
    value: str | Reference


@dataclass(frozen=True)
class Block:
    position: Position
    commands: tuple


@dataclass(frozen=True)
class DeclararVaga:
    position: Position
    space: str
    category: str


@dataclass(frozen=True)
class Entrada:
    position: Position
    plate: str | Reference


@dataclass(frozen=True)
class Estacionar:
    position: Position
    plate: str | Reference
    space: str


@dataclass(frozen=True)
class Liberar:
    position: Position
    space: str


@dataclass(frozen=True)
class Saida:
    position: Position
    plate: str | Reference


Command = DeclararVaga | Entrada | Estacionar | Liberar | Saida | Binding | Block


@dataclass(frozen=True)
class Program:
    name: str
    commands: tuple[Command, ...]

