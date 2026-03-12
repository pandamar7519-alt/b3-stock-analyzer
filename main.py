"""
B3 Stock Analyzer - Aplicação Profissional de Análise de Ações
================================================================
Autor: Engenheiro de Software Sênior & Analista Quantitativo
Versão: 1.0.0
Licença: MIT

Esta aplicação fornece análise fundamentalista e técnica para ações da B3.
NÃO constitui recomendação de investimento. Consulte um assessor credenciado.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
import yfinance as yf
import pandas_ta as ta
import warnings

# Suprimir warnings do yfinance
warnings.filterwarnings("ignore")

# ============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================================

st.set_page_config(
    page_title="B3 Stock Analyzer | Análise Profissional",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "B3 Stock Analyzer v1.0 - Ferramenta Educacional para Investidores"
    }
)

# ============================================================================
# ESTILIZAÇÃO CUSTOMIZADA (DARK MODE PROFISSIONAL)
# ============================================================================

def apply_custom_styles() -> None:
    """Aplica estilos CSS customizados para aparência profissional."""
    st.markdown("""
    <style>
    /* Dark Mode Professional */
    .stApp {
        background-color: #0e1117;
    }
    
    /* Cards e Métricas */
    .metric-card {
        background-color: #1a1f2e;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #00d4ff;
        margin: 10px 0;
    }
    
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #00d4ff;
    }
    
    .metric-label {
        font-size: 14px;
        color: #8b9bb4;
    }
    
    /* Score Badges */
    .score-excellent { color: #00ff88; font-weight: bold; }
    .score-good { color: #ffcc00; font-weight: bold; }
    .score-poor { color: #ff4444; font-weight: bold; }
    
    /* Disclaimer Box */
    .disclaimer-box {
        background-color: #2a1f1f;
        border-left: 4px solid #ff6b6b;
        padding: 15px;
        margin: 20px 0;
        border-radius: 5px;
    }
    
    /* Table Styling */
    .dataframe {
        background-color: #1a1f2e;
        color: #ffffff;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #ffffff;
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# CLASSE PRINCIPAL - ANALISADOR DE AÇÕES
# ============================================================================

class B3StockAnalyzer:
    """
    Classe principal para análise de ações da B3.
    
    Combina análise fundamentalista, técnica e scoring para identificar
    oportunidades de investimento de longo prazo.
    """
    
    def __init__(self, ticker: str):
        """
        Inicializa o analisador para um ticker específico.
        
        Args:
            ticker: Código da ação na B3 (ex: PETR4, VALE3)
        """
        self.ticker = ticker.upper()
        self.ticker_yf = f"{self.ticker}.SA"  # Formato yfinance
        self.data: Optional[pd.DataFrame] = None
        self.info: Optional[Dict] = None
        self.fundamentals: Optional[Dict] = None
        self.technicals: Optional[Dict] = None
        self.score: float = 0.0
        
    @st.cache_data(ttl=3600)
    def fetch_data(_self, period: str = "2y") -> bool:
        """
        Busca dados históricos e fundamentos da ação.
        
        Args:
            period: Período para dados históricos (default: 2 anos)
            
        Returns:
            bool: True se sucesso, False se falha
        """
        try:
            # Busca dados históricos
            stock = yf.Ticker(_self.ticker_yf)
            _self.data = stock.history(period=period)
            
            if _self.data.empty:
                st.error(f"⚠️ Nenhum dado encontrado para {_self.ticker}")
                return False
            
            # Busca informações fundamentais
            _self.info = stock.info
            _self.fundamentals = _self._extract_fundamentals(stock)
            
            # Calcula indicadores técnicos
            _self.technicals = _self._calculate_technicals()
            
            # Calcula score
            _self.score = _self._calculate_score()
            
            return True
            
        except Exception as e:
            st.error(f"❌ Erro ao buscar dados para {_self.ticker}: {str(e)}")
            return False
    
    def _extract_fundamentals(self, stock: yf.Ticker) -> Dict:
        """
        Extrai indicadores fundamentalistas das informações da ação.
        
        Args:
            stock: Objeto yfinance Ticker
            
        Returns:
            Dict: Dicionário com indicadores fundamentalistas
        """
        info = self.info
        
        fundamentals = {
            'preco_atual': info.get('currentPrice', info.get('regularMarketPrice', 0)),
            'pl': info.get('trailingPE', None),
            'pvp': info.get('priceToBook', None),
            'roe': info.get('returnOnEquity', None),
            'roa': info.get('returnOnAssets', None),
            'margem_liquida': info.get('profitMargins', None),
            'dividend_yield': info.get('dividendYield', None),
            'payout': info.get('payoutRatio', None),
            'divida_ebitda': info.get('debtToEbitda', None),
            'liquidez_corrente': info.get('currentRatio', None),
            'ebitda': info.get('ebitda', None),
            'receita': info.get('totalRevenue', None),
            'lucro_liquido': info.get('netIncomeToCommon', None),
            'valor_mercado': info.get('marketCap', None),
            'setor': info.get('sector', 'N/A'),
            'subsetor': info.get('industry', 'N/A'),
        }
        
        # Converte valores None para 0 ou None conforme apropriado
        for key, value in fundamentals.items():
            if value is not None and isinstance(value, (int, float)):
                if key in ['roe', 'margem_liquida', 'dividend_yield', 'payout']:
                    fundamentals[key] = value * 100  # Converte para porcentagem
                elif key in ['pl', 'pvp', 'divida_ebitda', 'liquidez_corrente']:
                    fundamentals[key] = round(value, 2)
                    
        return fundamentals
    
    def _calculate_technicals(self) -> Dict:
        """
        Calcula indicadores técnicos usando pandas-ta.
        
        Returns:
            Dict: Dicionário com indicadores técnicos
        """
        if self.data is None or self.data.empty:
            return {}
        
        df = self.data.copy()
        
        # Médias Móveis
        df['MM20'] = ta.sma(df['Close'], length=20)
        df['MM50'] = ta.sma(df['Close'], length=50)
        df['MM200'] = ta.sma(df['Close'], length=200)
        
        # IFR (RSI)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        # MACD
        macd = ta.macd(df['Close'], fast=12, slow=26, signal=9)
        df = pd.concat([df, macd], axis=1)
        
        # Bandas de Bollinger
        bbands = ta.bbands(df['Close'], length=20)
        df = pd.concat([df, bbands], axis=1)
        
        # Volume Médio
        df['Volume_MA20'] = ta.sma(df['Volume'], length=20)
        
        # Dados recentes para análise
        latest = df.iloc[-1]
        previous = df.iloc[-2] if len(df) > 1 else latest
        
        technicals = {
            'mm20': round(latest['MM20'], 2) if not pd.isna(latest['MM20']) else None,
            'mm50': round(latest['MM50'], 2) if not pd.isna(latest['MM50']) else None,
            'mm200': round(latest['MM200'], 2) if not pd.isna(latest['MM200']) else None,
            'rsi': round(latest['RSI'], 2) if not pd.isna(latest['RSI']) else None,
            'macd': round(latest['MACD_12_26_9'], 4) if 'MACD_12_26_9' in df.columns else None,
            'macd_signal': round(latest['MACDs_12_26_9'], 4) if 'MACDs_12_26_9' in df.columns else None,
            'bb_upper': round(latest['BBU_20_2.0'], 2) if 'BBU_20_2.0' in df.columns else None,
            'bb_lower': round(latest['BBL_20_2.0'], 2) if 'BBL_20_2.0' in df.columns else None,
            'volume_ma20': round(latest['Volume_MA20'], 0) if not pd.isna(latest['Volume_MA20']) else None,
            'tendencia_curto': self._analyze_short_term_trend(df),
            'tendencia_longo': self._analyze_long_term_trend(df),
            'sinal_tecnico': self._generate_technical_signal(latest, previous),
        }
        
        return technicals
    
    def _analyze_short_term_trend(self, df: pd.DataFrame) -> str:
        """Analisa tendência de curto prazo baseada em MM20."""
        latest_close = df['Close'].iloc[-1]
        mm20 = df['MM20'].iloc[-1]
        
        if pd.isna(mm20):
            return "Neutro"
        elif latest_close > mm20 * 1.02:
            return "Alta"
        elif latest_close < mm20 * 0.98:
            return "Baixa"
        else:
            return "Neutro"
    
    def _analyze_long_term_trend(self, df: pd.DataFrame) -> str:
        """Analisa tendência de longo prazo baseada em MM200."""
        latest_close = df['Close'].iloc[-1]
        mm200 = df['MM200'].iloc[-1]
        
        if pd.isna(mm200):
            return "Neutro"
        elif latest_close > mm200 * 1.05:
            return "Alta Forte"
        elif latest_close > mm200:
            return "Alta"
        elif latest_close < mm200 * 0.95:
            return "Baixa Forte"
        elif latest_close < mm200:
            return "Baixa"
        else:
            return "Neutro"
    
    def _generate_technical_signal(self, latest: pd.Series, previous: pd.Series) -> str:
        """
        Gera sinal técnico baseado em múltiplos indicadores.
        
        Returns:
            str: 'Compra', 'Neutro' ou 'Venda'
        """
        score = 0
        
        # RSI Analysis
        rsi = latest.get('RSI', 50)
        if not pd.isna(rsi):
            if rsi < 30:
                score += 2  # Sobrevenda - oportunidade
            elif rsi < 40:
                score += 1
            elif rsi > 70:
                score -= 2  # Sobrecompra - risco
            elif rsi > 60:
                score -= 1
        
        # MACD Analysis
        macd = latest.get('MACD_12_26_9', 0)
        macd_signal = latest.get('MACDs_12_26_9', 0)
        if not pd.isna(macd) and not pd.isna(macd_signal):
            if macd > macd_signal:
                score += 1
            else:
                score -= 1
        
        # Price vs MM200
        close = latest['Close']
        mm200 = latest.get('MM200', close)
        if not pd.isna(mm200):
            if close > mm200:
                score += 1
            else:
                score -= 1
        
        # Volume Analysis
        volume = latest.get('Volume', 0)
        volume_ma = latest.get('Volume_MA20', volume)
        if not pd.isna(volume_ma) and volume_ma > 0:
            if volume > volume_ma * 1.5:
                score += 1  # Volume acima da média
        
        # Generate Signal
        if score >= 3:
            return "Compra"
        elif score >= 1:
            return "Compra Fraca"
        elif score <= -3:
            return "Venda"
        elif score <= -1:
            return "Venda Fraca"
        else:
            return "Neutro"
    
    def _calculate_score(self) -> float:
        """
        Calcula score de saúde da empresa (0-100).
        
        Critérios:
        - Rentabilidade (ROE, Margens): 30 pontos
        - Endividamento: 25 pontos
        - Valuation: 25 pontos
        - Dividendos: 20 pontos
        
        Returns:
            float: Score entre 0 e 100
        """
        if not self.fundamentals:
            return 0.0
        
        score = 0.0
        f = self.fundamentals
        
        # === RENTABILIDADE (30 pontos) ===
        roe = f.get('roe')
        if roe is not None:
            if roe >= 20:
                score += 15
            elif roe >= 15:
                score += 12
            elif roe >= 10:
                score += 8
            elif roe >= 5:
                score += 4
        
        margem = f.get('margem_liquida')
        if margem is not None:
            if margem >= 20:
                score += 15
            elif margem >= 15:
                score += 12
            elif margem >= 10:
                score += 8
            elif margem >= 5:
                score += 4
        
        # === ENDIVIDAMENTO (25 pontos) ===
        div_ebitda = f.get('divida_ebitda')
        if div_ebitda is not None:
            if div_ebitda <= 1:
                score += 15
            elif div_ebitda <= 2:
                score += 12
            elif div_ebitda <= 3:
                score += 8
            elif div_ebitda <= 4:
                score += 4
        
        liq_corrente = f.get('liquidez_corrente')
        if liq_corrente is not None:
            if liq_corrente >= 2:
                score += 10
            elif liq_corrente >= 1.5:
                score += 7
            elif liq_corrente >= 1:
                score += 4
        
        # === VALUATION (25 pontos) ===
        pl = f.get('pl')
        if pl is not None and pl > 0:
            if pl <= 10:
                score += 15
            elif pl <= 15:
                score += 12
            elif pl <= 20:
                score += 8
            elif pl <= 25:
                score += 4
        
        pvp = f.get('pvp')
        if pvp is not None and pvp > 0:
            if pvp <= 1:
                score += 10
            elif pvp <= 1.5:
                score += 7
            elif pvp <= 2:
                score += 4
        
        # === DIVIDENDOS (20 pontos) ===
        dy = f.get('dividend_yield')
        if dy is not None:
            if dy >= 8:
                score += 12
            elif dy >= 6:
                score += 10
            elif dy >= 4:
                score += 7
            elif dy >= 2:
                score += 4
        
        payout = f.get('payout')
        if payout is not None:
            if 40 <= payout <= 70:
                score += 8  # Payout ideal
            elif 30 <= payout <= 80:
                score += 5
            elif payout <= 100:
                score += 2
        
        return min(100, max(0, score))
    
    def get_summary(self) -> Dict:
        """
        Retorna resumo completo da análise.
        
        Returns:
            Dict: Resumo com todos os indicadores
        """
        return {
            'ticker': self.ticker,
            'fundamentals': self.fundamentals,
            'technicals': self.technicals,
            'score': self.score,
            'score_category': self._get_score_category(self.score),
        }
    
    @staticmethod
    def _get_score_category(score: float) -> str:
        """Classifica o score em categorias."""
        if score >= 80:
            return "Excelente"
        elif score >= 60:
            return "Bom"
        elif score >= 40:
            return "Regular"
        else:
            return "Atenção"


# ============================================================================
# FUNÇÕES DE VISUALIZAÇÃO
# ============================================================================

def create_candlestick_chart(data: pd.DataFrame, ticker: str) -> go.Figure:
    """
    Cria gráfico de candlestick interativo com Plotly.
    
    Args:
        data: DataFrame com dados históricos
        ticker: Código da ação
        
    Returns:
        go.Figure: Gráfico Plotly
    """
    fig = go.Figure()
    
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='Preço',
        increasing_line_color='#00ff88',
        decreasing_line_color='#ff4444'
    ))
    
    # Médias Móveis
    if 'MM20' in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index, y=data['MM20'],
            line=dict(color='#00d4ff', width=1),
            name='MM20'
        ))
    
    if 'MM50' in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index, y=data['MM50'],
            line=dict(color='#ffcc00', width=1),
            name='MM50'
        ))
    
    if 'MM200' in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index, y=data['MM200'],
            line=dict(color='#ff6b6b', width=1),
            name='MM200'
        ))
    
    fig.update_layout(
        title=f"{ticker} - Evolução de Preço",
        yaxis_title="Preço (R$)",
        xaxis_title="Data",
        template="plotly_dark",
        height=600,
        showlegend=True,
        xaxis_rangeslider_visible=False
    )
    
    return fig


