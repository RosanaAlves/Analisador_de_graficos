# src/utils/imagem.py
"""
UTILITÁRIOS DE PROCESSAMENTO DE IMAGEM
Funções reutilizáveis para pré e pós-processamento de imagens
"""

import cv2
import numpy as np
from PIL import Image
from typing import Tuple, Optional, List, Union
from typing import Dict  # <-- ADICIONAR ESTA LINHA
import os
import math

def carregar_imagem(caminho: str, redimensionar_max: Optional[Tuple[int, int]] = None) -> Optional[np.ndarray]:
    """
    Carrega imagem do disco com tratamento de erros.
    
    Args:
        caminho: Caminho para o arquivo de imagem
        redimensionar_max: Tupla (largura_max, altura_max) para redimensionar
    
    Returns:
        Imagem em BGR (numpy array) ou None se erro
    """
    try:
        if not os.path.exists(caminho):
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
        
        img = cv2.imread(caminho)
        if img is None:
            raise ValueError(f"Não foi possível ler a imagem: {caminho}")
        
        if redimensionar_max:
            img = redimensionar_proporcional(img, redimensionar_max)
        
        return img
        
    except Exception as e:
        print(f"❌ Erro ao carregar imagem: {e}")
        return None


def redimensionar_proporcional(img: np.ndarray, tamanho_max: Tuple[int, int]) -> np.ndarray:
    """
    Redimensiona imagem mantendo proporção.
    
    Args:
        img: Imagem numpy array
        tamanho_max: (largura_max, altura_max)
    
    Returns:
        Imagem redimensionada
    """
    altura, largura = img.shape[:2]
    largura_max, altura_max = tamanho_max
    
    # Calcular proporções
    proporcao_largura = largura_max / largura
    proporcao_altura = altura_max / altura
    proporcao = min(proporcao_largura, proporcao_altura)
    
    if proporcao < 1:
        nova_largura = int(largura * proporcao)
        nova_altura = int(altura * proporcao)
        return cv2.resize(img, (nova_largura, nova_altura), interpolation=cv2.INTER_AREA)
    
    return img


def preprocessar_para_ocr(img: np.ndarray, 
                          aplicar_clahe: bool = True,
                          binarizar: bool = True,
                          resolver: bool = True) -> np.ndarray:
    """
    Pré-processa imagem para melhorar OCR.
    
    Args:
        img: Imagem em BGR ou escala de cinza
        aplicar_clahe: Aplicar CLAHE para melhorar contraste
        binarizar: Aplicar binarização adaptativa
        resolver: Aumentar resolução
    
    Returns:
        Imagem processada (escala de cinza)
    """
    # Converter para escala de cinza se necessário
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()
    
    # Aumentar resolução
    if resolver:
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    
    # Remover ruído
    gray = cv2.medianBlur(gray, 3)
    
    # Melhorar contraste
    if aplicar_clahe:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        gray = clahe.apply(gray)
    
    # Binarização
    if binarizar:
        gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY, 11, 2)
    
    return gray


def detectar_contorno_principal(img: np.ndarray, 
                               threshold: int = 240,
                               area_minima: float = 0.01) -> Optional[Tuple[int, int, int, int]]:
    """
    Detecta o contorno principal da imagem (geralmente o gráfico).
    
    Args:
        img: Imagem em BGR ou escala de cinza
        threshold: Valor para binarização
        area_minima: Área mínima relativa à imagem total (0-1)
    
    Returns:
        Tupla (x, y, largura, altura) ou None
    """
    try:
        # Converter para escala de cinza se necessário
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        
        # Binarização inversa
        _, thresh = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)
        
        # Encontrar contornos
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        # Filtrar por área mínima
        altura, largura = gray.shape
        area_min_pixels = altura * largura * area_minima
        
        contours_validos = [c for c in contours if cv2.contourArea(c) > area_min_pixels]
        
        if not contours_validos:
            return None
        
        # Pegar o maior contorno
        maior_contorno = max(contours_validos, key=cv2.contourArea)
        
        return cv2.boundingRect(maior_contorno)
        
    except Exception as e:
        print(f"⚠️ Erro ao detectar contorno: {e}")
        return None


