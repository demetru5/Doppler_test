import logging
from typing import Dict, Any, List
from flask import Blueprint, jsonify, request
from services.ml_pipeline import ml_pipeline
from services.ai_trading_coach_service import ai_trading_coach
from patterns.ai_pattern_evaluator import ai_pattern_evaluator
from ai_training_worker import ai_training_worker

# Create Blueprint
ai_dashboard_bp = Blueprint('ai_dashboard', __name__)

@ai_dashboard_bp.route('/status', methods=['GET'])
def get_ai_system_status():
    """Get overall AI system status"""
    try:
        # Get status from all AI components
        ml_status = ml_pipeline.get_model_performance_metrics()
        coaching_status = ai_trading_coach.get_ai_coaching_status()
        training_status = ai_training_worker.get_training_status()
        
        overall_status = {
            'ai_system_status': 'active',
            'timestamp': training_status.get('last_training_date'),
            'components': {
                'ml_pipeline': ml_status,
                'ai_coaching': coaching_status,
                'ai_training': training_status
            },
            'system_health': _calculate_system_health(ml_status, coaching_status, training_status)
        }
        
        return jsonify(overall_status)
        
    except Exception as e:
        logging.error(f"Error getting AI system status: {e}")
        return jsonify({'error': str(e)}), 500

@ai_dashboard_bp.route('/ml/models', methods=['GET'])
def get_ml_models():
    """Get ML model information and performance"""
    try:
        models_info = {
            'pattern_success_model': {
                'status': 'active' if ml_pipeline.pattern_success_model else 'not_trained',
                'performance': ml_pipeline.get_model_performance_metrics(),
                'features': [
                    'probability', 'match_score', 'pattern_type_encoded',
                    'entry_to_target_distance', 'entry_to_stop_distance', 'risk_reward_ratio',
                    'lock_to_buy_hours', 'buy_to_completion_hours',
                    'completion_day_of_week', 'completion_month', 'completion_hour'
                ],
                'model_type': 'RandomForest',
                'hyperparameters': {
                    'n_estimators': 100,
                    'max_depth': 10,
                    'random_state': 42,
                    'class_weight': 'balanced'
                }
            },
            'available_models': ['pattern_success_model', 'risk_assessment_model', 'market_regime_model'],
            'training_data_stats': _get_training_data_stats()
        }
        
        return jsonify(models_info)
        
    except Exception as e:
        logging.error(f"Error getting ML models: {e}")
        return jsonify({'error': str(e)}), 500

@ai_dashboard_bp.route('/ml/train', methods=['POST'])
def train_ml_models():
    """Trigger ML model training"""
    try:
        data = request.get_json() or {}
        force = data.get('force', False)
        
        if force:
            success = ai_training_worker.force_training()
        else:
            success = ai_training_worker.run_training()
        
        if success:
            return jsonify({
                'message': 'Training started successfully',
                'force_training': force,
                'status': 'training_in_progress'
            })
        else:
            return jsonify({
                'message': 'Training failed or skipped',
                'force_training': force,
                'status': 'training_failed'
            }), 400
            
    except Exception as e:
        logging.error(f"Error triggering ML training: {e}")
        return jsonify({'error': str(e)}), 500

@ai_dashboard_bp.route('/ml/performance', methods=['GET'])
def get_ml_performance():
    """Get detailed ML performance metrics"""
    try:
        performance = ml_pipeline.get_model_performance_metrics()
        
        if performance.get('error'):
            return jsonify(performance), 400
        
        # Add additional performance analysis
        enhanced_performance = {
            **performance,
            'performance_analysis': _analyze_performance(performance),
            'improvement_suggestions': _generate_improvement_suggestions(performance),
            'benchmark_comparison': _compare_to_benchmarks(performance)
        }
        
        return jsonify(enhanced_performance)
        
    except Exception as e:
        logging.error(f"Error getting ML performance: {e}")
        return jsonify({'error': str(e)}), 500