def create_rsi_chart(data: pd.DataFrame) -> go.Figure:
    """Cria gráfico do IFR (RSI)."""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=data.index, y=data['RSI'],
        line=dict(color='#00d4ff', width=2),
        name='RSI'
    ))
    
    # Linhas de sobrecompra/sobrevenda
    fig.add_hline(y=70, line_dash="dash", line_color="#ff4444", annotation_text="Sobrecompra")
    fig.add_hline(y=30, line_dash="dash", line_color="#00ff88", annotation_text="Sobrevenda")
    
    fig.update_layout(
        title="IFR (RSI) - 14 períodos",
        yaxis_title="RSI",
        template="plotly_dark",
        height=200,
        showlegend=False,
        yaxis_range=[0, 100]
    )
    
    return fig


def create_dividend_projection(
    initial_investment: float,
    monthly_contribution: float,
    annual_return: float,
    dividend_yield: float,
    years: int
) -> pd.DataFrame:
    """
    Calcula projeção de renda passiva com reinvestimento de dividendos.
    
    Args:
        initial_investment: Investimento inicial
        monthly_contribution: Aporte mensal
        annual_return: Retorno anual esperado (%)
        dividend_yield: Dividend Yield (%)
        years: Período em anos
        
    Returns:
        pd.DataFrame: Tabela com projeção ano a ano
    """
    data = []
    balance = initial_investment
    total_invested = initial_investment
    total_dividends = 0
    
    for year in range(1, years + 1):
        # Dividendos do ano
        dividends = balance * (dividend_yield / 100)
        total_dividends += dividends
        
        # Reinvestimento automático
        balance += dividends
        
        # Aportes mensais com juros compostos
        for month in range(12):
            balance += monthly_contribution
            total_invested += monthly_contribution
        
        # Retorno anual
        balance *= (1 + annual_return / 100)
        
        data.append({
            'Ano': year,
            'Patrimônio': round(balance, 2),
            'Investido': round(total_invested, 2),
            'Dividendos Acumulados': round(total_dividends, 2),
            'Renda Mensal Estimada': round((balance * dividend_yield / 100) / 12, 2)
        })
    
    return pd.DataFrame(data)


