"""
Módulo de visualizações e componentes de UI.
Compatível com Python 3.14+
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Tuple


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
    
    for col, color, name in [
        ('MM20', '#00d4ff', 'MM20'),
        ('MM50', '#ffcc00', 'MM50'),
        ('MM200', '#ff6b6b', 'MM200')
    ]:
        if col in data.columns:
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data[col],
                line=dict(color=color, width=1),
                name=name,
                hoverinfo='skip'
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
        x=data.index,
        y=data['RSI'],
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
    """Calcula projeção de renda passiva com reinvestimento."""
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


def create_projection_chart(projection_df: pd.DataFrame) -> go.Figure:
    """Cria gráfico de projeção de patrimônio."""
    fig = px.line(
        projection_df,
        x='Ano',
        y=['Patrimônio', 'Investido'],
        title='Projeção: Patrimônio vs Investido',
        template='plotly_dark',
        labels={'value': 'Valor (R$)', 'variable': 'Tipo'}
    )
    fig.update_layout(height=400)
    return fig


def get_signal_colors(signal: str) -> Tuple[str, str]:
    """Retorna emoji e cor para sinal técnico."""
    if "Compra" in signal:
        return "🟢", "#00ff88"
    elif "Venda" in signal:
        return "🔴", "#ff4444"
    return "🟡", "#ffcc00"
