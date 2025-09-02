import logging
from typing import Dict, Any, List, Optional
from .pattern_registry import PatternRegistry
from .pattern_utils import calculate_probability
from services.redis_manager import redis_manager
from services.ml_pipeline import ml_pipeline
from utils.util import get_current_session

class AIPatternEvaluator:
    """AI-Enhanced Pattern Evaluator using Machine Learning"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.patterns = {
            name: pattern_class() 
            for name, pattern_class in PatternRegistry.get_all_patterns().items()
        }
        
        # Initialize ML pipeline
        self.ml_pipeline = ml_pipeline
        
    def evaluate_all_patterns(self, ticker: str, min_score: float = 65) -> List[Dict[str, Any]]:
        """Evaluate all registered patterns with AI-enhanced probability"""
        results = []
        
        for pattern in self.patterns.values():
            try:
                result = pattern.evaluate(ticker)
                if result['match_score'] >= min_score:
                    # Get AI-enhanced probability
                    ai_probability = self._get_ai_enhanced_probability(ticker, result)
                    
                    # Update result with AI insights
                    result['probability'] = ai_probability['success_probability']
                    result['ai_confidence'] = ai_probability['confidence_score']
                    result['ml_model_used'] = ai_probability['ml_model_used']
                    result['feature_importance'] = ai_probability.get('feature_importance', {})
                    
                    # Add AI recommendations
                    result['ai_recommendations'] = self._generate_ai_recommendations(
                        ticker, result, ai_probability
                    )
                    
                    results.append(result)
            except Exception as e:
                logging.error(f"Error evaluating pattern {pattern.name}: {e}")
                continue
                
        # Sort by AI-enhanced probability instead of just match score
        results.sort(key=lambda x: x['probability'], reverse=True)
        return results

    def evaluate_pattern(self, ticker: str, pattern_name: str) -> Dict[str, Any]:
        """Evaluate a specific pattern with AI enhancement"""
        try:
            pattern = self.patterns[pattern_name]
            if pattern:
                result = pattern.evaluate(ticker)
                
                # Get AI-enhanced probability
                ai_probability = self._get_ai_enhanced_probability(ticker, result)
                
                # Update result with AI insights
                result['probability'] = ai_probability['success_probability']
                result['ai_confidence'] = ai_probability['confidence_score']
                result['ml_model_used'] = ai_probability['ml_model_used']
                result['feature_importance'] = ai_probability.get('feature_importance', {})
                
                # Add AI recommendations
                result['ai_recommendations'] = self._generate_ai_recommendations(
                    ticker, result, ai_probability
                )
                
                return result

            return {}
        except Exception as e:
            logging.error(f"Error evaluating pattern {pattern_name}: {e}")
            return {}

    def _get_ai_enhanced_probability(self, ticker: str, pattern_result: Dict[str, Any]) -> Dict[str, Any]:
        """Get AI-enhanced probability for a pattern"""
        try:
            # Prepare strategy data for ML prediction
            strategy_data = {
                'probability': pattern_result.get('probability', 0.65),
                'match_score': pattern_result.get('match_score', 70),
                'pattern_type': pattern_result.get('pattern_type', 'unknown'),
                'entry_price': pattern_result.get('entry_price', 0),
                'target_price': pattern_result.get('target_price', 0),
                'stop_price': pattern_result.get('stop_price', 0)
            }
            
            # Calculate derived features
            if strategy_data['entry_price'] > 0:
                strategy_data['entry_to_target_distance'] = (
                    strategy_data['target_price'] - strategy_data['entry_price']
                ) / strategy_data['entry_price']
                
                strategy_data['entry_to_stop_distance'] = (
                    strategy_data['entry_price'] - strategy_data['stop_price']
                ) / strategy_data['entry_price']
                
                if strategy_data['entry_to_stop_distance'] > 0:
                    strategy_data['risk_reward_ratio'] = (
                        strategy_data['entry_to_target_distance'] / strategy_data['entry_to_stop_distance']
                    )
                else:
                    strategy_data['risk_reward_ratio'] = 1.0
            else:
                strategy_data['entry_to_target_distance'] = 0.05
                strategy_data['entry_to_stop_distance'] = 0.03
                strategy_data['risk_reward_ratio'] = 1.67
            
            # Get AI prediction
            ai_prediction = self.ml_pipeline.predict_pattern_success(ticker, strategy_data)
            
            # Blend AI probability with technical probability
            technical_prob = pattern_result.get('probability', 0.65)
            ai_prob = ai_prediction['success_probability']
            
            # Weighted combination (can be adjusted based on AI model performance)
            ai_weight = 0.7 if ai_prediction['ml_model_used'] else 0.3
            technical_weight = 1 - ai_weight
            
            blended_probability = (ai_prob * ai_weight) + (technical_prob * technical_weight)
            
            return {
                'success_probability': blended_probability,
                'confidence_score': ai_prediction['confidence_score'],
                'ml_model_used': ai_prediction['ml_model_used'],
                'feature_importance': ai_prediction.get('feature_importance', {}),
                'technical_probability': technical_prob,
                'ai_probability': ai_prob,
                'blending_weights': {'ai': ai_weight, 'technical': technical_weight}
            }
            
        except Exception as e:
            self.logger.error(f"Error getting AI-enhanced probability: {e}")
            # Fallback to technical probability
            return {
                'success_probability': pattern_result.get('probability', 0.65),
                'confidence_score': 0.5,
                'ml_model_used': False,
                'feature_importance': {},
                'technical_probability': pattern_result.get('probability', 0.65),
                'ai_probability': 0.5,
                'blending_weights': {'ai': 0.0, 'technical': 1.0}
            }

    def _generate_ai_recommendations(self, ticker: str, pattern_result: Dict[str, Any], 
                                   ai_probability: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered trading recommendations"""
        try:
            recommendations = {
                'entry_timing': self._analyze_entry_timing(ticker, pattern_result),
                'position_sizing': self._analyze_position_sizing(ticker, pattern_result, ai_probability),
                'risk_management': self._analyze_risk_management(ticker, pattern_result, ai_probability),
                'market_context': self._analyze_market_context(ticker, pattern_result),
                'confidence_level': self._get_confidence_level(ai_probability['confidence_score'])
            }
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating AI recommendations: {e}")
            return {}

    def _analyze_entry_timing(self, ticker: str, pattern_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze optimal entry timing"""
        try:
            current_price = redis_manager.get_stock_price(ticker)
            entry_price = pattern_result.get('entry_price', current_price)
            
            if not current_price or not entry_price:
                return {'recommendation': 'insufficient_data', 'urgency': 'low'}
            
            price_distance = abs(current_price - entry_price) / entry_price
            
            if price_distance <= 0.005:  # Within 0.5%
                urgency = 'high'
                recommendation = 'immediate_entry'
            elif price_distance <= 0.02:  # Within 2%
                urgency = 'medium'
                recommendation = 'near_entry_zone'
            else:
                urgency = 'low'
                recommendation = 'wait_for_entry'
            
            return {
                'recommendation': recommendation,
                'urgency': urgency,
                'price_distance_percent': price_distance * 100,
                'current_price': current_price,
                'target_entry': entry_price
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing entry timing: {e}")
            return {'recommendation': 'error', 'urgency': 'low'}

    def _analyze_position_sizing(self, ticker: str, pattern_result: Dict[str, Any], 
                                ai_probability: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze optimal position sizing based on AI confidence"""
        try:
            confidence_score = ai_probability['confidence_score']
            success_probability = ai_probability['success_probability']
            
            # Base position size on confidence and probability
            if confidence_score >= 0.8 and success_probability >= 0.7:
                position_size = 'aggressive'
                size_multiplier = 1.0
            elif confidence_score >= 0.6 and success_probability >= 0.6:
                position_size = 'moderate'
                size_multiplier = 0.7
            else:
                position_size = 'conservative'
                size_multiplier = 0.5
            
            return {
                'recommended_size': position_size,
                'size_multiplier': size_multiplier,
                'confidence_threshold': confidence_score,
                'probability_threshold': success_probability,
                'reasoning': f"Based on {confidence_score:.1%} confidence and {success_probability:.1%} success probability"
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing position sizing: {e}")
            return {'recommended_size': 'moderate', 'size_multiplier': 0.7}

    def _analyze_risk_management(self, ticker: str, pattern_result: Dict[str, Any], 
                                ai_probability: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze risk management recommendations"""
        try:
            current_price = redis_manager.get_stock_price(ticker)
            stop_price = pattern_result.get('stop_price', 0)
            target_price = pattern_result.get('target_price', 0)
            
            if not current_price or not stop_price or not target_price:
                return {'recommendation': 'insufficient_data'}
            
            # Calculate risk metrics
            risk_amount = current_price - stop_price
            reward_amount = target_price - current_price
            risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
            
            # AI-based stop adjustment
            ai_confidence = ai_probability['confidence_score']
            if ai_confidence >= 0.8:
                stop_adjustment = 'tighten_stop'  # More confident = tighter stop
            elif ai_confidence <= 0.4:
                stop_adjustment = 'widen_stop'    # Less confident = wider stop
            else:
                stop_adjustment = 'maintain_stop'
            
            return {
                'current_risk_reward': risk_reward_ratio,
                'stop_adjustment': stop_adjustment,
                'ai_confidence': ai_confidence,
                'risk_amount': risk_amount,
                'reward_amount': reward_amount,
                'recommendation': f"Adjust stop based on {ai_confidence:.1%} AI confidence"
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing risk management: {e}")
            return {'recommendation': 'maintain_current_stops'}

    def _analyze_market_context(self, ticker: str, pattern_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market context for the pattern"""
        try:
            market_context = redis_manager.get_market_context()
            
            if not market_context:
                return {'recommendation': 'insufficient_market_data'}
            
            # Analyze market conditions
            market_trend = market_context.get('market_trend', 'neutral')
            volatility = market_context.get('volatility', 'medium')
            sector_strength = market_context.get('sector_strength', 'neutral')
            
            # Pattern-specific market analysis
            pattern_type = pattern_result.get('pattern_type', 'unknown')
            
            if pattern_type == 'breakout':
                if market_trend == 'bullish':
                    market_favorability = 'high'
                elif market_trend == 'bearish':
                    market_favorability = 'low'
                else:
                    market_favorability = 'medium'
            elif pattern_type == 'reversal':
                if market_trend == 'bearish':
                    market_favorability = 'high'
                elif market_trend == 'bullish':
                    market_favorability = 'low'
                else:
                    market_favorability = 'medium'
            else:
                market_favorability = 'medium'
            
            return {
                'market_trend': market_trend,
                'volatility': volatility,
                'sector_strength': sector_strength,
                'pattern_type': pattern_type,
                'market_favorability': market_favorability,
                'recommendation': f"Pattern {pattern_type} in {market_trend} market conditions"
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing market context: {e}")
            return {'recommendation': 'market_analysis_unavailable'}

    def _get_confidence_level(self, confidence_score: float) -> str:
        """Convert confidence score to human-readable level"""
        if confidence_score >= 0.9:
            return 'very_high'
        elif confidence_score >= 0.8:
            return 'high'
        elif confidence_score >= 0.7:
            return 'good'
        elif confidence_score >= 0.6:
            return 'moderate'
        elif confidence_score >= 0.5:
            return 'low'
        else:
            return 'very_low'

    def get_ai_model_status(self) -> Dict[str, Any]:
        """Get the status of AI models"""
        try:
            return self.ml_pipeline.get_model_performance_metrics()
        except Exception as e:
            self.logger.error(f"Error getting AI model status: {e}")
            return {'error': str(e)}

    def retrain_ai_models(self, force: bool = False) -> bool:
        """Retrain AI models with latest data"""
        try:
            return self.ml_pipeline.train_pattern_success_model(force_retrain=force)
        except Exception as e:
            self.logger.error(f"Error retraining AI models: {e}")
            return False

# Global instance
ai_pattern_evaluator = AIPatternEvaluator()
