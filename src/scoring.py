"""
Módulo de cálculo de score de saúde para empresas.
"""

from typing import Dict
from .fundamental_analysis import (
    evaluate_profitability,
    evaluate_debt,
    evaluate_valuation,
    evaluate_dividends
)


def calculate_health_score(fundamentals: Dict) -> float:
    """
    Calcula score de saúde da empresa (0-100).
    
    Critérios:
    - Rentabilidade: 30 pontos
    - Endividamento: 25 pontos
    - Valuation: 25 pontos
    - Dividendos: 20 pontos
    
    Args:
        fundamentals: Dict com indicadores fundamentalistas
        
    Returns:
        Score entre 0 e 100
    """
    if not fundamentals:
        return 0.0
    
    score = 0.0
    score += evaluate_profitability(fundamentals)  # 0-30
    score += evaluate_debt(fundamentals)           # 0-25
    score += evaluate_valuation(fundamentals)      # 0-25
    score += evaluate_dividends(fundamentals)      # 0-20
    
    return min(100.0, max(0.0, score))


def get_score_category(score: float) -> str:
    """
    Classifica o score em categorias descritivas.
    
    Args:
        score: Score entre 0 e 100
        
    Returns:
        String com categoria
    """
    if score >= 80:
        return "Excelente"
    elif score >= 60:
        return "Bom"
    elif score >= 40:
        return "Regular"
    return "Atenção"


def get_score_emoji(score: float) -> str:
    """
    Retorna emoji correspondente ao score.
    
    Args:
        score: Score entre 0 e 100
        
    Returns:
        Emoji string
    """
    if score >= 80:
        return "⭐"
    elif score >= 60:
        return "✅"
    elif score >= 40:
        return "⚠️"
    return "❌"
