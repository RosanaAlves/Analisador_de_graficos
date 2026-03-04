# scr/analisadores/fabrica.py
"""
FÁBRICA DE ANALISADORES DE GRÁFICO
Responsável por instanciar o analisador correto baseado no tipo
"""

import os
import cv2
import numpy as np
from typing import Optional, Dict, Any  # <<< ADICIONAR ESTA LINHA

from .base import AnalisadorBase
from .pizza import AnalisadorPizza
from .barras_verticais import AnalisadorBarrasVerticais
from .barras_horizontais import AnalisadorBarrasHorizontais
from .linhas import AnalisadorLinhas

from ..utils.config import get_tesseract_path
from ..utils.imagem import (
    carregar_imagem, 
    detectar_contorno_principal, 
    detectar_circulo_principal
)

class FabricaAnalisadores:
    """
    Fábrica que cria o analisador apropriado para cada tipo de gráfico.
    """
    
    # Mapeamento de tipos para classes
    _TIPOS = {
        'pizza': AnalisadorPizza,
        'barras_verticais': AnalisadorBarrasVerticais,
        'barras_horizontais': AnalisadorBarrasHorizontais,
        'linhas': AnalisadorLinhas
    }
    
    # Sinônimos para facilitar uso
    _SINONIMOS = {
        'pizza': 'pizza',
        'pie': 'pizza',
        'torta': 'pizza',
        'barras': 'barras_verticais',
        'barra': 'barras_verticais',
        'vertical': 'barras_verticais',
        'barras_vertical': 'barras_verticais',
        'barras_horizontal': 'barras_horizontais',
        'horizontal': 'barras_horizontais',
        'linha': 'linhas',
        'line': 'linhas',
        'tendencia': 'linhas',
        'tendência': 'linhas'
    }
    
    @classmethod
    def criar(cls, 
              tipo: str, 
              imagem_path: str, 
              num_categorias: Optional[int] = None,
              tesseract_cmd: Optional[str] = None,
              **kwargs) -> AnalisadorBase:
        """
        Cria e retorna o analisador apropriado.
        
        Args:
            tipo: Tipo de gráfico ('pizza', 'barras_verticais', 'barras_horizontais', 'linhas')
            imagem_path: Caminho para a imagem
            num_categorias: Número de categorias (opcional, ajuda na detecção)
            tesseract_cmd: Caminho do Tesseract (opcional)
            **kwargs: Argumentos adicionais para o analisador
        
        Returns:
            Instância do analisador apropriado
        
        Raises:
            ValueError: Se o tipo for inválido ou imagem não carregar
        """
        # Validar imagem
        if not os.path.exists(imagem_path):
            raise ValueError(f"Arquivo não encontrado: {imagem_path}")
        
        # Normalizar tipo
        tipo_normalizado = cls._normalizar_tipo(tipo)
        
        if tipo_normalizado not in cls._TIPOS:
            tipos_disponiveis = list(cls._TIPOS.keys()) + list(cls._SINONIMOS.keys())
            raise ValueError(
                f"Tipo de gráfico inválido: '{tipo}'. "
                f"Tipos suportados: {', '.join(sorted(set(tipos_disponiveis)))}"
            )
        
        # Obter caminho do Tesseract
        if tesseract_cmd is None:
            tesseract_cmd = get_tesseract_path()
        
        # Criar argumentos
        args = {
            'imagem_path': imagem_path,
            'tesseract_cmd': tesseract_cmd,
            'num_categorias': num_categorias,
            **kwargs
        }
        
        # Instanciar analisador
        analisador_class = cls._TIPOS[tipo_normalizado]
        return analisador_class(**args)
    
    @classmethod
    def criar_com_deteccao_automatica(cls,
                                      imagem_path: str,
                                      num_categorias: Optional[int] = None,
                                      tesseract_cmd: Optional[str] = None) -> AnalisadorBase:
        """
        Tenta detectar automaticamente o tipo de gráfico e cria o analisador.
        
        Args:
            imagem_path: Caminho para a imagem
            num_categorias: Número de categorias (opcional)
            tesseract_cmd: Caminho do Tesseract (opcional)
        
        Returns:
            Instância do analisador detectado
        """
        # Carregar imagem
        img = carregar_imagem(imagem_path)
        if img is None:
            raise ValueError(f"Não foi possível carregar a imagem: {imagem_path}")
        
        # Detectar tipo
        tipo_detectado = cls._detectar_tipo_imagem(img)
        print(f"🔍 Tipo detectado automaticamente: {tipo_detectado}")
        
        # Criar analisador
        return cls.criar(
            tipo=tipo_detectado,
            imagem_path=imagem_path,
            num_categorias=num_categorias,
            tesseract_cmd=tesseract_cmd
        )
    
    @classmethod
    def _normalizar_tipo(cls, tipo: str) -> str:
        """Normaliza o tipo de gráfico (aceita sinônimos)."""
        tipo_lower = tipo.lower().strip()
        
        # Verificar se é um tipo direto
        if tipo_lower in cls._TIPOS:
            return tipo_lower
        
        # Verificar sinônimos
        if tipo_lower in cls._SINONIMOS:
            return cls._SINONIMOS[tipo_lower]
        
        # Se não encontrar, retornar original (vai gerar erro)
        return tipo_lower
    
    @classmethod
    def _detectar_tipo_imagem(cls, img: np.ndarray) -> str:
        """
        Detecta o tipo de gráfico analisando a imagem.
        
        Estratégia:
        1. Pizza: detecta círculo
        2. Barras verticais: muitos retângulos verticais
        3. Barras horizontais: muitos retângulos horizontais
        4. Linhas: linhas contínuas
        """
        altura, largura = img.shape[:2]
        area_total = altura * largura
        
        # 1. Detectar círculo (pizza)
        circulo = detectar_circulo_principal(img)
        if circulo:
            cx, cy, raio = circulo
            area_circulo = 3.14159 * raio * raio
            
            # Se círculo ocupa área significativa, é pizza
            if area_circulo > area_total * 0.15:
                return 'pizza'
        
        # 2. Detectar contornos para barras
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        contagens = {
            'verticais': 0,
            'horizontais': 0,
            'linhas': 0
        }
        
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = cv2.contourArea(cnt)
            
            # Ignorar contornos muito pequenos
            if area < area_total * 0.005:
                continue
            
            # Classificar baseado na proporção
            if w > h * 3:  # Muito mais largo que alto
                contagens['horizontais'] += 1
            elif h > w * 3:  # Muito mais alto que largo
                contagens['verticais'] += 1
            else:
                # Verificar se é uma linha (contorno alongado)
                if cv2.arcLength(cnt, True) > max(w, h) * 2:
                    contagens['linhas'] += 1
        
        # Decidir baseado nas contagens
        if contagens['verticais'] > contagens['horizontais'] and contagens['verticais'] >= 2:
            return 'barras_verticais'
        elif contagens['horizontais'] > contagens['verticais'] and contagens['horizontais'] >= 2:
            return 'barras_horizontais'
        elif contagens['linhas'] >= 2:
            return 'linhas'
        
        # Padrão: barras verticais
        return 'barras_verticais'
    
    @classmethod
    def listar_tipos(cls) -> Dict[str, str]:
        """Lista todos os tipos de gráfico suportados com descrições."""
        return {
            'pizza': '🍕 Gráfico de Pizza / Torta',
            'barras_verticais': '📊 Barras Verticais',
            'barras_horizontais': '📈 Barras Horizontais',
            'linhas': '📉 Gráfico de Linhas'
        }
    
    @classmethod
    def testar_todos(cls, pasta_imagens: str) -> Dict[str, Any]:
        """
        Testa todos os analisadores com imagens de exemplo.
        Útil para debug e validação.
        
        Args:
            pasta_imagens: Pasta contendo imagens de teste
        
        Returns:
            Dicionário com resultados dos testes
        """
        import glob
        
        resultados = {}
        
        # Para cada tipo, procurar imagens correspondentes
        for tipo in cls._TIPOS.keys():
            padrao = os.path.join(pasta_imagens, f"*{tipo}*.png")
            arquivos = sorted(glob.glob(padrao))
            
            if not arquivos:
                continue
            
            resultados[tipo] = []
            for arquivo in arquivos[:3]:  # Limitar a 3 por tipo
                try:
                    nome = os.path.basename(arquivo)
                    print(f"\n🔍 Testando {tipo}: {nome}")
                    
                    analisador = cls.criar(tipo, arquivo)
                    dados = analisador.extrair_elementos()
                    
                    resultados[tipo].append({
                        'arquivo': nome,
                        'sucesso': not dados.get('erro', True),
                        'confianca': dados.get('confianca', 0),
                        'mensagens': dados.get('mensagens', [])
                    })
                    
                except Exception as e:
                    resultados[tipo].append({
                        'arquivo': os.path.basename(arquivo),
                        'sucesso': False,
                        'erro': str(e)
                    })
        
        return resultados


