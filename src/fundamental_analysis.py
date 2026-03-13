"""
Módulo de análise fundamentalista para ações da B3.
"""

from typing import Dict, Optional


def evaluate_profitability(fundamentals: Dict) -> float:
    """
    Avalia rentabilidade da empresa (0-30 pontos).
    
    Args:
        fundamentals: Dict com indicadores fundamentalistas
        
    Returns:
        Score de rentabilidade (0-30)
    """
    score = 0.0
    
    # ROE (0-15 pontos)
    roe = fundamentals.get('roe')
    if roe is not None:
        if roe >= 20:
            score += 15
        elif roe >= 15:
            score += 12
        elif roe >= 10:
            score += 8
        elif roe >= 5:
            score += 4
    
    # Margem Líquida (0-15 pontos)
    margem = fundamentals.get('margem_liquida')
    if margem is not None:
        if margem >= 20:
            score += 15
        elif margem >= 15:
            score += 12
        elif margem >= 10:
            score += 8
        elif margem >= 5:
            score += 4
    
    return score


def evaluate_debt(fundamentals: Dict) -> float:
    """
    Avalia endividamento da empresa (0-25 pontos).
    
    Args:
        fundamentals: Dict com indicadores fundamentalistas
        
    Returns:
        Score de endividamento (0-25)
    """
    score = 0.0
    
    # Dívida/EBITDA (0-15 pontos)
    div_ebitda = fundamentals.get('divida_ebitda')
    if div_ebitda is not None:
        if div_ebitda <= 1:
            score += 15
        elif div_ebitda <= 2:
            score += 12
        elif div_ebitda <= 3:
            score += 8
        elif div_ebitda <= 4:
            score += 4
    
    # Liquidez Corrente (0-10 pontos)
    liq_corrente = fundamentals.get('liquidez_corrente')
    if liq_corrente is not None:
        if liq_corrente >= 2:
            score += 10
        elif liq_corrente >= 1.5:
            score += 7
        elif liq_corrente >= 1:
            score += 4
    
    return score


def evaluate_valuation(fundamentals: Dict) -> float:
    """
    Avalia valuation da empresa (0-25 pontos).
    
    Args:
        fundamentals: Dict com indicadores fundamentalistas
        
    Returns:
        Score de valuation (0-25)
    """
    score = 0.0
    
    # P/L (0-15 pontos)
    pl = fundamentals.get('pl')
    if pl is not None and pl > 0:
        if pl <= 10:
            score += 15
        elif pl <= 15:
            score += 12
        elif pl <= 20:
            score += 8
        elif pl <= 25:
            score += 4
    
    # P/VP (0-10 pontos)
    pvp = fundamentals.get('pvp')
    if pvp is not None and pvp > 0:
        if pvp <= 1:
            score += 10
        elif pvp <= 1.5:
            score += 7
        elif pvp <= 2:
            score += 4
    
    return score


def evaluate_dividends(fundamentals: Dict) -> float:
    """
    Avalia política de dividendos (0-20 pontos).
    
    Args:
        fundamentals: Dict com indicadores fundamentalistas
        
    Returns:
        Score de dividendos (0-20)
    """
    score = 0.0
    
    # Dividend Yield (0-12 pontos)
    dy = fundamentals.get('dividend_yield')
    if dy is not None:
        if dy >= 8:
            score += 12
        elif dy >= 6:
            score += 10
        elif dy >= 4:
            score += 7
        elif dy >= 2:
            score += 4
    
    # Payout Ratio (0-8 pontos)
    payout = fundamentals.get('payout')
    if payout is not None:
        if 40 <= payout <= 70:
            score += 8  # Ideal
        elif 30 <= payout <= 80:
            score += 5
        elif payout <= 100:
            score += 2
    
    return score
