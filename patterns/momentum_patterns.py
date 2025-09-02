from typing import Dict, Any, Optional
from .base_pattern import BasePattern
from .pattern_registry import PatternRegistry
from services.redis_manager import redis_manager

@PatternRegistry.register
class VWAPBouncePattern(BasePattern):
    def __init__(self):
        super().__init__()
        self.description = "VWAP Bounce setup with volume confirmation"
        self.timeframes = ["1m", "5m"]
        self.categories = ["momentum", "intraday"]
        self.criteria = [
            {
                'type': 'price_touch',
                'target': 'vwap',
                'weight': 0.3,
                'evaluator': self._evaluate_price_touch
            },
            {
                'type': 'volume_profile',
                'condition': 'increasing',
                'weight': 0.25,
                'evaluator': self._evaluate_volume_profile
            },
            {
                'type': 'oscillator',
                'indicator': 'rsi',
                'condition': 'oversold',
                'weight': 0.2,
                'evaluator': self._evaluate_oscillator
            },
            {
                'type': 'order_flow',
                'condition': 'accumulation',
                'weight': 0.25,
                'evaluator': self._evaluate_order_flow
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
                'description': f"VWAP Bounce setup detected with {match_score:.0f}% confidence",
                'entry_price': targets['entry'],
                'target_price': targets['target'],
                'stop_price': targets['stop'],
                'probability': match_score / 100,
                'timeframe': "1m",
                'criteria_scores': evaluation['criteria_scores']
            }
        return self.get_default_result()

    def get_targets(self, ticker: str) -> Dict[str, float]:
        price = redis_manager.get_stock_price(ticker)
        return {
            'entry': price,
            'target': price * 1.02,  # 2% target
            'stop': price * 0.995    # 0.5% stop
        }

    def _evaluate_price_touch(self, ticker: str, criterion: Dict[str, Any]) -> float:
        price = redis_manager.get_stock_price(ticker)
        vwap = redis_manager.get_technical_indicator(ticker, 'VWAP', 1)
        if not vwap:
            return 0
        distance = abs(price - vwap) / vwap if vwap != 0 else 0
        return 1.0 if distance <= 0.003 else max(0, 1 - (distance / 0.01))

    def _evaluate_volume_profile(self, ticker: str, criterion: Dict[str, Any]) -> float:
        """Evaluate volume profile using the new helper method"""
        try:
            volume_profile = self.get_volume_profile(ticker, periods=5)
            
            # Score based on volume trend
            if volume_profile['trend'] == 'increasing':
                trend_score = 1.0
            elif volume_profile['trend'] == 'decreasing':
                trend_score = 0.2
            else:
                trend_score = 0.5
            
            # Score based on volume acceleration
            acceleration_score = min(1.0, max(0.0, volume_profile['acceleration']))
            
            # Score based on volume ratio
            ratio_score = min(1.0, volume_profile['ratio'] / 2.0)
            
            # Combine scores with weights
            final_score = (trend_score * 0.4) + (acceleration_score * 0.3) + (ratio_score * 0.3)
            
            return final_score
            
        except Exception as e:
            self.logger.error(f"Error evaluating volume profile: {e}")
            return 0.0

    def _evaluate_oscillator(self, ticker: str, criterion: Dict[str, Any]) -> float:
        stoch_rsi = redis_manager.get_technical_indicator(ticker, 'StochRSI_K', 1)
        if not stoch_rsi:
            return 0
        is_oversold = stoch_rsi <= 30
        return 1.0 if is_oversold else max(0, 1 - ((stoch_rsi - 30) / 20))

    def _evaluate_order_flow(self, ticker: str, criterion: Dict[str, Any]) -> float:
        """Evaluate order flow based on orderbook imbalance"""
        try:
            # Use the new helper method from base pattern
            orderbook = redis_manager.get_last_orderbook_snapshot(ticker)
            if not orderbook:
                return 0
            bid_volume = orderbook['bid_volume']
            ask_volume = orderbook['ask_volume']
            imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume) if (bid_volume + ask_volume) > 0 else 0
            
            # Convert imbalance to a score between 0 and 1
            # Positive imbalance (bullish) gets higher score
            # Negative imbalance (bearish) gets lower score
            if imbalance > 0:
                return min(1.0, imbalance * 2)  # Scale positive imbalance
            else:
                return max(0.0, 0.5 + (imbalance * 0.5))  # Scale negative imbalance
                
        except Exception as e:
            self.logger.error(f"Error evaluating order flow: {e}")
            return 0.0

