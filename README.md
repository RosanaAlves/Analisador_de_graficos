# Analisador_de_graficos

# 📊 Verificador de Integridade de Gráficos - CONRE-3

Ferraramenta educacional desenvolvida para o **CONRE-3** (Conselho Regional de Estatística) que verifica boas práticas na construção de gráficos estatísticos, detectando possíveis distorções e manipulações visuais.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.55-red)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8-green)
![Tesseract](https://img.shields.io/badge/Tesseract-OCR-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📋 **ÍNDICE**

- [Sobre o Projeto](#-sobre-o-projeto)
- [Funcionalidades](#-funcionalidades)
- [Tipos de Gráficos Suportados](#-tipos-de-gráficos-suportados)
- [Regras de Verificação](#-regras-de-verificação)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação](#-instalação)
- [Como Usar](#-como-usar)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Exemplos de Uso](#-exemplos-de-uso)
- [Tecnologias Utilizadas](#-tecnologias-utilizadas)
- [Contribuição](#-contribuição)
- [Licença](#-licença)
- [Contato](#-contato)

---

## 🎯 **SOBRE O PROJETO**

Este sistema utiliza técnicas de **visão computacional** e **OCR** para extrair dados de gráficos estatísticos e verificar se eles seguem as boas práticas de visualização de dados. O objetivo é educar e alertar sobre possíveis distorções que podem enganar o leitor.

### **Problema que resolve**
Gráficos podem ser manipulados visualmente para enganar o público:
- Eixos que não começam em zero
- Proporções distorcidas
- Falta de fonte dos dados
- Títulos ausentes ou enganosos

### **Solução**
O sistema analisa automaticamente o gráfico, extrai os dados e aplica regras éticas de visualização, gerando um relatório e uma versão corrigida do gráfico.

---

## ✨ **FUNCIONALIDADES**

### **Principais**
- ✅ **Upload de imagens** (PNG, JPG, JPEG)
- ✅ **Seleção do tipo de gráfico** (pizza, barras verticais, barras horizontais, linhas)
- ✅ **Informar número de categorias** para melhor precisão
- ✅ **Extração automática de dados** via OCR e visão computacional
- ✅ **Tabela editável** para correção manual dos dados
- ✅ **Relatório de verificações** com alertas por severidade
- ✅ **Visualização comparativa** (original vs corrigido)
- ✅ **Download do gráfico corrigido** em PNG

### **Extras** Trabalhos futuros
- 🔄 Detecção automática do tipo de gráfico (opcional)
- 📊 Histórico de verificações
- 🎨 Interface amigável com Streamlit
- 📈 Suporte a múltiplas séries em gráficos de linhas

---

## 📊 **TIPOS DE GRÁFICOS SUPORTADOS**

| Tipo | Descrição | Exemplo |
|------|-----------|---------|
| 🍕 **Pizza** | Gráficos de pizza/torta com múltiplas fatias | Vendas por categoria, participação de mercado |
| 📊 **Barras Verticais** | Barras na vertical | Comparação entre categorias |
| 📈 **Barras Horizontais** | Barras na horizontal | Rankings, comparações com muitos itens |
| 📉 **Linhas** | Gráficos de linha com uma ou mais séries | Tendências temporais, séries históricas |

---

## 📐 **REGRAS DE VERIFICAÇÃO**

O sistema aplica 4 regras éticas fundamentais:

### **1. Eixo Y Começa em Zero** (📊 Barras)
- **Problema**: Eixos que não começam em zero podem exagerar diferenças
- **Alerta**: ⚠️ Se eixo Y > 0
- **Severidade**: ALTA se > 10% do valor máximo, MÉDIA caso contrário

### **2. Proporções Visuais** (📊 Todos)
- **Problema**: Alturas visuais não correspondem aos valores numéricos
- **Alerta**: ⚠️ Se diferença > 5%
- **Severidade**: ALTA se > 20%, MÉDIA caso contrário

### **3. Título Presente** (📝 Todos)
- **Problema**: Gráfico sem título ou título muito curto
- **Alerta**: ⚠️ Se título ausente ou < 5 caracteres
- **Severidade**: MÉDIA se ausente, BAIXA se muito curto

### **4. Fonte dos Dados** (📌 Todos)
- **Problema**: Ausência da fonte compromete credibilidade
- **Alerta**: ⚠️ Se fonte não identificada
- **Severidade**: ALTA

---

## 🔧 **PRÉ-REQUISITOS**

### **Software Necessário**
- **Python 3.11** ou superior
- **Tesseract OCR** (para reconhecimento de texto)
- **Git** (opcional, para clonar o repositório)

### **Instalação do Tesseract OCR**

#### **Windows**
1. Baixe o instalador em: [GitHub - Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)
2. Execute o instalador (caminho padrão: `C:\Program Files\Tesseract-OCR\`)
3. Adicione ao PATH do sistema (opcional)

#### **Linux (Ubuntu/Debian)**
```bash
sudo apt update
sudo apt install tesseract-ocr
sudo apt install tesseract-ocr-por  # Idioma português
