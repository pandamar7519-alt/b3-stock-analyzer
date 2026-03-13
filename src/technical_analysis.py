"""
Módulo de análise técnica para ações da B3.
"""

import pandas as pd
from typing import Dict, Optional

# pandas-ta com fallback
try:
    import pandas_ta as ta
    HAS_PANDAS_TA = True
except ImportError:
    HAS_PANDAS_TA = False


def calculate_technical_indicators(
    data: pd.DataFrame
) -> Dict:
    """
    Calcula indicadores técnicos para uma série de preços.
    
    Args:
        data: DataFrame com dados OHLCV
        
    Returns:
        Dict com indicadores calculados
    """
    if data is None or data.empty:
        return {}
    
    # Fallback se pandas-ta não estiver disponível
    if not HAS_PANDAS_TA:
        return {
            'tendencia_curto': 'Neutro',
            'tendencia_longo': 'Neutro',
            'sinal_tecnico': 'Neutro',
        }
    
    df = data.copy()
    
    try:
        # Médias Móveis
        df['MM20'] = ta.sma(df['Close'], length=20)
        df['MM50'] = ta.sma(df['Close'], length=50)
        df['MM200'] = ta.sma(df['Close'], length=200)
        
        # IFR (RSI)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        # MACD
        macd_result = ta.macd(df['Close'], fast=12, slow=26, signal=9)
        if macd_result is not None and not macd_result.empty:
            df = pd.concat([df, macd_result], axis=1)
        
        latest = df.iloc[-1]
        
        return {
            'mm20': float(latest['MM20']) if 'MM20' in df.columns and pd.notna(latest.get('MM20')) else None,
            'mm50': float(latest['MM50']) if 'MM50' in df.columns and pd.notna(latest.get('MM50')) else None,
            'mm200': float(latest['MM200']) if 'MM200' in df.columns and pd.notna(latest.get('MM200')) else None,
            'rsi': float(latest['RSI']) if 'RSI' in df.columns and pd.notna(latest.get('RSI')) else None,
            'macd': float(latest['MACD_12_26_9']) if 'MACD_12_26_9' in df.columns and pd.notna(latest.get('MACD_12_26_9')) else None,
            'macd_signal': float(latest['MACDs_12_26_9']) if 'MACDs_12_26_9' in df.columns and pd.notna(latest.get('MACDs_12_26_9')) else None,
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