@ai_dashboard_bp.route('/patterns/ai-evaluation', methods=['POST'])
def evaluate_pattern_with_ai():
    """Evaluate a specific pattern using AI"""
    try:
        data = request.get_json()
        if not data or 'ticker' not in data:
            return jsonify({'error': 'ticker is required'}), 400
        
        ticker = data['ticker']
        pattern_name = data.get('pattern_name')
        
        if pattern_name:
            # Evaluate specific pattern
            result = ai_pattern_evaluator.evaluate_pattern(ticker, pattern_name)
        else:
            # Evaluate all patterns
            result = ai_pattern_evaluator.evaluate_all_patterns(ticker)
        
        return jsonify({
            'ticker': ticker,
            'pattern_name': pattern_name,
            'evaluation_result': result,
            'ai_enhanced': True
        })
        
    except Exception as e:
        logging.error(f"Error evaluating pattern with AI: {e}")
        return jsonify({'error': str(e)}), 500

@ai_dashboard_bp.route('/coaching/ai-narrative', methods=['POST'])
def generate_ai_narrative():
    """Generate AI-enhanced coaching narrative"""
    try:
        data = request.get_json()
        if not data or 'ticker' not in data:
            return jsonify({'error': 'ticker is required'}), 400
        
        ticker = data['ticker']
        narrative = ai_trading_coach.generate_ai_narrative(ticker)
        
        return jsonify({
            'ticker': ticker,
            'narrative': narrative.to_dict() if hasattr(narrative, 'to_dict') else narrative.__dict__,
            'ai_enhanced': True
        })
        
    except Exception as e:
        logging.error(f"Error generating AI narrative: {e}")
        return jsonify({'error': str(e)}), 500

@ai_dashboard_bp.route('/training/status', methods=['GET'])
def get_training_status():
    """Get AI training worker status"""
    try:
        status = ai_training_worker.get_training_status()
        return jsonify(status)
        
    except Exception as e:
        logging.error(f"Error getting training status: {e}")
        return jsonify({'error': str(e)}), 500

@ai_dashboard_bp.route('/training/configure', methods=['POST'])
def configure_training():
    """Configure AI training parameters"""
    try:
        data = request.get_json() or {}
        
        training_interval = data.get('training_interval_hours')
        data_collection_interval = data.get('data_collection_interval_minutes')
        performance_threshold = data.get('performance_threshold')
        
        ai_training_worker.update_training_parameters(
            training_interval_hours=training_interval,
            data_collection_interval_minutes=data_collection_interval,
            performance_threshold=performance_threshold
        )
        
        return jsonify({
            'message': 'Training parameters updated successfully',
            'new_config': {
                'training_interval_hours': training_interval,
                'data_collection_interval_minutes': data_collection_interval,
                'performance_threshold': performance_threshold
            }
        })
        
    except Exception as e:
        logging.error(f"Error configuring training: {e}")
        return jsonify({'error': str(e)}), 500

