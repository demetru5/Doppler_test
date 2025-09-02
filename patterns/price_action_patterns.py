from typing import Dict, Any, Optional
from .base_pattern import BasePattern
from .pattern_registry import PatternRegistry
from services.redis_manager import redis_manager

@PatternRegistry.register
class PriceActionPattern(BasePattern):
    def __init__(self):
        super().__init__()
        self.description = "Price Action Strategy with candlestick confirmation"
        self.timeframes = ["1m", "5m", "15m"]
        self.categories = ["price_action", "reversal"]
        self.criteria = [
            {
                'type': 'price_action',
                'pattern': 'engulfing',
                'weight': 0.4,
                'evaluator': self._evaluate_price_action
            },
            {
                'type': 'support_resistance',
                'condition': 'near_level',
                'weight': 0.3,
                'evaluator': self._evaluate_support_resistance
            },
            {
                'type': 'volume_surge',
                'threshold': 1.2,
                'weight': 0.2,
                'evaluator': self._evaluate_volume_surge
            },
            {
                'type': 'momentum',
                'indicator': 'rsi',
                'condition': 'divergence',
                'weight': 0.1,
                'evaluator': self._evaluate_momentum
            }
        ]

    def evaluate(self, ticker: str) -> Dict[str, Any]:
        if not self.validate_data(ticker):
            return self.get_default_result()

        evaluation = self.evaluate_criteria(ticker, self.criteria)
        match_score = evaluation['total_score']
        
        if match_score >= 65:
            targets = self.get_targets(ticker)
            return {
                'match_score': match_score,
                'pattern_name': self.name,
                'description': f"Price Action pattern detected with {match_score:.0f}% confidence",
                'entry_price': targets['entry'],
                'target_price': targets['target'],
                'stop_price': targets['stop'],
                'probability': match_score / 100,
                'timeframe': "5m",
                'criteria_scores': evaluation['criteria_scores']
            }
        return self.get_default_result()

    def get_targets(self, ticker: str) -> Dict[str, float]:
        price = redis_manager.get_stock_price(ticker)
        key_levels = redis_manager.get_key_levels(ticker)
        # Find nearest support and next resistance
        target = price * 1.02  # Default 2% target
        stop = price * 0.985   # Default 1.5% stop

        if key_levels:
            # Find next resistance for target
            resistances = [level for level in key_levels 
                         if level['price'] > price and level['type'] == 'resistance']
            if resistances:
                target = min(level['price'] for level in resistances)

            # Find nearest support for stop
            supports = [level for level in key_levels 
                       if level['price'] < price and level['type'] == 'support']
            if supports:
                stop = max(level['price'] for level in supports) * 0.995

        return {
            'entry': price,
            'target': target,
            'stop': stop
        }

    def _evaluate_price_action(self, ticker: str, criterion: Dict[str, Any]) -> float:
        candles = redis_manager.get_last_n_candles(ticker, 2)
        opens = [candle['open'] for candle in candles]
        closes = [candle['close'] for candle in candles]
        
        if len(opens) < 2 or len(closes) < 2:
            return 0.0

        # Check for bullish engulfing
        prev_open, prev_close = opens[-2], closes[-2]
        curr_open, curr_close = opens[-1], closes[-1]

        is_prev_bearish = prev_close < prev_open
        is_curr_bullish = curr_close > curr_open
        is_engulfing = curr_open <= prev_close and curr_close >= prev_open

        if is_prev_bearish and is_curr_bullish and is_engulfing:
            return 1.0
        
        # Check for partial engulfing
        if is_prev_bearish and is_curr_bullish:
            engulf_ratio = (curr_close - curr_open) / (prev_open - prev_close)
            return min(0.8, engulf_ratio)

        return 0.0

    def _evaluate_support_resistance(self, ticker: str, criterion: Dict[str, Any]) -> float:
        price = redis_manager.get_stock_price(ticker)
        key_levels = redis_manager.get_key_levels(ticker)
        
        if not key_levels:
            return 0.0

        # Find closest level
        closest_distance = float('inf')
        closest_strength = 0.0
        
        for level in key_levels:
            distance = abs(price - level['price']) / price
            if distance < closest_distance:
                closest_distance = distance
                closest_strength = level.get('strength', 50) / 100

        # Score based on proximity and level strength
        if closest_distance < 0.003:  # Within 0.3%
            return min(1.0, closest_strength + (1 - closest_distance / 0.003) * 0.5)
        
        return 0.0

    def _evaluate_volume_surge(self, ticker: str, criterion: Dict[str, Any]) -> float:
        volume_ratio = redis_manager.get_technical_indicator(ticker, 'Volume_Ratio', 1)
        if not volume_ratio:
            return 0
        threshold = criterion['threshold']
        return min(1.0, volume_ratio / threshold)

    def _evaluate_momentum(self, ticker: str, criterion: Dict[str, Any]) -> float:
        StochRSI_Ks = redis_manager.get_technical_indicator(ticker, 'StochRSI_K', 2)
        price = redis_manager.get_stock_price(ticker)
        candles = redis_manager.get_last_n_candles(ticker, 2)
        closes = [candle['close'] for candle in candles]
        
        if len(closes) < 2 or len(StochRSI_Ks) < 2:
            return 0.0

        # Check for bullish divergence
        price_change = (price - closes[-2]) / closes[-2] if closes[-2] != 0 else 0
        stoch_rsi_change = (StochRSI_Ks[-1] - StochRSI_Ks[-2]) / StochRSI_Ks[-2] if StochRSI_Ks[-2] != 0 else 0

        if price_change > 0 and stoch_rsi_change > 0:
            return min(1.0, (price_change + stoch_rsi_change) / 2)
        
        return 0.0 