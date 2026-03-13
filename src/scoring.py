"""
Módulo de cálculo de score de saúde para empresas.
Compatível com Python 3.14+
"""

from typing import Dict
from .fundamental_analysis import (
    evaluate_profitability,
    evaluate_debt,
    evaluate_valuation,
    evaluate_dividends
)


def calculate_health_score(fundamentals: Dict) -> float:
    """Calcula score de saúde da empresa (0-100)."""
    if not fundamentals:
        return 0.0
    
    score = 0.0
    score += evaluate_profitability(fundamentals)
    score += evaluate_debt(fundamentals)
    score += evaluate_valuation(fundamentals)
    score += evaluate_dividends(fundamentals)
    
    return min(100.0, max(0.0, score))


def get_score_category(score: float) -> str:
    """Classifica o score em categorias descritivas."""
    if score >= 80:
        return "Excelente"
    elif score >= 60:
        return "Bom"
    elif score >= 40:
        return "Regular"
    return "Atenção"


def get_score_emoji(score: float) -> str:
    """Retorna emoji correspondente ao score."""
    if score >= 80:
        return "⭐"
    elif score >= 60:
        return "✅"
    elif score >= 40:
        return "⚠️"
    return "❌"