@ai_dashboard_bp.route('/insights/feature-importance', methods=['GET'])
def get_feature_importance():
    """Get feature importance from trained models"""
    try:
        if not ml_pipeline.pattern_success_model:
            return jsonify({'error': 'No trained model available'}), 400
        
        # Get feature importance from the model
        feature_importance = {}
        if hasattr(ml_pipeline.pattern_success_model, 'feature_importances_'):
            feature_names = [
                'probability', 'match_score', 'pattern_type_encoded',
                'entry_to_target_distance', 'entry_to_stop_distance', 'risk_reward_ratio',
                'lock_to_buy_hours', 'buy_to_completion_hours',
                'completion_day_of_week', 'completion_month', 'completion_hour'
            ]
            
            feature_importance = dict(zip(
                feature_names, 
                ml_pipeline.pattern_success_model.feature_importances_
            ))
        
        # Sort by importance
        sorted_features = sorted(
            feature_importance.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return jsonify({
            'feature_importance': dict(sorted_features),
            'top_features': sorted_features[:5],
            'total_features': len(feature_importance)
        })
        
    except Exception as e:
        logging.error(f"Error getting feature importance: {e}")
        return jsonify({'error': str(e)}), 500

@ai_dashboard_bp.route('/insights/pattern-analysis', methods=['GET'])
def get_pattern_analysis():
    """Get AI pattern analysis insights"""
    try:
        # Get pattern success rates by type
        pattern_analysis = _analyze_pattern_performance()
        
        return jsonify({
            'pattern_analysis': pattern_analysis,
            'ai_insights': _generate_pattern_insights(pattern_analysis),
            'recommendations': _generate_pattern_recommendations(pattern_analysis)
        })
        
    except Exception as e:
        logging.error(f"Error getting pattern analysis: {e}")
        return jsonify({'error': str(e)}), 500

def _calculate_system_health(ml_status: Dict, coaching_status: Dict, training_status: Dict) -> str:
    """Calculate overall system health"""
    try:
        health_score = 0
        total_checks = 0
        
        # Check ML pipeline
        if not ml_status.get('error'):
            health_score += 1
        total_checks += 1
        
        # Check coaching service
        if coaching_status.get('ai_system_active'):
            health_score += 1
        total_checks += 1
        
        # Check training worker
        if training_status.get('worker_status') == 'active':
            health_score += 1
        total_checks += 1
        
        health_percentage = health_score / total_checks
        
        if health_percentage >= 0.8:
            return 'excellent'
        elif health_percentage >= 0.6:
            return 'good'
        elif health_percentage >= 0.4:
            return 'fair'
        else:
            return 'poor'
            
    except Exception as e:
        logging.error(f"Error calculating system health: {e}")
        return 'unknown'

def _get_training_data_stats() -> Dict[str, Any]:
    """Get training data statistics"""
    try:
        training_data = ml_pipeline.prepare_training_data()
        
        if training_data.empty:
            return {'error': 'No training data available'}
        
        return {
            'total_samples': len(training_data),
            'success_rate': training_data['success'].mean() if 'success' in training_data.columns else 0,
            'pattern_distribution': training_data['pattern_type'].value_counts().to_dict() if 'pattern_type' in training_data.columns else {},
            'date_range': {
                'earliest': training_data['created_at'].min().isoformat() if 'created_at' in training_data.columns else None,
                'latest': training_data['created_at'].max().isoformat() if 'created_at' in training_data.columns else None
            }
        }
        
    except Exception as e:
        logging.error(f"Error getting training data stats: {e}")
        return {'error': str(e)}

def _analyze_performance(performance: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze performance metrics"""
    try:
        metrics = performance.get('performance_metrics', {})
        
        analysis = {
            'success_rate_analysis': _analyze_success_rate(metrics.get('success_rate', 0)),
            'profit_loss_analysis': _analyze_profit_loss(metrics.get('avg_profit_loss_percent', 0)),
            'hold_time_analysis': _analyze_hold_time(metrics.get('avg_hold_time_hours', 0))
        }
        
        return analysis
        
    except Exception as e:
        logging.error(f"Error analyzing performance: {e}")
        return {'error': str(e)}

def _analyze_success_rate(success_rate: float) -> Dict[str, Any]:
    """Analyze success rate performance"""
    if success_rate >= 0.7:
        return {'rating': 'excellent', 'description': 'High success rate indicates strong model performance'}
    elif success_rate >= 0.6:
        return {'rating': 'good', 'description': 'Good success rate with room for improvement'}
    elif success_rate >= 0.5:
        return {'rating': 'fair', 'description': 'Moderate success rate, consider retraining'}
    else:
        return {'rating': 'poor', 'description': 'Low success rate, immediate retraining recommended'}

def _analyze_profit_loss(avg_profit_loss: float) -> Dict[str, Any]:
    """Analyze profit/loss performance"""
    if avg_profit_loss > 0:
        return {'rating': 'profitable', 'description': f'Average profit: {avg_profit_loss:.2f}%'}
    else:
        return {'rating': 'losing', 'description': f'Average loss: {abs(avg_profit_loss):.2f}%'}

def _analyze_hold_time(avg_hold_time: float) -> Dict[str, Any]:
    """Analyze hold time performance"""
    if avg_hold_time <= 24:
        return {'rating': 'fast', 'description': 'Quick trades, good for capital efficiency'}
    elif avg_hold_time <= 72:
        return {'rating': 'moderate', 'description': 'Balanced hold time'}
    else:
        return {'rating': 'slow', 'description': 'Longer holds, consider shorter-term strategies'}

def _generate_improvement_suggestions(performance: Dict[str, Any]) -> List[str]:
    """Generate improvement suggestions based on performance"""
    suggestions = []
    
    try:
        metrics = performance.get('performance_metrics', {})
        success_rate = metrics.get('success_rate', 0)
        
        if success_rate < 0.6:
            suggestions.append("Consider retraining the model with more recent data")
            suggestions.append("Review and adjust feature engineering")
            suggestions.append("Increase training data diversity")
        
        if metrics.get('avg_profit_loss_percent', 0) < 0:
            suggestions.append("Review stop-loss and take-profit strategies")
            suggestions.append("Analyze market regime changes")
            suggestions.append("Consider position sizing optimization")
        
        if not suggestions:
            suggestions.append("Model performing well, continue monitoring")
            suggestions.append("Consider expanding to additional pattern types")
        
    except Exception as e:
        logging.error(f"Error generating improvement suggestions: {e}")
        suggestions = ["Unable to generate suggestions due to error"]
    
    return suggestions

def _compare_to_benchmarks(performance: Dict[str, Any]) -> Dict[str, Any]:
    """Compare performance to industry benchmarks"""
    try:
        metrics = performance.get('performance_metrics', {})
        success_rate = metrics.get('success_rate', 0)
        
        benchmarks = {
            'industry_average': 0.55,  # Typical trading strategy success rate
            'professional_trader': 0.65,  # Professional trader success rate
            'ai_enhanced_target': 0.75   # Target for AI-enhanced strategies
        }
        
        comparison = {
            'vs_industry': success_rate - benchmarks['industry_average'],
            'vs_professional': success_rate - benchmarks['professional_trader'],
            'vs_ai_target': success_rate - benchmarks['ai_enhanced_target'],
            'benchmarks': benchmarks
        }
        
        return comparison
        
    except Exception as e:
        logging.error(f"Error comparing to benchmarks: {e}")
        return {'error': str(e)}

def _analyze_pattern_performance() -> Dict[str, Any]:
    """Analyze pattern performance by type"""
    try:
        # This would ideally query the database for pattern performance
        # For now, return a placeholder structure
        return {
            'breakout_patterns': {'success_rate': 0.68, 'avg_profit': 0.045},
            'reversal_patterns': {'success_rate': 0.62, 'avg_profit': 0.038},
            'momentum_patterns': {'success_rate': 0.71, 'avg_profit': 0.052},
            'price_action_patterns': {'success_rate': 0.65, 'avg_profit': 0.041}
        }
        
    except Exception as e:
        logging.error(f"Error analyzing pattern performance: {e}")
        return {'error': str(e)}

def _generate_pattern_insights(pattern_analysis: Dict[str, Any]) -> List[str]:
    """Generate insights from pattern analysis"""
    insights = []
    
    try:
        if 'breakout_patterns' in pattern_analysis:
            breakout = pattern_analysis['breakout_patterns']
            if breakout['success_rate'] > 0.65:
                insights.append("Breakout patterns showing strong performance")
        
        if 'momentum_patterns' in pattern_analysis:
            momentum = pattern_analysis['momentum_patterns']
            if momentum['success_rate'] > 0.7:
                insights.append("Momentum patterns are the most reliable")
        
        if not insights:
            insights.append("All pattern types performing within expected ranges")
            
    except Exception as e:
        logging.error(f"Error generating pattern insights: {e}")
        insights = ["Unable to generate insights due to error"]
    
    return insights

def _generate_pattern_recommendations(pattern_analysis: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on pattern analysis"""
    recommendations = []
    
    try:
        if 'momentum_patterns' in pattern_analysis:
            momentum = pattern_analysis['momentum_patterns']
            if momentum['success_rate'] > 0.7:
                recommendations.append("Focus on momentum patterns for higher success rates")
        
        if 'reversal_patterns' in pattern_analysis:
            reversal = pattern_analysis['reversal_patterns']
            if reversal['success_rate'] < 0.65:
                recommendations.append("Review reversal pattern criteria for improvement")
        
        if not recommendations:
            recommendations.append("Maintain current pattern selection strategy")
            
    except Exception as e:
        logging.error(f"Error generating pattern recommendations: {e}")
        recommendations = ["Unable to generate recommendations due to error"]
    
    return recommendations
