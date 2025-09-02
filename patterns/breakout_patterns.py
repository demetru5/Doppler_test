from typing import Dict, Any, Optional
from .base_pattern import BasePattern
from .pattern_registry import PatternRegistry
import logging
from services.redis_manager import redis_manager

@PatternRegistry.register
class EarlyParabolicPattern(BasePattern):
    def __init__(self):
        super().__init__()
        self.description = "Early Parabolic Setup with acceleration signals"
        self.timeframes = ["1m", "5m", "15m"]
        self.categories = ["breakout", "momentum"]
        self.criteria = [
            {
                'type': 'acceleration_change',
                'threshold': 1.5,
                'weight': 0.3,
                'evaluator': self._evaluate_acceleration_change
            },
            {
                'type': 'volume_trend_change',
                'threshold': 1.8,
                'weight': 0.25,
                'evaluator': self._evaluate_volume_trend_change
            },
            {
                'type': 'momentum_divergence',
                'indicator': 'macd',
                'weight': 0.25,
                'evaluator': self._evaluate_momentum_divergence
            },
            {
                'type': 'volatility_expansion',
                'threshold': 1.5,
                'weight': 0.2,
                'evaluator': self._evaluate_volatility_expansion
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
                'description': f"Early Parabolic Setup detected with {match_score:.0f}% confidence",
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
        return {
            'entry': price,
            'target': price * 1.04,  # 4% target
            'stop': price * 0.975    # 2.5% stop loss
        }

    def _evaluate_acceleration_change(self, ticker: str, criterion: Dict[str, Any]) -> float:
        candles = redis_manager.get_last_n_candles(ticker, 11)
        closes = [candle['close'] for candle in candles]
        if len(closes) < 11:
            return 0

        # Calculate recent vs previous acceleration
        recent_roc = (closes[-1] / closes[-2]) * 100
        recent_roc5 = (closes[-1] / closes[-6]) * 100
        recent_accel = recent_roc / (recent_roc5 / 5) if recent_roc5 != 0 else 0

        prev_roc = (closes[-6] / closes[-7]) * 100
        prev_roc5 = (closes[-6] / closes[-11]) * 100
        prev_accel = prev_roc / (prev_roc5 / 5) if prev_roc5 != 0 else 0

        accel_change = recent_accel / prev_accel if prev_accel != 0 else 0
        return min(1.0, accel_change / criterion['threshold'])

    def _evaluate_volume_trend_change(self, ticker: str, criterion: Dict[str, Any]) -> float:
        candles = redis_manager.get_last_n_candles(ticker, 10)
        volumes = [candle['volume'] for candle in candles]
        if len(volumes) < 10:
            return 0

        recent_avg = sum(volumes[-5:]) / 5
        prev_avg = sum(volumes[-10:-5]) / 5
        
        trend_change = recent_avg / prev_avg if prev_avg > 0 else 0
        return min(1.0, trend_change / criterion['threshold'])

    def _evaluate_momentum_divergence(self, ticker: str, criterion: Dict[str, Any]) -> float:
        try:
            MACDs = redis_manager.get_technical_indicator(ticker, 'MACD', 2)
            MACD_signals = redis_manager.get_technical_indicator(ticker, 'MACD_signal', 2)

            if len(MACDs) < 2 or len(MACD_signals) < 2:
                return 0.0
            
            # Calculate MACD values
            current_macd = MACDs[-1]
            current_signal = MACD_signals[-1]
            previous_macd = MACDs[-2]
            previous_signal = MACD_signals[-2]

            if previous_macd == 0 or previous_signal == 0:
                return 0.0

            # Compare current MACD divergence with previous
            current_divergence = current_macd - current_signal
            prev_divergence = previous_macd - previous_signal

            # Score based on MACD divergence improvement
            if current_divergence > 0 and current_divergence > prev_divergence:
                score = min(1.0, (current_divergence / (prev_divergence + 0.0001)))
                return max(0.0, score)
            
            return 0.0

        except Exception as e:
            self.logger.error(f"Error in momentum divergence evaluation: {e}")
            return 0.0 

    def _evaluate_volatility_expansion(self, ticker: str, criterion: Dict[str, Any]) -> float:
        candles = redis_manager.get_last_n_candles(ticker, 10)
        closes = [candle['close'] for candle in candles]
        if len(closes) < 10:
            return 0

        recent_returns = [((closes[i] - closes[i-1]) / closes[i-1]) * 100 
                         for i in range(len(closes)-5, len(closes))]
        prev_returns = [((closes[i] - closes[i-1]) / closes[i-1]) * 100 
                       for i in range(len(closes)-10, len(closes)-5)]

        recent_vol = (sum(r * r for r in recent_returns) / len(recent_returns)) ** 0.5
        prev_vol = (sum(r * r for r in prev_returns) / len(prev_returns)) ** 0.5

        vol_expansion = recent_vol / prev_vol if prev_vol > 0 else 0
        return min(1.0, vol_expansion / criterion['threshold'])

@PatternRegistry.register
class MomentumBreakoutPattern(BasePattern):
    def __init__(self):
        super().__init__()
        self.description = "Strong momentum breakout with Level 2 confirmation"
        self.timeframes = ["1m", "5m"]
        self.categories = ["breakout", "momentum"]
        self.criteria = [
            {
                'type': 'level2_pressure',
                'condition': 'bullish',
                'weight': 0.35,
                'evaluator': self._evaluate_level2_pressure
            },
            {
                'type': 'stoch_rsi_momentum',
                'condition': 'bullish_cross',
                'weight': 0.25,
                'evaluator': self._evaluate_stoch_rsi_momentum
            },
            {
                'type': 'volume_confirmation',
                'threshold': 1.5,
                'weight': 0.25,
                'evaluator': self._evaluate_volume_confirmation
            },
            {
                'type': 'price_consolidation',
                'duration': 3,
                'weight': 0.15,
                'evaluator': self._evaluate_price_consolidation
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
                'description': f"Momentum Breakout setup detected with {match_score:.0f}% confidence",
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
        key_levels = redis_manager.get_key_levels(ticker)
        # Find next resistance for target
        target = price * 1.03  # Default 3% target
        stop = price * 0.985   # Default 1.5% stop

        if key_levels:
            # Find nearest resistance above price
            resistances = [level for level in key_levels if level['price'] > price * 1.01 
                         and level['type'] == 'resistance']
            if resistances:
                target = min(level['price'] for level in resistances)

            # Find nearest support below price
            supports = [level for level in key_levels if level['price'] < price * 0.99 
                       and level['type'] == 'support']
            if supports:
                stop = max(level['price'] for level in supports)

        return {
            'entry': price,
            'target': target,
            'stop': stop
        }

    def _evaluate_level2_pressure(self, ticker: str, criterion: Dict[str, Any]) -> float:
        orderbook = redis_manager.get_last_orderbook_snapshot(ticker)
        if not orderbook:
            return 0

        bid_volume = sum(bid[1] for bid in orderbook['bids'])
        ask_volume = sum(ask[1] for ask in orderbook['asks'])
        
        if ask_volume == 0:
            return 1.0
            
        ratio = bid_volume / ask_volume
        
        # Detect bid walls
        avg_bid_size = bid_volume / len(orderbook['bids']) if orderbook['bids'] else 0
        large_bids = sum(1 for bid in orderbook['bids'] if bid[1] > avg_bid_size * 3)
        wall_strength = min(1.0, large_bids / 5)  # Normalize to 0-1

        return min(1.0, (ratio * 0.6 + wall_strength * 0.4))

    def _evaluate_stoch_rsi_momentum(self, ticker: str, criterion: Dict[str, Any]) -> float:
        StochRSI_Ks = redis_manager.get_technical_indicator(ticker, 'StochRSI_K', 2)
        if len(StochRSI_Ks) < 2:
            return 0.0
        stoch_rsi = StochRSI_Ks[-1]
        stoch_rsi_prev = StochRSI_Ks[-2]
        
        is_bullish_cross = stoch_rsi_prev < 20 and stoch_rsi > 20
        momentum = (stoch_rsi - stoch_rsi_prev) / stoch_rsi_prev if stoch_rsi_prev > 0 else 0
        
        return min(1.0, 0.7 + momentum * 0.3) if is_bullish_cross else max(0, momentum)

    def _evaluate_volume_confirmation(self, ticker: str, criterion: Dict[str, Any]) -> float:
        volume_ratio = redis_manager.get_technical_indicator(ticker, 'Volume_Ratio', 1)
        threshold = criterion['threshold']
        
        # Check volume trend
        candles = redis_manager.get_last_n_candles(ticker, 5)
        volumes = [candle['volume'] for candle in candles]
        increasing_intervals = sum(1 for i in range(1, len(volumes)) 
                                 if volumes[i] > volumes[i-1])
        
        volume_score = volume_ratio / threshold if volume_ratio is not None and threshold > 0 else 0
        trend_score = increasing_intervals / 4 if len(volumes) > 1 else 0
        
        return min(1.0, volume_score * 0.7 + trend_score * 0.3)

    def _evaluate_price_consolidation(self, ticker: str, criterion: Dict[str, Any]) -> float:
        candles = redis_manager.get_last_n_candles(ticker, criterion['duration'])
        recent_closes = [candle['close'] for candle in candles]
        if len(recent_closes) < criterion['duration']:
            return 0

        avg_price = sum(recent_closes) / len(recent_closes)
        max_deviation = max(abs(price - avg_price) / avg_price for price in recent_closes)
        
        is_consolidated = max_deviation < 0.005  # 0.5% threshold
        return 1.0 if is_consolidated else max(0, 1 - (max_deviation / 0.01))

    def _evaluate_resistance_breakout(self, ticker: str, criterion: Dict[str, Any]) -> float:
        try:
            price = redis_manager.get_stock_price(ticker)
            key_levels = redis_manager.get_key_levels(ticker)
            
            if not key_levels:
                return 0
            
            # Filter resistance levels above current price
            resistances = [level for level in key_levels 
                          if level.get('price', 0) > price * 1.01 
                          and level.get('type') == 'resistance']
            
            if not resistances:
                return 0
            
            # Find closest resistance
            closest_resistance = min(resistances, key=lambda x: abs(x['price'] - price))
            
            # Calculate distance to closest resistance
            distance = abs(closest_resistance['price'] - price) / price
            
            # Consider resistance strength in scoring
            strength_factor = closest_resistance.get('strength', 1.0)
            
            # Return normalized score
            base_score = 1.0 if distance < 0.003 else max(0, 1 - (distance / 0.01))
            return base_score * strength_factor
            
        except Exception as e:
            logging.error(f"Error evaluating resistance breakout: {e}")
            return 0 