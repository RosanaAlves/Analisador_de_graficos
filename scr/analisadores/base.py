# scr/analisadores/base.py
"""
CLASSE BASE PARA TODOS OS ANALISADORES DE GRÁFICO
Define a interface comum e funcionalidades compartilhadas
"""

from abc import ABC, abstractmethod
import cv2
import numpy as np
from PIL import Image
import pytesseract
from typing import Dict, List, Optional, Any, Tuple  # <<< LINHA ADICIONADA
import os
import re

# No topo do arquivo, substitua:
# from ..utils.imagem import ...  (ERRADO)
# por:
from scr.utils.imagem import (
    preprocessar_para_ocr,
    carregar_imagem,
    detectar_contorno_principal
)

class AnalisadorBase(ABC):
    """
    Classe abstrata que define o contrato para todos os analisadores de gráfico.
    
    Todos os analisadores específicos (pizza, barras, linhas) devem herdar desta classe
    e implementar os métodos abstratos.
    """
    
    def __init__(self, imagem_path: str, tesseract_cmd: Optional[str] = None):
        """
        Inicializa o analisador base.
        
        Args:
            imagem_path: Caminho para a imagem do gráfico
            tesseract_cmd: Caminho opcional para o executável do Tesseract
        """
        self.imagem_path = imagem_path
        self.nome_arquivo = os.path.basename(imagem_path).lower()
        
        # Carregar imagem
        self.img = cv2.imread(imagem_path)
        if self.img is None:
            raise ValueError(f"Não foi possível carregar a imagem: {imagem_path}")
        
        self.altura, self.largura = self.img.shape[:2]
        
        # Configurar Tesseract
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        # Atributos que serão preenchidos pelas subclasses
        self.metadados = {
            'titulo': '',
            'fonte': '',
            'tipo': self._get_tipo_grafico(),
            'dimensoes': {'largura': self.largura, 'altura': self.altura}
        }
        
        self.dados_extraidos = {}
        self.confianca_geral = 0.0
        self.mensagens = []
        
        # Características detectadas automaticamente
        self.caracteristicas = self._analisar_caracteristicas()
    
    # =========================================================================
    # MÉTODOS ABSTRATOS - DEVEM SER IMPLEMENTADOS POR CADA ANALISADOR
    # =========================================================================
    
    @abstractmethod
    def _get_tipo_grafico(self) -> str:
        """
        Retorna o tipo de gráfico (pizza, barras_verticais, etc.)
        Deve ser implementado por cada subclasse.
        """
        pass
    
    @abstractmethod
    def extrair_elementos(self) -> Dict[str, Any]:
        """
        Método principal de extração.
        Deve retornar um dicionário com todos os dados extraídos do gráfico.
        
        Estrutura mínima do retorno:
        {
            'erro': False,
            'metadados': {...},
            'dados_especificos': {...}  # Dados específicos do tipo
        }
        """
        pass
    
    @abstractmethod
    def _detectar_regioes_grafico(self) -> Optional[Tuple[int, int, int, int]]:
        """
        Detecta a região principal do gráfico (x, y, largura, altura).
        """
        pass
    
    # =========================================================================
    # MÉTODOS DE UTILIDADE - COMUNS A TODOS OS ANALISADORES
    # =========================================================================
    
    def _analisar_caracteristicas(self) -> Dict[str, Any]:
        """
        Analisa automaticamente características da imagem.
        Pode ser sobrescrito por subclasses para adicionar características específicas.
        """
        caracteristicas = {
            'contraste': 'normal',
            'qualidade': 'boa',
            'tem_texto': True,
            'tem_cores': True,
            'tamanho': f"{self.largura}x{self.altura}"
        }
        
        try:
            # Análise de contraste
            gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
            desvio_brilho = np.std(gray)
            
            if desvio_brilho < 30:
                caracteristicas['contraste'] = 'baixo'
            elif desvio_brilho > 80:
                caracteristicas['contraste'] = 'alto'
            
            # Verificar se há texto (presença de bordas)
            edges = cv2.Canny(gray, 50, 150)
            if np.sum(edges) < 1000:
                caracteristicas['tem_texto'] = False
            
        except Exception as e:
            self._adicionar_mensagem(f"⚠️ Erro na análise de características: {e}")
        
        return caracteristicas
    
    def _adicionar_mensagem(self, mensagem: str, tipo: str = "INFO"):
        """Adiciona mensagem ao log do analisador."""
        self.mensagens.append(f"{tipo}: {mensagem}")
        print(f"   {mensagem}")  # Debug
    
    def _extrair_texto_regiao(self, regiao: np.ndarray, 
                              config: str = '--psm 6', 
                              resize_factor: int = 3) -> str:
        """
        Extrai texto de uma região específica da imagem.
        
        Args:
            regiao: Região da imagem (numpy array)
            config: Configuração do Tesseract
            resize_factor: Fator de redimensionamento para melhorar OCR
        
        Returns:
            Texto extraído
        """
        try:
            if regiao.size == 0:
                return ""
            
            # Redimensionar para melhorar OCR
            if resize_factor > 1:
                regiao = cv2.resize(regiao, None, fx=resize_factor, fy=resize_factor, 
                                   interpolation=cv2.INTER_CUBIC)
            
            # Converter para escala de cinza se necessário
            if len(regiao.shape) == 3:
                gray = cv2.cvtColor(regiao, cv2.COLOR_BGR2GRAY)
            else:
                gray = regiao
            
            # Melhorar contraste
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            gray = clahe.apply(gray)
            
            # Binarização adaptativa
            binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                          cv2.THRESH_BINARY, 11, 2)
            
            # Executar OCR
            texto = pytesseract.image_to_string(binary, config=config).strip()
            
            return texto
            
        except Exception as e:
            self._adicionar_mensagem(f"⚠️ Erro no OCR: {e}")
            return ""
    
    def _extrair_numeros_regiao(self, regiao: np.ndarray) -> List[float]:
        """
        Extrai apenas números de uma região.
        
        Returns:
            Lista de números encontrados
        """
        config_numeros = r'--psm 6 -c tessedit_char_whitelist=0123456789.,'
        texto = self._extrair_texto_regiao(regiao, config=config_numeros)
        
        numeros = []
        for match in re.findall(r'(\d+[\.,]?\d*)', texto):
            try:
                # Converter vírgula para ponto
                num = float(match.replace(',', '.'))
                numeros.append(num)
            except:
                pass
        
        return numeros
    
    def _separar_regioes(self) -> Dict[str, np.ndarray]:
        """
        Separa a imagem em regiões (título, gráfico, eixo, fonte).
        Método genérico que pode ser ajustado por cada analisador.
        
        Returns:
            Dicionário com as regiões da imagem
        """
        # Proporções padrão (podem ser ajustadas)
        altura_titulo = int(self.altura * 0.12)      # 12% topo
        altura_fonte = int(self.altura * 0.10)       # 10% base
        
        regioes = {
            'titulo': self.img[0:altura_titulo, 0:self.largura],
            'fonte': self.img[self.altura - altura_fonte:self.altura, 0:self.largura],
            'grafico': self.img[altura_titulo:self.altura - altura_fonte, 0:self.largura]
        }
        
        return regioes
    
    def _detectar_por_cor(self, regiao: np.ndarray, 
                          lower: Tuple[int, int, int], 
                          upper: Tuple[int, int, int]) -> np.ndarray:
        """
        Detecta regiões por cor usando HSV.
        
        Args:
            regiao: Imagem em BGR
            lower: Limite inferior HSV
            upper: Limite superior HSV
        
        Returns:
            Máscara binária da cor detectada
        """
        hsv = cv2.cvtColor(regiao, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
        
        # Limpar ruído
        kernel = np.ones((3,3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        return mask
    
    def _calcular_confianca(self, criterios: Dict[str, bool]) -> float:
        """
        Calcula a confiança geral baseada em critérios.
        
        Args:
            criterios: Dicionário com critérios e se foram atendidos
        
        Returns:
            Percentual de confiança (0-100)
        """
        if not criterios:
            return 0.0
        
        pesos = {
            'titulo': 20,
            'fonte': 20,
            'valores': 30,
            'categorias': 30
        }
        
        confianca = 0.0
        for criterio, atendido in criterios.items():
            if atendido and criterio in pesos:
                confianca += pesos[criterio]
        
        return min(confianca, 100.0)
    
    def _criar_resultado_erro(self, mensagem: str) -> Dict[str, Any]:
        """
        Cria um dicionário de resultado para casos de erro.
        """
        return {
            'erro': True,
            'mensagem': mensagem,
            'metadados': self.metadados,
            'caracteristicas': self.caracteristicas,
            'confianca': 0.0,
            'mensagens': self.mensagens
        }
    
    def _criar_resultado_sucesso(self, dados_especificos: Dict) -> Dict[str, Any]:
        """
        Cria um dicionário de resultado para casos de sucesso.
        """
        # Calcular confiança baseada nos dados extraídos
        criterios = {
            'titulo': bool(self.metadados.get('titulo')),
            'fonte': bool(self.metadados.get('fonte')),
            'valores': bool(dados_especificos.get('valores')),
            'categorias': bool(dados_especificos.get('categorias'))
        }
        
        self.confianca_geral = self._calcular_confianca(criterios)
        
        return {
            'erro': False,
            'metadados': self.metadados,
            'caracteristicas': self.caracteristicas,
            'dados_especificos': dados_especificos,
            'confianca': self.confianca_geral,
            'mensagens': self.mensagens,
            'validacoes': self._validar_dados(dados_especificos)
        }
    
    def _validar_dados(self, dados: Dict) -> Dict:
        """
        Valida os dados extraídos. Pode ser sobrescrito por subclasses.
        """
        return {
            'valido': True,
            'alertas': []
        }
    
    def get_info(self) -> Dict:
        """
        Retorna informações básicas sobre o analisador.
        """
        return {
            'tipo': self._get_tipo_grafico(),
            'imagem': self.nome_arquivo,
            'dimensoes': f"{self.largura}x{self.altura}",
            'caracteristicas': self.caracteristicas
        }