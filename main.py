"""
B3 Stock Analyzer - Aplicação Profissional de Análise de Ações
================================================================
Autor: Engenheiro de Software Sênior & Analista Quantitativo
Versão: 1.1.0 (Corrigido para Streamlit Cloud)
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
        "About": "B3 Stock Analyzer v1.1 - Ferramenta Educacional para Investidores"
    }
)

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
        
    @st.cache_data(ttl=3600, show_spinner="Buscando dados financeiros...")
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
                return False
            
            # Busca informações fundamentais
            _self.info = stock.info
            _self.fundamentals = _self._extract_fundamentals(stock)
            
            # Calcula indicadores técnicos
            _self.technicals = _self._calculate_technicals()
            
            # Calcula score
            _self.score = _self._calculate_score()
            
            return True
            
        except Exception:
            return False
    
    def _extract_fundamentals(self, stock: yf.Ticker) -> Dict:
        """Extrai indicadores fundamentalistas das informações da ação."""
        info = self.info or {}
        
        fundamentals = {
            'preco_atual': info.get('currentPrice') or info.get('regularMarketPrice'),
            'pl': info.get('trailingPE'),
            'pvp': info.get('priceToBook'),
            'roe': info.get('returnOnEquity'),
            'roa': info.get('returnOnAssets'),
            'margem_liquida': info.get('profitMargins'),
            'dividend_yield': info.get('dividendYield'),
            'payout': info.get('payoutRatio'),
            'divida_ebitda': info.get('debtToEbitda'),
            'liquidez_corrente': info.get('currentRatio'),
            'valor_mercado': info.get('marketCap'),
            'setor': info.get('sector', 'N/A'),
            'subsetor': info.get('industry', 'N/A'),
        }
        
        # Converte valores para porcentagem quando aplicável
        for key in ['roe', 'margem_liquida', 'dividend_yield', 'payout']:
            if fundamentals[key] is not None:
                fundamentals[key] = fundamentals[key] * 100
                
        # Arredonda valores numéricos
        for key in ['pl', 'pvp', 'divida_ebitda', 'liquidez_corrente']:
            if fundamentals[key] is not None:
                fundamentals[key] = round(fundamentals[key], 2)
                    
        return fundamentals
    
    def _calculate_technicals(self) -> Dict:
        """Calcula indicadores técnicos usando pandas-ta."""
        if self.data is None or self.data.empty:
            return {}
        
        df = self.data.copy()
        
        try:
            # Médias Móveis
            df['MM20'] = ta.sma(df['Close'], length=20)
            df['MM50'] = ta.sma(df['Close'], length=50)
            df['MM200'] = ta.sma(df['Close'], length=200)
            
            # IFR (RSI)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            
            # MACD
            macd = ta.macd(df['Close'], fast=12, slow=26, signal=9)
            if macd is not None:
                df = pd.concat([df, macd], axis=1)
            
            # Dados recentes para análise
            latest = df.iloc[-1]
            
            technicals = {
                'mm20': float(latest['MM20']) if not pd.isna(latest.get('MM20')) else None,
                'mm50': float(latest['MM50']) if not pd.isna(latest.get('MM50')) else None,
                'mm200': float(latest['MM200']) if not pd.isna(latest.get('MM200')) else None,
                'rsi': float(latest['RSI']) if not pd.isna(latest.get('RSI')) else None,
                'macd': float(latest['MACD_12_26_9']) if 'MACD_12_26_9' in df.columns and not pd.isna(latest.get('MACD_12_26_9')) else None,
                'macd_signal': float(latest['MACDs_12_26_9']) if 'MACDs_12_26_9' in df.columns and not pd.isna(latest.get('MACDs_12_26_9')) else None,
                'tendencia_curto': self._analyze_short_term_trend(df),
                'tendencia_longo': self._analyze_long_term_trend(df),
                'sinal_tecnico': self._generate_technical_signal(latest),
            }
            
            return technicals
            
        except Exception:
            # Retorna técnico básico se cálculo falhar
            return {
                'tendencia_curto': 'Neutro',
                'tendencia_longo': 'Neutro', 
                'sinal_tecnico': 'Neutro',
            }
    
    def _analyze_short_term_trend(self, df: pd.DataFrame) -> str:
        """Analisa tendência de curto prazo baseada em MM20."""
        latest_close = df['Close'].iloc[-1]
        mm20 = df['MM20'].iloc[-1] if 'MM20' in df.columns else None
        
        if mm20 is None or pd.isna(mm20):
            return "Neutro"
        elif latest_close > mm20 * 1.02:
            return "Alta"
        elif latest_close < mm20 * 0.98:
            return "Baixa"
        return "Neutro"
    
    def _analyze_long_term_trend(self, df: pd.DataFrame) -> str:
        """Analisa tendência de longo prazo baseada em MM200."""
        latest_close = df['Close'].iloc[-1]
        mm200 = df['MM200'].iloc[-1] if 'MM200' in df.columns else None
        
        if mm200 is None or pd.isna(mm200):
            return "Neutro"
        elif latest_close > mm200 * 1.05:
            return "Alta Forte"
        elif latest_close > mm200:
            return "Alta"
        elif latest_close < mm200 * 0.95:
            return "Baixa Forte"
        elif latest_close < mm200:
            return "Baixa"
        return "Neutro"
    
    def _generate_technical_signal(self, latest: pd.Series) -> str:
        """Gera sinal técnico baseado em múltiplos indicadores."""
        score = 0
        
        # RSI Analysis
        rsi = latest.get('RSI')
        if rsi is not None and not pd.isna(rsi):
            if rsi < 30:
                score += 2
            elif rsi < 40:
                score += 1
            elif rsi > 70:
                score -= 2
            elif rsi > 60:
                score -= 1
        
        # MACD Analysis
        macd = latest.get('MACD_12_26_9')
        macd_signal = latest.get('MACDs_12_26_9')
        if macd is not None and macd_signal is not None and not pd.isna(macd) and not pd.isna(macd_signal):
            if macd > macd_signal:
                score += 1
            else:
                score -= 1
        
        # Price vs MM200
        close = latest['Close']
        mm200 = latest.get('MM200')
        if mm200 is not None and not pd.isna(mm200):
            if close > mm200:
                score += 1
            else:
                score -= 1
        
        # Generate Signal
        if score >= 3:
            return "Compra"
        elif score >= 1:
            return "Compra Fraca"
        elif score <= -3:
            return "Venda"
        elif score <= -1:
            return "Venda Fraca"
        return "Neutro"
    
    def _calculate_score(self) -> float:
        """Calcula score de saúde da empresa (0-100)."""
        if not self.fundamentals:
            return 0.0
        
        score = 0.0
        f = self.fundamentals
        
        # === RENTABILIDADE (30 pontos) ===
        roe = f.get('roe')
        if roe is not None and not pd.isna(roe):
            if roe >= 20: score += 15
            elif roe >= 15: score += 12
            elif roe >= 10: score += 8
            elif roe >= 5: score += 4
        
        margem = f.get('margem_liquida')
        if margem is not None and not pd.isna(margem):
            if margem >= 20: score += 15
            elif margem >= 15: score += 12
            elif margem >= 10: score += 8
            elif margem >= 5: score += 4
        
        # === ENDIVIDAMENTO (25 pontos) ===
        div_ebitda = f.get('divida_ebitda')
        if div_ebitda is not None and not pd.isna(div_ebitda):
            if div_ebitda <= 1: score += 15
            elif div_ebitda <= 2: score += 12
            elif div_ebitda <= 3: score += 8
            elif div_ebitda <= 4: score += 4
        
        liq_corrente = f.get('liquidez_corrente')
        if liq_corrente is not None and not pd.isna(liq_corrente):
            if liq_corrente >= 2: score += 10
            elif liq_corrente >= 1.5: score += 7
            elif liq_corrente >= 1: score += 4
        
        # === VALUATION (25 pontos) ===
        pl = f.get('pl')
        if pl is not None and not pd.isna(pl) and pl > 0:
            if pl <= 10: score += 15
            elif pl <= 15: score += 12
            elif pl <= 20: score += 8
            elif pl <= 25: score += 4
        
        pvp = f.get('pvp')
        if pvp is not None and not pd.isna(pvp) and pvp > 0:
            if pvp <= 1: score += 10
            elif pvp <= 1.5: score += 7
            elif pvp <= 2: score += 4
        
        # === DIVIDENDOS (20 pontos) ===
        dy = f.get('dividend_yield')
        if dy is not None and not pd.isna(dy):
            if dy >= 8: score += 12
            elif dy >= 6: score += 10
            elif dy >= 4: score += 7
            elif dy >= 2: score += 4
        
        payout = f.get('payout')
        if payout is not None and not pd.isna(payout):
            if 40 <= payout <= 70: score += 8
            elif 30 <= payout <= 80: score += 5
            elif payout <= 100: score += 2
        
        return min(100.0, max(0.0, score))
    
    def get_summary(self) -> Dict:
        """Retorna resumo completo da análise."""
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
        if score >= 80: return "Excelente"
        elif score >= 60: return "Bom"
        elif score >= 40: return "Regular"
        return "Atenção"


# ============================================================================
# FUNÇÕES DE VISUALIZAÇÃO
# ============================================================================

def create_candlestick_chart(data: pd.DataFrame, ticker: str) -> go.Figure:
    """Cria gráfico de candlestick interativo com Plotly."""
    fig = go.Figure()
    
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
    for col, color, name in [('MM20', '#00d4ff', 'MM20'), 
                              ('MM50', '#ffcc00', 'MM50'), 
                              ('MM200', '#ff6b6b', 'MM200')]:
        if col in data.columns:
            fig.add_trace(go.Scatter(
                x=data.index, y=data[col],
                line=dict(color=color, width=1),
                name=name
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
    if 'RSI' not in data.columns:
        return go.Figure()
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=data.index, y=data['RSI'],
        line=dict(color='#00d4ff', width=2),
        name='RSI'
    ))
    
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
    """Calcula projeção de renda passiva com reinvestimento de dividendos."""
    data = []
    balance = initial_investment
    total_invested = initial_investment
    total_dividends = 0.0
    
    for year in range(1, years + 1):
        dividends = balance * (dividend_yield / 100)
        total_dividends += dividends
        balance += dividends
        
        for _ in range(12):
            balance += monthly_contribution
            total_invested += monthly_contribution
        
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
# COMPONENTES DE UI (SEM HTML DINÂMICO PROBLEMÁTICO)
# ============================================================================

def render_disclaimer() -> None:
    """Exibe disclaimer legal obrigatório (Compliance CVM)."""
    st.warning("""
    **⚠️ DISCLAIMER LEGAL - LEIA ATENTAMENTE**
    
    Esta ferramenta é destinada exclusivamente para fins **educacionais e informativos**. 
    As informações apresentadas **NÃO constituem recomendação de investimento**, 
    oferta ou solicitação de compra ou venda de valores mobiliários.
    
    • Rentabilidade passada não garante retornos futuros
    • Todas as decisões de investimento são de responsabilidade exclusiva do investidor
    • Consulte um assessor de investimentos credenciado pela CVM antes de investir
    • Esta aplicação não possui registro na CVM como consultor de valores mobiliários
    
    *Em conformidade com a Instrução CVM 598/2018*
    """)


def render_score_badge(score: float) -> Tuple[str, str]:
    """
    Retorna emoji e cor para badge de score.
    
    Returns:
        Tuple[str, str]: (emoji, cor_hex)
    """
    if score >= 80:
        return "⭐", "#00ff88"
    elif score >= 60:
        return "✅", "#ffcc00"
    elif score >= 40:
        return "⚠️", "#ff9900"
    return "❌", "#ff4444"


def render_technical_signal(signal: str) -> Tuple[str, str]:
    """
    Retorna emoji e cor para sinal técnico.
    
    Returns:
        Tuple[str, str]: (emoji, cor_hex)
    """
    if "Compra" in signal:
        return "🟢", "#00ff88"
    elif "Venda" in signal:
        return "🔴", "#ff4444"
    return "🟡", "#ffcc00"


# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    """Função principal da aplicação."""
    
    # Header
    st.title("📊 B3 Stock Analyzer")
    st.caption("Análise Profissional de Ações para Investidores de Longo Prazo")
    
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
        tickers = tickers[:10]
        
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
        **Versão:** 1.1.0 (Corrigido)  
        **Desenvolvido por:** Analista Quantitativo  
        **Tecnologia:** Python + Streamlit  
        **Dados:** yfinance (B3 via .SA)
        """)
        
        st.divider()
        
        # Disclaimer na sidebar
        st.warning("⚠️ Esta ferramenta não constitui recomendação de investimento. Consulte um assessor credenciado CVM.")
    
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
        
        for ticker in tickers_list:
            analyzer = B3StockAnalyzer(ticker)
            if analyzer.fetch_data(period):
                results[ticker] = analyzer
        
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
            'Score': round(summary['score'], 1),
            'Categoria': summary['score_category'],
            'Preço (R$)': f"R$ {fund.get('preco_atual', 0):.2f}" if fund.get('preco_atual') else 'N/A',
            'P/L': f"{fund.get('pl', 0):.2f}" if isinstance(fund.get('pl'), (int, float)) and fund['pl'] > 0 else 'N/A',
            'ROE (%)': f"{fund.get('roe', 0):.1f}" if isinstance(fund.get('roe'), (int, float)) else 'N/A',
            'DY (%)': f"{fund.get('dividend_yield', 0):.2f}" if isinstance(fund.get('dividend_yield'), (int, float)) else 'N/A',
            'Dívida/EBITDA': f"{fund.get('divida_ebitda', 0):.2f}" if isinstance(fund.get('divida_ebitda'), (int, float)) else 'N/A',
            'Tendência': tech.get('tendencia_longo', 'N/A'),
            'Sinal Técnico': tech.get('sinal_tecnico', 'Neutro'),
            'Setor': fund.get('setor', 'N/A'),
        })
    
    df_comparison = pd.DataFrame(comparison_data)
    df_comparison = df_comparison.sort_values('Score', ascending=False)
    
    # Exibe tabela com formatação condicional
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
                format="%d"
            ),
        }
    )
    
    # ========================================================================
    # ANÁLISE DETALHADA POR ATIVO
    # ========================================================================
    
    st.header("🔍 Análise Detalhada por Ativo")
    
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
        
        # Métricas principais usando st.metric (NATIVO - SEM HTML)
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            emoji, color = render_score_badge(summary['score'])
            st.metric(
                label="Score de Saúde",
                value=f"{summary['score']:.0f}/100",
                delta=f"{emoji} {summary['score_category']}"
            )
        
        with col2:
            preco = fund.get('preco_atual')
            st.metric(
                label="Preço Atual",
                value=f"R$ {preco:.2f}" if preco else "N/A",
                delta=fund.get('subsetor', '')
            )
        
        with col3:
            sinal = tech.get('sinal_tecnico', 'Neutro')
            emoji_sinal, _ = render_technical_signal(sinal)
            st.metric(
                label="Sinal Técnico",
                value=sinal,
                delta=f"{emoji_sinal} {tech.get('tendencia_longo', 'N/A')}"
            )
        
        with col4:
            dy = fund.get('dividend_yield')
            st.metric(
                label="Dividend Yield",
                value=f"{dy:.2f}%" if isinstance(dy, (int, float)) else "N/A",
                delta=f"Payout: {fund.get('payout', 0):.1f}%" if isinstance(fund.get('payout'), (int, float)) else ""
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
            st.write(f"• P/L: {fund.get('pl', 'N/A')}")
            st.write(f"• P/VP: {fund.get('pvp', 'N/A')}")
            vm = fund.get('valor_mercado')
            if vm:
                st.write(f"• Valor Mercado: R$ {vm:,.0f}")
        
        with col_fund2:
            st.markdown("**Rentabilidade**")
            roe = fund.get('roe')
            st.write(f"• ROE: {roe:.2f}%" if isinstance(roe, (int, float)) else "• ROE: N/A")
            roa = fund.get('roa')
            st.write(f"• ROA: {roa:.2f}%" if isinstance(roa, (int, float)) else "• ROA: N/A")
            marg = fund.get('margem_liquida')
            st.write(f"• Marg. Líq.: {marg:.2f}%" if isinstance(marg, (int, float)) else "• Marg. Líq.: N/A")
        
        with col_fund3:
            st.markdown("**Endividamento**")
            st.write(f"• Dívida/EBITDA: {fund.get('divida_ebitda', 'N/A')}")
            st.write(f"• Liq. Corrente: {fund.get('liquidez_corrente', 'N/A')}")
            st.write(f"• Setor: {fund.get('setor', 'N/A')}")
        
        # Detalhes Técnicos
        st.subheader("📈 Indicadores Técnicos")
        
        col_tech1, col_tech2, col_tech3 = st.columns(3)
        
        with col_tech1:
            st.markdown("**Médias Móveis**")
            st.write(f"• MM20: R$ {tech.get('mm20', 'N/A')}")
            st.write(f"• MM50: R$ {tech.get('mm50', 'N/A')}")
            st.write(f"• MM200: R$ {tech.get('mm200', 'N/A')}")
        
        with col_tech2:
            st.markdown("**Osciladores**")
            st.write(f"• RSI (14): {tech.get('rsi', 'N/A')}")
            st.write(f"• MACD: {tech.get('macd', 'N/A')}")
            st.write(f"• Sinal: {tech.get('macd_signal', 'N/A')}")
        
        with col_tech3:
            st.markdown("**Tendências**")
            st.write(f"• Curto: {tech.get('tendencia_curto', 'N/A')}")
            st.write(f"• Longo: {tech.get('tendencia_longo', 'N/A')}")
    
    # ========================================================================
    # PROJEÇÃO DE RENDA PASSIVA
    # ========================================================================
    
    st.divider()
    st.header("💰 Projeção de Renda Passiva")
    
    # Calcula DY médio
    dy_values = [
        a.fundamentals.get('dividend_yield') 
        for a in analyzers.values() 
        if a.fundamentals and isinstance(a.fundamentals.get('dividend_yield'), (int, float))
    ]
    avg_dy = np.mean(dy_values) if dy_values else 6.0
    
    st.info(f"📊 Dividend Yield Médio dos Ativos: **{avg_dy:.2f}%**")
    
    # Calcula projeção
    projection_df = create_dividend_projection(
        initial_investment=initial_inv,
        monthly_contribution=monthly_contrib,
        annual_return=10.0,
        dividend_yield=avg_dy,
        years=years_proj
    )
    
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
        title='Projeção: Patrimônio vs Investido',
        template='plotly_dark',
        labels={'value': 'Valor (R$)', 'variable': 'Tipo'}
    )
    fig_proj.update_layout(height=400)
    st.plotly_chart(fig_proj, use_container_width=True)
    
    # ========================================================================
    # RODAPÉ
    # ========================================================================
    
    st.divider()
    
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        st.caption("**B3 Stock Analyzer** v1.1.0\n\nPython + Streamlit")
    
    with col_f2:
        st.caption("**Fontes de Dados**\n\nyfinance (Yahoo Finance)\n\nDelay: ~15min")
    
    with col_f3:
        st.caption("**Licença**\n\nMIT License\n\nGitHub: /b3-stock-analyzer")
    
    # Disclaimer final (componente nativo)
    st.caption("⚠️ Ferramenta educacional. Não constitui recomendação de investimento. Consulte assessor CVM.")


# ============================================================================
# EXECUÇÃO
# ============================================================================

if __name__ == "__main__":
    main()
