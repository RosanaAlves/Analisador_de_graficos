# scr/processamento/__init__.py
"""
Pacote de processamento de imagens e OCR
"""

from .carregador import CarregadorGrafico
from .ocr_engine_adaptado import OCREngineAdaptado

__all__ = ['CarregadorGrafico', 'OCREngineAdaptado']