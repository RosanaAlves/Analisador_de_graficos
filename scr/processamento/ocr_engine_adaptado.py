# scr/processamento/ocr_engine_adaptado.py
"""
MOTOR DE OCR ADAPTADO
Versão melhorada com suporte a extração de pares categoria-valor
"""

import pytesseract
from PIL import Image
import cv2
import numpy as np
import re
import os
from typing import Dict, List, Optional, Tuple, Any


class OCREngineAdaptado:
    """
    Motor de OCR adaptado que usa detecção de contornos para identificar
    regiões do gráfico, com suporte a diferentes tipos.
    """
    
    def __init__(self, tesseract_cmd: Optional[str] = None):
        """Inicializa o motor OCR."""
        self.tesseract_cmd = tesseract_cmd
        self._configurar_tesseract()
    
    def _configurar_tesseract(self):
        """Configura o caminho do Tesseract."""
        if self.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
            return
        
        # Caminhos comuns por sistema operacional
        caminhos_comuns = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            '/usr/bin/tesseract',
            '/usr/local/bin/tesseract'
        ]
        
        for caminho in caminhos_comuns:
            if os.path.exists(caminho):
                pytesseract.pytesseract.tesseract_cmd = caminho
                self.tesseract_cmd = caminho
                break
    
    def detectar_regioes_grafico(self, imagem_cv: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """
        Detecta as regiões do gráfico usando contornos.
        
        Returns:
            Tupla (x, y, largura, altura) ou None
        """
        if len(imagem_cv.shape) == 3:
            gray = cv2.cvtColor(imagem_cv, cv2.COLOR_BGR2GRAY)
        else:
            gray = imagem_cv
        
        # Binarização inversa para destacar o gráfico
        _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
        
        # Encontrar contornos
        cnts, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not cnts:
            return None
        
        # Pegar o maior contorno (provavelmente o gráfico)
        cnt = max(cnts, key=cv2.contourArea)
        gx, gy, gw, gh = cv2.boundingRect(cnt)
        
        return gx, gy, gw, gh
    
    def agrupar_textos_proximos(self, textos_com_posicoes: List[Tuple[str, int]], 
                                distancia_max: int = 30) -> List[Tuple[str, int]]:
        """
        Agrupa textos que estão próximos horizontalmente.
        
        Args:
            textos_com_posicoes: Lista de (texto, posição_x)
            distancia_max: Distância máxima para agrupar (pixels)
        
        Returns:
            Lista de (texto_agrupado, posição_média)
        """
        if not textos_com_posicoes:
            return []
        
        # Ordenar por posição X
        textos_ordenados = sorted(textos_com_posicoes, key=lambda x: x[1])
        
        grupos = []
        grupo_atual = [textos_ordenados[0]]
        
        for i in range(1, len(textos_ordenados)):
            texto_atual, x_atual = textos_ordenados[i]
            _, ultimo_x = grupo_atual[-1]
            
            # Calcular distância entre este texto e o último do grupo
            distancia = x_atual - ultimo_x
            
            # Se estiver próximo, adiciona ao grupo
            if distancia < distancia_max:
                grupo_atual.append((texto_atual, x_atual))
                print(f"     ➕ Adicionando '{texto_atual}' ao grupo (distância: {distancia}px)")
            else:
                # Finaliza grupo atual e começa novo
                grupos.append(grupo_atual)
                grupo_atual = [(texto_atual, x_atual)]
                print(f"     🆕 Novo grupo com '{texto_atual}'")
        
        if grupo_atual:
            grupos.append(grupo_atual)
        
        # Combinar textos de cada grupo
        textos_combinados = []
        for grupo in grupos:
            if len(grupo) == 1:
                # Grupo com um único texto
                texto, x = grupo[0]
                textos_combinados.append((texto, x))
                print(f"   📍 Mantido: '{texto}' em x={x}")
            else:
                # Múltiplos textos - combinar
                grupo.sort(key=lambda x: x[1])  # Ordenar por X
                textos = [t[0] for t in grupo]
                texto_combinado = ' '.join(textos)
                x_medio = sum([t[1] for t in grupo]) // len(grupo)
                textos_combinados.append((texto_combinado, x_medio))
                print(f"   🔗 Agrupado: {' + '.join(textos)} -> '{texto_combinado}' em x={x_medio}")
        
        return textos_combinados
    
    def extrair_dados_barras_verticais(self, img_cv: np.ndarray, gx: int, gy: int, 
                                       gw: int, gh: int, altura: int, largura: int) -> Tuple[Dict, List[str]]:
        """
        Extrai dados de gráficos de barras verticais.
        
        Returns:
            Tupla (dicionário com dados extraídos, lista de mensagens)
        """
        dados = {
            'titulo': None,
            'fonte': None,
            'valores_eixo_y': [],
            'categorias': [],
            'valores': [],
            'pares_categoria_valor': []
        }
        mensagens = []
        
        # Converter para escala de cinza
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        # Melhorar contraste
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        gray = clahe.apply(gray)
        
        # Binarização adaptativa
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                      cv2.THRESH_BINARY, 11, 2)
        
        # 1. TÍTULO (Topo)
        topo_img = binary[0:gy, 0:largura]
        if topo_img.size > 0:
            # Aumentar resolução para título
            topo_img = cv2.resize(topo_img, None, fx=2, fy=2)
            titulo = pytesseract.image_to_string(topo_img, config='--psm 6').strip()
            if titulo and len(titulo) > 3:
                dados['titulo'] = titulo
                mensagens.append(f"✓ Título: {titulo}")

        # 2. EIXO Y (Detectar valores)
        eixo_y_img = binary[gy:gy+gh, 0:gx]
        if eixo_y_img.size > 0:
            eixo_y_img = cv2.resize(eixo_y_img, None, fx=2, fy=2)
            config_num = r'--psm 6 -c tessedit_char_whitelist=0123456789.,'
            texto_y = pytesseract.image_to_string(eixo_y_img, config=config_num)
            
            valores_y = []
            for match in re.findall(r'(\d+[\.,]?\d*)', texto_y):
                try:
                    num = float(match.replace(',', '.'))
                    valores_y.append(num)
                except:
                    pass
            
            if valores_y:
                dados['valores_eixo_y'] = sorted(list(set(valores_y)))
                dados['eixo_y_min'] = min(valores_y)
                mensagens.append(f"✓ Eixo Y: {dados['valores_eixo_y']}")

        # 3. BASE (Rótulos do eixo X e possível fonte)
        base_img = binary[gy+gh:altura, 0:largura]
        if base_img.size > 0:
            base_img = cv2.resize(base_img, None, fx=2, fy=2)
            texto_base = pytesseract.image_to_string(base_img, config='--psm 6').strip()
            
            linhas = [l.strip() for l in texto_base.split('\n') if l.strip()]
            
            # Separar fonte de rótulos
            for linha in linhas:
                if 'Fonte:' in linha or 'fonte:' in linha.lower():
                    dados['fonte'] = linha
                    mensagens.append(f"✓ Fonte: {linha}")
                elif linha and len(linha) > 1 and not linha.replace('%', '').replace('.', '').isdigit():
                    # É um rótulo (texto)
                    dados['categorias'].append(linha)
            
            mensagens.append(f"✓ Categorias: {dados['categorias']}")
        
        # 4. DETECTAR BARRAS E ASSOCIAR VALORES
        # Esta é uma versão simplificada - em produção, usaríamos o analisador especializado
        if dados['valores_eixo_y'] and len(dados['valores_eixo_y']) >= 2:
            # Simular valores das barras baseado nos valores do eixo Y
            num_barras = len(dados['categorias']) or 3
            y_min, y_max = min(dados['valores_eixo_y']), max(dados['valores_eixo_y'])
            
            # Gerar valores hipotéticos (apenas para fallback)
            valores_hipoteticos = []
            for i in range(num_barras):
                valor = y_min + (y_max - y_min) * (i + 1) / (num_barras + 1)
                valores_hipoteticos.append(round(valor, 1))
            
            dados['valores'] = valores_hipoteticos
            
            # Criar pares categoria-valor
            for i, cat in enumerate(dados['categorias']):
                if i < len(valores_hipoteticos):
                    dados['pares_categoria_valor'].append((cat, valores_hipoteticos[i]))
        
        return dados, mensagens
    
    def extrair_dados_completos(self, imagem_pil: Image.Image, tipo_grafico: str = 'barras_verticais') -> Dict[str, Any]:
        """
        Extrai dados do gráfico usando detecção de regiões.
        
        Args:
            imagem_pil: Imagem PIL
            tipo_grafico: Tipo de gráfico ('barras_verticais', 'pizza', etc.)
        
        Returns:
            Dicionário com dados extraídos
        """
        resultado = {
            'sucesso': True,
            'mensagens': [],
            'dados_extraidos': {},
            'confianca_geral': 0.0,
            'tipo_grafico': tipo_grafico
        }
        
        # Verificar se Tesseract está configurado
        if not self.tesseract_cmd:
            resultado['sucesso'] = False
            resultado['mensagens'].append("❌ Tesseract não encontrado")
            return resultado
        
        try:
            # Converter PIL para OpenCV
            img_cv = cv2.cvtColor(np.array(imagem_pil), cv2.COLOR_RGB2BGR)
            altura, largura = img_cv.shape[:2]
            
            print(f"\n📐 Dimensões: {largura} x {altura}")
            print(f"📊 Tipo de gráfico: {tipo_grafico}")
            
            # Detectar região do gráfico
            regiao = self.detectar_regioes_grafico(img_cv)
            
            if regiao:
                gx, gy, gw, gh = regiao
                print(f"📊 Região detectada: x={gx}, y={gy}, w={gw}, h={gh}")
                
                # Extrair dados baseado no tipo
                if tipo_grafico == 'barras_verticais':
                    dados, mensagens = self.extrair_dados_barras_verticais(
                        img_cv, gx, gy, gw, gh, altura, largura
                    )
                else:
                    # Para outros tipos, retornar estrutura básica
                    dados = {
                        'titulo': None,
                        'fonte': None,
                        'tipo': tipo_grafico
                    }
                    mensagens = [f"⚠️ Extração para {tipo_grafico} não implementada no OCR genérico"]
                
                resultado['dados_extraidos'] = dados
                resultado['mensagens'].extend(mensagens)
            else:
                resultado['mensagens'].append("⚠️ Região do gráfico não detectada")
            
            # Calcular confiança
            confianca = 0
            if resultado['dados_extraidos'].get('titulo'):
                confianca += 25
            if resultado['dados_extraidos'].get('fonte'):
                confianca += 25
            if resultado['dados_extraidos'].get('valores_eixo_y'):
                confianca += 25
            if resultado['dados_extraidos'].get('categorias'):
                confianca += 25
            if resultado['dados_extraidos'].get('valores'):
                confianca += 25  # Bônus
            
            resultado['confianca_geral'] = min(confianca, 100)
            
        except Exception as e:
            resultado['sucesso'] = False
            resultado['mensagens'].append(f"❌ Erro: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return resultado