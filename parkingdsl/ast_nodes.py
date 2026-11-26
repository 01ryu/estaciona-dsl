# GUIA DE FALA PARA APRESENTACAO / TREINO
# Aqui definimos os objetos que representam os comandos da linguagem na árvore sintática.
# Um objeto de entrada guarda o veículo; um de estacionar guarda o veículo e a vaga.
# Usamos dataclasses para definir essas estruturas de dados, incluindo posições para apontar erros.
# A árvore representa o programa; quem aplica seus efeitos é o interpretador.

"""Árvore sintática abstrata com posição do início de cada comando."""
# dataclass gera inicialização e comparação dos objetos da árvore.
# Estes objetos descrevem comandos; seus efeitos são aplicados pelo interpretador.
from dataclasses import dataclass
from .diagnostics import Position


@dataclass(frozen=True)
# Um nome usado no lugar de um literal, como cliente em entrada cliente.
class Reference:
    name: str


@dataclass(frozen=True)
# Representa definir cliente: veiculo = "ABC1234".
class Binding:
    position: Position
    name: str
    declared_type: str
    value: str | Reference


@dataclass(frozen=True)
# Agrupa comandos cujo ambiente de nomes será local.
class Block:
    position: Position
    commands: tuple


@dataclass(frozen=True)
# Declara uma vaga física com identificador e categoria.
class DeclararVaga:
    position: Position
    space: str
    category: str


@dataclass(frozen=True)
# Registra a intenção de tornar um veículo presente.
class Entrada:
    position: Position
    plate: str | Reference


@dataclass(frozen=True)
# Associa um veículo a uma vaga; ambos ainda serão validados.
class Estacionar:
    position: Position
    plate: str | Reference
    space: str


@dataclass(frozen=True)
# Remove a ocupação da vaga sem retirar a presença do veículo.
class Liberar:
    position: Position
    space: str


@dataclass(frozen=True)
# Retira a presença de um veículo depois de liberar sua vaga.
class Saida:
    position: Position
    plate: str | Reference


# A união de tipos descreve todos os nós aceitos como comando.
Command = DeclararVaga | Entrada | Estacionar | Liberar | Saida | Binding | Block


@dataclass(frozen=True)
# Raiz da árvore: nome do estacionamento e sequência de comandos.
class Program:
    name: str
    commands: tuple[Command, ...]

