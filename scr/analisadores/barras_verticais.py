# scr/analisadores/barras_verticais.py
"""
ANALISADOR DE GRÁFICOS DE BARRAS VERTICAIS
Detecta barras, alturas, valores do eixo Y e rótulos do eixo X
"""

import cv2
import numpy as np
import re
import pytesseract
from typing import Dict, List, Optional, Tuple, Any

from .base import AnalisadorBase
from ..utils.imagem import (
    preprocessar_para_ocr,
    detectar_contorno_principal,
    detectar_barras_por_cor,
    calcular_proporcao_linear
)


class AnalisadorBarrasVerticais(AnalisadorBase):
    """
    Analisador especializado em gráficos de barras verticais.
    
    Características:
    - Detecta quadro do gráfico
    - Extrai valores do eixo Y
    - Detecta barras por cor
    - Calcula valores das barras por calibração linear
    - Extrai rótulos do eixo X
    """
    
    # Cores comuns para barras
    CORES_BARRAS = [
        {'nome': 'Azul', 'lower': (100, 50, 50), 'upper': (130, 255, 255)},
        {'nome': 'Vermelho', 'lower': (0, 50, 50), 'upper': (10, 255, 255)},
        {'nome': 'Vermelho2', 'lower': (160, 50, 50), 'upper': (180, 255, 255)},
        {'nome': 'Verde', 'lower': (40, 50, 50), 'upper': (80, 255, 255)},
        {'nome': 'Laranja', 'lower': (5, 50, 50), 'upper': (15, 255, 255)},
    ]
    
    def __init__(self, 
                 imagem_path: str, 
                 tesseract_cmd: Optional[str] = None,
                 num_categorias: Optional[int] = None):
        """
        Inicializa analisador de barras verticais.
        
        Args:
            imagem_path: Caminho da imagem
            tesseract_cmd: Caminho do Tesseract
            num_categorias: Número esperado de barras (ajuda na detecção)
        """
        super().__init__(imagem_path, tesseract_cmd)
        self.num_categorias = num_categorias
        
        # Atributos específicos
        self.quadro = None  # (x, y, w, h) do gráfico
        self.valores_y = []
        self.barras = []
        self.rotulos_x = []
        
        self._adicionar_mensagem(f"📊 Analisador Barras Verticais inicializado")
        if num_categorias:
            self._adicionar_mensagem(f"📊 Barras informadas: {num_categorias}")
    
    def _get_tipo_grafico(self) -> str:
        """Retorna o tipo de gráfico."""
        return 'barras_verticais'
    
    def extrair_elementos(self) -> Dict[str, Any]:
        """
        Método principal de extração para barras verticais.
        
        Fluxo:
        1. Extrair título e fonte
        2. Detectar quadro do gráfico
        3. Extrair valores do eixo Y
        4. Detectar barras
        5. Extrair rótulos do eixo X
        6. Calcular valores das barras
        7. Associar barras a rótulos
        """
        try:
            self._adicionar_mensagem("🔍 Iniciando extração de barras verticais...")
            
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
            # PASSO 3: EXTRAIR VALORES DO EIXO Y
            # ===========================================
            self._extrair_valores_y(gx, gy, gw, gh)
            
            if not self.valores_y:
                self._adicionar_mensagem("⚠️ Valores do eixo Y não detectados")
                self.valores_y = [0, 100]  # Fallback
            
            # ===========================================
            # PASSO 4: DETECTAR BARRAS
            # ===========================================
            self._detectar_barras(gy, gy+gh, gx, gx+gw)
            
            if not self.barras:
                return self._criar_resultado_erro("Nenhuma barra detectada")
            
            # ===========================================
            # PASSO 5: EXTRAIR RÓTULOS DO EIXO X
            # ===========================================
            self._extrair_rotulos_x(gy+gh)
            
            # ===========================================
            # PASSO 6: CALCULAR VALORES DAS BARRAS
            # ===========================================
            self._calcular_valores_barras(gy, gh)
            
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
    
    def _detectar_regioes_grafico(self) -> Optional[Tuple[int, int, int, int]]:
        """Implementação do método abstrato."""
        regioes = self._separar_regioes()
        return detectar_contorno_principal(regioes['grafico'])
    
    def _extrair_titulo_fonte(self):
        """Extrai título e fonte da imagem."""
        regioes = self._separar_regioes()
        
        # Título
        titulo = self._extrair_texto_regiao(regioes['titulo'])
        if titulo:
            self.metadados['titulo'] = titulo
            self._adicionar_mensagem(f"📝 Título: {titulo}")
        else:
            self.metadados['titulo'] = "Não identificado"
        
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
    
    def _extrair_valores_y(self, gx, gy, gw, gh):
        """Extrai valores do eixo Y da região esquerda."""
        # Região do eixo Y (esquerda do gráfico)
        regiao_y = self.img[gy:gy+gh, 0:gx]
        
        if regiao_y.size == 0:
            return
        
        # Aumentar resolução para melhor OCR
        regiao_y = cv2.resize(regiao_y, None, fx=2, fy=2)
        
        # Extrair números
        config_numeros = r'--psm 6 -c tessedit_char_whitelist=0123456789.,'
        gray = cv2.cvtColor(regiao_y, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        
        texto = pytesseract.image_to_string(binary, config=config_numeros)
        
        # Processar números
        valores = []
        for match in re.findall(r'(\d+[\.,]?\d*)', texto):
            try:
                num = float(match.replace(',', '.'))
                valores.append(num)
            except:
                pass
        
        if valores:
            self.valores_y = sorted(list(set(valores)))
            self._adicionar_mensagem(f"📊 Valores Y: {self.valores_y}")
    
    def _extrair_rotulos_x(self, y_base_grafico):
        """Extrai rótulos do eixo X."""
        # Região dos rótulos (abaixo do gráfico)
        regiao_rotulos = self.img[y_base_grafico:self.altura, 0:self.largura]
        
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
            if linha and len(linha) > 1 and 'Fonte:' not in linha:
                self.rotulos_x.append(linha)
        
        self._adicionar_mensagem(f"🏷️ Rótulos X: {self.rotulos_x}")
    
    def _detectar_barras(self, y_inicio, y_fim, x_inicio, x_fim):
        """Detecta barras na região do gráfico."""
        # Recortar região do gráfico
        grafico = self.img[y_inicio:y_fim, x_inicio:x_fim]
        
        # Tentar detectar para cada cor
        todas_barras = []
        
        for cor_info in self.CORES_BARRAS:
            barras = detectar_barras_por_cor(
                grafico,
                (cor_info['lower'], cor_info['upper']),
                area_minima=300
            )
            
            for barra in barras:
                barra['cor'] = cor_info['nome']
                todas_barras.append(barra)
        
        # Se não encontrou com cores, tentar método alternativo (bordas)
        if not todas_barras:
            self._adicionar_mensagem("⚠️ Nenhuma barra por cor, tentando detecção por bordas")
            todas_barras = self._detectar_barras_por_bordas(grafico)
        
        # Remover duplicatas (barras muito próximas)
        self.barras = self._remover_duplicatas_barras(todas_barras, x_inicio, y_inicio)
        
        # Ordenar por posição x
        self.barras.sort(key=lambda b: b['x'])
        
        self._adicionar_mensagem(f"✅ {len(self.barras)} barras detectadas")
    
    def _detectar_barras_por_bordas(self, grafico):
        """Método alternativo: detectar barras por bordas Canny."""
        gray = cv2.cvtColor(grafico, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        # Dilatar para conectar bordas
        kernel = np.ones((3,3), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=2)
        
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        barras = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = cv2.contourArea(cnt)
            
            # Filtrar: altura significativa e formato vertical
            if h > 30 and w > 10 and h > w * 1.5:
                barras.append({
                    'x': x,
                    'y': y,
                    'largura': w,
                    'altura': h,
                    'area': area,
                    'x_centro': x + w//2
                })
        
        return barras
    
    def _remover_duplicatas_barras(self, barras, x_inicio, y_inicio):
        """Remove barras duplicadas (múltiplas detecções para mesma barra)."""
        if not barras:
            return []
        
        # Ordenar por área (maiores primeiro)
        barras.sort(key=lambda b: b['area'], reverse=True)
        
        unicas = []
        for barra in barras:
            # Verificar se já temos uma barra próxima
            duplicata = False
            for existente in unicas:
                if abs(barra['x_centro'] - existente['x_centro']) < 30:
                    duplicata = True
                    break
            
            if not duplicata:
                unicas.append({
                    'x': barra['x'] + x_inicio,
                    'y_topo': barra['y'] + y_inicio,
                    'y_base': barra['y'] + barra['altura'] + y_inicio,
                    'largura': barra['largura'],
                    'altura': barra['altura'],
                    'x_centro': barra['x'] + x_inicio + barra['largura']//2,
                    'cor': barra.get('cor', 'desconhecida')
                })
        
        return unicas
    
    def _calcular_valores_barras(self, gy, gh):
        """Calcula valores das barras por calibração linear."""
        if not self.barras or not self.valores_y:
            return
        
        # Ordenar valores Y
        y_vals = sorted(self.valores_y)
        y_min = min(y_vals)
        y_max = max(y_vals)
        
        # Encontrar limites em pixels
        y_min_pixel = gy + gh  # Base do gráfico (maior y)
        y_max_pixel = gy       # Topo do gráfico (menor y)
        
        self._adicionar_mensagem(f"📐 Calibração: {y_min}% → {y_min_pixel}px, {y_max}% → {y_max_pixel}px")
        
        # Calcular para cada barra
        for barra in self.barras:
            y_topo = barra['y_topo']
            
            # Calcular valor proporcional
            proporcao = (y_min_pixel - y_topo) / (y_min_pixel - y_max_pixel)
            valor = y_min + proporcao * (y_max - y_min)
            
            barra['valor_calculado'] = round(valor, 1)
    
    def _associar_rotulos(self):
        """Associa rótulos do eixo X às barras por posição."""
        if not self.rotulos_x or not self.barras:
            # Criar rótulos padrão
            for i, barra in enumerate(self.barras):
                barra['rotulo'] = f"Barra {i+1}"
            return
        
        # Ordenar barras por x
        self.barras.sort(key=lambda b: b['x'])
        
        # Associar por ordem (primeira barra = primeiro rótulo)
        for i, barra in enumerate(self.barras):
            if i < len(self.rotulos_x):
                barra['rotulo'] = self.rotulos_x[i]
            else:
                barra['rotulo'] = f"Barra {i+1}"
    
    def _criar_dados_especificos(self) -> Dict:
        """Cria dicionário com dados específicos de barras verticais."""
        barras_final = []
        
        for i, barra in enumerate(self.barras):
            barras_final.append({
                'id': i + 1,
                'rotulo': barra.get('rotulo', f'Barra {i+1}'),
                'valor': barra.get('valor_calculado', 0),
                'altura': barra['altura'],
                'y_topo': barra['y_topo']
            })
        
        return {
            'tipo': 'barras_verticais',
            'barras': barras_final,
            'total_barras': len(barras_final),
            'valores_y': self.valores_y,
            'eixo_y_min': min(self.valores_y) if self.valores_y else 0,
            'eixo_y_max': max(self.valores_y) if self.valores_y else 100,
            'rotulos_x': self.rotulos_x,
            'valores': [b['valor'] for b in barras_final],
            'categorias': [b['rotulo'] for b in barras_final]
        }
    
    def _validar_dados(self, dados: Dict) -> Dict:
        """Valida dados extraídos das barras."""
        validacoes = super()._validar_dados(dados)
        
        barras = dados.get('barras', [])
        alertas = []
        
        # Regra 1: Eixo Y começa em zero?
        eixo_min = dados.get('eixo_y_min', 0)
        if eixo_min > 0:
            alertas.append({
                'tipo': 'EIXO_Y_NAO_ZERO',
                'severidade': 'ALTA' if eixo_min > 10 else 'MEDIA',
                'mensagem': f'Eixo Y começa em {eixo_min}% (deveria ser 0)'
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
    
    def _criar_resultado_erro(self, mensagem: str) -> Dict[str, Any]:
        """Sobrescreve método da classe base."""
        return {
            'erro': True,
            'mensagem': mensagem,
            'metadados': self.metadados,
            'caracteristicas': self.caracteristicas,
            'barras': [],
            'total_barras': 0,
            'confianca': 0.0,
            'mensagens': self.mensagens
        }
    
    def _criar_resultado_sucesso(self, dados_especificos: Dict) -> Dict[str, Any]:
        """Sobrescreve método da classe base."""
        # Calcular confiança
        criterios = {
            'titulo': bool(self.metadados.get('titulo') and self.metadados['titulo'] != "Não identificado"),
            'fonte': bool(self.metadados.get('fonte') and self.metadados['fonte'] != "Não identificada"),
            'valores': bool(dados_especificos.get('valores')),
            'categorias': bool(dados_especificos.get('categorias'))
        }
        
        self.confianca_geral = self._calcular_confianca(criterios)
        
        # Adicionar validações
        validacoes = self._validar_dados(dados_especificos)
        
        return {
            'erro': False,
            'metadados': self.metadados,
            'caracteristicas': self.caracteristicas,
            'dados_especificos': dados_especificos,
            'barras': dados_especificos['barras'],
            'total_barras': dados_especificos['total_barras'],
            'valores_y': dados_especificos['valores_y'],
            'confianca': self.confianca_geral,
            'mensagens': self.mensagens,
            'validacoes': validacoes
        }