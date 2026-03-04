# src/analisadores/linhas.py
"""
ANALISADOR DE GRÁFICOS DE LINHAS
Detecta múltiplas séries, pontos, valores do eixo X e Y
"""

import cv2
import numpy as np
import re
from typing import Dict, List, Optional, Tuple, Any

from .base import AnalisadorBase
from ..utils.imagem import (
    preprocessar_para_ocr,
    detectar_contorno_principal
)


class AnalisadorLinhas(AnalisadorBase):
    """
    Analisador especializado em gráficos de linhas.
    
    Características:
    - Detecta múltiplas séries por cor
    - Extrai pontos de cada linha
    - Reconhece valores do eixo X (datas, categorias)
    - Extrai título e fonte
    """
    
    # Cores típicas para séries (HSV)
    CORES_SERIES = [
        {'nome': 'Azul', 'lower': (100, 50, 50), 'upper': (130, 255, 255), 'bgr': (255, 0, 0)},
        {'nome': 'Vermelho', 'lower': (0, 50, 50), 'upper': (10, 255, 255), 'bgr': (0, 0, 255)},
        {'nome': 'Verde', 'lower': (40, 50, 50), 'upper': (80, 255, 255), 'bgr': (0, 255, 0)},
        {'nome': 'Laranja', 'lower': (5, 50, 50), 'upper': (15, 255, 255), 'bgr': (0, 165, 255)},
        {'nome': 'Roxo', 'lower': (130, 50, 50), 'upper': (160, 255, 255), 'bgr': (255, 0, 255)},
        {'nome': 'Amarelo', 'lower': (20, 50, 50), 'upper': (35, 255, 255), 'bgr': (0, 255, 255)},
        {'nome': 'Marrom', 'lower': (10, 50, 30), 'upper': (20, 255, 150), 'bgr': (42, 42, 165)},
        {'nome': 'Rosa', 'lower': (140, 50, 50), 'upper': (170, 255, 255), 'bgr': (203, 192, 255)},
    ]
    
    def __init__(self, 
                 imagem_path: str, 
                 tesseract_cmd: Optional[str] = None,
                 num_series: Optional[int] = None):
        """
        Inicializa analisador de linhas.
        
        Args:
            imagem_path: Caminho da imagem
            tesseract_cmd: Caminho do Tesseract
            num_series: Número esperado de séries (ajuda na detecção)
        """
        super().__init__(imagem_path, tesseract_cmd)
        self.num_series = num_series
        
        # Atributos específicos
        self.regioes = {}
        self.series = []
        self.valores_x = []
        self.offset_y = 0
        
        self._adicionar_mensagem(f"📉 Analisador Linhas inicializado")
        if num_series:
            self._adicionar_mensagem(f"📊 Séries informadas: {num_series}")
    
    def _get_tipo_grafico(self) -> str:
        return 'linhas'
    
    def extrair_elementos(self) -> Dict[str, Any]:
        """
        Método principal de extração para gráficos de linhas.
        
        Fluxo:
        1. Separar regiões da imagem
        2. Extrair título e fonte
        3. Extrair valores do eixo X
        4. Detectar séries por cor
        5. Extrair pontos de cada série
        6. Calcular valores Y (opcional)
        """
        try:
            self._adicionar_mensagem("🔍 Iniciando extração de linhas...")
            
            # ===========================================
            # PASSO 1: SEPARAR REGIÕES
            # ===========================================
            self._separar_regioes_especificas()
            
            # ===========================================
            # PASSO 2: EXTRAIR TÍTULO E FONTE
            # ===========================================
            self._extrair_titulo_fonte()
            
            # ===========================================
            # PASSO 3: EXTRAIR VALORES DO EIXO X
            # ===========================================
            self._extrair_valores_x()
            
            if not self.valores_x:
                self._adicionar_mensagem("⚠️ Valores do eixo X não detectados")
                self.valores_x = self._gerar_valores_x_padrao()
            
            # ===========================================
            # PASSO 4: DETECTAR SÉRIES
            # ===========================================
            self._detectar_series()
            
            if not self.series:
                return self._criar_resultado_erro("Nenhuma série detectada")
            
            # ===========================================
            # PASSO 5: EXTRAIR PONTOS DAS SÉRIES
            # ===========================================
            self._extrair_pontos_series()
            
            # ===========================================
            # PASSO 6: CRIAR RESULTADO
            # ===========================================
            dados_especificos = self._criar_dados_especificos()
            
            return self._criar_resultado_sucesso(dados_especificos)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return self._criar_resultado_erro(f"Erro durante análise: {str(e)}")
    
    def _separar_regioes_especificas(self):
        """Separa regiões específicas para gráfico de linhas."""
        altura_titulo = int(self.altura * 0.12)      # 12% topo
        altura_eixo_x = int(self.altura * 0.06)      # 6% para eixo X
        altura_fonte = int(self.altura * 0.10)       # 10% base
        
        self.regioes = {
            'titulo': self.img[0:altura_titulo, 0:self.largura],
            'eixo_x': self.img[self.altura - altura_eixo_x - altura_fonte:self.altura - altura_fonte, 0:self.largura],
            'fonte': self.img[self.altura - altura_fonte:self.altura, 0:self.largura],
        }
        
        # Região do gráfico (centro)
        self.offset_y = altura_titulo
        inicio_grafico = altura_titulo
        fim_grafico = self.altura - altura_eixo_x - altura_fonte
        self.regioes['grafico'] = self.img[inicio_grafico:fim_grafico, 0:self.largura]
        
        self._adicionar_mensagem(f"📌 Regiões: título={altura_titulo}, eixo_x={altura_eixo_x}, fonte={altura_fonte}")
    
    def _extrair_titulo_fonte(self):
        """Extrai título e fonte."""
        # Título
        titulo = self._extrair_texto_regiao(self.regioes['titulo'])
        if titulo:
            # Limpar caracteres especiais
            titulo = re.sub(r'[^a-zA-Z0-9áéíóúãõç\s\-]', '', titulo).strip()
            self.metadados['titulo'] = titulo
            self._adicionar_mensagem(f"📝 Título: {titulo}")
        
        # Fonte
        texto_fonte = self._extrair_texto_regiao(self.regioes['fonte'])
        for linha in texto_fonte.split('\n'):
            if 'Fonte:' in linha or 'fonte:' in linha.lower():
                self.metadados['fonte'] = linha.strip()
                self._adicionar_mensagem(f"📌 Fonte: {linha.strip()}")
                break
        
        if not self.metadados['fonte']:
            self.metadados['fonte'] = "Não identificada"
    
    def _extrair_valores_x(self):
        """Extrai valores do eixo X."""
        regiao = self.regioes['eixo_x']
        
        if regiao.size == 0:
            return
        
        # Aumentar resolução
        regiao = cv2.resize(regiao, None, fx=3, fy=3)
        gray = cv2.cvtColor(regiao, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        
        # OCR para texto
        texto = pytesseract.image_to_string(binary, config='--psm 6').strip()
        
        # Detectar tipo pelo nome do arquivo
        if 'tendencia' in self.nome_arquivo or 'ano' in self.nome_arquivo:
            self.valores_x = self._extrair_anos(texto)
        elif 'trimestre' in self.nome_arquivo or 'q1' in self.nome_arquivo.lower():
            self.valores_x = self._extrair_trimestres(texto)
        elif 'mes' in self.nome_arquivo:
            self.valores_x = self._extrair_meses(texto)
        else:
            # Tentar detectar automaticamente
            self.valores_x = self._detectar_valores_x_auto(texto)
        
        self._adicionar_mensagem(f"📊 Eixo X: {self.valores_x}")
    
    def _extrair_anos(self, texto):
        """Extrai anos do texto."""
        anos = re.findall(r'\b(19|20)\d{2}\b', texto)
        if anos:
            return sorted(list(set(anos)))
        return [str(ano) for ano in range(2016, 2027)]  # Fallback
    
    def _extrair_trimestres(self, texto):
        """Extrai trimestres (Q1, Q2, etc.) do texto."""
        trimestres = ['Q1', 'Q2', 'Q3', 'Q4']
        encontrados = [t for t in trimestres if t in texto]
        return encontrados if encontrados else trimestres
    
    def _extrair_meses(self, texto):
        """Extrai meses do texto."""
        meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 
                 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        encontrados = [m for m in meses if m in texto]
        return encontrados if encontrados else meses[:6]  # Fallback
    
    def _detectar_valores_x_auto(self, texto):
        """Detecta automaticamente valores do eixo X."""
        # Tentar números
        numeros = re.findall(r'\b\d+\b', texto)
        if numeros and len(numeros) >= 3:
            return numeros
        
        # Tentar palavras
        palavras = texto.split()
        if palavras and len(palavras) >= 3:
            return palavras[:8]  # Limitar a 8 itens
        
        return [f"Item {i+1}" for i in range(6)]  # Fallback
    
    def _gerar_valores_x_padrao(self) -> List[str]:
        """Gera valores padrão para eixo X."""
        if 'tendencia' in self.nome_arquivo:
            return [str(ano) for ano in range(2016, 2023)]
        elif 'trimestre' in self.nome_arquivo:
            return ['Q1', 'Q2', 'Q3', 'Q4']
        else:
            return ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun']
    
    def _detectar_series(self):
        """Detecta séries por cor."""
        img_grafico = self.regioes['grafico']
        h, w = img_grafico.shape[:2]
        
        todas_series = []
        
        # Converter para HSV
        hsv = cv2.cvtColor(img_grafico, cv2.COLOR_BGR2HSV)
        
        # Detectar para cada cor
        for cor_info in self.CORES_SERIES:
            mask = cv2.inRange(hsv, np.array(cor_info['lower']), np.array(cor_info['upper']))
            
            # Limpar ruído
            kernel = np.ones((2,2), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            
            # Encontrar contornos (segmentos da linha)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Coletar pontos
                pontos = []
                for cnt in contours:
                    for ponto in cnt:
                        x, y = ponto[0]
                        pontos.append({
                            'x': x,
                            'y': y + self.offset_y,  # Ajustar para imagem original
                            'x_rel': x,
                            'y_rel': y
                        })
                
                if len(pontos) >= 5:  # Mínimo de pontos para considerar uma série
                    todas_series.append({
                        'nome': cor_info['nome'],
                        'cor': cor_info['bgr'],
                        'pontos': pontos,
                        'total_pontos': len(pontos),
                        'segmentos': len(contours)
                    })
        
        # Ordenar por quantidade de pontos
        todas_series.sort(key=lambda s: s['total_pontos'], reverse=True)
        
        # Selecionar séries
        if self.num_series:
            self.series = todas_series[:self.num_series]
            self._adicionar_mensagem(f"📊 Usando {self.num_series} séries (informado)")
        else:
            self.series = [s for s in todas_series if s['total_pontos'] >= 10]
        
        # Se não detectou nada, tentar método alternativo
        if not self.series:
            self._adicionar_mensagem("⚠️ Nenhuma série detectada, tentando método alternativo")
            self._detectar_series_alternativo()
        
        for serie in self.series:
            self._adicionar_mensagem(f"   ✅ {serie['nome']}: {serie['total_pontos']} pontos, {serie['segmentos']} segmentos")
    
    def _detectar_series_alternativo(self):
        """Método alternativo para detectar séries."""
        img_grafico = self.regioes['grafico']
        
        # Converter para escala de cinza
        gray = cv2.cvtColor(img_grafico, cv2.COLOR_BGR2GRAY)
        
        # Melhorar contraste
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        gray = clahe.apply(gray)
        
        # Detectar bordas
        edges = cv2.Canny(gray, 20, 60)
        
        # Dilatar para conectar pontos
        kernel = np.ones((2,2), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)
        
        # Encontrar contornos
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        pontos = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = cv2.contourArea(cnt)
            
            if area > 50 and w > h * 2:  # Linhas são alongadas
                for ponto in cnt:
                    px, py = ponto[0]
                    pontos.append({
                        'x': px,
                        'y': py + self.offset_y,
                        'x_rel': px,
                        'y_rel': py
                    })
        
        if pontos:
            pontos.sort(key=lambda p: p['x'])
            self.series.append({
                'nome': 'Série Principal',
                'cor': (128, 128, 128),
                'pontos': pontos,
                'total_pontos': len(pontos),
                'segmentos': len(contours)
            })
    
    def _extrair_pontos_series(self):
        """Processa pontos de cada série (ordenação, etc.)."""
        for serie in self.series:
            # Ordenar pontos por x
            serie['pontos'].sort(key=lambda p: p['x'])
            
            # Extrair apenas valores y para facilitar
            serie['valores_y'] = [p['y_rel'] for p in serie['pontos']]
    
    def _criar_dados_especificos(self) -> Dict:
        """Cria dicionário com dados específicos de linhas."""
        series_final = []
        
        for i, serie in enumerate(self.series):
            series_final.append({
                'id': i + 1,
                'nome': serie['nome'],
                'cor': serie['cor'],
                'pontos': serie['pontos'],
                'total_pontos': serie['total_pontos'],
                'segmentos': serie['segmentos']
            })
        
        return {
            'tipo': 'linhas',
            'series': series_final,
            'total_series': len(series_final),
            'valores_x': self.valores_x,
            'total_pontos': sum(s['total_pontos'] for s in series_final)
        }
    
    def _validar_dados(self, dados: Dict) -> Dict:
        """Valida dados extraídos das linhas."""
        validacoes = super()._validar_dados(dados)
        
        series = dados.get('series', [])
        alertas = []
        
        # Regra 1: Número de séries
        if self.num_series:
            if len(series) != self.num_series:
                alertas.append({
                    'tipo': 'NUMERO_SERIES',
                    'severidade': 'MEDIA',
                    'mensagem': f'Número de séries ({len(series)}) diferente do informado ({self.num_series})'
                })
        
        # Regra 2: Pontos suficientes
        for serie in series:
            if serie['total_pontos'] < 3:
                alertas.append({
                    'tipo': 'PONTOS_INSUFICIENTES',
                    'severidade': 'BAIXA',
                    'mensagem': f"Série '{serie['nome']}' tem apenas {serie['total_pontos']} pontos"
                })
        
        validacoes['alertas'] = alertas
        validacoes['valido'] = len(alertas) == 0
        
        return validacoes