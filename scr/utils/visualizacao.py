# scr/utils/visualizacao.py
"""
Gerador de gráficos corrigidos para visualização e download
"""

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from typing import Optional, Dict, Any  # <-- ADICIONAR ESTAS LINHAS
import io


class GeradorGraficos:
    
    def gerar_comparativo(self, imagem_original, dados, tipo):
        """Gera figura comparativa: original vs corrigido"""
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        fig.patch.set_facecolor('#F8F9FB')
        
        # Original
        if isinstance(imagem_original, str):
            img = Image.open(imagem_original)
        else:
            img = Image.open(imagem_original)
            
        ax1.imshow(img)
        ax1.set_title("📸 Gráfico Original", fontsize=12, fontweight='bold')
        ax1.axis('off')
        
        # Corrigido
        if tipo == 'pizza':
            self._plot_pizza_corrigido(ax2, dados)
        elif tipo == 'barras_verticais':
            self._plot_barras_verticais_corrigido(ax2, dados)
        elif tipo == 'barras_horizontais':
            self._plot_barras_horizontais_corrigido(ax2, dados)
        elif tipo == 'linhas':
            self._plot_linhas_corrigido(ax2, dados)
        
        ax2.set_title("✅ Gráfico Corrigido", fontsize=12, fontweight='bold')
        
        plt.tight_layout()
        return fig
    
    def gerar_corrigido(self, dados, tipo):
        """Gera apenas o gráfico corrigido"""
        
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor('#F8F9FB')
        
        if tipo == 'pizza':
            self._plot_pizza_corrigido(ax, dados)
        elif tipo == 'barras_verticais':
            self._plot_barras_verticais_corrigido(ax, dados)
        elif tipo == 'barras_horizontais':
            self._plot_barras_horizontais_corrigido(ax, dados)
        elif tipo == 'linhas':
            self._plot_linhas_corrigido(ax, dados)
        
        plt.tight_layout()
        return fig
    
    def _plot_pizza_corrigido(self, ax, dados):
        """Plota pizza corrigida"""
        if 'dados_especificos' in dados:
            fatias = dados['dados_especificos'].get('fatias', [])
        else:
            fatias = dados.get('fatias', [])
            
        if not fatias:
            ax.text(0.5, 0.5, "Sem dados para exibir", ha='center', va='center')
            return
            
        valores = [f['percentual'] for f in fatias]
        rotulos = [f['rotulo'] for f in fatias]
        
        cores = plt.cm.Set3(np.linspace(0, 1, len(valores)))
        
        wedges, texts, autotexts = ax.pie(
            valores,
            labels=rotulos,
            autopct='%1.1f%%',
            colors=cores,
            startangle=90,
            textprops={'fontsize': 9}
        )
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
    
    def _plot_barras_verticais_corrigido(self, ax, dados):
        """Plota barras verticais corrigidas (eixo Y começando em 0)"""
        if 'dados_especificos' in dados:
            barras = dados['dados_especificos'].get('barras', [])
        else:
            barras = dados.get('barras', [])
            
        if not barras:
            ax.text(0.5, 0.5, "Sem dados para exibir", ha='center', va='center')
            return
            
        categorias = [b['rotulo'] for b in barras]
        valores = [b['valor'] for b in barras]
        
        x = np.arange(len(categorias))
        bars = ax.bar(x, valores, color='#2980B9', alpha=0.8)
        
        ax.set_xticks(x)
        ax.set_xticklabels(categorias, rotation=45, ha='right')
        ax.set_ylim(bottom=0)
        ax.set_ylabel("Valor")
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}', ha='center', va='bottom', fontweight='bold')
    
    def _plot_barras_horizontais_corrigido(self, ax, dados):
        """Plota barras horizontais corrigidas"""
        if 'dados_especificos' in dados:
            barras = dados['dados_especificos'].get('barras', [])
        else:
            barras = dados.get('barras', [])
            
        if not barras:
            ax.text(0.5, 0.5, "Sem dados para exibir", ha='center', va='center')
            return
            
        categorias = [b['rotulo'] for b in barras]
        valores = [b['valor'] for b in barras]
        
        y = np.arange(len(categorias))
        bars = ax.barh(y, valores, color='#27AE60', alpha=0.8)
        
        ax.set_yticks(y)
        ax.set_yticklabels(categorias)
        ax.set_xlim(left=0)
        ax.set_xlabel("Valor")
        
        for bar in bars:
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2.,
                   f'{width:.1f}', ha='left', va='center', fontweight='bold')
    
    def _plot_linhas_corrigido(self, ax, dados):
        """Plota gráfico de linhas corrigido"""
        if 'dados_especificos' in dados:
            series = dados['dados_especificos'].get('series', [])
            valores_x = dados['dados_especificos'].get('valores_x', [])
        else:
            series = dados.get('series', [])
            valores_x = dados.get('valores_x', [])
            
        if not series:
            ax.text(0.5, 0.5, "Sem dados para exibir", ha='center', va='center')
            return
            
        x = np.arange(len(valores_x)) if valores_x else np.arange(max(s.get('total_pontos', 0) for s in series))
        
        for serie in series:
            pontos = serie.get('pontos', [])
            if pontos:
                # Extrair valores y relativos
                y_vals = [p['y_rel'] for p in pontos]
                # Normalizar para 0-100
                if y_vals:
                    y_min, y_max = min(y_vals), max(y_vals)
                    if y_max > y_min:
                        y_norm = [(y - y_min) / (y_max - y_min) * 100 for y in y_vals]
                    else:
                        y_norm = y_vals
                    
                    # Plotar
                    x_vals = [p['x_rel'] for p in pontos]
                    ax.plot(x_vals, y_norm, marker='o', label=serie['nome'], 
                           color=[c/255 for c in serie['cor']])
        
        ax.set_ylabel("Valor (%)")
        ax.set_xlabel("Pontos")
        ax.legend()
        ax.grid(True, alpha=0.3)