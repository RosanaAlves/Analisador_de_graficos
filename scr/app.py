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
    # PASSO 4: REVISÃO E CORREÇÃO DOS DADOS (CORRIGIDO)
    # =======================================
    with st.expander("✏️ PASSO 4: Revisar e corrigir dados extraídos", expanded=True):
        
        # DIFERENTE PARA CADA TIPO DE GRÁFICO
        if tipo == 'pizza':
            # Para pizza, os dados estão em dados['dados_especificos']['fatias']
            if 'dados_especificos' in dados and 'fatias' in dados['dados_especificos']:
                fatias = dados['dados_especificos']['fatias']
                
                st.markdown("### 🍕 Dados das fatias")
                st.caption("Edite os valores se necessário")
                
                # Criar DataFrame para edição
                df = pd.DataFrame({
                    'Categoria': [f.get('rotulo', f'Fatia {i+1}') for i, f in enumerate(fatias)],
                    'Percentual (%)': [f.get('percentual', 0) for f in fatias]
                })
                
                # Editor de dados
                edited_df = st.data_editor(
                    df,
                    width='stretch',
                    num_rows="fixed",
                    use_container_width=True,
                    column_config={
                        "Percentual (%)": st.column_config.NumberColumn(
                            "Percentual (%)",
                            min_value=0,
                            max_value=100,
                            step=0.1,
                            format="%.1f %%",
                            required=True
                        )
                    }
                )
                
                # Botão para aplicar correções
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    if st.button("✅ Aplicar correções", type="primary"):
                        # Atualizar dados
                        for i, row in edited_df.iterrows():
                            if i < len(fatias):
                                fatias[i]['rotulo'] = row['Categoria']
                                fatias[i]['percentual'] = row['Percentual (%)']
                        
                        # Recalcular soma
                        soma = sum(f['percentual'] for f in fatias)
                        dados['dados_especificos']['soma_percentuais'] = round(soma, 1)
                        
                        st.success("✅ Correções aplicadas com sucesso!")
                        st.rerun()
                
                with col2:
                    if st.button("🔄 Recalcular percentuais"):
                        # Recalcular para somar 100%
                        total = sum(f['percentual'] for f in fatias)
                        if total > 0:
                            for f in fatias:
                                f['percentual'] = round((f['percentual'] / total) * 100, 1)
                        st.success("✅ Percentuais recalculados para 100%!")
                        st.rerun()
                
                # Mostrar soma total
                soma_atual = sum(f['percentual'] for f in fatias)
                if abs(soma_atual - 100) > 0.1:
                    st.warning(f"⚠️ Soma total: {soma_atual:.1f}% (deveria ser 100%)")
                else:
                    st.success(f"✅ Soma total: {soma_atual:.1f}%")
        
        elif tipo in ['barras_verticais', 'barras_horizontais']:
            # Para barras, os dados estão em dados['dados_especificos']['barras']
            if 'dados_especificos' in dados and 'barras' in dados['dados_especificos']:
                barras = dados['dados_especificos']['barras']
                
                st.markdown(f"### {'📊' if tipo == 'barras_verticais' else '📈'} Dados das barras")
                st.caption("Edite os valores se necessário")
                
                # Criar DataFrame para edição
                df = pd.DataFrame({
                    'Categoria': [b.get('rotulo', f'Barra {i+1}') for i, b in enumerate(barras)],
                    'Valor': [b.get('valor', 0) for b in barras]
                })
                
                # Editor de dados
                edited_df = st.data_editor(
                    df,
                    width='stretch',
                    num_rows="fixed",
                    use_container_width=True,
                    column_config={
                        "Valor": st.column_config.NumberColumn(
                            "Valor",
                            min_value=0,
                            format="%.1f",
                            required=True
                        )
                    }
                )
                
                # Botão para aplicar correções
                if st.button("✅ Aplicar correções", type="primary"):
                    for i, row in edited_df.iterrows():
                        if i < len(barras):
                            barras[i]['rotulo'] = row['Categoria']
                            barras[i]['valor'] = row['Valor']
                    
                    # Atualizar também as listas valores/categorias
                    dados['dados_especificos']['valores'] = [b['valor'] for b in barras]
                    dados['dados_especificos']['categorias'] = [b['rotulo'] for b in barras]
                    
                    st.success("✅ Correções aplicadas com sucesso!")
                    st.rerun()
        
        elif tipo == 'linhas':
            # Para linhas, mostrar informações das séries
            if 'dados_especificos' in dados and 'series' in dados['dados_especificos']:
                series = dados['dados_especificos']['series']
                
                st.markdown("### 📉 Dados das séries")
                st.info("Para gráficos de linhas, a correção manual será implementada em breve.")
                
                # Mostrar informações das séries
                for i, serie in enumerate(series):
                    with st.expander(f"Série {i+1}: {serie.get('nome', 'Desconhecida')}"):
                        st.write(f"**Cor:** {serie.get('cor', 'N/A')}")
                        st.write(f"**Pontos detectados:** {serie.get('total_pontos', 0)}")
                        
                        # Mostrar primeiros pontos como exemplo
                        pontos = serie.get('pontos', [])[:5]
                        if pontos:
                            st.write("**Primeiros pontos:**")
                            for p in pontos:
                                st.write(f"  • x={p.get('x', 0)}, y={p.get('y_rel', 0)}")

    # =======================================
    # PASSO 5: VERIFICAÇÃO E RELATÓRIO
    # =======================================
    with st.expander("📋 PASSO 5: Verificação e relatório", expanded=True):
        
        # Instanciar verificador
        verificador = VerificadorGrafico()
        
        # Preparar dados para o verificador
        if tipo == 'pizza' and 'dados_especificos' in dados:
            fatias = dados['dados_especificos'].get('fatias', [])
            valores = [f['percentual'] for f in fatias]
            categorias = [f['rotulo'] for f in fatias]
            
            dados_verificador = {
                'tipo': 'pizza',
                'titulo': dados['metadados'].get('titulo', ''),
                'fonte': dados['metadados'].get('fonte', ''),
                'valores': valores,
                'categorias': categorias,
                'eixo_y_min': 0
            }
            
        elif tipo in ['barras_verticais', 'barras_horizontais'] and 'dados_especificos' in dados:
            barras = dados['dados_especificos'].get('barras', [])
            valores = [b['valor'] for b in barras]
            categorias = [b['rotulo'] for b in barras]
            
            # Determinar eixo mínimo
            if tipo == 'barras_verticais':
                eixo_min = dados['dados_especificos'].get('eixo_y_min', 0)
            else:
                eixo_min = dados['dados_especificos'].get('eixo_x_min', 0)
            
            dados_verificador = {
                'tipo': tipo,
                'titulo': dados['metadados'].get('titulo', ''),
                'fonte': dados['metadados'].get('fonte', ''),
                'valores': valores,
                'categorias': categorias,
                'eixo_y_min': eixo_min
            }
            
        elif tipo == 'linhas' and 'dados_especificos' in dados:
            series = dados['dados_especificos'].get('series', [])
            dados_verificador = {
                'tipo': 'linhas',
                'titulo': dados['metadados'].get('titulo', ''),
                'fonte': dados['metadados'].get('fonte', ''),
                'valores': [s['total_pontos'] for s in series],
                'categorias': [s['nome'] for s in series],
                'eixo_y_min': 0
            }
        else:
            dados_verificador = {
                'tipo': tipo,
                'titulo': dados['metadados'].get('titulo', ''),
                'fonte': dados['metadados'].get('fonte', ''),
                'valores': [],
                'categorias': [],
                'eixo_y_min': 0
            }
        
        # Executar verificações
        with st.spinner("Aplicando regras de verificação..."):
            resultados = verificador.verificar_tudo(dados_verificador)
            relatorio = verificador.gerar_relatorio(dados_verificador)
        
        # Mostrar resultados em colunas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("✅ Regras verificadas", verificador.regras_verificadas)
        with col2:
            st.metric("✅ Regras aprovadas", verificador.regras_aprovadas)
        with col3:
            taxa = relatorio.get('pontuacao', 0)
            st.metric("📊 Pontuação", f"{taxa:.1f}%")
        
        # Mostrar status geral
        if taxa >= 80:
            st.success("🎉 **Gráfico APROVADO!** Segue as boas práticas.")
        elif taxa >= 50:
            st.warning("⚠️ **Gráfico com RESSALVAS.** Algumas regras não foram atendidas.")
        else:
            st.error("❌ **Gráfico REJEITADO.** Múltiplas violações das boas práticas.")
        
        # Alertas por severidade
        if verificador.alertas:
            # Contar por severidade
            criticos = [a for a in verificador.alertas if a['severidade'] == 'CRITICA']
            altos = [a for a in verificador.alertas if a['severidade'] == 'ALTA']
            medios = [a for a in verificador.alertas if a['severidade'] == 'MEDIA']
            baixos = [a for a in verificador.alertas if a['severidade'] == 'BAIXA']
            
            # Mostrar contagem
            st.markdown("### ⚠️ Alertas encontrados")
            
            cols = st.columns(4)
            with cols[0]:
                st.metric("🔴 Críticos", len(criticos))
            with cols[1]:
                st.metric("🟠 Altos", len(altos))
            with cols[2]:
                st.metric("🟡 Médios", len(medios))
            with cols[3]:
                st.metric("🟢 Baixos", len(baixos))
            
            # Detalhar cada alerta
            st.markdown("### 📝 Detalhamento dos alertas")
            for alerta in verificador.alertas:
                severidade_emoji = {
                    'CRITICA': '🔴',
                    'ALTA': '🟠', 
                    'MEDIA': '🟡',
                    'BAIXA': '🟢'
                }.get(alerta['severidade'], '⚪')
                
                st.info(f"{severidade_emoji} **[{alerta['tipo']}]** {alerta['mensagem']}")
        else:
            st.success("✅ **Nenhum alerta encontrado!** O gráfico segue todas as boas práticas.")
        
        # Mostrar detalhes das regras
        with st.expander("📋 Detalhes das regras aplicadas"):
            st.markdown("""
            ### Regras de verificação:
            
            1. **Eixo Y começa em zero** (para gráficos de barras)
               - Gráficos de barras devem ter eixo Y começando em 0
               - Evita exagerar diferenças visuais
            
            2. **Proporções visuais** (para todos os tipos)
               - Alturas visuais devem corresponder aos valores numéricos
               - Para pizza: soma dos percentuais deve ser 100%
               - Tolerância de 5% de diferença
            
            3. **Título presente** (para todos os tipos)
               - Gráfico deve ter título descritivo
               - Mínimo de 5 caracteres
            
            4. **Fonte dos dados** (para todos os tipos)
               - Fonte deve ser citada
               - Garante credibilidade e rastreabilidade
            """)
    
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