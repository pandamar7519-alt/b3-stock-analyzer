"""
Módulo para busca e processamento de dados financeiros da B3.
Compatível com Python 3.14+
"""

import pandas as pd
import yfinance as yf
from typing import Optional, Dict
import warnings

warnings.filterwarnings("ignore")


def fetch_stock_data(ticker: str, period: str = "2y") -> Optional[pd.DataFrame]:
    """
    Busca dados históricos de uma ação da B3 via yfinance.
    
    Args:
        ticker: Código da ação (ex: PETR4)
        period: Período para dados históricos
        
    Returns:
        DataFrame com dados OHLCV ou None se falhar
    """
    try:
        ticker_yf = f"{ticker.upper()}.SA"
        stock = yf.Ticker(ticker_yf)
        data = stock.history(period=period)
        
        if data is None or data.empty:
            return None
            
        return data
    except Exception:
        return None


def fetch_stock_info(ticker: str) -> Optional[Dict]:
    """
    Busca informações fundamentais de uma ação.
    
    Args:
        ticker: Código da ação
        
    Returns:
        Dict com informações ou None se falhar
    """
    try:
        ticker_yf = f"{ticker.upper()}.SA"
        stock = yf.Ticker(ticker_yf)
        info = stock.info
        
        if not info:
            return None
            
        return info
    except Exception:
        return None


def extract_fundamentals(info: Dict) -> Dict:
    """
    Extrai e formata indicadores fundamentalistas.
    
    Args:
        info: Dicionário de informações do yfinance
        
    Returns:
        Dict com indicadores formatados
    """
    if not info:
        return {}
    
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
    
    # Converte para porcentagem quando aplicável
    for key in ['roe', 'margem_liquida', 'dividend_yield', 'payout']:
        if fundamentals[key] is not None:
            fundamentals[key] = fundamentals[key] * 100
    
    # Arredonda valores
    for key in ['pl', 'pvp', 'divida_ebitda', 'liquidez_corrente']:
        if fundamentals[key] is not None:
            fundamentals[key] = round(fundamentals[key], 2)
    
    return fundamentals
