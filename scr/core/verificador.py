# scr/core/verificador.py
"""
VERIFICADOR DE GRÁFICOS - VERSÃO ÚNICA OTIMIZADA
Contém: regras básicas + regras melhoradas + integração
"""

from typing import Dict, List, Optional, Any
from datetime import datetime


class VerificadorGrafico:
    def __init__(self):
        self.alertas = []
        self.regras_verificadas = 0
        self.regras_aprovadas = 0
        self.historico = []
    
    def adicionar_alerta(self, tipo: str, mensagem: str, severidade: str = "MEDIA") -> Dict:
        """
        Adiciona um alerta padronizado
        
        Args:
            tipo: "EIXO_Y", "PROPORCAO", "FONTE", etc.
            mensagem: Descrição em português
            severidade: "BAIXA", "MEDIA", "ALTA", "CRITICA"
        """
        alerta = {
            'id': len(self.alertas) + 1,
            'tipo': tipo,
            'mensagem': mensagem,
            'severidade': severidade
        }
        self.alertas.append(alerta)
        return alerta
    
    # ===== REGRAS BÁSICAS =====
    def verificar_eixo_y(self, dados: Dict) -> bool:
        """
        REGRA 1: Verifica se o eixo Y começa em zero para gráficos de barras
        
        Args:
            dados: Dicionário com 'tipo', 'eixo_y_min', 'valores'
        """
        self.regras_verificadas += 1
        
        # Verifica se é gráfico de barras
        if dados.get('tipo') not in ['barras_verticais', 'barras_horizontais']:
            return True  # Regra não se aplica
        
        # Pega o valor mínimo do eixo
        eixo_min = dados.get('eixo_y_min', 0)
        
        # Se eixo não começar em 0
        if eixo_min > 0:
            valores = dados.get('valores', [1])
            if valores:
                porcentagem = (eixo_min / max(valores)) * 100
                self.adicionar_alerta(
                    tipo="EIXO_Y",
                    mensagem=f"Eixo começa em {eixo_min} ({porcentagem:.1f}% do valor máximo)",
                    severidade="ALTA" if porcentagem > 10 else "MEDIA"
                )
                return False
        
        self.regras_aprovadas += 1
        return True
    
    def verificar_proporcoes(self, dados: Dict) -> bool:
        """
        REGRA 2: Verifica se proporções correspondem a valores numéricos
        """
        self.regras_verificadas += 1
        
        valores = dados.get('valores', [])
        if not valores or len(valores) < 2:
            return True
        
        # Para pizza, verificar se soma é 100%
        if dados.get('tipo') == 'pizza':
            soma = sum(valores)
            if abs(soma - 100) > 2:
                self.adicionar_alerta(
                    tipo="PROPORCAO",
                    mensagem=f"Soma dos percentuais é {soma:.1f}% (deveria ser 100%)",
                    severidade="ALTA"
                )
                return False
            self.regras_aprovadas += 1
            return True
        
        # Para outros tipos, verificar consistência
        self.regras_aprovadas += 1
        return True
    
    # ===== REGRAS MELHORADAS =====
    def verificar_titulo(self, dados: Dict) -> bool:
        """
        REGRA 3: Verifica se o gráfico tem título
        """
        self.regras_verificadas += 1
        
        titulo = dados.get('titulo', '')
        if titulo is None:
            titulo = ''
        titulo = str(titulo).strip()
        
        if not titulo or titulo == "Não identificado":
            self.adicionar_alerta(
                tipo="TITULO",
                mensagem="Gráfico não possui título identificado",
                severidade="MEDIA"
            )
            return False
        elif len(titulo) < 5:
            self.adicionar_alerta(
                tipo="TITULO_CURTO",
                mensagem=f"Título muito curto ('{titulo}')",
                severidade="BAIXA"
            )
            return True
        
        self.regras_aprovadas += 1
        return True
    
    def verificar_fonte(self, dados: Dict) -> bool:
        """
        REGRA 4: Verifica se há fonte dos dados
        """
        self.regras_verificadas += 1
        
        fonte = dados.get('fonte', '')
        if fonte is None:
            fonte = ''
        fonte = str(fonte).strip()
        
        if not fonte or fonte == "Não identificada":
            self.adicionar_alerta(
                tipo="FONTE",
                mensagem="Fonte dos dados não especificada",
                severidade="ALTA"
            )
            return False
        
        self.regras_aprovadas += 1
        return True
    
    # ===== MÉTODO PRINCIPAL =====
    def verificar_tudo(self, dados: Dict) -> Dict:
        """
        Executa TODAS as verificações disponíveis
        
        Args:
            dados: Dicionário com dados do gráfico
        
        Returns:
            Dicionário com resultados das verificações
        """
        # Limpa estado anterior
        self.alertas = []
        self.regras_verificadas = 0
        self.regras_aprovadas = 0
        
        # Executa todas as verificações em ordem
        resultados = {
            'eixo_y': self.verificar_eixo_y(dados),
            'proporcoes': self.verificar_proporcoes(dados),
            'titulo': self.verificar_titulo(dados),
            'fonte': self.verificar_fonte(dados)
        }
        
        # Salva no histórico
        self.historico.append({
            'dados': dados,
            'resultados': resultados,
            'alertas': self.alertas.copy(),
            'timestamp': datetime.now()
        })
        
        return resultados
    
    # ===== RELATÓRIO =====
    def gerar_relatorio(self, dados: Dict) -> Dict:
        """
        Gera um relatório completo
        
        Args:
            dados: Dicionário com dados do gráfico
        
        Returns:
            Dicionário com relatório estruturado
        """
        # Executa verificações se necessário
        if self.regras_verificadas == 0:
            self.verificar_tudo(dados)
        
        # Cabeçalho
        print("=" * 70)
        print("RELATÓRIO DE VERIFICAÇÃO DE GRÁFICO - CONRE-3")
        print("=" * 70)
        
        # Informações do gráfico
        print(f"\n📊 INFORMAÇÕES DO GRÁFICO:")
        print(f"   • Tipo: {dados.get('tipo', 'desconhecido')}")
        print(f"   • Título: {dados.get('titulo', 'Não informado')}")
        print(f"   • Fonte: {dados.get('fonte', 'Não informada')}")
        print(f"   • Valores: {dados.get('valores', [])}")
        print(f"   • Categorias: {dados.get('categorias', [])}")
        
        # Resumo das verificações
        print(f"\n✅ VERIFICAÇÕES REALIZADAS:")
        print(f"   • Regras verificadas: {self.regras_verificadas}")
        print(f"   • Regras aprovadas: {self.regras_aprovadas}")
        taxa_aprovacao = (self.regras_aprovadas / self.regras_verificadas * 100) if self.regras_verificadas > 0 else 0
        print(f"   • Taxa de aprovação: {taxa_aprovacao:.1f}%")
        
        # Alertas por severidade
        if self.alertas:
            criticos = [a for a in self.alertas if a['severidade'] == 'CRITICA']
            altos = [a for a in self.alertas if a['severidade'] == 'ALTA']
            medios = [a for a in self.alertas if a['severidade'] == 'MEDIA']
            baixos = [a for a in self.alertas if a['severidade'] == 'BAIXA']
            
            print(f"\n⚠️  ALERTAS ENCONTRADOS:")
            print(f"   • Críticos: {len(criticos)}")
            print(f"   • Altos: {len(altos)}")
            print(f"   • Médios: {len(medios)}")
            print(f"   • Baixos: {len(baixos)}")
            
            # Detalha cada alerta
            print(f"\n📝 DETALHAMENTO DOS ALERTAS:")
            for alerta in self.alertas:
                severidade_emoji = {
                    'CRITICA': '🔴',
                    'ALTA': '🟠', 
                    'MEDIA': '🟡',
                    'BAIXA': '🟢'
                }.get(alerta['severidade'], '⚪')
                
                print(f"   {severidade_emoji} [{alerta['tipo']}] {alerta['mensagem']}")
        else:
            print(f"\n🎉 NENHUM ALERTA ENCONTRADO!")
            print("   O gráfico segue as boas práticas verificadas.")
        
        # Rodapé
        print("\n" + "=" * 70)
        print("CONRE-3 | Ferramenta Educacional v1.0")
        print("=" * 70)
        
        # Retorna dados estruturados
        return {
            'regras_verificadas': self.regras_verificadas,
            'regras_aprovadas': self.regras_aprovadas,
            'alertas': self.alertas,
            'pontuacao': taxa_aprovacao
        }
    
    # ===== PARA INTEGRAÇÃO COM ANALISADORES =====
    def preparar_dados_analisador(self, dados_analisador: Dict, tipo: str) -> Dict:
        """
        Converte dados do analisador específico para formato do verificador
        
        Args:
            dados_analisador: Dados retornados pelo analisador
            tipo: Tipo de gráfico
        
        Returns:
            Dicionário no formato esperado pelo verificador
        """
        dados_verificador = {
            'tipo': tipo,
            'titulo': dados_analisador.get('metadados', {}).get('titulo', ''),
            'fonte': dados_analisador.get('metadados', {}).get('fonte', ''),
            'valores': [],
            'categorias': [],
            'eixo_y_min': 0
        }
        
        if tipo == 'pizza':
            # Pizza: valores são percentuais
            fatias = dados_analisador.get('dados_especificos', {}).get('fatias', [])
            dados_verificador['valores'] = [f.get('percentual', 0) for f in fatias]
            dados_verificador['categorias'] = [f.get('rotulo', f'Fatia {i+1}') for i, f in enumerate(fatias)]
            
        elif tipo == 'barras_verticais':
            # Barras verticais
            barras = dados_analisador.get('dados_especificos', {}).get('barras', [])
            dados_verificador['valores'] = [b.get('valor', 0) for b in barras]
            dados_verificador['categorias'] = [b.get('rotulo', f'Barra {i+1}') for i, b in enumerate(barras)]
            dados_verificador['eixo_y_min'] = dados_analisador.get('dados_especificos', {}).get('eixo_y_min', 0)
                
        elif tipo == 'barras_horizontais':
            # Barras horizontais
            barras = dados_analisador.get('dados_especificos', {}).get('barras', [])
            dados_verificador['valores'] = [b.get('valor', 0) for b in barras]
            dados_verificador['categorias'] = [b.get('rotulo', f'Barra {i+1}') for i, b in enumerate(barras)]
            dados_verificador['eixo_y_min'] = dados_analisador.get('dados_especificos', {}).get('eixo_x_min', 0)
            
        elif tipo == 'linhas':
            # Linhas - simplificado
            series = dados_analisador.get('dados_especificos', {}).get('series', [])
            if series:
                # Pega valores da primeira série como exemplo
                pontos = series[0].get('pontos', [])
                if pontos:
                    dados_verificador['valores'] = [p.get('y_rel', 0) for p in pontos]
                dados_verificador['categorias'] = [s.get('nome', f'Série {i+1}') for i, s in enumerate(series)]
        
        return dados_verificador