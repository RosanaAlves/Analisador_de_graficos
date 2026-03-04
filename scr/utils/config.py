# scr/utils/config.py
"""
Configurações centrais do sistema
"""

import os


def get_tesseract_path() -> str:
    """
    Retorna o caminho do executável do Tesseract OCR.
    """
    # Caminhos comuns por sistema operacional
    caminhos = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        '/usr/bin/tesseract',
        '/usr/local/bin/tesseract'
    ]
    
    for caminho in caminhos:
        if os.path.exists(caminho):
            return caminho
    
    # Se não encontrar, retorna None (vai usar o padrão do sistema)
    return None


def get_config() -> dict:
    """
    Retorna configurações gerais do sistema.
    """
    return {
        'tesseract_cmd': get_tesseract_path(),
        'redimensionamento_max': (1200, 900),
        'confianca_minima': 50,
        'suportados': ['png', 'jpg', 'jpeg']
    }