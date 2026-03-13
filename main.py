
"""
B3 Stock Analyzer - Aplicação Profissional de Análise de Ações
================================================================
Versão: 1.2.0 (Corrigido para Python 3.14 + Streamlit Cloud)
Licença: MIT

Esta aplicação fornece análise fundamentalista e técnica para ações da B3.
NÃO constitui recomendação de investimento. Consulte um assessor credenciado.
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import warnings

# Imports locais
from src.data_fetcher import fetch_stock_data, fetch_stock_info, extract_fundamentals
from src.technical_analysis import calculate_technical_indicators
from src.scoring import calculate_health_score, get_score_category, get_score_emoji
from src.visualizations import (
    create_candlestick_chart,
    create_rsi_chart,
    create_dividend_projection,
    create_projection_chart,
    get_signal_colors
)

# Suprimir warnings
warnings.filterwarnings("ignore")

# ============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================================

st.set_page_config(
    page_title="B3 Stock Analyzer | Análise Profissional",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    """Função principal da aplicação."""
    
    # Header
    st.title("📊 B3 Stock Analyzer")
    st.caption("Análise Profissional de Ações para Investidores de Longo Prazo")
    
    # Disclaimer obrigatório (Compliance CVM)
    render_disclaimer()
    
    # ========================================================================
    # SIDEBAR
    # ========================================================================
    
    with st.sidebar:
        st.header("⚙️ Configurações")
        
        # Input de Tickers
        st.subheader("📝 Tickers para Análise")
        st.info("Insira até 10 tickers separados por vírgula (ex: PETR4, VALE3)")
        
        tickers_input = st.text_area(
            "Tickers B3",
            value="PETR4, VALE3, ITUB4, BBAS3, WEGE3",
            height=100
        )
        
        # Processa input
        tickers = [t.strip().upper() for t in tickers_input.split(',') if t.strip()]
        tickers = tickers[:10]
        
        if tickers:
            st.success(f"✅ {len(tickers)} ticker(s)")
        else:
            st.warning("⚠️ Insira pelo menos 1 ticker")
        
        st.divider()
        
        # Parâmetros
        st.subheader("🔧 Parâmetros")
        period = st.selectbox(
            "Período de Dados",
            options=["1y", "2y", "5y", "10y"],
            index=1
        )
        
        st.divider()
        
        # Projeção
        st.subheader("💰 Projeção de Renda")
        initial_inv = st.number_input("Investimento Inicial (R$)", min_value=0.0, value=10000.0, step=1000.0)
        monthly_contrib = st.number_input("Aporte Mensal (R$)", min_value=0.0, value=500.0, step=100.0)
        years_proj = st.slider("Período (anos)", min_value=1, max_value=30, value=10)
        
        st.divider()
        st.caption("**B3 Stock Analyzer** v1.2.0\n\nPython + Streamlit")
        st.warning("⚠️ Ferramenta educacional. Não é recomendação de investimento.")
    
    # ========================================================================
    # VALIDAÇÃO INICIAL
    # ========================================================================
    
    if not tickers:
        st.info("👈 Insira tickers na sidebar para iniciar a análise")
        return
    
    # ========================================================================
    # ANÁLISE DOS ATIVOS
    # ========================================================================
    
    @st.cache_data(ttl=3600)
    def analyze_tickers_cached(tickers_list: List[str], period: str) -> Dict:
        """Analisa múltiplos tickers com cache."""
        results = {}
        
        for ticker in tickers_list:
            try:
                # Busca dados
                data = fetch_stock_data(ticker, period)
                if data is None or data.empty:
                    continue
                
                info = fetch_stock_info(ticker)
                fundamentals = extract_fundamentals(info) if info else {}
                technicals = calculate_technical_indicators(data)
                score = calculate_health_score(fundamentals)
                
                results[ticker] = {
                    'data': data,
                    'fundamentals': fundamentals,
                    'technicals': technicals,
                    'score': score,
                    'category': get_score_category(score),
                    'emoji': get_score_emoji(score)
                }
            except Exception:
                continue
        
        return results
    
    with st.spinner("🔄 Analisando ativos..."):
        analyzers = analyze_tickers_cached(tuple(tickers), period)
    
    if not analyzers:
        st.error("❌ Nenhum dado válido foi retornado. Verifique os tickers.")
        return
    
    # ========================================================================
    # DASHBOARD COMPARATIVO
    # ========================================================================
    
    st.header("📈 Dashboard Comparativo")
    
    comparison_data = []
    for ticker, result in analyzers.items():
        fund = result['fundamentals']
        tech = result['technicals']
        
        comparison_data.append({
            'Ticker': ticker,
            'Score': round(result['score'], 1),
            'Categoria': result['category'],
            'Preço (R$)': f"R$ {fund.get('preco_atual', 0):.2f}" if fund.get('preco_atual') else 'N/A',
            'P/L': f"{fund.get('pl', 0):.2f}" if isinstance(fund.get('pl'), (int, float)) and fund['pl'] > 0 else 'N/A',
            'ROE (%)': f"{fund.get('roe', 0):.1f}" if isinstance(fund.get('roe'), (int, float)) else 'N/A',
            'DY (%)': f"{fund.get('dividend_yield', 0):.2f}" if isinstance(fund.get('dividend_yield'), (int, float)) else 'N/A',
            'Dívida/EBITDA': f"{fund.get('divida_ebitda', 0):.2f}" if isinstance(fund.get('divida_ebitda'), (int, float)) else 'N/A',
            'Tendência': tech.get('tendencia_longo', 'N/A'),
            'Sinal Técnico': tech.get('sinal_tecnico', 'Neutro'),
            'Setor': fund.get('setor', 'N/A'),
        })
    
    df_comp = pd.DataFrame(comparison_data).sort_values('Score', ascending=False)
    
    st.dataframe(
        df_comp,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%d"),
        }
    )
    
    # ========================================================================
    # ANÁLISE DETALHADA
    # ========================================================================
    
    st.header("🔍 Análise Detalhada por Ativo")
    
    selected = st.selectbox("Selecione um ativo", options=list(analyzers.keys()), index=0)
    
    if selected:
        result = analyzers[selected]
        fund = result['fundamentals']
        tech = result['technicals']
        data = result['data']
        
        # Métricas principais (usando st.metric - NATIVO)
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Score de Saúde",
                value=f"{result['score']:.0f}/100",
                delta=f"{result['emoji']} {result['category']}"
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
            emoji_sinal, _ = get_signal_colors(sinal)
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
        col_c1, col_c2 = st.columns([2, 1])
        
        with col_c1:
            fig_candle = create_candlestick_chart(data, selected)
            st.plotly_chart(fig_candle, use_container_width=True)
        
        with col_c2:
            if 'RSI' in data.columns:
                fig_rsi = create_rsi_chart(data)
                st.plotly_chart(fig_rsi, use_container_width=True)
        
        # Detalhes Fundamentalistas
        st.subheader("📊 Indicadores Fundamentalistas")
        
        col_f1, col_f2, col_f3 = st.columns(3)
        
        with col_f1:
            st.markdown("**Valuation**")
            st.write(f"• P/L: {fund.get('pl', 'N/A')}")
            st.write(f"• P/VP: {fund.get('pvp', 'N/A')}")
            vm = fund.get('valor_mercado')
            if vm: st.write(f"• Valor Mercado: R$ {vm:,.0f}")
        
        with col_f2:
            st.markdown("**Rentabilidade**")
            roe = fund.get('roe')
            st.write(f"• ROE: {roe:.2f}%" if isinstance(roe, (int, float)) else "• ROE: N/A")
            roa = fund.get('roa')
            st.write(f"• ROA: {roa:.2f}%" if isinstance(roa, (int, float)) else "• ROA: N/A")
            marg = fund.get('margem_liquida')
            st.write(f"• Marg. Líq.: {marg:.2f}%" if isinstance(marg, (int, float)) else "• Marg. Líq.: N/A")
        
        with col_f3:
            st.markdown("**Endividamento**")
            st.write(f"• Dívida/EBITDA: {fund.get('divida_ebitda', 'N/A')}")
            st.write(f"• Liq. Corrente: {fund.get('liquidez_corrente', 'N/A')}")
            st.write(f"• Setor: {fund.get('setor', 'N/A')}")
        
        # Detalhes Técnicos
        st.subheader("📈 Indicadores Técnicos")
        
        col_t1, col_t2, col_t3 = st.columns(3)
        
        with col_t1:
            st.markdown("**Médias Móveis**")
            st.write(f"• MM20: R$ {tech.get('mm20', 'N/A')}")
            st.write(f"• MM50: R$ {tech.get('mm50', 'N/A')}")
            st.write(f"• MM200: R$ {tech.get('mm200', 'N/A')}")
        
        with col_t2:
            st.markdown("**Osciladores**")
            st.write(f"• RSI (14): {tech.get('rsi', 'N/A')}")
            st.write(f"• MACD: {tech.get('macd', 'N/A')}")
            st.write(f"• Sinal: {tech.get('macd_signal', 'N/A')}")
        
        with col_t3:
            st.markdown("**Tendências**")
            st.write(f"• Curto: {tech.get('tendencia_curto', 'N/A')}")
            st.write(f"• Longo: {tech.get('tendencia_longo', 'N/A')}")
    
    # ========================================================================
    # PROJEÇÃO DE RENDA
    # ========================================================================
    
    st.divider()
    st.header("💰 Projeção de Renda Passiva")
    
    # DY médio dos ativos
    dy_values = [
        a['fundamentals'].get('dividend_yield')
        for a in analyzers.values()
        if isinstance(a['fundamentals'].get('dividend_yield'), (int, float))
    ]
    avg_dy = np.mean(dy_values) if dy_values else 6.0
    
    st.info(f"📊 Dividend Yield Médio: **{avg_dy:.2f}%**")
    
    proj_df = create_dividend_projection(
        initial_investment=initial_inv,
        monthly_contribution=monthly_contrib,
        annual_return=10.0,
        dividend_yield=avg_dy,
        years=years_proj
    )
    
    st.dataframe(
        proj_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Patrimônio": st.column_config.NumberColumn(format="R$ %d"),
            "Investido": st.column_config.NumberColumn(format="R$ %d"),
            "Dividendos Acumulados": st.column_config.NumberColumn(format="R$ %d"),
            "Renda Mensal Estimada": st.column_config.NumberColumn(format="R$ %d"),
        }
    )
    
    fig_proj = create_projection_chart(proj_df)
    st.plotly_chart(fig_proj, use_container_width=True)
    
    # ========================================================================
    # RODAPÉ
    # ========================================================================
    
    st.divider()
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        st.caption("**B3 Stock Analyzer** v1.2.0\n\nPython + Streamlit")
    with col_f2:
        st.caption("**Fontes**\n\nyfinance (Yahoo Finance)\n\nDelay: ~15min")
    with col_f3:
        st.caption("**Licença**\n\nMIT License\n\nGitHub: /b3-stock-analyzer")
    
    st.caption("⚠️ Ferramenta educacional. Não constitui recomendação de investimento. Consulte assessor CVM.")


def render_disclaimer():
    """Exibe disclaimer legal obrigatório."""
    st.warning("""
    **⚠️ DISCLAIMER LEGAL - LEIA ATENTAMENTE**
    
    Esta ferramenta é destinada exclusivamente para fins **educacionais e informativos**. 
    As informações apresentadas **NÃO constituem recomendação de investimento**.
    
    • Rentabilidade passada não garante retornos futuros
    • Decisões de investimento são de responsabilidade exclusiva do investidor
    • Consulte um assessor credenciado pela CVM antes de investir
    • Esta aplicação não possui registro na CVM
    
    *Em conformidade com a Instrução CVM 598/2018*
    """)


if __name__ == "__main__":
    main()