def detectar_barras_por_cor(img: np.ndarray, 
                           cor_hsv: Tuple[Tuple[int, int, int], Tuple[int, int, int]],
                           area_minima: int = 500) -> List[Dict]:
    """
    Detecta barras de uma cor específica.
    
    Args:
        img: Imagem em BGR
        cor_hsv: Tupla (lower, upper) com limites HSV
        area_minima: Área mínima para considerar uma barra
    
    Returns:
        Lista de dicionários com informações das barras
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower, upper = cor_hsv
    
    # Criar máscara
    mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
    
    # Limpar ruído
    kernel = np.ones((3,3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    # Encontrar contornos
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    barras = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > area_minima:
            x, y, w, h = cv2.boundingRect(cnt)
            barras.append({
                'x': x,
                'y': y,
                'largura': w,
                'altura': h,
                'area': area,
                'x_centro': x + w//2,
                'y_centro': y + h//2
            })
    
    # Ordenar por posição x (esquerda para direita)
    barras.sort(key=lambda b: b['x'])
    
    return barras


def detectar_circulo_principal(img: np.ndarray,
                              raio_min: Optional[int] = None,
                              raio_max: Optional[int] = None) -> Optional[Tuple[int, int, int]]:
    """
    Detecta o círculo principal na imagem (para gráficos de pizza).
    
    Args:
        img: Imagem em BGR
        raio_min: Raio mínimo (opcional)
        raio_max: Raio máximo (opcional)
    
    Returns:
        Tupla (cx, cy, raio) ou None
    """
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        altura, largura = gray.shape
        
        # Definir raios se não fornecidos
        if raio_min is None:
            raio_min = altura // 6
        if raio_max is None:
            raio_max = altura // 2
        
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=altura//3,
            param1=50,
            param2=25,
            minRadius=raio_min,
            maxRadius=raio_max
        )
        
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            
            # Filtrar círculos próximos ao centro
            centro_x, centro_y = largura//2, altura//2
            circulos_validos = []
            
            for x, y, r in circles:
                # Verificar se está razoavelmente centralizado
                if abs(x - centro_x) < largura*0.25 and abs(y - centro_y) < altura*0.25:
                    circulos_validos.append((x, y, r))
            
            if circulos_validos:
                # Pegar o maior raio
                return max(circulos_validos, key=lambda c: c[2])
        
        return None
        
    except Exception as e:
        print(f"⚠️ Erro ao detectar círculo: {e}")
        return None


def extrair_regioes_proximas(img: np.ndarray, 
                             centro: Tuple[int, int],
                             raio: int,
                             num_amostras: int = 360) -> List[Dict]:
    """
    Extrai amostras ao redor de um círculo.
    Útil para detectar fatias em gráficos de pizza.
    
    Args:
        img: Imagem em BGR
        centro: (cx, cy) do círculo
        raio: Raio do círculo
        num_amostras: Número de pontos para amostrar
    
    Returns:
        Lista de dicionários com ângulo e cor
    """
    import math
    
    cx, cy = centro
    altura, largura = img.shape[:2]
    
    amostras = []
    raio_amostra = int(raio * 0.7)  # Amostrar dentro da pizza
    
    for ang in range(0, 360, max(1, 360 // num_amostras)):
        x = int(cx + raio_amostra * math.cos(math.radians(ang)))
        y = int(cy + raio_amostra * math.sin(math.radians(ang)))
        
        if 0 <= x < largura and 0 <= y < altura:
            cor = img[y, x]
            amostras.append({
                'angulo': ang,
                'cor': cor.tolist(),
                'x': x,
                'y': y
            })
    
    return amostras


def calcular_proporcao_linear(valor_pixel: float,
                             min_pixel: float,
                             max_pixel: float,
                             min_valor: float = 0,
                             max_valor: float = 100) -> float:
    """
    Calcula proporção linear (pixel -> valor).
    
    Args:
        valor_pixel: Valor em pixels
        min_pixel: Pixel mínimo (geralmente base do gráfico)
        max_pixel: Pixel máximo (geralmente topo do gráfico)
        min_valor: Valor mínimo da escala
        max_valor: Valor máximo da escala
    
    Returns:
        Valor proporcional calculado
    """
    proporcao = (max_pixel - valor_pixel) / (max_pixel - min_pixel)
    return min_valor + proporcao * (max_valor - min_valor)


def salvar_imagem_temp(img: np.ndarray, prefixo: str = "temp") -> str:
    """
    Salva imagem temporariamente para debug.
    
    Args:
        img: Imagem numpy array
        prefixo: Prefixo do arquivo
    
    Returns:
        Caminho do arquivo salvo
    """
    import tempfile
    import uuid
    
    # Gerar nome único
    nome = f"{prefixo}_{uuid.uuid4().hex[:8]}.png"
    caminho = os.path.join(tempfile.gettempdir(), nome)
    
    cv2.imwrite(caminho, img)
    return caminho


def overlays_deteccao(img_original: np.ndarray,
                      deteccoes: List[Dict],
                      cor: Tuple[int, int, int] = (0, 255, 0)) -> np.ndarray:
    """
    Cria imagem com overlays das detecções (para debug).
    
    Args:
        img_original: Imagem original
        deteccoes: Lista de dicionários com 'x', 'y', 'largura', 'altura'
        cor: Cor do retângulo BGR
    
    Returns:
        Imagem com retângulos desenhados
    """
    img = img_original.copy()
    
    for det in deteccoes:
        x = det.get('x', 0)
        y = det.get('y', 0)
        w = det.get('largura', det.get('w', 20))
        h = det.get('altura', det.get('h', 20))
        
        cv2.rectangle(img, (x, y), (x + w, y + h), cor, 2)
        
        if 'rotulo' in det:
            cv2.putText(img, str(det['rotulo']), (x, y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, cor, 2)
    
    return img


# =========================================================================
# FUNÇÕES ESPECÍFICAS PARA CADA TIPO DE GRÁFICO
# =========================================================================

def ajustar_para_barras_verticais(dados: Dict) -> Dict:
    """
    Ajusta dados para o formato de barras verticais.
    """
    return {
        'tipo': 'barras_verticais',
        'eixo_y_min': dados.get('eixo_y_min', 0),
        'valores': dados.get('valores', []),
        'categorias': dados.get('categorias', []),
        'alturas_visuais': dados.get('alturas_visuais', [])
    }


def ajustar_para_pizza(dados: Dict) -> Dict:
    """
    Ajusta dados para o formato de pizza.
    """
    fatias = dados.get('fatias', [])
    return {
        'tipo': 'pizza',
        'valores': [f.get('percentual', 0) for f in fatias],
        'categorias': [f.get('rotulo', f'Fatia {i+1}') for i, f in enumerate(fatias)],
        'total': sum(f.get('percentual', 0) for f in fatias)
    }


def ajustar_para_barras_horizontais(dados: Dict) -> Dict:
    """
    Ajusta dados para o formato de barras horizontais.
    """
    return {
        'tipo': 'barras_horizontais',
        'valores': dados.get('valores', []),
        'categorias': dados.get('categorias', []),
        'comprimentos': dados.get('comprimentos', [])
    }


def ajustar_para_linhas(dados: Dict) -> Dict:
    """
    Ajusta dados para o formato de linhas.
    """
    series = dados.get('series', [])
    return {
        'tipo': 'linhas',
        'series': [
            {
                'nome': s.get('nome', f'Série {i+1}'),
                'valores': [p.get('y', 0) for p in s.get('pontos', [])],
                'pontos': s.get('pontos', [])
            }
            for i, s in enumerate(series)
        ],
        'eixo_x': dados.get('valores_x', [])
    }