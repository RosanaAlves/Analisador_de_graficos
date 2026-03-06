# scr/app.py
"""
APLICATIVO PRINCIPAL STREAMLIT
"""

import sys
import os
import streamlit as st
import pandas as pd
from PIL import Image
import io
from datetime import datetime
import json
from typing import Dict, List, Optional, Any, Tuple  

#  importar de scr
from scr.analisadores.fabrica import FabricaAnalisadores
from scr.utils.visualizacao import GeradorGraficos
from scr.core.verificador import VerificadorGrafico
from scr.core.regras import RegrasGrafico

import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

# Ou use esta configuração mais robusta:
import matplotlib
matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans', 'Bitstream Vera Sans', 'sans-serif']

# Adicionar o diretório raiz ao path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Função de debug para mostrar a estrutura dos dados
def mostrar_estrutura_dados(dados, nivel=0):
    """Mostra a estrutura completa dos dados para debug"""
    if dados is None:
        return "None"
    
    resultado = ""
    espaco = "  " * nivel
    
    if isinstance(dados, dict):
        resultado += f"{espaco}Dict com {len(dados)} chaves:\n"
        for chave, valor in list(dados.items())[:5]:  # Mostra só as primeiras 5 chaves
            if isinstance(valor, (dict, list)):
                resultado += f"{espaco}  - {chave}: {type(valor).__name__}\n"
            else:
                resultado += f"{espaco}  - {chave}: {valor}\n"
        if len(dados) > 5:
            resultado += f"{espaco}  ... e mais {len(dados)-5} chaves\n"
    elif isinstance(dados, list):
        resultado += f"{espaco}Lista com {len(dados)} itens\n"
        if len(dados) > 0:
            resultado += f"{espaco}  Primeiro item: {type(dados[0]).__name__}\n"
    else:
        resultado += f"{espaco}{type(dados).__name__}: {dados}\n"
    
    return resultado


# ===========================================
# FUNÇÕES AUXILIARES (DEFINIR ANTES DE USAR)
# ===========================================

def mostrar_resultado_verificacao(resultado: Dict, tipo: str):
    """
    Mostra o resultado da verificação de forma visual e organizada
    """
    if not resultado:
        st.warning("Resultado da verificação vazio")
        return
        
    pontuacao = resultado.get('pontuacao', 0)
    alertas = resultado.get('alertas', [])
    
    st.markdown("---")
    
    # Título com cor baseada na pontuação
    if pontuacao >= 80:
        st.success(f"### 🎉 RESULTADO: APROVADO ({pontuacao:.0f}%)")
    elif pontuacao >= 50:
        st.warning(f"### ⚠️ RESULTADO: COM RESSALVAS ({pontuacao:.0f}%)")
    else:
        st.error(f"### ❌ RESULTADO: REJEITADO ({pontuacao:.0f}%)")
    
    # Métricas principais
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📋 Regras verificadas", resultado.get('total_regras', 0))
    with col2:
        st.metric("✅ Regras aprovadas", resultado.get('aprovacoes', 0))
    with col3:
        st.metric("📊 Pontuação", f"{pontuacao:.0f}%")
    
    # MOSTRAR ALERTAS DIRETAMENTE DO RESULTADO
    st.markdown("### ⚠️ Alertas encontrados")
    
    if not alertas:
        st.success("✅ Nenhum alerta encontrado! Todas as regras foram aprovadas.")
    else:
        # Agrupar alertas por severidade
        alertas_altos = [a for a in alertas if a.get('severidade') == 'ALTA']
        alertas_medios = [a for a in alertas if a.get('severidade') == 'MÉDIA']
        alertas_baixos = [a for a in alertas if a.get('severidade') == 'BAIXA']
        
        # Mostrar alertas críticos primeiro
        if alertas_altos:
            with st.expander("🔴 CRÍTICOS - Devem ser corrigidos", expanded=True):
                for alerta in alertas_altos:
                    st.error(f"""
                    **{alerta.get('regra')}**  
                    {alerta.get('mensagem')}  
                    💡 *Dica: {alerta.get('dica', 'Corrija este item')}*
                    """)
        
        if alertas_medios:
            with st.expander("🟡 MÉDIOS - Recomenda-se corrigir", expanded=True):
                for alerta in alertas_medios:
                    st.warning(f"""
                    **{alerta.get('regra')}**  
                    {alerta.get('mensagem')}  
                    💡 *Dica: {alerta.get('dica', 'Melhore este item')}*
                    """)
        
        if alertas_baixos:
            with st.expander("🟢 BAIXOS - Sugestões de melhoria", expanded=False):
                for alerta in alertas_baixos:
                    st.info(f"""
                    **{alerta.get('regra')}**  
                    {alerta.get('mensagem')}  
                    💡 *Dica: {alerta.get('dica', 'Considere esta melhoria')}*
                    """)
    
    # TABELA DETALHADA COM BASE NOS ALERTAS REAIS
    with st.expander("📊 Ver detalhamento completo", expanded=False):
        
        # Descobrir quantas regras foram realmente avaliadas
        regras_avaliadas = set()
        for alerta in alertas:
            regras_avaliadas.add(alerta.get('regra'))
        
        # Adicionar regras que passaram (inferidas)
        total_regras = resultado.get('total_regras', 0)
        aprovacoes = resultado.get('aprovacoes', 0)
        regras_aprovadas = total_regras - len(alertas)
        
        st.write(f"**Total de regras avaliadas:** {total_regras}")
        st.write(f"**Regras com alertas:** {len(alertas)}")
        st.write(f"**Regras aprovadas:** {regras_aprovadas}")
        
        # Tabela de alertas
        if alertas:
            df_alertas = pd.DataFrame([
                {
                    'Regra': a.get('regra', ''),
                    'Severidade': a.get('severidade', ''),
                    'Mensagem': a.get('mensagem', ''),
                    'Dica': a.get('dica', '')
                }
                for a in alertas
            ])
            st.dataframe(df_alertas, use_container_width=True)
        else:
            st.success("✅ Todas as regras foram aprovadas!")

