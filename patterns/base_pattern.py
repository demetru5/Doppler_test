from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging
from services.redis_manager import redis_manager

class BasePattern(ABC):
    """Base class for all trading patterns"""
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.description = ""
        self.timeframes = ["1m", "5m"]
        self.required_fields = ['price', 'candles']
        self.logger = logging.getLogger(f"patterns.{self.name}")
        
    @abstractmethod
    def evaluate(self, ticker: str) -> Dict[str, Any]:
        """Evaluate if pattern is present in stock data"""
        pass
    
    @abstractmethod
    def get_targets(self, ticker: str) -> Dict[str, float]:
        """Calculate entry, target and stop prices"""
        pass

    def validate_data(self, ticker: str) -> bool:
        """Validate required data is present from StockManager"""
        try:
            if not ticker:
                return False
            
            price = redis_manager.get_stock_price(ticker)
            if not price:
                return False
            
            candles = redis_manager.get_candles(ticker)
            if not candles:
                return False

            if len(candles) < 5:
                logging.warning(f"Not enough candles for {ticker}")
                return False

            return True
        except Exception as e:
            self.logger.error(f"Error validating data: {e}")
            return False

    def get_default_result(self) -> Dict[str, Any]:
        """Get default result when pattern evaluation fails"""
        return {
            'match_score': 0,
            'pattern_name': self.name,
            'description': "Insufficient data for pattern evaluation",
            'entry_price': 0,
            'target_price': 0,
            'stop_price': 0,
            'probability': 0,
            'timeframe': "1m",
            'criteria_scores': {}
        }

    def evaluate_criteria(self, ticker: str, criteria: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate pattern criteria and calculate weighted score"""
        if not self.validate_data(ticker):
            return {'total_score': 0, 'criteria_scores': {}}

        total_score = 0
        total_weight = 0
        criteria_scores = {}

        for criterion in criteria:
            try:
                score = criterion['evaluator'](ticker, criterion)
                weighted_score = score * criterion['weight']
                total_score += weighted_score
                total_weight += criterion['weight']
                criteria_scores[criterion['type']] = score
            except Exception as e:
                self.logger.error(f"Error evaluating criterion {criterion['type']}: {e}")
                continue

        if total_weight == 0:
            return {'total_score': 0, 'criteria_scores': criteria_scores}

        return {
            'total_score': (total_score / total_weight) * 100,
            'criteria_scores': criteria_scores
        }

    def get_volume_profile(self, ticker: str, periods: int = 5) -> Dict[str, Any]:
        """Get volume profile analysis for recent periods"""
        try:
            candles = redis_manager.get_last_n_candles(ticker, periods)
            recent_volumes = [candle['volume'] for candle in candles]
            
            if len(recent_volumes) < periods:
                return {'trend': 'neutral', 'acceleration': 0.0, 'ratio': 1.0}
            
            # Calculate volume trend
            if len(recent_volumes) >= 2:
                increasing_count = sum(1 for i in range(1, len(recent_volumes)) 
                                     if recent_volumes[i] > recent_volumes[i-1])
                trend_ratio = increasing_count / (len(recent_volumes) - 1)
                
                if trend_ratio > 0.6:
                    trend = 'increasing'
                elif trend_ratio < 0.4:
                    trend = 'decreasing'
                else:
                    trend = 'neutral'
            else:
                trend = 'neutral'
            
            # Calculate volume acceleration
            if len(recent_volumes) >= 4:
                first_half = sum(recent_volumes[:len(recent_volumes)//2])
                second_half = sum(recent_volumes[len(recent_volumes)//2:])
                
                if first_half > 0:
                    acceleration = (second_half / first_half) - 1.0
                else:
                    acceleration = 0.0
            else:
                acceleration = 0.0
            
            # Calculate volume ratio vs average
            volume_ratio = redis_manager.get_technical_indicator(ticker, 'Volume_Ratio', 1)
            
            return {
                'trend': trend,
                'acceleration': acceleration,
                'ratio': volume_ratio if volume_ratio else 1.0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting volume profile: {e}")
            return {'trend': 'neutral', 'acceleration': 0.0, 'ratio': 1.0} 