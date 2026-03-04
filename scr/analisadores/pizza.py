# scr/analisadores/pizza.py
"""
ANALISADOR DE GRÁFICOS DE PIZZA
Detecta fatias, ângulos, percentuais, rótulos e valores
"""

import cv2
import numpy as np
import math
import re
import pytesseract
from typing import Dict, List, Optional, Tuple, Any

# CORREÇÃO: Import da classe base (relativo)
from .base import AnalisadorBase
from ..utils.imagem import (
    preprocessar_para_ocr,
    detectar_circulo_principal,
    extrair_regioes_proximas,
    calcular_proporcao_linear
)


class AnalisadorPizza(AnalisadorBase):
    """
    Analisador especializado em gráficos de pizza/torta.
    
    Características:
    - Detecta círculo da pizza
    - Identifica fatias por mudanças de cor
    - Extrai ângulos e percentuais
    - OCR para rótulos e valores
    - Valida soma 100%
    """
    
    # Cores comuns em gráficos de pizza (HSV)
    CORES_PIZZA = [
        {'nome': 'Azul', 'lower': (100, 50, 50), 'upper': (130, 255, 255)},
        {'nome': 'Vermelho', 'lower': (0, 50, 50), 'upper': (10, 255, 255)},
        {'nome': 'Vermelho2', 'lower': (160, 50, 50), 'upper': (180, 255, 255)},
        {'nome': 'Verde', 'lower': (40, 50, 50), 'upper': (80, 255, 255)},
        {'nome': 'Amarelo', 'lower': (20, 50, 50), 'upper': (35, 255, 255)},
        {'nome': 'Laranja', 'lower': (5, 50, 50), 'upper': (15, 255, 255)},
        {'nome': 'Roxo', 'lower': (130, 50, 50), 'upper': (160, 255, 255)},
        {'nome': 'Rosa', 'lower': (140, 50, 50), 'upper': (170, 255, 255)},
        {'nome': 'Marrom', 'lower': (10, 50, 30), 'upper': (20, 255, 150)}
    ]
    
    def __init__(self, 
                 imagem_path: str, 
                 tesseract_cmd: Optional[str] = None,
                 num_categorias: Optional[int] = None):
        """
        Inicializa analisador de pizza.
        
        Args:
            imagem_path: Caminho da imagem
            tesseract_cmd: Caminho do Tesseract
            num_categorias: Número esperado de categorias (ajuda na detecção)
        """
        super().__init__(imagem_path, tesseract_cmd)
        self.num_categorias = num_categorias
        self.num_categorias_usuario = num_categorias  # Para compatibilidade
        
        # Atributos específicos
        self.circulo = None
        self.fatias = []
        self.centro = None
        self.raio = 0
        
        self._adicionar_mensagem(f"🍕 Analisador Pizza inicializado")
        if num_categorias:
            self._adicionar_mensagem(f"📊 Categorias informadas: {num_categorias}")
    
    def _get_tipo_grafico(self) -> str:
        """Retorna o tipo de gráfico."""
        return 'pizza'
    
    def extrair_elementos(self) -> Dict[str, Any]:
        """
        Método principal de extração para gráficos de pizza.
        
        Fluxo:
        1. Extrair título e fonte
        2. Encontrar círculo da pizza
        3. Detectar fatias por cor
        4. Extrair rótulos e valores
        5. Calcular percentuais
        6. Validar resultados
        """
        try:
            self._adicionar_mensagem("🔍 Iniciando extração de pizza...")
            
            # ===========================================
            # PASSO 1: EXTRAIR TÍTULO E FONTE
            # ===========================================
            self._extrair_titulo_fonte()
            
            # ===========================================
            # PASSO 2: ENCONTRAR CÍRCULO
            # ===========================================
            self._encontrar_circulo()
            if not self.circulo:
                return self._criar_resultado_erro("Não foi possível encontrar o círculo da pizza")
            
            # ===========================================
            # PASSO 3: DETECTAR FATIAS
            # ===========================================
            self._detectar_fatias()
            
            if not self.fatias:
                return self._criar_resultado_erro("Nenhuma fatia detectada")
            
            # ===========================================
            # PASSO 4: EXTRAIR RÓTULOS E VALORES
            # ===========================================
            self._extrair_rotulos_valores()
            
            # ===========================================
            # PASSO 5: CALCULAR PERCENTUAIS
            # ===========================================
            self._calcular_percentuais()
            
            # ===========================================
            # PASSO 6: CRIAR RESULTADO
            # ===========================================
            dados_especificos = self._criar_dados_especificos()
            
            return self._criar_resultado_sucesso(dados_especificos)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return self._criar_resultado_erro(f"Erro durante análise: {str(e)}")
    
    def _detectar_regioes_grafico(self) -> Optional[Tuple[int, int, int, int]]:
        """Implementação do método abstrato - detecta região do gráfico."""
        regioes = self._separar_regioes()
        return detectar_contorno_principal(regioes['grafico'])
    
    def _extrair_titulo_fonte(self):
        """Extrai título e fonte da imagem."""
        regioes = self._separar_regioes()
        
        # Título
        titulo = self._extrair_texto_regiao(regioes['titulo'])
        if titulo:
            # Limpar caracteres especiais
            titulo = re.sub(r'[^a-zA-Z0-9áéíóúãõç\s\-]', '', titulo).strip()
            self.metadados['titulo'] = titulo
            self._adicionar_mensagem(f"📝 Título: {titulo}")
        else:
            self.metadados['titulo'] = "Não identificado"
        
        # Fonte (procurar por "Fonte:")
        texto_fonte = self._extrair_texto_regiao(regioes['fonte'])
        for linha in texto_fonte.split('\n'):
            if 'Fonte:' in linha or 'fonte:' in linha.lower():
                self.metadados['fonte'] = linha.strip()
                self._adicionar_mensagem(f"📌 Fonte: {linha.strip()}")
                break
        
        if not self.metadados['fonte']:
            self.metadados['fonte'] = "Não identificada"
    
    def _extrair_texto_regiao(self, regiao, tipo='texto'):
        """Extrai texto de uma região específica"""
        try:
            if regiao.size == 0:
                return ""
            
            regiao = cv2.resize(regiao, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
            
            if len(regiao.shape) == 3:
                gray = cv2.cvtColor(regiao, cv2.COLOR_BGR2GRAY)
            else:
                gray = regiao
            
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            gray = clahe.apply(gray)
            
            binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                          cv2.THRESH_BINARY, 11, 2)
            
            if tipo == 'numero':
                config = '--psm 8 --oem 3 -c tessedit_char_whitelist=0123456789'
            else:
                config = '--psm 6 --oem 3'
            
            texto = pytesseract.image_to_string(binary, config=config).strip()
            return texto
            
        except Exception as e:
            self._adicionar_mensagem(f"⚠️ Erro no OCR: {e}")
            return ""
    
    def _extrair_fonte(self, regiao_fonte):
        """Extrai a fonte da imagem"""
        try:
            gray = cv2.cvtColor(regiao_fonte, cv2.COLOR_BGR2GRAY)
            
            for thresh in [150, 180, 200]:
                _, binary = cv2.threshold(gray, thresh, 255, cv2.THRESH_BINARY)
                binary = cv2.resize(binary, None, fx=3, fy=3)
                
                texto = pytesseract.image_to_string(binary, config='--psm 6').strip()
                
                if "Fonte:" in texto or "fonte:" in texto.lower():
                    return texto
            
        except Exception as e:
            self._adicionar_mensagem(f"⚠️ Erro ao extrair fonte: {e}")
        
        return "Não identificada"
    
    def _encontrar_circulo(self):
        """Encontra o círculo da pizza."""
        regioes = self._separar_regioes()
        img_grafico = regioes['grafico']
        
        # Detectar círculo
        circulo = detectar_circulo_principal(img_grafico)
        
        if circulo:
            cx, cy, raio = circulo
            # Ajustar coordenadas para imagem original
            altura_titulo = int(self.altura * 0.12)
            self.centro = (cx, cy + altura_titulo)
            self.raio = raio
            self.circulo = (cx, cy + altura_titulo, raio)
            
            self._adicionar_mensagem(f"🎯 Círculo encontrado: centro=({cx}, {cy+altura_titulo}), raio={raio}")
    
    def _detectar_fatias(self):
        """Detecta as fatias da pizza"""
        regioes = self._separar_regioes()
        img_grafico = regioes['grafico']
        
        if not self.circulo:
            return
        
        cx, cy, raio = self.circulo
        cy_grafico = cy - int(self.altura * 0.12)  # Ajustar para coordenadas do gráfico
        
        # Amostrar cores ao redor da pizza
        amostras = []
        raio_amostra = int(raio * 0.7)
        
        h, w = img_grafico.shape[:2]
        
        for ang in range(0, 360, 2):
            x = int(cx + raio_amostra * math.cos(math.radians(ang)))
            y = int(cy_grafico + raio_amostra * math.sin(math.radians(ang)))
            
            if 0 <= x < w and 0 <= y < h:
                cor = img_grafico[y, x]
                amostras.append((ang, cor))
        
        if len(amostras) < 30:
            self._adicionar_mensagem("⚠️ Poucas amostras coletadas")
            return
        
        # Detectar mudanças de cor
        amostras.sort(key=lambda a: a[0])
        mudancas = []
        
        if amostras:
            cor_anterior = amostras[0][1]
            
            for i in range(1, len(amostras)):
                ang, cor = amostras[i]
                diff = np.sum(np.abs(cor.astype(np.int32) - cor_anterior.astype(np.int32)))
                
                if diff > 50:
                    mudancas.append(ang)
                    cor_anterior = cor
        
        if len(mudancas) < 2:
            self._adicionar_mensagem("⚠️ Poucas mudanças de cor detectadas")
            return
        
        # Criar fatias baseado nos ângulos de mudança
        angulos_fatias = [0] + mudancas + [360]
        angulos_fatias = sorted(list(set(angulos_fatias)))
        
        # Se temos número esperado de categorias, tentar ajustar
        if self.num_categorias and len(angulos_fatias) - 1 != self.num_categorias:
            self._adicionar_mensagem(f"🔄 Ajustando de {len(angulos_fatias)-1} para {self.num_categorias} fatias")
            angulos_fatias = self._ajustar_numero_fatias(angulos_fatias, self.num_categorias)
        
        # Criar fatias
        for i in range(len(angulos_fatias) - 1):
            ang_inicio = angulos_fatias[i]
            ang_fim = angulos_fatias[i + 1]
            ang_medio = (ang_inicio + ang_fim) / 2
            
            self.fatias.append({
                'id': i + 1,
                'angulo_inicio': ang_inicio,
                'angulo_fim': ang_fim,
                'angulo_medio': ang_medio,
                'percentual': 0,  # Será calculado depois
                'rotulo': None,
                'valor_detectado': None,
                'explodido': False
            })
        
        self._adicionar_mensagem(f"✅ {len(self.fatias)} fatias detectadas")
    
    def _ajustar_numero_fatias(self, angulos: List[float], num_desejado: int) -> List[float]:
        """Ajusta o número de fatias para o esperado."""
        num_atual = len(angulos) - 1
        
        if num_atual == num_desejado:
            return angulos
        
        if num_atual < num_desejado:
            # Precisa dividir algumas fatias
            while len(angulos) - 1 < num_desejado:
                # Encontrar maior intervalo
                maiores = []
                for i in range(len(angulos) - 1):
                    tamanho = angulos[i + 1] - angulos[i]
                    maiores.append((tamanho, i))
                
                maiores.sort(reverse=True)
                idx = maiores[0][1]
                
                # Dividir ao meio
                meio = (angulos[idx] + angulos[idx + 1]) / 2
                angulos.insert(idx + 1, meio)
        else:
            # Precisa combinar fatias
            while len(angulos) - 1 > num_desejado:
                # Encontrar menor intervalo para combinar
                menores = []
                for i in range(len(angulos) - 2):
                    tamanho = angulos[i + 1] - angulos[i]
                    menores.append((tamanho, i))
                
                menores.sort()
                idx = menores[0][1]
                
                # Remover o ponto (combinar com próximo)
                del angulos[idx + 1]
        
        return angulos
    
    def _extrair_rotulos_valores(self):
        """Extrai rótulos e valores próximos a cada fatia."""
        regioes = self._separar_regioes()
        img_grafico = regioes['grafico']
        altura_titulo = int(self.altura * 0.12)
        
        for fatia in self.fatias:
            angulo = fatia['angulo_medio']
            
            # Tentar diferentes distâncias do centro
            for distancia in [int(self.raio * 1.2), int(self.raio * 1.5), int(self.raio * 1.8)]:
                x = int(self.centro[0] + distancia * math.cos(math.radians(angulo)))
                y = int(self.centro[1] + distancia * math.sin(math.radians(angulo)))
                
                # Ajustar y para coordenadas do gráfico
                y_grafico = y - altura_titulo
                
                if 0 <= x < self.largura and 0 <= y_grafico < img_grafico.shape[0]:
                    # Extrair região ao redor do ponto
                    tamanho = 60
                    x1 = max(0, x - tamanho)
                    x2 = min(self.largura, x + tamanho)
                    y1 = max(0, y_grafico - tamanho)
                    y2 = min(img_grafico.shape[0], y_grafico + tamanho)
                    
                    if x2 - x1 > 30 and y2 - y1 > 30:
                        regiao = img_grafico[y1:y2, x1:x2]
                        
                        # OCR para texto
                        texto = self._extrair_texto_regiao(regiao, 'texto')
                        
                        if texto:
                            # Extrair números
                            numeros = re.findall(r'\d+', texto)
                            texto_limpo = re.sub(r'\d+', '', texto).strip()
                            texto_limpo = re.sub(r'[^a-zA-Záéíóúãõç\s]', '', texto_limpo).strip()
                            
                            # Guardar informações
                            if texto_limpo and len(texto_limpo) > 1:
                                fatia['rotulo'] = texto_limpo
                            
                            if numeros:
                                # Pegar o primeiro número que parece percentual (1-100)
                                for num in numeros:
                                    num_int = int(num)
                                    if 1 <= num_int <= 100:
                                        fatia['valor_detectado'] = num_int
                                        break
                            
                            break  # Encontrou algo, não precisa tentar outras distâncias
    
    def _calcular_percentuais(self):
        """Calcula percentuais baseado nos ângulos."""
        total_angulos = 0
        
        for fatia in self.fatias:
            angulo = fatia['angulo_fim'] - fatia['angulo_inicio']
            if angulo < 0:
                angulo += 360
            fatia['angulo_tamanho'] = angulo
            total_angulos += angulo
        
        if total_angulos > 0:
            for fatia in self.fatias:
                percentual = (fatia['angulo_tamanho'] / total_angulos) * 100
                fatia['percentual'] = round(percentual, 1)
    
    def _criar_dados_especificos(self) -> Dict:
        """Cria dicionário com dados específicos de pizza."""
        # Ordenar fatias por ângulo
        self.fatias.sort(key=lambda f: f['angulo_inicio'])
        
        # Preparar lista final
        fatias_final = []
        for i, fatia in enumerate(self.fatias):
            rotulo = fatia.get('rotulo')
            if not rotulo:
                if fatia.get('valor_detectado'):
                    rotulo = f"{fatia['valor_detectado']}%"
                else:
                    rotulo = f"Fatia {i+1}"
            
            # Limpar rótulo
            if rotulo:
                rotulo = re.sub(r'\s+', ' ', rotulo).strip()
                if len(rotulo) > 25:
                    rotulo = rotulo[:25] + "..."
            
            fatias_final.append({
                'id': i + 1,
                'rotulo': rotulo,
                'percentual': fatia['percentual'],
                'valor_detectado': fatia.get('valor_detectado'),
                'angulo_inicio': round(fatia['angulo_inicio']),
                'angulo_fim': round(fatia['angulo_fim'])
            })
        
        # Calcular soma
        soma = sum(f['percentual'] for f in fatias_final)
        
        return {
            'tipo': 'pizza',
            'fatias': fatias_final,
            'total_fatias': len(fatias_final),
            'soma_percentuais': round(soma, 1),
            'centro': self.centro,
            'raio': self.raio,
            'valores': [f['percentual'] for f in fatias_final],
            'categorias': [f['rotulo'] for f in fatias_final]
        }
    
    def _validar_dados(self, dados: Dict) -> Dict:
        """Valida dados extraídos da pizza."""
        validacoes = super()._validar_dados(dados)
        
        fatias = dados.get('fatias', [])
        soma = dados.get('soma_percentuais', 0)
        num_fatias = len(fatias)
        
        alertas = []
        
        # Regra 1: Soma deve ser aproximadamente 100%
        if abs(soma - 100) > 2:
            alertas.append({
                'tipo': 'SOMA_INCORRETA',
                'severidade': 'ALTA',
                'mensagem': f'Soma total é {soma}% (deveria ser 100%)'
            })
        
        # Regra 2: Número de categorias
        if self.num_categorias_usuario:
            if abs(num_fatias - self.num_categorias_usuario) > 1:
                alertas.append({
                    'tipo': 'NUMERO_CATEGORIAS',
                    'severidade': 'MEDIA',
                    'mensagem': f'Número de fatias ({num_fatias}) diferente do informado ({self.num_categorias_usuario})'
                })
        else:
            if num_fatias < 2:
                alertas.append({
                    'tipo': 'POUCAS_FATIAS',
                    'severidade': 'ALTA',
                    'mensagem': f'Apenas {num_fatias} fatias (mínimo recomendado: 2)'
                })
            elif num_fatias > 8:
                alertas.append({
                    'tipo': 'MUITAS_FATIAS',
                    'severidade': 'BAIXA',
                    'mensagem': f'{num_fatias} fatias (recomendado ≤ 8)'
                })
        
        # Regra 3: Rótulos
        if fatias:
            rotulos_validos = sum(1 for f in fatias if f.get('rotulo') and 'Fatia' not in f['rotulo'])
            if rotulos_validos < num_fatias * 0.5:
                alertas.append({
                    'tipo': 'ROTULOS_INSUFICIENTES',
                    'severidade': 'MEDIA',
                    'mensagem': f'Apenas {rotulos_validos}/{num_fatias} fatias com rótulos identificados'
                })
        
        validacoes['alertas'] = alertas
        validacoes['valido'] = len(alertas) == 0
        
        return validacoes
    
    def _criar_resultado_erro(self, mensagem: str) -> Dict[str, Any]:
        """Sobrescreve método da classe base para formato específico."""
        return {
            'erro': True,
            'mensagem': mensagem,
            'metadados': self.metadados,
            'caracteristicas': self.caracteristicas,
            'fatias': [],
            'total_fatias': 0,
            'soma_percentuais': 0,
            'confianca': 0.0,
            'mensagens': self.mensagens
        }
    
    def _criar_resultado_sucesso(self, dados_especificos: Dict) -> Dict[str, Any]:
        """Sobrescreve método da classe base para formato específico."""
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
            'fatias': dados_especificos['fatias'],
            'total_fatias': dados_especificos['total_fatias'],
            'soma_percentuais': dados_especificos['soma_percentuais'],
            'confianca': self.confianca_geral,
            'mensagens': self.mensagens,
            'validacoes': validacoes
        }


