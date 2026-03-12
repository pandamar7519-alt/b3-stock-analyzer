# 📊 B3 Stock Analyzer

**Análise Profissional de Ações da B3 para Investidores de Longo Prazo**

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32.0-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## 🎯 Sobre o Projeto

Aplicação web desenvolvida em Python + Streamlit para análise fundamentalista e técnica de ações listadas na Bolsa de Valores Brasileira (B3). Focada em investidores de longo prazo que buscam renda passiva através de dividendos e valorização patrimonial.

### ✨ Funcionalidades Principais

- ✅ Análise de até 10 ativos simultaneamente
- ✅ Score de Saúde da Empresa (0-100)
- ✅ Indicadores Fundamentalistas (P/L, ROE, DY, Dívida/EBITDA)
- ✅ Indicadores Técnicos (RSI, Médias Móveis, MACD)
- ✅ Gráficos Interativos (Plotly)
- ✅ Projeção de Renda Passiva com Juros Compostos
- ✅ Dark Mode Profissional
- ✅ Compliance CVM (Disclaimers Obrigatórios)

---

## 🚀 Instalação e Uso

### Pré-requisitos

- Python 3.9 ou superior
- pip (gerenciador de pacotes Python)
- Conta GitHub (opcional, para deploy)

### Instalação Local

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/b3-stock-analyzer.git
cd b3-stock-analyzer

# 2. Crie ambiente virtual (recomendado)
python -m venv venv

# 3. Ative o ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Instale dependências
pip install -r requirements.txt

# 5. Execute a aplicação
streamlit run main.py
