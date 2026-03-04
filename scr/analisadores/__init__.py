# scr/analisadores/__init__.py
"""
Pacote de analisadores especializados por tipo de gráfico
"""

from .base import AnalisadorBase
from .pizza import AnalisadorPizza
from .barras_verticais import AnalisadorBarrasVerticais
from .barras_horizontais import AnalisadorBarrasHorizontais
from .linhas import AnalisadorLinhas
from .fabrica import FabricaAnalisadores

__all__ = [
    'AnalisadorBase',
    'AnalisadorPizza',
    'AnalisadorBarrasVerticais',
    'AnalisadorBarrasHorizontais',
    'AnalisadorLinhas',
    'FabricaAnalisadores'
]