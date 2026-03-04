# scr/app.py
"""
APLICATIVO PRINCIPAL STREAMLIT
"""

import sys
import os

# Adicionar o diretório raiz ao path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
import pandas as pd
from PIL import Image
import io
from datetime import datetime

# Agora podemos importar de scr
from scr.analisadores.fabrica import FabricaAnalisadores
from scr.utils.visualizacao import GeradorGraficos
from scr.core.verificador import VerificadorGrafico

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
        st.image(uploaded_file, caption="Imagem carregada", use_container_width=True)
        
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
        if st.button("🔍 Extrair Dados", type="primary", use_container_width=True):
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
        
        if tipo == 'pizza' and 'dados_especificos' in dados:
            fatias = dados['dados_especificos'].get('fatias', [])
            
            st.markdown("### 🍕 Dados das fatias")
            
            df = pd.DataFrame({
                'Categoria': [f.get('rotulo', f'Fatia {i+1}') for i, f in enumerate(fatias)],
                'Percentual (%)': [f.get('percentual', 0) for f in fatias]
            })
            
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                num_rows="dynamic",
                column_config={
                    "Percentual (%)": st.column_config.NumberColumn(
                        "Percentual (%)",
                        min_value=0,
                        max_value=100,
                        step=0.1,
                        format="%.1f %%"
                    )
                }
            )
            
            if st.button("✅ Aplicar correções"):
                for i, row in edited_df.iterrows():
                    if i < len(fatias):
                        fatias[i]['rotulo'] = row['Categoria']
                        fatias[i]['percentual'] = row['Percentual (%)']
                st.success("Correções aplicadas!")
                st.rerun()
        
        elif tipo in ['barras_verticais', 'barras_horizontais'] and 'dados_especificos' in dados:
            barras = dados['dados_especificos'].get('barras', [])
            
            st.markdown("### 📊 Dados das barras")
            
            df = pd.DataFrame({
                'Categoria': [b.get('rotulo', f'Barra {i+1}') for i, b in enumerate(barras)],
                'Valor': [b.get('valor', 0) for b in barras]
            })
            
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                num_rows="dynamic"
            )
            
            if st.button("✅ Aplicar correções"):
                for i, row in edited_df.iterrows():
                    if i < len(barras):
                        barras[i]['rotulo'] = row['Categoria']
                        barras[i]['valor'] = row['Valor']
                st.success("Correções aplicadas!")
                st.rerun()
    
    # =======================================
    # PASSO 5: VISUALIZAÇÃO DO GRÁFICO CORRIGIDO
    # =======================================
    with st.expander("📊 PASSO 5: Visualizar gráfico corrigido", expanded=True):
        
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
                use_container_width=True
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
        6. **Visualizar** gráfico corrigido
        7. **Baixar** imagem gerada
        """)