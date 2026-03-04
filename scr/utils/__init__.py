# scr/utils/__init__.py
"""
Pacote de utilitários
"""

from .imagem import (
    carregar_imagem,
    preprocessar_para_ocr,
    detectar_contorno_principal,
    detectar_circulo_principal,
    detectar_barras_por_cor,
    extrair_regioes_proximas,
    calcular_proporcao_linear
)
from .visualizacao import GeradorGraficos
from .config import get_tesseract_path, get_config

__all__ = [
    'carregar_imagem',
    'preprocessar_para_ocr',
    'detectar_contorno_principal',
    'detectar_circulo_principal',
    'detectar_barras_por_cor',
    'extrair_regioes_proximas',
    'calcular_proporcao_linear',
    'GeradorGraficos',
    'get_tesseract_path',
    'get_config'
]