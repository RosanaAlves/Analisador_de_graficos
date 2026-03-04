# scr/processamento/carregador.py
"""
GERENCIADOR DE CARREGAMENTO DE IMAGENS
Adaptado para usar os novos analisadores especializados
"""

from PIL import Image
import os
import sys
from typing import Optional, Dict, Any

# CORREÇÃO: Import absoluto em vez de relativo
from scr.processamento.ocr_engine_adaptado import OCREngineAdaptado
from scr.analisadores.fabrica import FabricaAnalisadores
from scr.utils.config import get_tesseract_path


class CarregadorGrafico:
    """
    Gerencia o carregamento e processamento inicial de gráficos.
    Agora integrado com os analisadores especializados.
    """
    
    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        Inicializa o carregador.
        
        Args:
            tesseract_cmd: Caminho opcional para o Tesseract OCR
        """
        self.tesseract_cmd = tesseract_cmd or get_tesseract_path()
        self.ocr = OCREngineAdaptado(self.tesseract_cmd)
        self.formatos_suportados = ('.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG')
    
    def carregar_imagem(self, caminho: str) -> Optional[Image.Image]:
        """
        Carrega imagem do disco.
        
        Args:
            caminho: Caminho para o arquivo de imagem
            
        Returns:
            Objeto PIL.Image ou None se erro
        """
        try:
            if not os.path.exists(caminho):
                raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
            
            ext = os.path.splitext(caminho)[1].lower()
            if ext not in self.formatos_suportados:
                raise ValueError(f"Formato não suportado: {ext}")
            
            print(f"📂 Carregando imagem: {caminho}")
            imagem = Image.open(caminho)
            
            # Redimensionar se muito grande (mantendo proporção)
            max_size = (1200, 900)
            if imagem.width > max_size[0] or imagem.height > max_size[1]:
                imagem.thumbnail(max_size, Image.Resampling.LANCZOS)
                print(f"📏 Imagem redimensionada para: {imagem.width} x {imagem.height}")
            
            return imagem
            
        except Exception as e:
            print(f"❌ Erro ao carregar imagem: {e}")
            return None
    
    def extrair_dados_imagem(self, imagem: Image.Image, tipo_grafico: str = 'barras_verticais') -> Dict:
        """
        Extrai dados do gráfico usando OCR.
        
        Args:
            imagem: Imagem PIL
            tipo_grafico: Tipo de gráfico para extração específica
        
        Returns:
            Dicionário com dados extraídos e metadados
        """
        print("🔍 Iniciando extração OCR...")
        return self.ocr.extrair_dados_completos(imagem, tipo_grafico)
    
    def processar_upload(self, caminho_imagem: str, tipo_grafico: str = 'barras_verticais', 
                        num_categorias: Optional[int] = None) -> Dict[str, Any]:
        """
        Fluxo completo: carrega imagem, extrai dados, retorna estruturado.
        Agora usa os analisadores especializados.
        
        Args:
            caminho_imagem: Caminho da imagem
            tipo_grafico: Tipo de gráfico para extração específica
            num_categorias: Número de categorias (ajuda na detecção)
        """
        resultado = {
            'sucesso': False,
            'imagem': None,
            'dados': None,
            'erro': None,
            'tipo': tipo_grafico
        }
        
        print(f"\n{'='*60}")
        print(f"🔍 PROCESSANDO UPLOAD: {caminho_imagem}")
        print(f"📊 Tipo: {tipo_grafico}")
        if num_categorias:
            print(f"📊 Categorias informadas: {num_categorias}")
        print(f"{'='*60}")
        
        try:
            # ===========================================
            # OPÇÃO 1: Usar analisador especializado (recomendado)
            # ===========================================
            print("🔍 Usando analisador especializado...")
            
            # Criar analisador via fábrica
            analisador = FabricaAnalisadores.criar(
                tipo=tipo_grafico,
                imagem_path=caminho_imagem,
                num_categorias=num_categorias,
                tesseract_cmd=self.tesseract_cmd
            )
            
            # Extrair dados
            dados_extraidos = analisador.extrair_elementos()
            
            if dados_extraidos.get('erro'):
                resultado['erro'] = dados_extraidos['mensagem']
                print(f"❌ Erro no analisador: {dados_extraidos['mensagem']}")
                
                # Fallback: tentar OCR genérico
                print("⚠️ Tentando fallback com OCR genérico...")
                return self._processar_upload_fallback(caminho_imagem, tipo_grafico, resultado)
            
            # Sucesso
            resultado['sucesso'] = True
            resultado['dados'] = dados_extraidos
            resultado['imagem'] = self.carregar_imagem(caminho_imagem)
            
            print(f"\n✅ Upload processado com sucesso!")
            print(f"   Confiança: {dados_extraidos.get('confianca', 0)}%")
            
        except Exception as e:
            resultado['erro'] = f"Erro no processamento: {str(e)}"
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback: tentar OCR genérico
            return self._processar_upload_fallback(caminho_imagem, tipo_grafico, resultado)
        
        return resultado
    
    def _processar_upload_fallback(self, caminho_imagem: str, tipo_grafico: str, 
                                   resultado: Dict) -> Dict:
        """
        Método de fallback usando OCR genérico quando o analisador especializado falha.
        """
        print("🔍 Executando OCR genérico (fallback)...")
        
        try:
            # Carregar imagem
            imagem = self.carregar_imagem(caminho_imagem)
            if not imagem:
                resultado['erro'] = "Falha ao carregar imagem no fallback"
                return resultado
            
            resultado['imagem'] = imagem
            
            # Extrair dados com OCR genérico
            dados_ocr = self.ocr.extrair_dados_completos(imagem, tipo_grafico)
            
            # Mostrar resultado do OCR
            print(f"\n📋 Resultado do OCR (fallback):")
            for msg in dados_ocr.get('mensagens', []):
                print(f"   {msg}")
            
            # Validar dados
            dados_validados = self._validar_dados_fallback(dados_ocr)
            
            resultado['dados'] = dados_validados
            resultado['sucesso'] = True
            resultado['fallback_used'] = True
            print(f"\n✅ Fallback concluído com sucesso!")
            
        except Exception as e:
            resultado['erro'] = f"Erro no fallback: {str(e)}"
            print(f"❌ Erro no fallback: {e}")
        
        return resultado
    
    def _validar_dados_fallback(self, dados_ocr: Dict) -> Dict:
        """
        Valida dados do OCR genérico (versão simplificada).
        """
        dados = dados_ocr.get('dados_extraidos', {})
        
        print("\n🔍 Validando dados do fallback...")
        
        # Extrair valores disponíveis
        valores = []
        categorias = []
        
        # Tentar extrair de diferentes fontes
        if dados.get('pares_categoria_valor'):
            pares = dados['pares_categoria_valor']
            categorias = [p[0] for p in pares]
            valores = [p[1] for p in pares]
            print(f"📊 Usando pares categoria-valor: {pares}")
        
        elif dados.get('valores_barras'):
            valores = dados['valores_barras']
            categorias = dados.get('categorias', [])
            print(f"📊 Usando valores das barras: {valores}")
        
        elif dados.get('valores_eixo_y'):
            valores = dados['valores_eixo_y']
            print(f"📊 Usando valores do eixo Y: {valores}")
        
        # Converter valores para float
        valores_float = []
        for v in valores:
            try:
                valores_float.append(float(v))
            except (ValueError, TypeError):
                pass
        
        resultado = {
            'titulo': dados.get('titulo', 'Gráfico não identificado'),
            'fonte': dados.get('fonte', 'Fonte não detectada'),
            'valores': valores_float,
            'categorias': categorias,
            'eixo_y_min': dados.get('eixo_y_min', 0.0),
            'ocr_confianca': dados_ocr.get('confianca_geral', 0),
            'ocr_mensagens': dados_ocr.get('mensagens', []),
            'fallback': True
        }
        
        print(f"\n✅ Dados validados (fallback):")
        print(f"   Título: {resultado['titulo']}")
        print(f"   Valores: {resultado['valores']}")
        print(f"   Categorias: {resultado['categorias']}")
        
        return resultado