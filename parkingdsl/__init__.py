# GUIA DE FALA PARA APRESENTACAO / TREINO
# Este arquivo apresenta o pacote parkingdsl e disponibiliza seus principais recursos para importação.
# Ele exporta Interpreter, execute e DSLError e informa a versão do pacote.

"""DSL educacional para operações de estacionamento."""
from .interpreter import Interpreter, execute
from .diagnostics import DSLError

__all__ = ['Interpreter', 'execute', 'DSLError']
__version__ = '2.0.0'