# ===========================================
# FUNÇÃO PARA TESTE (mantida para compatibilidade)
# ===========================================
def testar_analisador():
    """Testa o analisador com todos os gráficos"""
    
    import os
    import glob
    
    print("🍕 ANALISADOR DE GRÁFICOS DE PIZZA")
    print("="*70)
    
    pasta = 'data/exemplos/pizza'
    if not os.path.exists(pasta):
        print(f"❌ Pasta não encontrada: {pasta}")
        return
    
    padrao = os.path.join(pasta, 'pizza_*.png')
    arquivos = sorted(glob.glob(padrao))
    
    if not arquivos:
        print("❌ Nenhum arquivo encontrado")
        return
    
    resultados = []
    
    for arquivo in arquivos:
        nome = os.path.basename(arquivo)
        print(f"\n{'='*70}")
        print(f"🍕 Testando: {nome}")
        print('='*70)
        
        # Determinar número esperado de categorias
        num_categorias = None
        if '3d' in nome:
            num_categorias = 5
        elif '4_fatias' in nome:
            num_categorias = 4
        elif 'eleicoes' in nome:
            num_categorias = 5
        elif 'legenda' in nome:
            num_categorias = 6
        elif 'pb' in nome:
            num_categorias = 4
        elif 'pequenos' in nome:
            num_categorias = 6
        elif 'rosca' in nome:
            num_categorias = 3
        elif 'simples' in nome:
            num_categorias = 3
        
        try:
            print(f"📊 Analisando...")
            analisador = AnalisadorPizza(arquivo, num_categorias=num_categorias)
            resultado = analisador.extrair_elementos()
            
            if resultado.get('erro'):
                print(f"\n❌ ERRO: {resultado['mensagem']}")
            else:
                print(f"\n📊 RESULTADO:")
                print(f"   Total de fatias: {resultado['total_fatias']}")
                print(f"   Soma: {resultado['soma_percentuais']}%")
                print(f"   Confiança: {resultado['confianca']}%")
                print(f"   📌 Título: {resultado['metadados']['titulo']}")
                print(f"   📌 Fonte: {resultado['metadados']['fonte']}")
                
                print(f"\n   📋 FATIAS:")
                for fatia in resultado['fatias']:
                    valor_str = f" [valor: {fatia['valor_detectado']}%]" if fatia.get('valor_detectado') else ""
                    print(f"      {fatia['id']}. {fatia['rotulo']}: {fatia['percentual']}%{valor_str}")
                
                resultados.append({
                    'arquivo': nome,
                    'total_fatias': resultado['total_fatias'],
                    'soma': resultado['soma_percentuais'],
                    'confianca': resultado['confianca']
                })
                
        except Exception as e:
            print(f"❌ Erro inesperado: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Resumo final
    print(f"\n{'='*70}")
    print("📊 RESUMO FINAL")
    print('='*70)
    
    if resultados:
        print(f"Total de gráficos testados: {len(resultados)}")
        for r in resultados:
            print(f"   {r['arquivo']}: {r['total_fatias']} fatias, soma {r['soma']}%, confiança {r['confianca']}%")
    else:
        print("Nenhum resultado obtido")


# ===========================================
# EXECUÇÃO
# ===========================================
if __name__ == "__main__":
    testar_analisador()