# ============================================================================
# COMPONENTES DE UI
# ============================================================================

def render_disclaimer() -> None:
    """Exibe disclaimer legal obrigatório (Compliance CVM)."""
    st.markdown("""
    <div class="disclaimer-box">
    <strong>⚠️ DISCLAIMER LEGAL - LEIA ATENTAMENTE</strong><br><br>
    Esta ferramenta é destinada exclusivamente para fins <strong>educacionais e informativos</strong>. 
    As informações apresentadas <strong>NÃO constituem recomendação de investimento</strong>, 
    oferta ou solicitação de compra ou venda de valores mobiliários.<br><br>
    • Rentabilidade passada não garante retornos futuros<br>
    • Todas as decisões de investimento são de responsabilidade exclusiva do investidor<br>
    • Consulte um assessor de investimentos credenciado pela CVM antes de investir<br>
    • Esta aplicação não possui registro na CVM como consultor de valores mobiliários<br><br>
    <em>Em conformidade com a Instrução CVM 598/2018</em>
    </div>
    """, unsafe_allow_html=True)


def render_metric_card(label: str, value: str, subtext: str = "") -> None:
    """Renderiza card de métrica estilizado."""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-label">{subtext}</div>
    </div>
    """, unsafe_allow_html=True)


def render_score_badge(score: float) -> str:
    """Retorna HTML do badge de score."""
    if score >= 80:
        return f'<span class="score-excellent">★ {score:.0f}/100 - Excelente</span>'
    elif score >= 60:
        return f'<span class="score-good">● {score:.0f}/100 - Bom</span>'
    elif score >= 40:
        return f'<span class="score-poor">▲ {score:.0f}/100 - Regular</span>'
    else:
        return f'<span class="score-poor">▼ {score:.0f}/100 - Atenção</span>'


def render_technical_signal(signal: str) -> str:
    """Retorna HTML do sinal técnico."""
    if "Compra" in signal:
        color = "#00ff88"
        icon = "🟢"
    elif "Venda" in signal:
        color = "#ff4444"
        icon = "🔴"
    else:
        color = "#ffcc00"
        icon = "🟡"
    
    return f'<span style="color: {color}; font-weight: bold;">{icon} {signal}</span>'


# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    """Função principal da aplicação."""
    
    # Aplica estilos customizados
    apply_custom_styles()
    
    # Header
    st.title("📊 B3 Stock Analyzer")
    st.subtitle("Análise Profissional de Ações para Investidores de Longo Prazo")
    
    # Disclaimer no topo
    render_disclaimer()
    
    # ========================================================================
    # SIDEBAR - INPUT DE DADOS
    # ========================================================================
    
    with st.sidebar:
        st.header("⚙️ Configurações")
        
        # Input de Tickers
        st.subheader("📝 Tickers para Análise")
        st.info("Insira até 10 tickers separados por vírgula (ex: PETR4, VALE3, ITUB4)")
        
        tickers_input = st.text_area(
            "Tickers B3",
            value="PETR4, VALE3, ITUB4, BBAS3, WEGE3",
            height=100,
            help="Códigos das ações na B3 (4 caracteres + número)"
        )
        
        # Processa input
        tickers = [t.strip().upper() for t in tickers_input.split(',') if t.strip()]
        tickers = tickers[:10]  # Limita a 10
        
        if tickers:
            st.success(f"✅ {len(tickers)} ticker(s) carregado(s)")
        else:
            st.warning("⚠️ Insira pelo menos 1 ticker")
        
        st.divider()
        
        # Configurações de Análise
        st.subheader("🔧 Parâmetros")
        
        period = st.selectbox(
            "Período de Dados",
            options=["1y", "2y", "5y", "10y"],
            index=1,
            help="Período para cálculo de indicadores técnicos"
        )
        
        st.divider()
        
        # Calculadora de Projeção
        st.subheader("💰 Projeção de Renda")
        
        initial_inv = st.number_input(
            "Investimento Inicial (R$)",
            min_value=0.0,
            value=10000.0,
            step=1000.0
        )
        
        monthly_contrib = st.number_input(
            "Aporte Mensal (R$)",
            min_value=0.0,
            value=500.0,
            step=100.0
        )
        
        years_proj = st.slider(
            "Período (anos)",
            min_value=1,
            max_value=30,
            value=10
        )
        
        st.divider()
        
        # Informações
        st.subheader("ℹ️ Sobre")
        st.markdown("""
        **Versão:** 1.0.0<br>
        **Desenvolvido por:** Analista Quantitativo<br>
        **Tecnologia:** Python + Streamlit<br>
        **Dados:** yfinance (B3 via .SA)<br>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Disclaimer na sidebar
        st.warning("""
        ⚠️ **Atenção:** Esta ferramenta não 
        constitui recomendação de investimento. 
        Consulte um assessor credenciado CVM.
        """)
    
    # ========================================================================
    # ÁREA PRINCIPAL
    # ========================================================================
    
    if not tickers:
        st.info("👈 Insira tickers na sidebar para iniciar a análise")
        return
    
    # Cache para evitar requisições repetidas
    @st.cache_data(ttl=3600)
    def analyze_tickers(tickers_list: List[str], period: str) -> Dict[str, B3StockAnalyzer]:
        """Analisa múltiplos tickers com cache."""
        results = {}
        progress_bar = st.progress(0)
        
        for i, ticker in enumerate(tickers_list):
            analyzer = B3StockAnalyzer(ticker)
            if analyzer.fetch_data(period):
                results[ticker] = analyzer
            progress_bar.progress((i + 1) / len(tickers_list))
        
        progress_bar.empty()
        return results
    
    # Executa análise
    with st.spinner("🔄 Analisando ativos..."):
        analyzers = analyze_tickers(tickers, period)
    
    if not analyzers:
        st.error("❌ Nenhum dado válido foi retornado. Verifique os tickers.")
        return
    
    # ========================================================================
    # DASHBOARD COMPARATIVO
    # ========================================================================
    
    st.header("📈 Dashboard Comparativo")
    
    # Cria tabela comparativa
    comparison_data = []
    
    for ticker, analyzer in analyzers.items():
        summary = analyzer.get_summary()
        fund = summary['fundamentals'] or {}
        tech = summary['technicals'] or {}
        
        comparison_data.append({
            'Ticker': ticker,
            'Score': summary['score'],
            'Categoria': summary['score_category'],
            'Preço (R$)': f"R$ {fund.get('preco_atual', 0):.2f}" if fund.get('preco_atual') else 'N/A',
            'P/L': f"{fund.get('pl', 'N/A'):.2f}" if isinstance(fund.get('pl'), (int, float)) else 'N/A',
            'ROE (%)': f"{fund.get('roe', 0):.1f}" if isinstance(fund.get('roe'), (int, float)) else 'N/A',
            'DY (%)': f"{fund.get('dividend_yield', 0):.2f}" if isinstance(fund.get('dividend_yield'), (int, float)) else 'N/A',
            'Dívida/EBITDA': f"{fund.get('divida_ebitda', 'N/A'):.2f}" if isinstance(fund.get('divida_ebitda'), (int, float)) else 'N/A',
            'Tendência': tech.get('tendencia_longo', 'N/A'),
            'Sinal Técnico': tech.get('sinal_tecnico', 'Neutro'),
            'Setor': fund.get('setor', 'N/A'),
        })
    
    df_comparison = pd.DataFrame(comparison_data)
    
    # Ordena por score
    df_comparison = df_comparison.sort_values('Score', ascending=False)
    
    # Exibe tabela
    st.dataframe(
        df_comparison,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Score": st.column_config.ProgressColumn(
                "Score",
                help="Score de Saúde da Empresa",
                min_value=0,
                max_value=100,
            ),
        }
    )
    
    # ========================================================================
    # ANÁLISE DETALHADA POR ATIVO
    # ========================================================================
    
    st.header("🔍 Análise Detalhada por Ativo")
    
    # Selector de ativo
    selected_ticker = st.selectbox(
        "Selecione um ativo para análise detalhada",
        options=list(analyzers.keys()),
        index=0
    )
    
    if selected_ticker:
        analyzer = analyzers[selected_ticker]
        summary = analyzer.get_summary()
        fund = summary['fundamentals'] or {}
        tech = summary['technicals'] or {}
        
        # Colunas para métricas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            render_metric_card(
                "Score de Saúde",
                f"{summary['score']:.0f}/100",
                summary['score_category']
            )
        
        with col2:
            render_metric_card(
                "Preço Atual",
                f"R$ {fund.get('preco_atual', 0):.2f}" if fund.get('preco_atual') else "N/A",
                fund.get('subsetor', '')
            )
        
        with col3:
            render_metric_card(
                "Sinal Técnico",
                tech.get('sinal_tecnico', 'Neutro'),
                f"Tendência: {tech.get('tendencia_longo', 'N/A')}"
            )
        
        with col4:
            render_metric_card(
                "Dividend Yield",
                f"{fund.get('dividend_yield', 0):.2f}%" if isinstance(fund.get('dividend_yield'), (int, float)) else "N/A",
                f"Payout: {fund.get('payout', 0):.1f}%" if isinstance(fund.get('payout'), (int, float)) else "N/A"
            )
        
        # Gráficos
        col_chart1, col_chart2 = st.columns([2, 1])
        
        with col_chart1:
            if analyzer.data is not None and not analyzer.data.empty:
                fig_candle = create_candlestick_chart(analyzer.data, selected_ticker)
                st.plotly_chart(fig_candle, use_container_width=True)
        
        with col_chart2:
            if analyzer.data is not None and 'RSI' in analyzer.data.columns:
                fig_rsi = create_rsi_chart(analyzer.data)
                st.plotly_chart(fig_rsi, use_container_width=True)
        
        # Detalhes Fundamentalistas
        st.subheader("📊 Indicadores Fundamentalistas")
        
        col_fund1, col_fund2, col_fund3 = st.columns(3)
        
        with col_fund1:
            st.markdown("**Valuation**")
            st.write(f"P/L: {fund.get('pl', 'N/A')}")
            st.write(f"P/VP: {fund.get('pvp', 'N/A')}")
            st.write(f"Valor de Mercado: R$ {fund.get('valor_mercado', 0):,.0f}" if fund.get('valor_mercado') else "N/A")
        
        with col_fund2:
            st.markdown("**Rentabilidade**")
            st.write(f"ROE: {fund.get('roe', 0):.2f}%" if isinstance(fund.get('roe'), (int, float)) else "N/A")
            st.write(f"ROA: {fund.get('roa', 0):.2f}%" if isinstance(fund.get('roa'), (int, float)) else "N/A")
            st.write(f"Margem Líquida: {fund.get('margem_liquida', 0):.2f}%" if isinstance(fund.get('margem_liquida'), (int, float)) else "N/A")
        
        with col_fund3:
            st.markdown(**Endividamento**)
            st.write(f"Dívida/EBITDA: {fund.get('divida_ebitda', 'N/A')}")
            st.write(f"Liquidez Corrente: {fund.get('liquidez_corrente', 'N/A')}")
            st.write(f"Setor: {fund.get('setor', 'N/A')}")
        
        # Detalhes Técnicos
        st.subheader("📈 Indicadores Técnicos")
        
        col_tech1, col_tech2, col_tech3 = st.columns(3)
        
        with col_tech1:
            st.markdown("**Médias Móveis**")
            st.write(f"MM20: R$ {tech.get('mm20', 'N/A')}")
            st.write(f"MM50: R$ {tech.get('mm50', 'N/A')}")
            st.write(f"MM200: R$ {tech.get('mm200', 'N/A')}")
        
        with col_tech2:
            st.markdown(**Osciladores**)
            st.write(f"RSI (14): {tech.get('rsi', 'N/A')}")
            st.write(f"MACD: {tech.get('macd', 'N/A')}")
            st.write(f"Sinal MACD: {tech.get('macd_signal', 'N/A')}")
        
        with col_tech3:
            st.markdown("**Tendências**")
            st.write(f"Curto Prazo: {tech.get('tendencia_curto', 'N/A')}")
            st.write(f"Longo Prazo: {tech.get('tendencia_longo', 'N/A')}")
            st.write(f"Volume vs Média: {'Acima' if analyzer.data['Volume'].iloc[-1] > tech.get('volume_ma20', 0) else 'Abaixo'}")
    
    # ========================================================================
    # PROJEÇÃO DE RENDA PASSIVA
    # ========================================================================
    
    st.divider()
    st.header("💰 Projeção de Renda Passiva")
    
    # Usa DY médio dos ativos selecionados
    avg_dy = 0
    dy_count = 0
    for analyzer in analyzers.values():
        dy = analyzer.fundamentals.get('dividend_yield') if analyzer.fundamentals else None
        if dy and isinstance(dy, (int, float)):
            avg_dy += dy
            dy_count += 1
    
    avg_dy = (avg_dy / dy_count) if dy_count > 0 else 6.0
    
    st.info(f"📊 Dividend Yield Médio dos Ativos Selecionados: **{avg_dy:.2f}%**")
    
    # Calcula projeção
    projection_df = create_dividend_projection(
        initial_investment=initial_inv,
        monthly_contribution=monthly_contrib,
        annual_return=10.0,  # Retorno anual estimado
        dividend_yield=avg_dy,
        years=years_proj
    )
    
    # Exibe tabela de projeção
    st.dataframe(
        projection_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Patrimônio": st.column_config.NumberColumn(format="R$ %d"),
            "Investido": st.column_config.NumberColumn(format="R$ %d"),
            "Dividendos Acumulados": st.column_config.NumberColumn(format="R$ %d"),
            "Renda Mensal Estimada": st.column_config.NumberColumn(format="R$ %d"),
        }
    )
    
    # Gráfico de projeção
    fig_proj = px.line(
        projection_df,
        x='Ano',
        y=['Patrimônio', 'Investido'],
        title='Projeção de Patrimônio vs Investido',
        template='plotly_dark',
        labels={'value': 'Valor (R$)', 'variable': 'Tipo'}
    )
    fig_proj.update_layout(height=400)
    st.plotly_chart(fig_proj, use_container_width=True)
    
    # ========================================================================
    # RODAPÉ
    # ========================================================================
    
    st.divider()
    
    col_footer1, col_footer2, col_footer3 = st.columns(3)
    
    with col_footer1:
        st.markdown("""
        **B3 Stock Analyzer**<br>
        Versão 1.0.0<br>
        Desenvolvido com Python + Streamlit
        """, unsafe_allow_html=True)
    
    with col_footer2:
        st.markdown("""
        **Fontes de Dados**<br>
        yfinance (Yahoo Finance)<br>
        Dados com delay de 15min
        """, unsafe_allow_html=True)
    
    with col_footer3:
        st.markdown("""
        **Contato**<br>
        GitHub: /b3-stock-analyzer<br>
        License: MIT
        """, unsafe_allow_html=True)
    
    # Disclaimer final
    st.markdown("""
    <div style="text-align: center; color: #8b9bb4; font-size: 12px; margin-top: 20px;">
    ⚠️ Esta ferramenta é para fins educacionais e não constitui recomendação de investimento. 
    Consulte um assessor credenciado pela CVM. Rentabilidade passada não garante retornos futuros.
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# EXECUÇÃO
# ============================================================================

if __name__ == "__main__":
    main()