# ===========================================
# CONFIGURAÇÃO DA PÁGINA
# ===========================================
st.set_page_config(
    page_title="Verificador de Gráficos - CONRE-3",
    page_icon="📊",
    layout="wide"
)

# Inicializar sessão
if 'dados_extraidos' not in st.session_state:
    st.session_state.dados_extraidos = None
if 'dados_corrigidos' not in st.session_state:
    st.session_state.dados_corrigidos = None
if 'modo_visualizacao' not in st.session_state:
    st.session_state.modo_visualizacao = 'comparativo'
if 'tipo_grafico' not in st.session_state:
    st.session_state.tipo_grafico = None

# ===========================================
# TÍTULO E DESCRIÇÃO
# ===========================================
st.title("📊 Verificador de Integridade de Gráficos")
st.markdown("""
    Ferramenta educacional do **CONRE-3** para verificar boas práticas 
    na construção de gráficos estatísticos.
""")

# ===========================================
# SIDEBAR - UPLOAD E CONFIGURAÇÕES
# ===========================================
with st.sidebar:
    st.header("📤 Upload do Gráfico")
    
    uploaded_file = st.file_uploader(
        "Escolha uma imagem",
        type=['png', 'jpg', 'jpeg'],
        help="Formatos aceitos: PNG, JPG, JPEG"
    )
    
    if uploaded_file:
        st.image(uploaded_file, caption="Imagem carregada", width='stretch')
        
        st.divider()
        st.header("⚙️ Configurações")
        
        # PASSO 1: Selecionar tipo de gráfico
        tipo_grafico = st.selectbox(
            "Tipo de gráfico",
            options=['pizza', 'barras_verticais', 'barras_horizontais', 'linhas'],
            format_func=lambda x: {
                'pizza': '🍕 Pizza',
                'barras_verticais': '📊 Barras Verticais',
                'barras_horizontais': '📈 Barras Horizontais',
                'linhas': '📉 Linhas'
            }[x],
            key='tipo_grafico'
        )
        
        # PASSO 2: Informar número de categorias
        if tipo_grafico == 'pizza':
            num_categorias = st.number_input(
                "Número de categorias",
                min_value=2,
                max_value=15,
                value=4,
                help="Quantas fatias tem o gráfico?"
            )
        elif tipo_grafico in ['barras_verticais', 'barras_horizontais']:
            num_categorias = st.number_input(
                "Número de barras",
                min_value=1,
                max_value=20,
                value=3,
                help="Quantas barras tem o gráfico?"
            )
        elif tipo_grafico == 'linhas':
            num_categorias = st.number_input(
                "Número de séries",
                min_value=1,
                max_value=10,
                value=1,
                help="Quantas linhas tem o gráfico?"
            )
        else:
            num_categorias = None
            
        # PASSO 3: Botão para processar
        if st.button("🔍 Extrair Dados", type="primary", width='stretch'):
            with st.spinner("Processando imagem..."):
                try:
                    # Salvar arquivo temporariamente
                    temp_path = f"temp_{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Instanciar analisador correto
                    analisador = FabricaAnalisadores.criar(
                        tipo=tipo_grafico,
                        imagem_path=temp_path,
                        num_categorias=num_categorias
                    )
                    
                    # Extrair dados
                    st.session_state.dados_extraidos = analisador.extrair_elementos()
                    st.session_state.dados_corrigidos = st.session_state.dados_extraidos.copy()
                    
                    # Limpar arquivo temporário
                    os.remove(temp_path)
                    
                    st.success("✅ Dados extraídos com sucesso!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Erro: {str(e)}")
                    import traceback
                    traceback.print_exc()

