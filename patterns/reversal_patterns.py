from typing import Dict, Any, Optional
from .base_pattern import BasePattern
from .pattern_registry import PatternRegistry
import logging
from services.redis_manager import redis_manager

@PatternRegistry.register
class DeadCatBouncePattern(BasePattern):
    def __init__(self):
        super().__init__()
        self.description = "Dead Cat Bounce reversal with exhaustion signals"
        self.timeframes = ["1m", "5m"]
        self.categories = ["reversal", "scalp"]
        self.criteria = [
            {
                'type': 'seller_exhaustion',
                'weight': 0.3,
                'evaluator': self._evaluate_seller_exhaustion
            },
            {
                'type': 'stoch_rsi_divergence',
                'condition': 'bearish',
                'weight': 0.25,
                'evaluator': self._evaluate_stoch_rsi_divergence
            },
            {
                'type': 'candlestick_reversal',
                'patterns': ['hammer', 'doji'],
                'weight': 0.25,
                'evaluator': self._evaluate_candlestick_reversal
            },
            {
                'type': 'support_test',
                'weight': 0.2,
                'evaluator': self._evaluate_support_test
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
                'description': f"Dead Cat Bounce reversal detected with {match_score:.0f}% confidence",
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
            'target': price * 1.02,  # 2% target for quick reversal
            'stop': price * 0.995    # 0.5% stop loss
        }

    def _evaluate_seller_exhaustion(self, ticker: str, criterion: Dict[str, Any]) -> float:
        candles = redis_manager.get_last_n_candles(ticker, 5)
        volumes = [candle['volume'] for candle in candles]
        closes = [candle['close'] for candle in candles]
        if len(volumes) < 5 or len(closes) < 5:
            return 0

        # Check for declining volume on down moves
        declining_vol_on_down = 0
        for i in range(1, 5):
            price_down = closes[-i] < closes[-i-1]
            volume_down = volumes[-i] < volumes[-i-1]
            if price_down and volume_down:
                declining_vol_on_down += 1

        # Consider current volume ratio
        volume_ratio = redis_manager.get_technical_indicator(ticker, 'Volume_Ratio', 1)
        volume_score = min(1.0, volume_ratio / 2) if volume_ratio is not None else 0

        return (declining_vol_on_down / 4) * 0.6 + volume_score * 0.4

    def _evaluate_stoch_rsi_divergence(self, ticker: str, criterion: Dict[str, Any]) -> float:
        stoch_rsi = redis_manager.get_technical_indicator(ticker, 'StochRSI_K', 1)
        candles = redis_manager.get_last_n_candles(ticker, 2)
        closes = [candle['close'] for candle in candles]
        
        if not closes or len(closes) < 2:
            return 0

        current_price = closes[-1]
        prev_price = closes[-2]
        
        # Bearish divergence: Price making higher highs, StochRSI making lower highs
        price_higher = current_price > prev_price
        stoch_rsi_lower = stoch_rsi < 80 if stoch_rsi is not None else False

        return min(1.0, (80 - stoch_rsi) / 30) if price_higher and stoch_rsi_lower else 0

    def _evaluate_candlestick_reversal(self, ticker: str, criterion: Dict[str, Any]) -> float:
        candles = redis_manager.get_last_n_candles(ticker, 1)
        opens = [candle['open'] for candle in candles]
        highs = [candle['high'] for candle in candles]
        lows = [candle['low'] for candle in candles]
        closes = [candle['close'] for candle in candles]
        
        if len(opens) < 1 or len(highs) < 1 or len(lows) < 1 or len(closes) < 1:
            return 0

        # Check for hammer pattern
        last_candle = {
            'open': opens[-1],
            'high': highs[-1],
            'low': lows[-1],
            'close': closes[-1]
        }
        
        body_size = abs(last_candle['close'] - last_candle['open'])
        lower_wick = min(last_candle['open'], last_candle['close']) - last_candle['low']
        upper_wick = last_candle['high'] - max(last_candle['open'], last_candle['close'])

        # Hammer criteria
        is_hammer = (lower_wick > body_size * 2 and upper_wick < body_size * 0.5)
        
        # Doji criteria
        is_doji = body_size < (last_candle['high'] - last_candle['low']) * 0.1

        if is_hammer:
            return 1.0
        elif is_doji:
            return 0.8
        return 0.0

    def _evaluate_support_test(self, ticker: str, criterion: Dict[str, Any]) -> float:
        try:
            price = redis_manager.get_stock_price(ticker)
            key_levels = redis_manager.get_key_levels(ticker)
            support_levels = [level for level in key_levels if level['type'] == 'support']
            
            if not support_levels:
                return 0

            # Find closest support level
            closest_support = min(support_levels, 
                                key=lambda x: abs(x['price'] - price))
            
            distance = abs(price - closest_support['price']) / price
            return 1.0 if distance < 0.003 else max(0, 1 - (distance / 0.01))
        except Exception as e:
            logging.error(f"Error evaluating support test: {e}")
            return 0

@PatternRegistry.register
class LiquidityGrabPattern(BasePattern):
    def __init__(self):
        super().__init__()
        self.description = "Liquidity Grab Scalp with hidden orders"
        self.timeframes = ["1m", "5m"]
        self.categories = ["reversal", "scalp"]
        self.criteria = [
            {
                'type': 'hidden_orders',
                'weight': 0.35,
                'evaluator': self._evaluate_hidden_orders
            },
            {
                'type': 'stoch_rsi_extreme',
                'condition': 'any',
                'weight': 0.25,
                'evaluator': self._evaluate_stoch_rsi_extreme
            },
            {
                'type': 'quick_reversal',
                'timeframe': '5m',
                'weight': 0.25,
                'evaluator': self._evaluate_quick_reversal
            },
            {
                'type': 'volume_spike',
                'threshold': 2.0,
                'weight': 0.15,
                'evaluator': self._evaluate_volume_spike
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
                'description': f"Liquidity Grab opportunity detected with {match_score:.0f}% confidence",
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
        target = price * 1.01  # Default 1% target
        
        if key_levels:
            # Find next resistance level
            resistances = [level for level in key_levels 
                         if level['price'] > price and level['type'] == 'resistance']
            if resistances:
                target = min(level['price'] for level in resistances)

        return {
            'entry': price,
            'target': target,
            'stop': price * 0.997  # Tight 0.3% stop for scalping
        }

    def _evaluate_hidden_orders(self, ticker: str, criterion: Dict[str, Any]) -> float:
        orderbook = redis_manager.get_last_orderbook_snapshot(ticker)
        if not orderbook:
            return 0

        # Use average 30-day volume as reference
        avg_volume = redis_manager.get_avg_30d_volume(ticker)
        if avg_volume == 0:
            return 0

        # Look for large hidden orders
        large_orders = sum(1 for bid in orderbook['bids'] 
                         if bid[1] > avg_volume * 0.01)
        
        # Calculate order imbalance
        total_bids = orderbook['bid_volume']
        total_asks = orderbook['ask_volume']
        
        if total_bids + total_asks == 0:
            return 0
            
        imbalance = abs(total_bids - total_asks) / (total_bids + total_asks)
        
        return min(1.0, (large_orders * 0.2) + (imbalance * 0.8))

    def _evaluate_stoch_rsi_extreme(self, ticker: str, criterion: Dict[str, Any]) -> float:
        stoch_rsi = redis_manager.get_technical_indicator(ticker, 'StochRSI_K', 1)
        if not stoch_rsi:
            return 0

        if stoch_rsi >= 80:
            return min(1.0, (stoch_rsi - 80) / 20)
        elif stoch_rsi <= 20:
            return min(1.0, (20 - stoch_rsi) / 20)
        return 0

    def _evaluate_quick_reversal(self, ticker: str, criterion: Dict[str, Any]) -> float:
        """
        Evaluate quick price reversals within recent periods.
        Returns a score between 0 and 1.
        """
        try:
            candles = redis_manager.get_last_n_candles(ticker, 5)
            closes = [candle['close'] for candle in candles]
            if len(closes) < 5:
                return 0

            # Calculate price changes
            changes = []
            for i in range(1, len(closes)):
                changes.append((closes[i] - closes[i-1]) / closes[i-1])

            # Look for direction changes in the last 5 periods
            recent_changes = changes[-5:]  # Only consider last 5 periods
            reversals = 0
            for i in range(1, len(recent_changes)):
                if (recent_changes[i] > 0 and recent_changes[i-1] < 0) or \
                   (recent_changes[i] < 0 and recent_changes[i-1] > 0):
                    reversals += 1

            # Maximum possible reversals in 4 intervals (5 periods) is 4
            # Normalize score to [0, 1]
            score = min(reversals / 4, 1.0)
            
            return score

        except Exception as e:
            logging.error(f"Error evaluating quick reversal: {e}")
            return 0

    def _evaluate_volume_spike(self, ticker: str, criterion: Dict[str, Any]) -> float:
        volume_ratio = redis_manager.get_technical_indicator(ticker, 'Volume_Ratio', 1)
        if not volume_ratio:
            return 0
        threshold = criterion['threshold']
        return min(1.0, volume_ratio / threshold) 