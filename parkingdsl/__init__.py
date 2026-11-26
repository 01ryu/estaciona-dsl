# APRESENTACAO: pacote parkingdsl | exporta Interpreter, execute e DSLError

"""DSL educacional para operações de estacionamento."""
from .interpreter import Interpreter, execute
from .diagnostics import DSLError

__all__ = ['Interpreter', 'execute', 'DSLError']
__version__ = '2.0.0'
