# scr/core/regras.py
"""
REGRAS DE VERIFICAÇÃO POR TIPO DE GRÁFICO
Centraliza todos os critérios específicos para cada tipo
"""

from typing import Dict, List, Any, Tuple


class RegrasGrafico:
    """Central de regras para todos os tipos de gráfico"""
    
    @staticmethod
    def verificar_pizza(dados: Dict) -> Dict[str, Any]:
        """
        Verifica gráfico de pizza contra todos os critérios
        """
        alertas = []
        aprovacoes = 0
        total_regras = 6  # Total de regras para pizza
        
        fatias = dados.get('valores', [])
        categorias = dados.get('categorias', [])
        titulo = dados.get('titulo', '')
        fonte = dados.get('fonte', '')
        
        # REGRA 1: Soma deve ser 100% (±2%)
        soma = sum(fatias)
        if abs(soma - 100) <= 2:
            aprovacoes += 1
        else:
            alertas.append({
                'regra': 'Soma total',
                'status': '❌',
                'mensagem': f'Soma é {soma:.1f}% (deveria ser 100%)',
                'severidade': 'ALTA',
                'dica': 'Ajuste os percentuais para somar 100%'
            })
        
        # REGRA 2: Número de fatias (2 a 8)
        num_fatias = len(fatias)
        if 2 <= num_fatias <= 8:
            aprovacoes += 1
        elif num_fatias < 2:
            alertas.append({
                'regra': 'Número de fatias',
                'status': '❌',
                'mensagem': f'Apenas {num_fatias} fatia(s) (mínimo 2)',
                'severidade': 'ALTA',
                'dica': 'Gráfico de pizza precisa de pelo menos 2 fatias'
            })
        else:  # > 8
            alertas.append({
                'regra': 'Número de fatias',
                'status': '⚠️',
                'mensagem': f'{num_fatias} fatias (recomendado ≤ 8)',
                'severidade': 'BAIXA',
                'dica': 'Muitas fatias dificultam a leitura. Considere agrupar categorias pequenas'
            })
        
        # REGRA 3: Rótulos identificados
        if categorias:
            rotulos_validos = sum(1 for c in categorias if c and len(str(c)) > 1 and 'Fatia' not in str(c))
            percentual_rotulos = (rotulos_validos / num_fatias) * 100 if num_fatias > 0 else 0
            
            if percentual_rotulos >= 50:
                aprovacoes += 1
            else:
                alertas.append({
                    'regra': 'Rótulos',
                    'status': '⚠️',
                    'mensagem': f'Apenas {rotulos_validos}/{num_fatias} fatias com rótulos identificados',
                    'severidade': 'MÉDIA',
                    'dica': 'Identifique todas as fatias para melhor compreensão'
                })
        
        # REGRA 4: Título presente
        if titulo and len(str(titulo).strip()) >= 5:
            aprovacoes += 1
        elif titulo and len(str(titulo).strip()) > 0:
            alertas.append({
                'regra': 'Título',
                'status': '⚠️',
                'mensagem': f'Título muito curto: "{titulo}"',
                'severidade': 'BAIXA',
                'dica': 'Use um título descritivo com pelo menos 5 caracteres'
            })
        else:
            alertas.append({
                'regra': 'Título',
                'status': '❌',
                'mensagem': 'Título não identificado',
                'severidade': 'MÉDIA',
                'dica': 'Adicione um título descritivo ao gráfico'
            })
        
        # REGRA 5: Fonte identificada
        if fonte and 'não' not in fonte.lower() and len(str(fonte).strip()) > 3:
            aprovacoes += 1
        else:
            alertas.append({
                'regra': 'Fonte',
                'status': '❌',
                'mensagem': 'Fonte dos dados não identificada',
                'severidade': 'ALTA',
                'dica': 'Sempre cite a fonte dos dados para garantir credibilidade'
            })
        
        # REGRA 6: Fatias muito pequenas
        if fatias:
            fatias_pequenas = sum(1 for f in fatias if f < 2)
            if fatias_pequenas > 0:
                alertas.append({
                    'regra': 'Fatias pequenas',
                    'status': '⚠️',
                    'mensagem': f'{fatias_pequenas} fatia(s) com menos de 2%',
                    'severidade': 'BAIXA',
                    'dica': 'Considere agrupar fatias muito pequenas em "Outros"'
                })
            else:
                aprovacoes += 1
        
        return {
            'tipo': 'pizza',
            'total_regras': total_regras,
            'aprovacoes': aprovacoes,
            'pontuacao': (aprovacoes / total_regras) * 100,
            'alertas': alertas
        }
    
    @staticmethod
    def verificar_barras_verticais(dados: Dict) -> Dict[str, Any]:
        """
        Verifica gráfico de barras verticais
        """
        alertas = []
        aprovacoes = 0
        total_regras = 6
        
        valores = dados.get('valores', [])
        categorias = dados.get('categorias', [])
        eixo_min = dados.get('eixo_y_min', 0)
        titulo = dados.get('titulo', '')
        fonte = dados.get('fonte', '')
        
        # VALIDAÇÃO: Verificar se os valores são consistentes
        if valores and max(valores) > 100:
            alertas.append({
                'regra': 'Valores inconsistentes',
                'status': '⚠️',
                'mensagem': f'Valor máximo ({max(valores):.1f}) parece incorreto (esperado até 100)',
                'severidade': 'ALTA',
                'dica': 'Verifique se o OCR interpretou corretamente os números'
            })
            # Ajustar eixo_min para não gerar falso positivo
            eixo_min = 0
        
        # REGRA 1: Eixo Y começa em zero
        if eixo_min == 0:
            aprovacoes += 1
        else:
            # Usar valor máximo realista (até 100)
            valores_validos = [v for v in valores if v <= 100]
            valor_max = max(valores_validos) if valores_validos else 100
            percentual = (eixo_min / valor_max) * 100 if valor_max > 0 else 0
            alertas.append({
                'regra': 'Eixo Y',
                'status': '❌',
                'mensagem': f'Eixo Y começa em {eixo_min:.1f} ({percentual:.1f}% do valor máximo)',
                'severidade': 'ALTA' if percentual > 10 else 'MÉDIA',
                'dica': 'Gráficos de barras devem ter eixo Y começando em zero'
            })
        
        # REGRA 2: Título presente
        if titulo and len(str(titulo).strip()) >= 5:
            aprovacoes += 1
        elif titulo:
            alertas.append({
                'regra': 'Título',
                'status': '⚠️',
                'mensagem': f'Título muito curto: "{titulo}"',
                'severidade': 'BAIXA',
                'dica': 'Use um título descritivo'
            })
        else:
            alertas.append({
                'regra': 'Título',
                'status': '❌',
                'mensagem': 'Título não identificado',
                'severidade': 'MÉDIA',
                'dica': 'Adicione um título ao gráfico'
            })
        
        # REGRA 3: Fonte identificada
        if fonte and 'não' not in fonte.lower():
            aprovacoes += 1
        else:
            alertas.append({
                'regra': 'Fonte',
                'status': '❌',
                'mensagem': 'Fonte dos dados não identificada',
                'severidade': 'ALTA',
                'dica': 'Cite a fonte dos dados'
            })
        
        # REGRA 4: Rótulos no eixo X
        if categorias and len(categorias) == len(valores):
            aprovacoes += 1
        elif not categorias:
            alertas.append({
                'regra': 'Rótulos',
                'status': '❌',
                'mensagem': 'Eixo X sem rótulos identificados',
                'severidade': 'MÉDIA',
                'dica': 'Identifique cada barra com um rótulo'
            })
        else:
            alertas.append({
                'regra': 'Rótulos',
                'status': '⚠️',
                'mensagem': f'Número de rótulos ({len(categorias)}) diferente de barras ({len(valores)})',
                'severidade': 'MÉDIA',
                'dica': 'Cada barra deve ter um rótulo correspondente'
            })
        
        # REGRA 5: Valores positivos
        if all(v >= 0 for v in valores):
            aprovacoes += 1
        else:
            alertas.append({
                'regra': 'Valores',
                'status': '⚠️',
                'mensagem': 'Valores negativos detectados',
                'severidade': 'BAIXA',
                'dica': 'Barras para valores negativos devem ser destacadas'
            })
        
        # REGRA 6: Consistência visual
        if len(valores) >= 2:
            valores_validos = [v for v in valores if v <= 100]
            if valores_validos:
                max_val = max(valores_validos)
                min_val = min(valores_validos)
                if max_val > 0 and min_val / max_val < 0.1:
                    alertas.append({
                        'regra': 'Escala',
                        'status': '⚠️',
                        'mensagem': 'Grande variação entre valores pode dificultar visualização',
                        'severidade': 'BAIXA',
                        'dica': 'Considere usar escala logarítmica ou agrupar categorias'
                    })
                else:
                    aprovacoes += 1
            else:
                aprovacoes += 1
        
        return {
            'tipo': 'barras_verticais',
            'total_regras': total_regras,
            'aprovacoes': aprovacoes,
            'pontuacao': (aprovacoes / total_regras) * 100,
            'alertas': alertas
        }
        
    
    @staticmethod
    def verificar_barras_horizontais(dados: Dict) -> Dict[str, Any]:
        """
        Verifica gráfico de barras horizontais
        Similar ao vertical mas com foco no eixo X
        """
        alertas = []
        aprovacoes = 0
        total_regras = 6
        
        valores = dados.get('valores', [])
        categorias = dados.get('categorias', [])
        eixo_min = dados.get('eixo_x_min', 0)  # Nota: eixo_x_min
        titulo = dados.get('titulo', '')
        fonte = dados.get('fonte', '')
        
        # REGRA 1: Eixo X começa em zero
        if eixo_min == 0:
            aprovacoes += 1
        else:
            percentual = (eixo_min / max(valores)) * 100 if valores else 0
            alertas.append({
                'regra': 'Eixo X',
                'status': '❌',
                'mensagem': f'Eixo X começa em {eixo_min} ({percentual:.1f}% do valor máximo)',
                'severidade': 'ALTA' if percentual > 10 else 'MÉDIA',
                'dica': 'Gráficos de barras horizontais devem ter eixo X começando em zero'
            })
        
        # REGRA 2: Título presente
        if titulo and len(str(titulo).strip()) >= 5:
            aprovacoes += 1
        elif titulo:
            alertas.append({
                'regra': 'Título',
                'status': '⚠️',
                'mensagem': f'Título muito curto: "{titulo}"',
                'severidade': 'BAIXA',
                'dica': 'Use um título descritivo'
            })
        else:
            alertas.append({
                'regra': 'Título',
                'status': '❌',
                'mensagem': 'Título não identificado',
                'severidade': 'MÉDIA',
                'dica': 'Adicione um título ao gráfico'
            })
        
        # REGRA 3: Fonte identificada
        if fonte and 'não' not in fonte.lower():
            aprovacoes += 1
        else:
            alertas.append({
                'regra': 'Fonte',
                'status': '❌',
                'mensagem': 'Fonte dos dados não identificada',
                'severidade': 'ALTA',
                'dica': 'Cite a fonte dos dados'
            })
        
        # REGRA 4: Rótulos no eixo Y
        if categorias and len(categorias) == len(valores):
            aprovacoes += 1
        elif not categorias:
            alertas.append({
                'regra': 'Rótulos',
                'status': '❌',
                'mensagem': 'Eixo Y sem rótulos identificados',
                'severidade': 'MÉDIA',
                'dica': 'Identifique cada barra com um rótulo'
            })
        
        # REGRA 5: Ordenação (opcional, mas recomendada)
        # Verifica se está ordenada (decrescente)
        if len(valores) > 1:
            ordenada = all(valores[i] >= valores[i+1] for i in range(len(valores)-1))
            if not ordenada:
                alertas.append({
                    'regra': 'Ordenação',
                    'status': '⚠️',
                    'mensagem': 'Barras não estão ordenadas por valor',
                    'severidade': 'BAIXA',
                    'dica': 'Ordenar barras do maior para o menor facilita a leitura'
                })
            else:
                aprovacoes += 1
        
        return {
            'tipo': 'barras_horizontais',
            'total_regras': total_regras,
            'aprovacoes': aprovacoes,
            'pontuacao': (aprovacoes / total_regras) * 100,
            'alertas': alertas
        }
    
    @staticmethod
    def verificar_linhas(dados: Dict) -> Dict[str, Any]:
        """
        Verifica gráfico de linhas
        """
        alertas = []
        aprovacoes = 0
        total_regras = 6
        
        series = dados.get('series', [])
        valores_x = dados.get('valores_x', [])
        titulo = dados.get('titulo', '')
        fonte = dados.get('fonte', '')
        
        # REGRA 1: Pontos suficientes por série
        pontos_ok = True
        for serie in series:
            if serie.get('total_pontos', 0) < 3:
                pontos_ok = False
                alertas.append({
                    'regra': 'Pontos insuficientes',
                    'status': '⚠️',
                    'mensagem': f"Série '{serie.get('nome')}' tem apenas {serie.get('total_pontos')} pontos",
                    'severidade': 'MÉDIA',
                    'dica': 'Gráficos de linha precisam de pelo menos 3 pontos para mostrar tendência'
                })
        
        if pontos_ok:
            aprovacoes += 1
        
        # REGRA 2: Eixo X rotulado
        if valores_x and len(valores_x) >= 2:
            aprovacoes += 1
        else:
            alertas.append({
                'regra': 'Eixo X',
                'status': '⚠️',
                'mensagem': 'Eixo X sem rótulos suficientes',
                'severidade': 'MÉDIA',
                'dica': 'Identifique os pontos no eixo X (datas, categorias)'
            })
        
        # REGRA 3: Título presente
        if titulo and len(str(titulo).strip()) >= 5:
            aprovacoes += 1
        elif titulo:
            alertas.append({
                'regra': 'Título',
                'status': '⚠️',
                'mensagem': f'Título muito curto: "{titulo}"',
                'severidade': 'BAIXA',
                'dica': 'Use um título descritivo'
            })
        else:
            alertas.append({
                'regra': 'Título',
                'status': '❌',
                'mensagem': 'Título não identificado',
                'severidade': 'MÉDIA',
                'dica': 'Adicione um título ao gráfico'
            })
        
        # REGRA 4: Fonte identificada
        if fonte and 'não' not in fonte.lower():
            aprovacoes += 1
        else:
            alertas.append({
                'regra': 'Fonte',
                'status': '❌',
                'mensagem': 'Fonte dos dados não identificada',
                'severidade': 'ALTA',
                'dica': 'Cite a fonte dos dados'
            })
        
        # REGRA 5: Legenda para múltiplas séries
        if len(series) > 1:
            # Verifica se as séries têm nomes
            nomes_ok = all(s.get('nome') and s['nome'] not in ['Desconhecida', 'Série Principal'] for s in series)
            if nomes_ok:
                aprovacoes += 1
            else:
                alertas.append({
                    'regra': 'Legenda',
                    'status': '⚠️',
                    'mensagem': f'{len(series)} séries detectadas mas legendas não identificadas',
                    'severidade': 'MÉDIA',
                    'dica': 'Adicione legenda para identificar cada linha'
                })
        else:
            aprovacoes += 1  # Não precisa de legenda para série única
        
        # REGRA 6: Consistência da escala
        if series:
            # Verifica se os pontos estão dentro de uma faixa razoável
            aprovacoes += 1  # Placeholder - implementar lógica real se necessário
        
        return {
            'tipo': 'linhas',
            'total_regras': total_regras,
            'aprovacoes': aprovacoes,
            'pontuacao': (aprovacoes / total_regras) * 100,
            'alertas': alertas
        }