from typing import Dict, Any, List
import numpy as np
import logging
from services.redis_manager import redis_manager

def calculate_pattern_strength(ticker: str, pattern_type: str) -> float:
    """Calculate overall pattern strength based on technical indicators"""
    try:
        indicators = redis_manager.get_technical_indicators(ticker)
        scores = redis_manager.get_technical_scores(ticker)
        
        # Base strength from technical scores
        base_strength = scores.get('technical_score', 0)
        
        # Pattern-specific adjustments
        if pattern_type == 'breakout':
            # Breakout patterns benefit from strong momentum and volume
            volume_ratio = indicators.get('Volume_Ratio', 1)
            stoch_rsi = indicators.get('StochRSI_K', 50)
            adx = indicators.get('ADX', 0)
            
            volume_factor = min(1.0, volume_ratio / 2)
            momentum_factor = min(1.0, stoch_rsi / 100)
            trend_factor = min(1.0, adx / 50)
            
            pattern_strength = (volume_factor + momentum_factor + trend_factor) / 3
            
        elif pattern_type == 'reversal':
            # Reversal patterns benefit from oversold/overbought conditions
            stoch_rsi = indicators.get('StochRSI_K', 50)
            williams_r = indicators.get('Williams_R', 0)
            
            # Score based on extreme conditions
            rsi_factor = 1.0 if stoch_rsi <= 20 or stoch_rsi >= 80 else 0.5
            williams_factor = 1.0 if williams_r <= -80 or williams_r >= -20 else 0.5
            
            pattern_strength = (rsi_factor + williams_factor) / 2
            
        elif pattern_type == 'momentum':
            # Momentum patterns benefit from strong trends and acceleration
            roc = indicators.get('ROC', 0)
            vwap_slope = indicators.get('VWAP_Slope', 0)
            supertrend = indicators.get('Supertrend', 0)
            
            roc_factor = min(1.0, max(0, roc) / 5)
            slope_factor = 1.0 if vwap_slope >= 0 else 0.5
            trend_factor = 1.0 if supertrend == 1 else 0.5
            
            pattern_strength = (roc_factor + slope_factor + trend_factor) / 3
            
        else:
            # Default pattern strength
            pattern_strength = 0.5
        
        # Combine base strength with pattern-specific strength
        final_strength = (base_strength * 0.6 + pattern_strength * 0.4)
        
        return min(1.0, max(0.0, final_strength))
        
    except Exception as e:
        logging.error(f"Error calculating pattern strength: {e}")
        return 0.5

def calculate_probability(ticker: str, target_price: float) -> float:
    """Calculate pattern success probability"""
    try:
        current_price = redis_manager.get_stock_price(ticker)
        atr = redis_manager.get_technical_indicator(ticker, 'ATR', 1)
        scores = redis_manager.get_technical_scores(ticker)

        price_gap = target_price - current_price
        volatility_score = 0
        if atr:
            if atr > price_gap:
                volatility_score = 1
            elif atr >= 0.5 * price_gap:
                volatility_score = 0.5
            else:
                volatility_score = 0

        distance_score = 1 - min(1, price_gap / (atr * 2)) if atr else (1 - min(1, price_gap))

        return 0.25 * scores['momentum_score'] + 0.4 * scores['volume_score'] + 0.2 * volatility_score + 0.15 * distance_score
    except Exception as e:
        logging.error(f"Error calculating probability: {e}")
        return 0

def calculate_volatility(prices: List[float]) -> float:
    """Calculate volatility from price data"""
    try:
        if len(prices) < 2:
            return 0.0
        
        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] > 0:
                returns.append((prices[i] - prices[i-1]) / prices[i-1])
        
        if not returns:
            return 0.0
        
        return np.std(returns) * 100  # Return as percentage
    except Exception as e:
        logging.error(f"Error calculating volatility: {e}")
        return 0.0

def detect_consolidation(prices: List[float], threshold: float = 0.02) -> bool:
    """Detect price consolidation"""
    if len(prices) < 5:
        return False
        
    recent_prices = prices[-5:]
    avg_price = sum(recent_prices) / len(recent_prices)
    max_deviation = max([abs(p - avg_price) / avg_price for p in recent_prices])
    
    return max_deviation < threshold 
