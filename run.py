# run.py (na raiz do projeto: analisador_versao_3.0/run.py)
"""
Arquivo para executar o aplicativo Streamlit
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar e executar o app
if __name__ == "__main__":
    os.system("streamlit run scr/app.py")