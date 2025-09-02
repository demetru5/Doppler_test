import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, accuracy_score, precision_recall_fscore_support
from sklearn.pipeline import Pipeline
import joblib
import os
from datetime import datetime, timedelta
from core.db import get_db, StrategyHistory
from services.redis_manager import redis_manager
from utils.util import get_current_session

logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Define the logging format
    datefmt='%Y-%m-%d %H:%M:%S'  # Define the date format
)

class MLPipeline:
    """Machine Learning Pipeline for Trading Strategy Optimization"""
    
    def __init__(self):
        self.models_dir = "models"
        self.scalers_dir = "scalers"
        self.encoders_dir = "encoders"
        
        # Create directories if they don't exist
        for directory in [self.models_dir, self.scalers_dir, self.encoders_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # Initialize models
        self.pattern_success_model = None
        self.risk_assessment_model = None
        self.market_regime_model = None
        
        # Initialize scalers and encoders
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        
        # Load existing models if available
        self._load_models()
    
    def _load_models(self):
        """Load pre-trained models if they exist"""
        try:
            if os.path.exists(f"{self.models_dir}/pattern_success_model.pkl"):
                self.pattern_success_model = joblib.load(f"{self.models_dir}/pattern_success_model.pkl")
                logging.info("Loaded existing pattern success model")
            
            if os.path.exists(f"{self.scalers_dir}/scaler.pkl"):
                self.scaler = joblib.load(f"{self.scalers_dir}/scaler.pkl")
                logging.info("Loaded existing scaler")
            
            if os.path.exists(f"{self.models_dir}/feature_names.pkl"):
                self.feature_names = joblib.load(f"{self.models_dir}/feature_names.pkl")
                logging.info("Loaded feature names")
                
        except Exception as e:
            logging.warning(f"Could not load existing models: {e}")
    
    def prepare_training_data(self, days_back: int = 180) -> pd.DataFrame:
        """Prepare training data from strategy history"""
        try:
            with get_db() as db:
                # Get strategy history from database
                cutoff_date = datetime.now() - timedelta(days=days_back)
                strategies = db.query(StrategyHistory).filter(
                    StrategyHistory.created_at >= cutoff_date,
                    StrategyHistory.session != None,
                    StrategyHistory.session != 'closed'
                ).all()
                
                if not strategies:
                    logging.warning("No strategy history found for training")
                    return pd.DataFrame()
                
                # Convert to DataFrame
                data = []
                for strategy in strategies:
                    strategy_dict = {
                        'ticker': strategy.ticker,
                        'strategy_name': strategy.strategy_name,
                        'entry_price': strategy.entry_price,
                        'target_price': strategy.target_price,
                        'stop_price': strategy.stop_price,
                        'probability': strategy.probability,
                        'match_score': strategy.match_score,
                        'pattern_type': strategy.pattern_type,
                        'completion_type': strategy.completion_type,
                        'profit_loss': strategy.profit_loss,
                        'profit_loss_percent': strategy.profit_loss_percent,
                        'lock_time': strategy.lock_time,
                        'buy_time': strategy.buy_time,
                        'completion_time': strategy.completion_time,
                        'created_at': strategy.created_at,
                        'VWAP': strategy.VWAP,
                        'RSI': strategy.RSI,
                        'StochRSI_K': strategy.StochRSI_K,
                        'StochRSI_D': strategy.StochRSI_D,
                        'MACD': strategy.MACD,
                        'MACD_signal': strategy.MACD_signal,
                        'MACD_hist': strategy.MACD_hist,
                        'ADX': strategy.ADX,
                        'DMP': strategy.DMP,
                        'DMN': strategy.DMN,
                        'Supertrend': strategy.Supertrend,
                        'Trend': strategy.Trend,
                        'PSAR_L': strategy.PSAR_L,
                        'PSAR_S': strategy.PSAR_S,
                        'PSAR_R': strategy.PSAR_R,
                        'EMA200': strategy.EMA200,
                        'EMA21': strategy.EMA21,
                        'EMA9': strategy.EMA9,
                        'EMA4': strategy.EMA4,
                        'EMA5': strategy.EMA5,
                        'VWAP_Slope': strategy.VWAP_Slope,
                        'Volume_Ratio': strategy.Volume_Ratio,
                        'ROC': strategy.ROC,
                        'Williams_R': strategy.Williams_R,
                        'ATR': strategy.ATR,
                        'HOD': strategy.HOD,
                        'ATR_to_HOD': strategy.ATR_to_HOD,
                        'ATR_to_VWAP': strategy.ATR_to_VWAP,
                        'ZenP': strategy.ZenP,
                        'RVol': strategy.RVol,
                        'BB_lower': strategy.BB_lower,
                        'BB_mid': strategy.BB_mid,
                        'BB_upper': strategy.BB_upper,
                        'ATR_Spread': strategy.ATR_Spread,
                        'session': strategy.session,
                    }
                    data.append(strategy_dict)
                
                df = pd.DataFrame(data)
                
                # Add derived features
                df = self._add_derived_features(df)
                
                return df
                
        except Exception as e:
            logging.error(f"Error preparing training data: {e}")
            return pd.DataFrame()
    
    def _add_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add derived features for ML training"""
        try:
            # Time-based features
            df['lock_to_buy_hours'] = df.apply(
                lambda x: (pd.to_datetime(x['buy_time']) - pd.to_datetime(x['lock_time'])).total_seconds() / 3600 
                if pd.notna(x['buy_time']) and pd.notna(x['lock_time']) else 0, axis=1
            )
            
            df['buy_to_completion_hours'] = df.apply(
                lambda x: (pd.to_datetime(x['completion_time']) - pd.to_datetime(x['buy_time'])).total_seconds() / 3600 
                if pd.notna(x['buy_time']) and pd.notna(x['completion_time']) else 0, axis=1
            )
            
            # Price-based features
            df['entry_to_target_distance'] = (df['target_price'] - df['entry_price']) / df['entry_price']
            df['entry_to_stop_distance'] = (df['entry_price'] - df['stop_price']) / df['entry_price']
            df['risk_reward_ratio'] = df['entry_to_target_distance'] / df['entry_to_stop_distance']
            
            # Strategy success label
            df['success'] = df['completion_type'].apply(
                lambda x: 1 if x == 'target' else 0
            )
            
            # Pattern type encoding
            df['pattern_type_encoded'] = self.label_encoder.fit_transform(
                df['pattern_type'].fillna('unknown')
            )
            
            # Session encoding
            df['session_encoded'] = df['session'].apply(self._encode_session)
            
            return df
            
        except Exception as e:
            logging.error(f"Error adding derived features: {e}")
            return df
    
    def train_pattern_success_model(self, force_retrain: bool = False) -> bool:
        """Train the pattern success prediction model"""
        try:
            if self.pattern_success_model and not force_retrain:
                logging.info("Pattern success model already exists, skipping training")
                return True
            
            # Prepare training data
            df = self.prepare_training_data()
            if df.empty:
                logging.error("No training data available")
                return False

            df = df.replace([np.inf, -np.inf], np.nan)

            # Select features for training - now including technical indicators
            feature_columns = [
                # Strategy features
                'probability', 'match_score', 'pattern_type_encoded',
                'entry_to_target_distance', 'entry_to_stop_distance', 'risk_reward_ratio',
                'lock_to_buy_hours', 'buy_to_completion_hours', 'session_encoded',
                # Technical indicator features
                'VWAP', 'RSI', 'StochRSI_K', 'StochRSI_D', 'MACD', 'MACD_signal', 'MACD_hist', 'ADX', 'DMP', 'DMN', 'Supertrend', 'Trend', 'PSAR_L', 'PSAR_S', 'PSAR_R', 'EMA200', 'EMA21', 'EMA9', 'EMA4', 'EMA5', 'VWAP_Slope', 'Volume_Ratio', 'ROC', 'Williams_R', 'ATR', 'HOD', 'ATR_to_HOD', 'ATR_to_VWAP', 'ZenP', 'RVol', 'BB_lower', 'BB_mid', 'BB_upper', 'ATR_Spread'
            ]
            
            # Filter to only include columns that exist in the dataframe
            available_features = [col for col in feature_columns if col in df.columns]
            
            X = df[available_features].fillna(0)
            y = df['success']
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            self.pattern_success_model = RandomForestClassifier(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                class_weight='balanced',
                n_jobs=-1  # Use all available cores
            )
            
            self.pattern_success_model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = self.pattern_success_model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='weighted')
            
            logging.info(f"Pattern success model trained successfully:")
            logging.info(f"Features used: {len(available_features)}")
            logging.info(f"Accuracy: {accuracy:.3f}")
            logging.info(f"Precision: {precision:.3f}")
            logging.info(f"Recall: {recall:.3f}")
            logging.info(f"F1-Score: {f1:.3f}")
            
            # Save model and scaler
            joblib.dump(self.pattern_success_model, f"{self.models_dir}/pattern_success_model.pkl")
            joblib.dump(self.scaler, f"{self.scalers_dir}/scaler.pkl")
            
            # Save feature names for later use
            self.feature_names = available_features
            joblib.dump(available_features, f"{self.models_dir}/feature_names.pkl")
            
            return True
            
        except Exception as e:
            logging.error(f"Error training pattern success model: {e}")
            return False
    
    def predict_pattern_success(self, ticker: str, strategy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict the success probability of a pattern/strategy"""
        try:
            if not self.pattern_success_model:
                logging.warning("Pattern success model not trained, using fallback")
                return self._fallback_probability_prediction(ticker, strategy_data)
            
            # Prepare features for prediction
            features = self._prepare_prediction_features(ticker, strategy_data)
            if not features:
                return self._fallback_probability_prediction(ticker, strategy_data)
            
            # Ensure feature count matches training features
            if hasattr(self, 'feature_names') and len(features) != len(self.feature_names):
                logging.warning(f"Feature count mismatch: expected {len(self.feature_names)}, got {len(features)}")
                # Truncate or pad features to match
                if len(features) > len(self.feature_names):
                    features = features[:len(self.feature_names)]
                else:
                    features.extend([0] * (len(self.feature_names) - len(features)))
            
            # Scale features
            features_scaled = self.scaler.transform([features])
            
            # Make prediction
            prediction = self.pattern_success_model.predict(features_scaled)[0]
            probabilities = self.pattern_success_model.predict_proba(features_scaled)[0]
            
            # Get feature importance if available
            feature_importance = {}
            if hasattr(self.pattern_success_model, 'feature_importances_'):
                feature_names = getattr(self, 'feature_names', [f'feature_{i}' for i in range(len(features))])
                feature_importance = dict(zip(feature_names, self.pattern_success_model.feature_importances_))
            
            return {
                'predicted_success': prediction,
                'success_probability': probabilities[1] if len(probabilities) > 1 else 0.5,
                'confidence_score': max(probabilities),
                'feature_importance': feature_importance,
                'ml_model_used': True,
                'features_used': len(features)
            }
            
        except Exception as e:
            logging.error(f"Error predicting pattern success: {e}")
            return self._fallback_probability_prediction(ticker, strategy_data)
    
    def _prepare_prediction_features(self, ticker: str, strategy_data: Dict[str, Any]) -> Optional[List[float]]:
        """Prepare features for ML prediction with proper technical indicators"""
        try:
            # Get current technical indicators
            indicators = redis_manager.get_technical_indicators(ticker)
            
            # Get current session
            session = get_current_session()
            
            # Build feature vector matching training features
            features = [
                # Strategy features
                strategy_data.get('probability', 0.65),
                strategy_data.get('match_score', 70),
                self._encode_pattern_type(strategy_data.get('pattern_type', 'unknown')),
                strategy_data.get('entry_to_target_distance', 0.05),
                strategy_data.get('entry_to_stop_distance', 0.03),
                strategy_data.get('risk_reward_ratio', 1.67),
                0,  # lock_to_buy_hours (will be updated when strategy is executed)
                0,  # buy_to_completion_hours (will be updated when strategy is completed)
                self._encode_session(session),  # Encode session to numeric value
                # Technical indicator features
                indicators.get('VWAP', 0),
                indicators.get('RSI', 0),
                indicators.get('StochRSI_K', 0),
                indicators.get('StochRSI_D', 0),
                indicators.get('MACD', 0),
                indicators.get('MACD_signal', 0),
                indicators.get('MACD_hist', 0),
                indicators.get('ADX', 0),
                indicators.get('DMP', 0),
                indicators.get('DMN', 0),
                indicators.get('Supertrend', 0),
                indicators.get('Trend', 0),
                indicators.get('PSAR_L', 0),
                indicators.get('PSAR_S', 0),
                indicators.get('PSAR_R', 0),
                indicators.get('EMA200', 0),
                indicators.get('EMA21', 0),
                indicators.get('EMA9', 0),
                indicators.get('EMA4', 0),
                indicators.get('EMA5', 0),
                indicators.get('VWAP_Slope', 0),
                indicators.get('Volume_Ratio', 0),
                indicators.get('ROC', 0),
                indicators.get('Williams_R', 0),
                indicators.get('ATR', 0),
                indicators.get('HOD', 0),
                indicators.get('ATR_to_HOD', 0),
                indicators.get('ATR_to_VWAP', 0),
                indicators.get('ZenP', 0),
                indicators.get('RVol', 0),
                indicators.get('BB_lower', 0),
                indicators.get('BB_mid', 0),
                indicators.get('BB_upper', 0),
                indicators.get('ATR_Spread', 0),
            ]
            
            return features
            
        except Exception as e:
            logging.error(f"Error preparing prediction features: {e}")
            return None
    
    def _encode_pattern_type(self, pattern_type: str) -> int:
        """Encode pattern type to numeric value"""
        try:
            if not hasattr(self, '_pattern_type_mapping'):
                self._pattern_type_mapping = {
                    'breakout': 0, 'reversal': 1, 'momentum': 2, 
                    'price_action': 3, 'unknown': 4
                }
            return self._pattern_type_mapping.get(pattern_type, 4)
        except:
            return 4
    
    def _encode_session(self, session: str) -> int:
        """Encode session to numeric value"""
        try:
            if not hasattr(self, '_session_mapping'):
                self._session_mapping = {
                    'premarket': 0,
                    'regular': 1, 
                    'afterhours': 2,
                    'unknown': 3
                }
            return self._session_mapping.get(session, 3)
        except:
            return 3
    
    def _fallback_probability_prediction(self, ticker: str, strategy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback probability prediction when ML model is not available"""
        try:
            # Use existing probability calculation as fallback
            base_probability = strategy_data.get('probability', 0.65)
            match_score = strategy_data.get('match_score', 70)
            
            # Simple adjustment based on match score
            adjusted_probability = base_probability * (match_score / 100)
            
            return {
                'predicted_success': 1 if adjusted_probability > 0.6 else 0,
                'success_probability': adjusted_probability,
                'confidence_score': 0.5,
                'feature_importance': {},
                'ml_model_used': False
            }
            
        except Exception as e:
            logging.error(f"Error in fallback prediction: {e}")
            return {
                'predicted_success': 1,
                'success_probability': 0.65,
                'confidence_score': 0.5,
                'feature_importance': {},
                'ml_model_used': False
            }
    
    def get_model_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the trained models"""
        try:
            if not self.pattern_success_model:
                return {'error': 'No trained models available'}
            
            # Get recent predictions vs actual outcomes
            recent_strategies = self._get_recent_completed_strategies()
            
            if not recent_strategies:
                return {'error': 'No recent strategies for evaluation'}
            
            # Calculate metrics
            metrics = self._calculate_performance_metrics(recent_strategies)
            
            # Add model information
            model_info = {
                'model_type': 'RandomForest',
                'last_training_date': self._get_last_training_date(),
                'performance_metrics': metrics,
                'model_status': 'active',
                'features_count': len(getattr(self, 'feature_names', [])),
                'feature_names': getattr(self, 'feature_names', [])
            }
            
            return model_info
            
        except Exception as e:
            logging.error(f"Error getting model performance metrics: {e}")
            return {'error': str(e)}
    
    def _get_recent_completed_strategies(self, days: int = 30) -> List[Dict]:
        """Get recent completed strategies for performance evaluation"""
        try:
            with get_db() as db:
                cutoff_date = datetime.now() - timedelta(days=days)
                strategies = db.query(StrategyHistory).filter(
                    StrategyHistory.completion_time >= cutoff_date
                ).all()
                
                return [strategy.__dict__ for strategy in strategies]
                
        except Exception as e:
            logging.error(f"Error getting recent strategies: {e}")
            return []
    
    def _calculate_performance_metrics(self, strategies: List[Dict]) -> Dict[str, Any]:
        """Calculate performance metrics for recent strategies"""
        try:
            if not strategies:
                return {}
            
            total_strategies = len(strategies)
            successful_strategies = len([s for s in strategies if s.get('completion_type') == 'target'])
            success_rate = successful_strategies / total_strategies if total_strategies > 0 else 0
            
            avg_profit_loss = np.mean([s.get('profit_loss_percent', 0) for s in strategies])
            avg_hold_time = np.mean([
                (pd.to_datetime(s.get('completion_time')) - pd.to_datetime(s.get('buy_time'))).total_seconds() / 3600
                for s in strategies if s.get('buy_time') and s.get('completion_time')
            ])
            
            return {
                'total_strategies': total_strategies,
                'success_rate': success_rate,
                'avg_profit_loss_percent': avg_profit_loss,
                'avg_hold_time_hours': avg_hold_time,
                'evaluation_period_days': 30
            }
            
        except Exception as e:
            logging.error(f"Error calculating performance metrics: {e}")
            return {}
    
    def _get_last_training_date(self) -> Optional[str]:
        """Get the last training date for the model"""
        try:
            model_path = f"{self.models_dir}/pattern_success_model.pkl"
            if os.path.exists(model_path):
                return datetime.fromtimestamp(os.path.getmtime(model_path)).isoformat()
            return None
        except:
            return None

# Global instance
ml_pipeline = MLPipeline()