@PatternRegistry.register
class ParabolicMovePattern(BasePattern):
    def __init__(self):
        super().__init__()
        self.description = "Parabolic Move with strong momentum and volume"
        self.timeframes = ["1m", "5m"]
        self.categories = ["momentum", "breakout"]
        self.criteria = [
            {
                'type': 'acceleration',
                'threshold': 2.0,
                'weight': 0.35,
                'evaluator': self._evaluate_acceleration
            },
            {
                'type': 'volume_surge',
                'threshold': 2.5,
                'weight': 0.25,
                'evaluator': self._evaluate_volume_surge
            },
            {
                'type': 'momentum_extreme',
                'indicator': 'rsi',
                'threshold': 80,
                'weight': 0.2,
                'evaluator': self._evaluate_momentum_extreme
            },
            {
                'type': 'price_velocity',
                'threshold': 3.0,
                'weight': 0.2,
                'evaluator': self._evaluate_price_velocity
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
                'description': f"Parabolic Move detected with {match_score:.0f}% confidence",
                'entry_price': targets['entry'],
                'target_price': targets['target'],
                'stop_price': targets['stop'],
                'probability': match_score / 100,
                'timeframe': "1m",
                'criteria_scores': evaluation['criteria_scores']
            }
        return self.get_default_result()

    def get_targets(self, ticker: str) -> Dict[str, float]:
        price = redis_manager.get_stock_price(ticker)
        return {
            'entry': price,
            'target': price * 1.05,  # 5% target for parabolic moves
            'stop': price * 0.97     # 3% stop loss due to higher volatility
        }

    def _evaluate_acceleration(self, ticker: str, criterion: Dict[str, Any]) -> float:
        candles = redis_manager.get_last_n_candles(ticker, 20)
        closes = [candle['close'] for candle in candles]
        if len(closes) < 20:
            return 0

        # Calculate rate of change for different periods
        roc1 = (closes[-1] / closes[-2] - 1) * 100
        roc3 = (closes[-1] / closes[-4] - 1) * 100
        roc5 = (closes[-1] / closes[-6] - 1) * 100
        roc10 = (closes[-1] / closes[-11] - 1) * 100

        # Calculate acceleration factors
        accel1 = roc1 / (roc3 / 3) if roc3 != 0 else 0
        accel2 = roc3 / (roc5 / 5) if roc5 != 0 else 0
        accel3 = roc5 / (roc10 / 10) if roc10 != 0 else 0

        avg_accel = (accel1 + accel2 + accel3) / 3
        threshold = criterion['threshold']
        
        return min(1.0, avg_accel / threshold)

    def _evaluate_volume_surge(self, ticker: str, criterion: Dict[str, Any]) -> float:
        volume_ratio = redis_manager.get_technical_indicator(ticker, 'Volume_Ratio', 1)
        if not volume_ratio:
            return 0
        threshold = criterion['threshold']
        return min(1.0, volume_ratio / threshold)

    def _evaluate_momentum_extreme(self, ticker: str, criterion: Dict[str, Any]) -> float:
        stoch_rsi = redis_manager.get_technical_indicator(ticker, 'StochRSI_K', 1)
        if not stoch_rsi:
            return 0
        threshold = criterion['threshold']
        if stoch_rsi > threshold:
            return min(1.0, (stoch_rsi - threshold) / (100 - threshold))
        return 0

    def _evaluate_price_velocity(self, ticker: str, criterion: Dict[str, Any]) -> float:
        candles = redis_manager.get_last_n_candles(ticker, 10)
        closes = [candle['close'] for candle in candles]
        if len(closes) < 10:
            return 0

        # Calculate price velocity (rate of change over time)
        recent_velocity = (closes[-1] / closes[-5] - 1) * 100  # 5-period velocity
        threshold = criterion['threshold']
        
        return min(1.0, recent_velocity / threshold) 
