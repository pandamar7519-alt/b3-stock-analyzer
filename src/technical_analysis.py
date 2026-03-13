"""
Módulo de análise técnica para ações da B3.
IMPLEMENTAÇÃO MANUAL - Compatível com Python 3.14+
(Sem dependência do pandas-ta/numba)
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional


def calculate_sma(series: pd.Series, length: int) -> pd.Series:
    """
    Calcula Média Móvel Simples (SMA).
    
    Args:
        series: Série de preços
        length: Período da média
        
    Returns:
        Série com SMA calculada
    """
    return series.rolling(window=length).mean()


def calculate_rsi(series: pd.Series, length: int = 14) -> pd.Series:
    """
    Calcula Índice de Força Relativa (RSI/IFR).
    Implementação manual compatível com Python 3.14.
    
    Args:
        series: Série de preços de fechamento
        length: Período do RSI (padrão: 14)
        
    Returns:
        Série com RSI calculado (0-100)
    """
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    
    avg_gain = gain.rolling(window=length).mean()
    avg_loss = loss.rolling(window=length).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> Dict[str, pd.Series]:
    """
    Calcula MACD (Moving Average Convergence Divergence).
    Implementação manual compatível com Python 3.14.
    
    Args:
        series: Série de preços de fechamento
        fast: Período da EMA rápida (padrão: 12)
        slow: Período da EMA lenta (padrão: 26)
        signal: Período da linha de sinal (padrão: 9)
        
    Returns:
        Dict com MACD, Signal e Histogram
    """
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    }


def calculate_technical_indicators(data: pd.DataFrame) -> Dict:
    """
    Calcula todos os indicadores técnicos para uma série de preços.
    Implementação manual - SEM dependência do pandas-ta.
    
    Args:
        data: DataFrame com dados OHLCV
        
    Returns:
        Dict com indicadores calculados
    """
    if data is None or data.empty:
        return {
            'tendencia_curto': 'Neutro',
            'tendencia_longo': 'Neutro',
            'sinal_tecnico': 'Neutro',
        }
    
    df = data.copy()
    
    try:
        # Médias Móveis
        df['MM20'] = calculate_sma(df['Close'], 20)
        df['MM50'] = calculate_sma(df['Close'], 50)
        df['MM200'] = calculate_sma(df['Close'], 200)
        
        # IFR (RSI)
        df['RSI'] = calculate_rsi(df['Close'], 14)
        
        # MACD
        macd_result = calculate_macd(df['Close'])
        df['MACD'] = macd_result['macd']
        df['MACD_Signal'] = macd_result['signal']
        df['MACD_Hist'] = macd_result['histogram']
        
        latest = df.iloc[-1]
        
        return {
            'mm20': float(latest['MM20']) if pd.notna(latest.get('MM20')) else None,
            'mm50': float(latest['MM50']) if pd.notna(latest.get('MM50')) else None,
            'mm200': float(latest['MM200']) if pd.notna(latest.get('MM200')) else None,
            'rsi': float(latest['RSI']) if pd.notna(latest.get('RSI')) else None,
            'macd': float(latest['MACD']) if pd.notna(latest.get('MACD')) else None,
            'macd_signal': float(latest['MACD_Signal']) if pd.notna(latest.get('MACD_Signal')) else None,
            'tendencia_curto': _analyze_short_term_trend(df),
            'tendencia_longo': _analyze_long_term_trend(df),
            'sinal_tecnico': _generate_technical_signal(latest),
        }
        
    except Exception:
        return {
            'tendencia_curto': 'Neutro',
            'tendencia_longo': 'Neutro',
            'sinal_tecnico': 'Neutro',
        }


def _analyze_short_term_trend(df: pd.DataFrame) -> str:
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


def _analyze_long_term_trend(df: pd.DataFrame) -> str:
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


def _generate_technical_signal(latest: pd.Series) -> str:
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
    macd = latest.get('MACD')
    macd_signal = latest.get('MACD_Signal')
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
