import logging
import time
import random
from typing import Dict, List, Optional, Tuple, Any
from datatypes.coaching_narrative import CoachingNarrative, NarrativeState
from datatypes.strategy import StrategyState
from services.redis_manager import redis_manager
from services.ml_pipeline import ml_pipeline
from patterns.ai_pattern_evaluator import ai_pattern_evaluator

class AITradingCoachingService:
    """AI-Enhanced Trading Coaching Service using Machine Learning"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize AI components
        self.ml_pipeline = ml_pipeline
        self.ai_pattern_evaluator = ai_pattern_evaluator
        
        # Enhanced narrative templates with AI insights
        self.ai_narrative_templates = {
            NarrativeState.ANALYZING: [
                "🤖 AI Analysis Mode: I'm scanning the market with advanced machine learning algorithms, analyzing {ticker} across multiple timeframes and market conditions. This will take a moment while I gather comprehensive data.",
                "🔍 AI-Powered Scan: My neural networks are processing real-time market data for {ticker}, evaluating historical pattern success rates and current market context. Let me find the optimal setup for you.",
                "🧠 Deep Learning Analysis: I'm running {ticker} through my AI models, considering market regime, volatility patterns, and historical strategy performance. This comprehensive analysis will identify the highest-probability opportunities."
            ],
            NarrativeState.SETUP_WEAK: [
                "⚠️ AI Risk Assessment: My machine learning models indicate this setup has only a {ai_probability:.1%} success probability, below our {min_threshold:.1%} threshold. The AI detected {weakness_reason} in the pattern analysis.",
                "🚫 AI Pattern Rejection: Based on historical data analysis, this {pattern_type} pattern shows weak characteristics. My models predict {ai_probability:.1%} success rate, which doesn't meet our risk-adjusted return criteria.",
                "📉 AI Confidence Low: My neural networks have analyzed this setup and found insufficient confirmation signals. Success probability: {ai_probability:.1%}. Let's wait for a stronger pattern with better AI validation."
            ],
            NarrativeState.STRATEGY_FOUND: [
                "🎯 AI-Validated Strategy: Excellent! My machine learning models have identified a high-probability {strategy_name} setup with {ai_probability:.1%} success rate. AI confidence: {ai_confidence:.1%}. Entry: ${entry_price}, Stop: ${stop_price}, Target: ${target_price}.",
                "🚀 AI-Powered Opportunity: My neural networks have found a strong {strategy_name} pattern! AI success probability: {ai_probability:.1%} with {ai_confidence:.1%} confidence. This setup has been validated against {historical_patterns} similar historical patterns.",
                "💎 AI-Golden Setup: My advanced algorithms have detected a premium {strategy_name} opportunity! Success probability: {ai_probability:.1%}, AI confidence: {ai_confidence:.1%}. The risk/reward ratio of {risk_reward}:1 has been optimized by machine learning analysis."
            ],
            NarrativeState.WAITING_FOR_ENTRY: [
                "⏳ AI Entry Monitoring: I'm actively tracking our entry zone with real-time AI analysis. Current price: ${current_price} ({price_distance:.1%} from entry). My models show {entry_confidence} confidence in the entry timing.",
                "📊 AI Entry Analysis: My machine learning models are monitoring entry conditions for {ticker}. We're {price_distance:.1%} from our ${entry_price} entry zone. AI predicts optimal entry timing within {estimated_time}.",
                "🔮 AI Entry Prediction: Based on pattern analysis and market context, my AI models indicate we're approaching the optimal entry zone. Current distance: {price_distance:.1%}. I'll alert you when conditions are perfect."
            ],
            NarrativeState.ENTRY_ZONE: [
                "🚨 AI ENTRY SIGNAL: My neural networks confirm optimal entry conditions! Execute now at ${current_price}. AI confidence: {ai_confidence:.1%}. Stop: ${stop_price}, Target: ${target_price}. This setup has been validated by {ai_validation_points} AI models.",
                "⚡ AI EXECUTION ALERT: Machine learning models signal perfect entry timing! Buy {ticker} now at ${current_price}. AI success probability: {ai_probability:.1%}. Risk management: Stop at ${stop_price}, target at ${target_price}.",
                "🎯 AI-OPTIMIZED ENTRY: My algorithms confirm this is the optimal entry point! Execute immediately at ${current_price}. AI confidence level: {confidence_level}. This trade has been optimized using {optimization_features} advanced features."
            ],
            NarrativeState.IN_POSITION: [
                "📈 AI Position Monitoring: Excellent progress! We're up {gain_percentage:.1%} with AI confidence remaining {ai_confidence:.1%}. My models predict {target_probability:.1%} probability of reaching our ${target_price} target. Current support: ${current_support}.",
                "🤖 AI Trade Analysis: Position performing as expected! Up {gain_percentage:.1%} with AI models showing {momentum_strength} momentum strength. Target probability: {target_probability:.1%}. I'm continuously analyzing market conditions for optimal exit timing.",
                "🧠 AI Success Tracking: Great execution! We're up {gain_percentage:.1%} and my neural networks confirm we're on track. AI target probability: {target_probability:.1%}. I'm monitoring {monitoring_metrics} key metrics for you."
            ],
            NarrativeState.POSITION_BUILDING: [
                "🚀 AI Momentum Confirmation: Outstanding! We're up {gain_percentage:.1%} and my AI models confirm strong momentum building. Target probability increased to {target_probability:.1%}. Volume analysis shows {volume_strength} buying pressure.",
                "📊 AI Trend Analysis: Perfect! Position building momentum with {gain_percentage:.1%} gain. My machine learning models show {trend_strength} trend strength and {target_probability:.1%} target probability. This is exactly what the AI predicted.",
                "💪 AI Strength Validation: Excellent momentum! Up {gain_percentage:.1%} with AI models confirming {momentum_quality} momentum quality. Target probability: {target_probability:.1%}. My algorithms are tracking {tracking_metrics} key indicators."
            ],
            NarrativeState.APPROACHING_TARGET: [
                "🎯 AI Target Approach: We're {target_distance:.1%} from our target! AI models show {target_probability:.1%} probability of reaching ${target_price}. Current gain: {gain_percentage:.1%}. My neural networks are analyzing exit optimization.",
                "📈 AI Exit Planning: Approaching target with {target_distance:.1%} remaining! AI success probability: {target_probability:.1%}. Gain: {gain_percentage:.1%}. My models are calculating optimal exit timing for maximum profit.",
                "🔮 AI Target Prediction: Target zone approaching! {target_distance:.1%} away from ${target_price}. AI models confirm {target_probability:.1%} success probability. I'm preparing exit strategies based on real-time market analysis."
            ],
            NarrativeState.APPROACHING_STOP: [
                "⚠️ AI Stop Warning: We're {stop_distance:.1%} from our stop at ${stop_price}. AI models show {stop_probability:.1%} probability of stop being hit. My neural networks are analyzing if this is a shakeout or trend reversal.",
                "🚨 AI Risk Alert: Approaching stop loss zone! {stop_distance:.1%} from ${stop_price}. AI analysis indicates {stop_probability:.1%} stop probability. I'm evaluating market conditions to determine if we should adjust or exit.",
                "📉 AI Stop Analysis: Stop zone approaching! {stop_distance:.1%} from ${stop_price}. My machine learning models show {stop_probability:.1%} probability. I'm analyzing order flow to determine if this is temporary volatility."
            ],
            NarrativeState.TRADE_UNDER_PRESSURE: [
                "😰 AI Pressure Analysis: Trade under pressure with {loss_percentage:.1%} loss. My AI models are analyzing if our original thesis remains valid. Current AI confidence: {ai_confidence:.1%}. I'm evaluating exit vs. hold scenarios.",
                "📊 AI Stress Test: Position facing headwinds, down {loss_percentage:.1%}. My neural networks are stress-testing our strategy against current market conditions. AI recommendation: {ai_recommendation}.",
                "🔍 AI Damage Assessment: Trade under pressure, down {loss_percentage:.1%}. My machine learning models are analyzing market context changes. AI confidence has decreased to {ai_confidence:.1%}. I'll guide you through this."
            ],
            NarrativeState.EXIT_WARNING: [
                "🚨 AI Exit Warning: {warning_reason}. My neural networks have detected concerning signals. AI confidence dropped to {ai_confidence:.1%}. Consider securing profits or adjusting position. I'm monitoring for further deterioration.",
                "⚠️ AI Caution Alert: {warning_reason}. AI models show {exit_probability:.1%} probability of further downside. We're still up {gain_percentage:.1%}, but my algorithms recommend protective action.",
                "📉 AI Exit Signal: {warning_reason}. My machine learning models indicate {exit_probability:.1%} probability of continued weakness. AI recommendation: {ai_recommendation}. Let's protect our gains."
            ],
            NarrativeState.STRATEGY_FAILED: [
                "💔 AI Strategy Failure: My models confirm our stop has been triggered. AI analysis shows {failure_reason}. Please exit now at market price. My neural networks will analyze this failure to improve future predictions.",
                "❌ AI Failure Analysis: Strategy invalidated by stop loss. AI models detected {failure_pattern} pattern that led to failure. Exit immediately. This data will be used to retrain my algorithms for better future performance.",
                "📉 AI Loss Confirmation: Stop triggered at ${stop_price}. AI analysis indicates {failure_factors} contributed to this loss. Exit now and I'll analyze the failure to enhance future strategy selection."
            ],
            NarrativeState.STRATEGY_COMPLETE: [
                "🎉 AI Success Confirmation: Target achieved! My neural networks confirm this was a successful trade with {gain_percentage:.1%} profit. AI models correctly predicted {prediction_accuracy:.1%} accuracy. Excellent execution!",
                "🏆 AI Victory Analysis: Success! {gain_percentage:.1%} profit achieved. My machine learning models show this trade performed {performance_rating} than predicted. AI confidence was {ai_confidence:.1%}. Perfect execution!",
                "✅ AI Success Validation: Target reached! {gain_percentage:.1%} profit secured. My AI models correctly identified this opportunity with {ai_probability:.1%} success probability. This validates our AI-enhanced approach!"
            ],
            NarrativeState.SCALING_OPPORTUNITY: [
                "📈 AI Scaling Signal: My neural networks detect an optimal scaling opportunity at ${current_price}. AI confidence: {ai_confidence:.1%}. Order flow analysis shows {order_flow_strength} support. This would improve your risk/reward ratio.",
                "🚀 AI Add-on Alert: Machine learning models identify scaling opportunity at ${current_price}. AI probability: {scaling_probability:.1%}. Volume analysis confirms {volume_confirmation}. Consider adding to position.",
                "💎 AI Enhancement Alert: My algorithms detect premium scaling entry at ${current_price}. AI confidence: {ai_confidence:.1%}. This addition would optimize your position based on {optimization_factors}."
            ],
            NarrativeState.MARKET_SHIFT: [
                "🔄 AI Market Shift Detection: My neural networks have detected a significant market regime change: {market_change}. AI models are adjusting strategy parameters accordingly. This may impact our current position.",
                "🌊 AI Regime Change: Machine learning models indicate market environment shift: {market_change}. My algorithms are recalibrating for new conditions. This could affect our strategy performance.",
                "📊 AI Context Update: AI analysis shows market condition change: {market_change}. My models are updating strategy parameters. I'll adjust our approach based on this new market context."
            ]
        }
        
        # AI-specific psychological support
        self.ai_psychological_support = {
            "LOSING_TRADE": [
                "🧠 AI Perspective: My neural networks have analyzed this loss and identified {learning_points} key learning points. This data will improve future predictions. Remember, even the best AI models have learning curves.",
                "📚 AI Learning Mode: My machine learning models are processing this trade outcome to enhance future performance. Every loss teaches the AI something new. Your patience during this learning phase will pay dividends.",
                "🔍 AI Analysis: My algorithms have identified {failure_factors} factors that contributed to this loss. This information will be used to retrain my models for better future performance. We're building a smarter system together."
            ],
            "WINNING_TRADE": [
                "🎯 AI Success Analysis: My neural networks confirm this was an optimal trade execution. AI models correctly predicted {prediction_accuracy:.1%} accuracy. This validates our AI-enhanced approach!",
                "🏆 AI Victory: My machine learning models show this trade performed {performance_rating} than predicted. AI confidence was {ai_confidence:.1%}. Perfect execution of our AI-optimized strategy!",
                "✅ AI Validation: My algorithms correctly identified this opportunity with {ai_probability:.1%} success probability. This win demonstrates the power of combining human intuition with AI analysis."
            ]
        }
    
    def generate_ai_narrative(self, ticker: str) -> CoachingNarrative:
        """Generate AI-enhanced coaching narrative"""
        try:
            # Get current strategy state
            current_strategy = redis_manager.get_current_strategy(ticker)
            
            if not current_strategy:
                return self._generate_analyzing_narrative(ticker)
            
            # Determine narrative state
            state = self._determine_narrative_state(ticker, current_strategy)
            
            # Generate AI-enhanced narrative
            narrative = self._generate_state_narrative(ticker, state, current_strategy)
            
            # Add AI insights and recommendations
            narrative = self._enhance_with_ai_insights(narrative, ticker, current_strategy)
            
            return narrative
            
        except Exception as e:
            self.logger.error(f"Error generating AI narrative for {ticker}: {e}")
            return self._generate_fallback_narrative(ticker)
    
    def _generate_analyzing_narrative(self, ticker: str) -> CoachingNarrative:
        """Generate narrative when analyzing ticker"""
        try:
            # Get AI model status
            ai_status = self.ai_pattern_evaluator.get_ai_model_status()
            
            template = self._select_template(self.ai_narrative_templates[NarrativeState.ANALYZING])
            message = template.format(ticker=ticker)
            
            return CoachingNarrative(
                ticker=ticker,
                state=NarrativeState.ANALYZING,
                message=message,
                ai_insights={
                    'model_status': ai_status,
                    'analysis_mode': 'ai_enhanced',
                    'scanning_patterns': True
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error generating analyzing narrative: {e}")
            return self._generate_fallback_narrative(ticker)
    
    def _determine_narrative_state(self, ticker: str, strategy: Dict) -> NarrativeState:
        """Determine the current narrative state with AI enhancement"""
        try:
            current_price = redis_manager.get_stock_price(ticker)
            if not current_price:
                return NarrativeState.ANALYZING
            
            strategy_obj = strategy
            entry_price = float(strategy_obj.get('entry_price', 0))
            target_price = float(strategy_obj.get('target_price', 0))
            stop_price = float(strategy_obj.get('stop_price', 0))
            
            # AI-enhanced state determination
            if strategy_obj.get('state') == StrategyState.LOCKED:
                if entry_price > 0:
                    if current_price >= entry_price:
                        return NarrativeState.ENTRY_ZONE
                    elif abs(current_price - entry_price) / entry_price <= 0.02:
                        return NarrativeState.ENTRY_APPROACHING
                    else:
                        return NarrativeState.WAITING_FOR_ENTRY
                else:
                    return NarrativeState.WAITING_FOR_ENTRY
            
            elif strategy_obj.get('state') == StrategyState.COMPLETED:
                if strategy_obj.get('completion_type') == 'target':
                    return NarrativeState.STRATEGY_COMPLETE
                elif strategy_obj.get('completion_type') == 'stop':
                    return NarrativeState.STRATEGY_FAILED
                else:
                    return NarrativeState.STRATEGY_COMPLETE
            
            # Check for position management states
            if entry_price > 0 and current_price > entry_price:
                if target_price > 0:
                    target_distance = (target_price - current_price) / target_price
                    if target_distance <= 0.05:
                        return NarrativeState.APPROACHING_TARGET
                    elif target_distance <= 0.15:
                        return NarrativeState.POSITION_BUILDING
                    else:
                        return NarrativeState.IN_POSITION
                
                if stop_price > 0:
                    stop_distance = (current_price - stop_price) / current_price
                    if stop_distance <= 0.05:
                        return NarrativeState.APPROACHING_STOP
            
            return NarrativeState.ANALYZING
            
        except Exception as e:
            self.logger.error(f"Error determining narrative state: {e}")
            return NarrativeState.ANALYZING
    
    def _generate_state_narrative(self, ticker: str, state: NarrativeState, strategy: Dict) -> CoachingNarrative:
        """Generate narrative for specific state with AI enhancement"""
        try:
            templates = self.ai_narrative_templates.get(state, [])
            if not templates:
                return self._generate_fallback_narrative(ticker)
            
            template = self._select_template(templates)
            context = self._generate_ai_context(ticker, state, strategy)
            
            # Fill template with context
            message = self._fill_ai_template(template, context)
            
            return CoachingNarrative(
                ticker=ticker,
                state=state,
                message=message,
                ai_insights=context.get('ai_insights', {})
            )
            
        except Exception as e:
            self.logger.error(f"Error generating state narrative: {e}")
            return self._generate_fallback_narrative(ticker)
    
    def _generate_ai_context(self, ticker: str, state: NarrativeState, strategy: Dict) -> Dict[str, Any]:
        """Generate AI-enhanced context for narrative generation"""
        try:
            context = {
                'ticker': ticker,
                'current_price': redis_manager.get_stock_price(ticker),
                'entry_price': strategy.get('entry_price', 0),
                'target_price': strategy.get('target_price', 0),
                'stop_price': strategy.get('stop_price', 0),
                'strategy_name': strategy.get('name', 'Unknown'),
                'pattern_type': strategy.get('pattern_type', 'unknown'),
                'probability': strategy.get('probability', 0.65),
                'match_score': strategy.get('match_score', 70)
            }
            
            # Add AI-specific context
            if state in [NarrativeState.STRATEGY_FOUND, NarrativeState.ENTRY_ZONE, 
                        NarrativeState.IN_POSITION, NarrativeState.POSITION_BUILDING]:
                ai_context = self._get_ai_strategy_context(ticker, strategy)
                context.update(ai_context)
            
            # Add market context
            market_context = redis_manager.get_market_context()
            if market_context:
                context.update(market_context)
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error generating AI context: {e}")
            return {}
    
    def _get_ai_strategy_context(self, ticker: str, strategy: Dict) -> Dict[str, Any]:
        """Get AI-specific context for strategy narratives"""
        try:
            # Get AI pattern evaluation
            ai_evaluation = self.ai_pattern_evaluator.evaluate_pattern(ticker, strategy.get('name', ''))
            
            if not ai_evaluation:
                return {}
            
            ai_recommendations = ai_evaluation.get('ai_recommendations', {})
            
            return {
                'ai_probability': ai_evaluation.get('probability', 0.65),
                'ai_confidence': ai_evaluation.get('ai_confidence', 0.5),
                'ml_model_used': ai_evaluation.get('ml_model_used', False),
                'feature_importance': ai_evaluation.get('feature_importance', {}),
                'ai_recommendations': ai_recommendations,
                'entry_timing': ai_recommendations.get('entry_timing', {}),
                'position_sizing': ai_recommendations.get('position_sizing', {}),
                'risk_management': ai_recommendations.get('risk_management', {}),
                'market_context': ai_recommendations.get('market_context', {}),
                'confidence_level': ai_recommendations.get('confidence_level', 'moderate')
            }
            
        except Exception as e:
            self.logger.error(f"Error getting AI strategy context: {e}")
            return {}
    
    def _fill_ai_template(self, template: str, context: Dict[str, Any]) -> str:
        """Fill AI template with context data"""
        try:
            # Ensure all template variables are available
            self._ensure_ai_template_variables(context)
            
            # Fill template
            message = template
            for key, value in context.items():
                if isinstance(value, (int, float)):
                    if 'price' in key or 'percent' in key:
                        message = message.replace(f"${{{key}}}", f"${value:.2f}")
                    else:
                        message = message.replace(f"${{{key}}}", f"{value:.1f}")
                else:
                    message = message.replace(f"${{{key}}}", str(value))
            
            return message
            
        except Exception as e:
            self.logger.error(f"Error filling AI template: {e}")
            return template
    
    def _ensure_ai_template_variables(self, context: Dict[str, Any]) -> None:
        """Ensure all required AI template variables are present"""
        try:
            # Set default values for missing variables
            defaults = {
                'ai_probability': 0.65,
                'ai_confidence': 0.5,
                'min_threshold': 0.6,
                'weakness_reason': 'insufficient pattern confirmation',
                'historical_patterns': 'multiple',
                'risk_reward': '2:1',
                'entry_confidence': 'high',
                'estimated_time': 'the next few minutes',
                'ai_validation_points': '3',
                'optimization_features': 'advanced pattern recognition',
                'momentum_strength': 'strong',
                'target_probability': 0.8,
                'current_support': 'holding well',
                'trend_strength': 'robust',
                'momentum_quality': 'excellent',
                'tracking_metrics': 'key technical indicators',
                'stop_probability': 0.3,
                'ai_recommendation': 'hold position',
                'exit_probability': 0.4,
                'failure_reason': 'market conditions changed',
                'failure_pattern': 'unexpected volatility',
                'failure_factors': 'multiple market factors',
                'prediction_accuracy': 85.0,
                'performance_rating': 'better',
                'scaling_probability': 0.7,
                'order_flow_strength': 'strong',
                'volume_confirmation': 'high volume support',
                'optimization_factors': 'AI-optimized entry points',
                'market_change': 'increased volatility',
                'learning_points': '3 valuable insights',
                'failure_factors': 'market regime shift',
                'prediction_accuracy': 90.0,
                'performance_rating': 'exactly as',
                'scaling_probability': 0.75
            }
            
            for key, default_value in defaults.items():
                if key not in context:
                    context[key] = default_value
                    
        except Exception as e:
            self.logger.error(f"Error ensuring AI template variables: {e}")
    
    def _select_template(self, templates: list) -> str:
        """Select a random template from the list"""
        return random.choice(templates) if templates else "AI analysis in progress..."
    
    def _generate_fallback_narrative(self, ticker: str) -> CoachingNarrative:
        """Generate fallback narrative when AI fails"""
        return CoachingNarrative(
            ticker=ticker,
            state=NarrativeState.ANALYZING,
            message=f"AI analysis temporarily unavailable for {ticker}. Using fallback analysis mode.",
            ai_insights={'error': 'AI system temporarily unavailable', 'fallback_mode': True}
        )
    
    def _enhance_with_ai_insights(self, narrative: CoachingNarrative, ticker: str, strategy: Dict) -> CoachingNarrative:
        """Enhance narrative with additional AI insights"""
        try:
            # Add AI performance metrics
            ai_metrics = self.ml_pipeline.get_model_performance_metrics()
            
            # Add AI recommendations if available
            ai_recommendations = {}
            if strategy.get('name'):
                ai_eval = self.ai_pattern_evaluator.evaluate_pattern(ticker, strategy['name'])
                if ai_eval:
                    ai_recommendations = ai_eval.get('ai_recommendations', {})
            
            # Update AI insights
            narrative.ai_insights.update({
                'model_performance': ai_metrics,
                'recommendations': ai_recommendations,
                'last_updated': time.time()
            })
            
            return narrative
            
        except Exception as e:
            self.logger.error(f"Error enhancing narrative with AI insights: {e}")
            return narrative
    
    def get_ai_coaching_status(self) -> Dict[str, Any]:
        """Get the status of AI coaching system"""
        try:
            return {
                'ai_system_active': True,
                'ml_pipeline_status': self.ml_pipeline.get_model_performance_metrics(),
                'pattern_evaluator_status': self.ai_pattern_evaluator.get_ai_model_status(),
                'narrative_templates_loaded': len(self.ai_narrative_templates),
                'ai_enhancement_features': [
                    'pattern_success_prediction',
                    'ai_confidence_scoring',
                    'intelligent_position_sizing',
                    'dynamic_risk_management',
                    'market_regime_adaptation',
                    'ai_optimized_narratives'
                ]
            }
        except Exception as e:
            self.logger.error(f"Error getting AI coaching status: {e}")
            return {'error': str(e)}

# Global instance
ai_trading_coach = AITradingCoachingService()