# ===========================================
# ÁREA PRINCIPAL - RESULTADOS
# ===========================================
if st.session_state.dados_extraidos and not st.session_state.dados_extraidos.get('erro'):
    
    dados = st.session_state.dados_extraidos
    tipo = st.session_state.tipo_grafico
    
    # Mostrar informações básicas
    st.success("✅ Dados extraídos com sucesso!")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Confiança", f"{dados.get('confianca', 0)}%")
    with col2:
        st.metric("Título", dados['metadados'].get('titulo', 'N/A')[:20])
    with col3:
        st.metric("Fonte", dados['metadados'].get('fonte', 'N/A')[:20])
    
    
    # =======================================
    # PASSO 4: REVISÃO E CORREÇÃO DOS DADOS
    # =======================================
    with st.expander("✏️ PASSO 4: Revisar e corrigir dados extraídos", expanded=True):
        
        st.info(f"Editando gráfico do tipo: **{tipo}**")
        
        # === SEÇÃO DE METADADOS (TÍTULO E FONTE) - DISPONÍVEL PARA TODOS OS TIPOS ===
        with st.expander("📝 Metadados do gráfico (título e fonte)", expanded=False):
            st.markdown("#### Editar informações do gráfico")
            
            # Editar título
            titulo_atual = dados['metadados'].get('titulo', '')
            novo_titulo = st.text_input("Título do gráfico", value=titulo_atual, key="titulo_global")
            
            # Editar fonte
            fonte_atual = dados['metadados'].get('fonte', '')
            nova_fonte = st.text_input("Fonte dos dados", value=fonte_atual, key="fonte_global")
            
            if st.button("✅ Atualizar metadados", key="update_metadados_global"):
                dados['metadados']['titulo'] = novo_titulo
                dados['metadados']['fonte'] = nova_fonte
                st.success("Metadados atualizados!")
                st.rerun()
        
        st.markdown("---")
        
        # === EDIÇÃO ESPECÍFICA POR TIPO DE GRÁFICO ===
        
        # PIZZA
        if tipo == 'pizza' and 'dados_especificos' in dados and 'fatias' in dados['dados_especificos']:
            fatias = dados['dados_especificos']['fatias']
            
            st.markdown("### 🍕 Dados das fatias")
            
            df = pd.DataFrame({
                'Categoria': [f.get('rotulo', f'Fatia {i+1}') for i, f in enumerate(fatias)],
                'Percentual (%)': [f.get('percentual', 0) for f in fatias]
            })
            
            edited_df = st.data_editor(df, use_container_width=True)
            
            if st.button("✅ Aplicar correções nas fatias"):
                for i, row in edited_df.iterrows():
                    if i < len(fatias):
                        fatias[i]['rotulo'] = row['Categoria']
                        fatias[i]['percentual'] = row['Percentual (%)']
                st.success("Correções aplicadas!")
                st.rerun()
        
        # BARRAS (VERTICAIS E HORIZONTAIS)
        elif tipo in ['barras_verticais', 'barras_horizontais'] and 'dados_especificos' in dados:
            if 'barras' in dados['dados_especificos']:
                barras = dados['dados_especificos']['barras']
                
                st.markdown(f"### {'📊' if tipo == 'barras_verticais' else '📈'} Dados das barras")
                
                # Verificar valores inconsistentes
                valores = [b.get('valor', 0) for b in barras]
                if valores and max(valores) > 100:
                    st.warning(f"⚠️ Valor máximo detectado: {max(valores):.1f} (possível erro de OCR - esperado até 100)")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🔧 Normalizar (dividir por 10)"):
                            for b in barras:
                                b['valor'] = b.get('valor', 0) / 10
                            st.success("Valores normalizados!")
                            st.rerun()
                    with col2:
                        if st.button("✏️ Editar manualmente"):
                            st.session_state.editando_manual = True
                
                df = pd.DataFrame({
                    'Categoria': [b.get('rotulo', f'Barra {i+1}') for i, b in enumerate(barras)],
                    'Valor': [b.get('valor', 0) for b in barras]
                })
                
                edited_df = st.data_editor(df, use_container_width=True)
                
                if st.button("✅ Aplicar correções nas barras"):
                    for i, row in edited_df.iterrows():
                        if i < len(barras):
                            barras[i]['rotulo'] = row['Categoria']
                            barras[i]['valor'] = row['Valor']
                    st.success("Correções aplicadas!")
                    st.rerun()
            else:
                st.warning("Nenhuma barra encontrada em 'dados_especificos'")
        
        # LINHAS
        elif tipo == 'linhas' and 'dados_especificos' in dados:
            st.markdown("### 📉 Dados do gráfico de linhas")
            
            # Abas para diferentes tipos de edição
            tab1, tab2 = st.tabs(["📌 Eixo X", "📊 Séries"])
            
            with tab1:
                st.markdown("#### 📌 Rótulos do eixo X")
                valores_x = dados['dados_especificos'].get('valores_x', [])
                
                if valores_x:
                    df_x = pd.DataFrame({
                        'Posição': [f'Ponto {i+1}' for i in range(len(valores_x))],
                        'Rótulo': valores_x
                    })
                    
                    edited_x = st.data_editor(df_x, use_container_width=True, num_rows="dynamic")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Aplicar rótulos", key="apply_x"):
                            novos_valores = edited_x['Rótulo'].tolist()
                            dados['dados_especificos']['valores_x'] = novos_valores
                            st.success("Rótulos atualizados!")
                            st.rerun()
                    
                    with col2:
                        if st.button("➕ Adicionar ponto", key="add_x"):
                            novos_valores = edited_x['Rótulo'].tolist()
                            novos_valores.append(f"Ponto {len(novos_valores)+1}")
                            dados['dados_especificos']['valores_x'] = novos_valores
                            st.success("Ponto adicionado!")
                            st.rerun()
                else:
                    st.warning("Nenhum valor no eixo X detectado")
                    novo_valor = st.text_input("Adicionar rótulo", key="novo_x")
                    if st.button("Adicionar", key="add_x_simple") and novo_valor:
                        dados['dados_especificos']['valores_x'] = [novo_valor]
                        st.rerun()
            
            with tab2:
                st.markdown("#### 📊 Séries detectadas")
                series = dados['dados_especificos'].get('series', [])
                
                if not series:
                    st.warning("Nenhuma série detectada")
                    
                    # Opção para criar nova série manualmente
                    with st.expander("➕ Criar nova série manualmente", expanded=True):
                        nome_serie = st.text_input("Nome da série", value="Nova Série")
                        cor_serie = st.color_picker("Cor da série", value="#FF0000")
                        
                        # Criar pontos padrão
                        num_pontos = st.number_input("Número de pontos", min_value=2, max_value=20, value=5)
                        
                        if st.button("Criar série", key="create_series"):
                            # Converter cor hex para BGR
                            r = int(cor_serie[1:3], 16)
                            g = int(cor_serie[3:5], 16)
                            b = int(cor_serie[5:7], 16)
                            
                            # Criar pontos
                            pontos = []
                            valores_x = dados['dados_especificos'].get('valores_x', [f"Ponto {i+1}" for i in range(num_pontos)])
                            
                            for i in range(num_pontos):
                                pontos.append({
                                    'x': i * 50,
                                    'y': 100 + i * 10,
                                    'x_rel': i * 50,
                                    'y_rel': 100 + i * 10
                                })
                            
                            nova_serie = {
                                'id': len(series) + 1,
                                'nome': nome_serie,
                                'cor': (b, g, r),  # BGR
                                'pontos': pontos,
                                'total_pontos': num_pontos,
                                'segmentos': 1
                            }
                            
                            if 'series' not in dados['dados_especificos']:
                                dados['dados_especificos']['series'] = []
                            dados['dados_especificos']['series'].append(nova_serie)
                            st.success("Série criada com sucesso!")
                            st.rerun()
                
                else:
                    # Listar todas as séries com opções de edição
                    for idx, serie in enumerate(series):
                        with st.expander(f"Série {idx+1}: {serie.get('nome', 'Desconhecida')}", expanded=(idx==0)):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                # Editar nome da série
                                novo_nome = st.text_input("Nome da série", 
                                                        value=serie.get('nome', f'Série {idx+1}'),
                                                        key=f"nome_serie_{idx}")
                                
                                # Editar cor (converter BGR para HEX)
                                cor_bgr = serie.get('cor', (255, 0, 0))
                                cor_hex = f"#{cor_bgr[2]:02x}{cor_bgr[1]:02x}{cor_bgr[0]:02x}"
                                nova_cor = st.color_picker("Cor da série", value=cor_hex, key=f"cor_serie_{idx}")
                                
                                # Mostrar estatísticas
                                st.write(f"**Pontos detectados:** {serie.get('total_pontos', 0)}")
                            
                            with col2:
                                if st.button("🗑️ Remover", key=f"remover_{idx}"):
                                    series.pop(idx)
                                    st.success(f"Série removida!")
                                    st.rerun()
                            
                            # Botão para aplicar alterações no nome/cor
                            if st.button("✅ Aplicar", key=f"aplicar_{idx}"):
                                # Converter HEX para BGR
                                r = int(nova_cor[1:3], 16)
                                g = int(nova_cor[3:5], 16)
                                b = int(nova_cor[5:7], 16)
                                
                                serie['nome'] = novo_nome
                                serie['cor'] = (b, g, r)
                                st.success("Alterações aplicadas!")
                                st.rerun()
        
        else:
            st.warning(f"Tipo de gráfico '{tipo}' não suportado ou dados não encontrados")

    # =======================================
    # PASSO 5: VERIFICAÇÃO E RELATÓRIO
    # =======================================
    with st.expander("📋 PASSO 5: Verificação e relatório", expanded=False):
        
        st.markdown("### 🔍 Analisando o gráfico segundo critérios específicos")
        
        # Verificar se temos dados suficientes
        if 'dados_especificos' not in dados:
            st.warning("Dados específicos não encontrados para verificação")
        else:
            resultado = None  # Inicializar resultado
            
            # Preparar dados para verificação baseado no tipo
            if tipo == 'pizza':
                fatias = dados['dados_especificos'].get('fatias', [])
                if not fatias:
                    st.warning("Nenhuma fatia encontrada para verificação")
                else:
                    dados_verificacao = {
                        'valores': [f.get('percentual', 0) for f in fatias],
                        'categorias': [f.get('rotulo', '') for f in fatias],
                        'titulo': dados['metadados'].get('titulo', ''),
                        'fonte': dados['metadados'].get('fonte', '')
                    }
                    with st.spinner("Aplicando regras para gráfico de pizza..."):
                        resultado = RegrasGrafico.verificar_pizza(dados_verificacao)
            
            elif tipo == 'barras_verticais':
                barras = dados['dados_especificos'].get('barras', [])
                if not barras:
                    st.warning("Nenhuma barra encontrada para verificação")
                else:
                    dados_verificacao = {
                        'valores': [b.get('valor', 0) for b in barras],
                        'categorias': [b.get('rotulo', '') for b in barras],
                        'eixo_y_min': dados['dados_especificos'].get('eixo_y_min', 0),
                        'titulo': dados['metadados'].get('titulo', ''),
                        'fonte': dados['metadados'].get('fonte', '')
                    }
                    with st.spinner("Aplicando regras para gráfico de barras verticais..."):
                        resultado = RegrasGrafico.verificar_barras_verticais(dados_verificacao)
            
            elif tipo == 'barras_horizontais':
                barras = dados['dados_especificos'].get('barras', [])
                if not barras:
                    st.warning("Nenhuma barra encontrada para verificação")
                else:
                    dados_verificacao = {
                        'valores': [b.get('valor', 0) for b in barras],
                        'categorias': [b.get('rotulo', '') for b in barras],
                        'eixo_x_min': dados['dados_especificos'].get('eixo_x_min', 0),
                        'titulo': dados['metadados'].get('titulo', ''),
                        'fonte': dados['metadados'].get('fonte', '')
                    }
                    with st.spinner("Aplicando regras para gráfico de barras horizontais..."):
                        resultado = RegrasGrafico.verificar_barras_horizontais(dados_verificacao)
            
            elif tipo == 'linhas':
                series = dados['dados_especificos'].get('series', [])
                valores_x = dados['dados_especificos'].get('valores_x', [])
                
                if not series:
                    st.warning("Nenhuma série encontrada para verificação")
                else:
                    dados_verificacao = {
                        'series': series,
                        'valores_x': valores_x,
                        'titulo': dados['metadados'].get('titulo', ''),
                        'fonte': dados['metadados'].get('fonte', '')
                    }
                    with st.spinner("Aplicando regras para gráfico de linhas..."):
                        resultado = RegrasGrafico.verificar_linhas(dados_verificacao)
            
            else:
                st.warning(f"Tipo de gráfico '{tipo}' não suportado para verificação detalhada")
            
            # MOSTRAR O RESULTADO (se existir)
            if resultado:
                st.success("✅ Verificação concluída!")
                mostrar_resultado_verificacao(resultado, tipo)
                
                # DEBUG: Mostrar o resultado bruto (opcional)
                with st.expander("🔍 Dados brutos da verificação (debug)"):
                    st.json(resultado)
            else:
                st.error("❌ Não foi possível gerar o resultado da verificação")

    # =======================================
    # PASSO 6: VISUALIZAÇÃO DO GRÁFICO CORRIGIDO
    # =======================================
    with st.expander("📊 PASSO 6: Visualizar gráfico corrigido", expanded=True):
        
        # Opções de visualização
        col1, col2 = st.columns(2)
        with col1:
            modo = st.radio(
                "Modo de visualização",
                options=['comparativo', 'apenas_corrigido'],
                format_func=lambda x: {
                    'comparativo': '🔄 Comparativo (original vs corrigido)',
                    'apenas_corrigido': '✅ Apenas gráfico corrigido'
                }[x],
                index=0
            )
        
        # Gerar gráfico
        gerador = GeradorGraficos()
        
        try:
            if modo == 'comparativo' and uploaded_file:
                # Mostrar original e corrigido lado a lado
                fig = gerador.gerar_comparativo(
                    uploaded_file,
                    dados,
                    tipo
                )
            else:
                # Mostrar apenas corrigido
                fig = gerador.gerar_corrigido(
                    dados,
                    tipo
                )
            
            # Exibir gráfico
            st.pyplot(fig)
            
            # Botão para download
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
            buf.seek(0)
            
            st.download_button(
                label="📥 Baixar imagem",
                data=buf,
                file_name=f"grafico_corrigido_{tipo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                mime="image/png",
                width='stretch'
            )
        except Exception as e:
            st.error(f"Erro ao gerar gráfico: {e}")

else:
    # Mensagem inicial
    st.info("👈 Faça upload de uma imagem no menu lateral para começar!")
    
    with st.expander("ℹ️ Como usar"):
        st.markdown("""
        1. **Upload** da imagem do gráfico
        2. **Selecionar** o tipo de gráfico
        3. **Informar** número de categorias/barras/séries
        4. **Extrair** dados automaticamente
        5. **Revisar** e corrigir dados se necessário
        6. **Verificar** regras éticas e gerar relatório
        7. **Visualizar** gráfico corrigido
        8. **Baixar** imagem gerada
        """)