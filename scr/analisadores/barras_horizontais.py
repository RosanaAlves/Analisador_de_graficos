# scr/analisadores/barras_horizontais.py
"""
ANALISADOR DE GRÁFICOS DE BARRAS HORIZONTAIS
"""

import cv2
import numpy as np
import re
import pytesseract  # <-- LINHA ADICIONADA
from typing import Dict, List, Optional, Tuple, Any

from .base import AnalisadorBase
from ..utils.imagem import (
    preprocessar_para_ocr,
    detectar_contorno_principal,
    calcular_proporcao_linear
)


class AnalisadorBarrasHorizontais(AnalisadorBase):
    """
    Analisador especializado em gráficos de barras horizontais.
    
    Características:
    - Detecta quadro do gráfico
    - Extrai valores do eixo X
    - Detecta barras horizontais
    - Calcula valores por comprimento
    - Extrai rótulos do eixo Y
    """
    
    # Cores comuns para barras horizontais
    CORES_BARRAS = [
        {'nome': 'Verde', 'lower': (40, 50, 50), 'upper': (80, 255, 255)},
        {'nome': 'Azul', 'lower': (100, 50, 50), 'upper': (130, 255, 255)},
        {'nome': 'Laranja', 'lower': (5, 50, 50), 'upper': (15, 255, 255)},
        {'nome': 'Roxo', 'lower': (130, 50, 50), 'upper': (160, 255, 255)},
    ]
    
    def __init__(self, 
                 imagem_path: str, 
                 tesseract_cmd: Optional[str] = None,
                 num_categorias: Optional[int] = None):
        """
        Inicializa analisador de barras horizontais.
        
        Args:
            imagem_path: Caminho da imagem
            tesseract_cmd: Caminho do Tesseract
            num_categorias: Número esperado de barras (ajuda na detecção)
        """
        super().__init__(imagem_path, tesseract_cmd)
        self.num_categorias = num_categorias
        
        # Atributos específicos
        self.quadro = None  # (x, y, w, h) do gráfico
        self.valores_x = []
        self.barras = []
        self.rotulos_y = []
        
        self._adicionar_mensagem(f"📈 Analisador Barras Horizontais inicializado")
        if num_categorias:
            self._adicionar_mensagem(f"📊 Barras informadas: {num_categorias}")
    
    def _get_tipo_grafico(self) -> str:
        return 'barras_horizontais'
    
    def extrair_elementos(self) -> Dict[str, Any]:
        """
        Método principal de extração para barras horizontais.
        
        Fluxo:
        1. Extrair título e fonte
        2. Detectar quadro do gráfico
        3. Extrair valores do eixo X
        4. Detectar barras horizontais
        5. Extrair rótulos do eixo Y
        6. Calcular valores das barras
        7. Associar barras a rótulos
        """
        try:
            self._adicionar_mensagem("🔍 Iniciando extração de barras horizontais...")
            
            # ===========================================
            # PASSO 1: EXTRAIR TÍTULO E FONTE
            # ===========================================
            self._extrair_titulo_fonte()
            
            # ===========================================
            # PASSO 2: DETECTAR QUADRO DO GRÁFICO
            # ===========================================
            self._detectar_quadro()
            if not self.quadro:
                return self._criar_resultado_erro("Não foi possível detectar o quadro do gráfico")
            
            gx, gy, gw, gh = self.quadro
            
            # ===========================================
            # PASSO 3: EXTRAIR VALORES DO EIXO X
            # ===========================================
            self._extrair_valores_x(gy+gh)
            
            if not self.valores_x:
                self._adicionar_mensagem("⚠️ Valores do eixo X não detectados")
                self.valores_x = [0, 100]  # Fallback
            
            # ===========================================
            # PASSO 4: DETECTAR BARRAS HORIZONTAIS
            # ===========================================
            self._detectar_barras_horizontais(gy, gy+gh, gx, gx+gw)
            
            if not self.barras:
                return self._criar_resultado_erro("Nenhuma barra detectada")
            
            # ===========================================
            # PASSO 5: EXTRAIR RÓTULOS DO EIXO Y
            # ===========================================
            self._extrair_rotulos_y(gy, gh, gx)
            
            # ===========================================
            # PASSO 6: CALCULAR VALORES DAS BARRAS
            # ===========================================
            self._calcular_valores_barras(gx, gw)
            
            # ===========================================
            # PASSO 7: ASSOCIAR RÓTULOS
            # ===========================================
            self._associar_rotulos()
            
            # ===========================================
            # PASSO 8: CRIAR RESULTADO
            # ===========================================
            dados_especificos = self._criar_dados_especificos()
            
            return self._criar_resultado_sucesso(dados_especificos)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return self._criar_resultado_erro(f"Erro durante análise: {str(e)}")
    
    def _extrair_titulo_fonte(self):
        """Extrai título e fonte da imagem."""
        regioes = self._separar_regioes()
        
        # Título
        titulo = self._extrair_texto_regiao(regioes['titulo'])
        if titulo:
            self.metadados['titulo'] = titulo
            self._adicionar_mensagem(f"📝 Título: {titulo}")
        
        # Fonte
        texto_fonte = self._extrair_texto_regiao(regioes['fonte'])
        for linha in texto_fonte.split('\n'):
            if 'Fonte:' in linha or 'fonte:' in linha.lower():
                self.metadados['fonte'] = linha.strip()
                self._adicionar_mensagem(f"📌 Fonte: {linha.strip()}")
                break
        
        if not self.metadados['fonte']:
            self.metadados['fonte'] = "Não identificada"
    
    def _detectar_quadro(self):
        """Detecta o quadro (bounding box) do gráfico."""
        regioes = self._separar_regioes()
        img_grafico = regioes['grafico']
        
        quadro = detectar_contorno_principal(img_grafico)
        
        if quadro:
            x, y, w, h = quadro
            # Ajustar para coordenadas da imagem original
            altura_titulo = int(self.altura * 0.12)
            self.quadro = (x, y + altura_titulo, w, h)
            self._adicionar_mensagem(f"📐 Quadro do gráfico: x={x}, y={y+altura_titulo}, w={w}, h={h}")
    
    def _extrair_valores_x(self, y_base_grafico):
        """Extrai valores do eixo X (parte inferior)."""
        # Região dos valores (abaixo do gráfico)
        regiao_valores = self.img[y_base_grafico:self.altura, 0:self.largura]
        
        if regiao_valores.size == 0:
            return
        
        # Aumentar resolução
        regiao_valores = cv2.resize(regiao_valores, None, fx=2, fy=2)
        gray = cv2.cvtColor(regiao_valores, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        
        # OCR para números
        config_numeros = r'--psm 6 -c tessedit_char_whitelist=0123456789.,'
        texto = pytesseract.image_to_string(binary, config=config_numeros)
        
        # Extrair números
        valores = []
        for match in re.findall(r'(\d+[\.,]?\d*)', texto):
            try:
                num = float(match.replace(',', '.'))
                valores.append(num)
            except:
                pass
        
        if valores:
            # Garantir que 0% está presente
            if min(valores) > 0:
                valores.append(0.0)
            
            self.valores_x = sorted(list(set(valores)))
            self._adicionar_mensagem(f"📊 Valores X: {self.valores_x}")
    
    def _extrair_rotulos_y(self, gy, gh, gx):
        """Extrai rótulos do eixo Y (lado esquerdo)."""
        # Região dos rótulos (esquerda do gráfico)
        regiao_rotulos = self.img[gy:gy+gh, 0:gx]
        
        if regiao_rotulos.size == 0:
            return
        
        # Aumentar resolução
        regiao_rotulos = cv2.resize(regiao_rotulos, None, fx=2, fy=2)
        gray = cv2.cvtColor(regiao_rotulos, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        
        # OCR para texto
        texto = pytesseract.image_to_string(binary, config='--psm 6')
        
        # Processar linhas
        for linha in texto.split('\n'):
            linha = linha.strip()
            if linha and len(linha) > 1 and not any(c.isdigit() for c in linha):
                self.rotulos_y.append(linha)
        
        self._adicionar_mensagem(f"🏷️ Rótulos Y: {self.rotulos_y}")
    
    def _detectar_barras_horizontais(self, y_inicio, y_fim, x_inicio, x_fim):
        """Detecta barras horizontais."""
        # Recortar região do gráfico
        grafico = self.img[y_inicio:y_fim, x_inicio:x_fim]
        h, w = grafico.shape[:2]
        
        # Converter para HSV
        hsv = cv2.cvtColor(grafico, cv2.COLOR_BGR2HSV)
        
        # Detectar cores
        todas_barras = []
        
        for cor_info in self.CORES_BARRAS:
            mask = cv2.inRange(hsv, np.array(cor_info['lower']), np.array(cor_info['upper']))
            
            # Limpar ruído
            kernel = np.ones((3,3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            
            # Encontrar contornos
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for cnt in contours:
                x, y, w_cnt, h_cnt = cv2.boundingRect(cnt)
                area = cv2.contourArea(cnt)
                
                # Filtrar: formato horizontal (largura > altura)
                if w_cnt > h_cnt * 2 and h_cnt > 15 and area > 300:
                    todas_barras.append({
                        'x': x,
                        'y': y,
                        'largura': w_cnt,
                        'altura': h_cnt,
                        'area': area,
                        'y_centro': y + h_cnt//2,
                        'x_fim': x + w_cnt,
                        'cor': cor_info['nome']
                    })
        
        # Se não encontrou, tentar método alternativo
        if not todas_barras:
            self._adicionar_mensagem("⚠️ Nenhuma barra por cor, tentando detecção por bordas")
            todas_barras = self._detectar_barras_por_bordas(grafico)
        
        # Remover duplicatas e ajustar coordenadas
        self.barras = self._processar_barras(todas_barras, x_inicio, y_inicio)
        
        # Ordenar por posição y (de cima para baixo)
        self.barras.sort(key=lambda b: b['y_centro'])
        
        self._adicionar_mensagem(f"✅ {len(self.barras)} barras horizontais detectadas")
    
    def _detectar_barras_por_bordas(self, grafico):
        """Método alternativo: detectar por bordas."""
        gray = cv2.cvtColor(grafico, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        kernel = np.ones((3,3), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=2)
        
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        barras = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = cv2.contourArea(cnt)
            
            if w > h * 1.5 and h > 15 and area > 300:
                barras.append({
                    'x': x,
                    'y': y,
                    'largura': w,
                    'altura': h,
                    'area': area,
                    'y_centro': y + h//2,
                    'x_fim': x + w
                })
        
        return barras
    
    def _processar_barras(self, barras, x_inicio, y_inicio):
        """Processa lista de barras: remove duplicatas e ajusta coordenadas."""
        if not barras:
            return []
        
        # Ordenar por área
        barras.sort(key=lambda b: b['area'], reverse=True)
        
        # Remover duplicatas (mesma posição y)
        unicas = []
        tolerancia_y = 15
        
        for barra in barras:
            duplicata = False
            for existente in unicas:
                if abs(barra['y_centro'] - existente['y_centro']) < tolerancia_y:
                    duplicata = True
                    break
            
            if not duplicata:
                # Subtrair margem para não incluir o texto do valor
                x_fim_ajustado = barra['x'] + barra['largura'] - 8
                
                unicas.append({
                    'x_inicio': barra['x'] + x_inicio,
                    'x_fim': x_fim_ajustado + x_inicio,
                    'y_centro': barra['y'] + y_inicio + barra['altura']//2,
                    'comprimento': barra['largura'] - 8,
                    'altura': barra['altura'],
                    'cor': barra.get('cor', 'desconhecida')
                })
        
        return unicas
    
    def _calcular_valores_barras(self, x_inicio, largura_grafico):
        """Calcula valores das barras por calibração linear."""
        if not self.barras or not self.valores_x:
            return
        
        # Ordenar valores X
        x_vals = sorted(self.valores_x)
        x_min = min(x_vals)  # Deve ser 0
        x_max = max(x_vals)  # Deve ser 100
        
        # Limites em pixels
        x_min_pixel = x_inicio
        x_max_pixel = x_inicio + largura_grafico
        comprimento_max = x_max_pixel - x_min_pixel
        
        self._adicionar_mensagem(f"📐 Calibração: {x_min}% → {x_min_pixel}px, {x_max}% → {x_max_pixel}px")
        
        # Calcular para cada barra
        for barra in self.barras:
            x_fim = barra['x_fim']
            comprimento = x_fim - x_min_pixel
            
            # Garantir que não ultrapasse
            if comprimento > comprimento_max:
                comprimento = comprimento_max
            
            proporcao = comprimento / comprimento_max
            valor = x_min + proporcao * (x_max - x_min)
            
            barra['valor_calculado'] = round(valor, 1)
    
    def _associar_rotulos(self):
        """Associa rótulos do eixo Y às barras por posição."""
        if not self.rotulos_y or not self.barras:
            # Criar rótulos padrão
            for i, barra in enumerate(self.barras):
                barra['rotulo'] = f"Barra {i+1}"
            return
        
        # Ordenar barras por y (cima para baixo)
        self.barras.sort(key=lambda b: b['y_centro'])
        
        # Associar (primeira barra = primeiro rótulo)
        for i, barra in enumerate(self.barras):
            if i < len(self.rotulos_y):
                barra['rotulo'] = self.rotulos_y[i]
            else:
                barra['rotulo'] = f"Barra {i+1}"
    
    def _criar_dados_especificos(self) -> Dict:
        """Cria dicionário com dados específicos de barras horizontais."""
        barras_final = []
        
        for i, barra in enumerate(self.barras):
            barras_final.append({
                'id': i + 1,
                'rotulo': barra.get('rotulo', f'Barra {i+1}'),
                'valor': barra.get('valor_calculado', 0),
                'comprimento': barra['comprimento'],
                'y_centro': barra['y_centro']
            })
        
        return {
            'tipo': 'barras_horizontais',
            'barras': barras_final,
            'total_barras': len(barras_final),
            'valores_x': self.valores_x,
            'eixo_x_min': min(self.valores_x) if self.valores_x else 0,
            'eixo_x_max': max(self.valores_x) if self.valores_x else 100,
            'rotulos_y': self.rotulos_y,
            'valores': [b['valor'] for b in barras_final],
            'categorias': [b['rotulo'] for b in barras_final]
        }
    
    def _validar_dados(self, dados: Dict) -> Dict:
        """Valida dados extraídos das barras horizontais."""
        validacoes = super()._validar_dados(dados)
        
        barras = dados.get('barras', [])
        alertas = []
        
        # Regra 1: Eixo X começa em zero?
        eixo_min = dados.get('eixo_x_min', 0)
        if eixo_min > 0:
            alertas.append({
                'tipo': 'EIXO_X_NAO_ZERO',
                'severidade': 'ALTA' if eixo_min > 10 else 'MEDIA',
                'mensagem': f'Eixo X começa em {eixo_min}% (deveria ser 0)'
            })
        
        # Regra 2: Número de barras
        if self.num_categorias:
            if len(barras) != self.num_categorias:
                alertas.append({
                    'tipo': 'NUMERO_BARRAS',
                    'severidade': 'MEDIA',
                    'mensagem': f'Número de barras ({len(barras)}) diferente do informado ({self.num_categorias})'
                })
        
        validacoes['alertas'] = alertas
        validacoes['valido'] = len(alertas) == 0
        
        return validacoes