# =========================================================================
# FUNÇÃO DE ATALHO PARA USO RÁPIDO
# =========================================================================

def analisar_grafico(imagem_path: str, 
                    tipo: Optional[str] = None,
                    num_categorias: Optional[int] = None) -> Dict[str, Any]:
    """
    Função de atalho para analisar um gráfico.
    
    Args:
        imagem_path: Caminho da imagem
        tipo: Tipo de gráfico (opcional, se None tenta detectar)
        num_categorias: Número de categorias (opcional)
    
    Returns:
        Dicionário com dados extraídos
    """
    try:
        if tipo:
            analisador = FabricaAnalisadores.criar(tipo, imagem_path, num_categorias)
        else:
            analisador = FabricaAnalisadores.criar_com_deteccao_automatica(
                imagem_path, num_categorias
            )
        
        return analisador.extrair_elementos()
        
    except Exception as e:
        return {
            'erro': True,
            'mensagem': str(e),
            'tipo': tipo or 'desconhecido'
        }


# Teste rápido
if __name__ == "__main__":
    print("🏭 TESTANDO FÁBRICA DE ANALISADORES")
    print("=" * 50)
    
    # Listar tipos
    print("\n📋 Tipos suportados:")
    for tipo, desc in FabricaAnalisadores.listar_tipos().items():
        print(f"   - {tipo}: {desc}")
    
    # Testar com uma imagem (se existir)
    imagem_teste = "data/exemplos/teste_pizza.png"
    if os.path.exists(imagem_teste):
        print(f"\n🔍 Testando com: {imagem_teste}")
        resultado = analisar_grafico(imagem_teste, tipo='pizza', num_categorias=4)
        print(f"   Sucesso: {not resultado.get('erro', True)}")
        print(f"   Confiança: {resultado.get('confianca', 0)}%")