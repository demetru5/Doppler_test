import logging
import time
import schedule
from datetime import datetime, timedelta
from typing import Dict, Any, List
from services.ml_pipeline import ml_pipeline
from services.redis_manager import redis_manager
from core.db import get_db, StrategyHistory
from patterns.ai_pattern_evaluator import ai_pattern_evaluator

logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Define the logging format
    datefmt='%Y-%m-%d %H:%M:%S'  # Define the date format
)

class AITrainingWorker:
    """AI Training Worker for Continuous Model Improvement"""
    
    def __init__(self):
        self.training_interval_hours = 24  # Retrain every 24 hours
        self.data_collection_interval_minutes = 30  # Collect data every 30 minutes
        self.performance_threshold = 0.7  # Minimum performance threshold
        self.last_training_date = None
        self.last_data_collection = None
        
        # Initialize AI components
        self.ml_pipeline = ml_pipeline
        self.ai_pattern_evaluator = ai_pattern_evaluator
        
        # Training statistics
        self.training_stats = {
            'total_training_runs': 0,
            'successful_training_runs': 0,
            'failed_training_runs': 0,
            'last_training_accuracy': 0.0,
            'best_training_accuracy': 0.0,
            'model_improvement_count': 0,
            'last_training_duration': 0.0
        }
        
        logging.info("AI Training Worker initialized")
    
    def start(self):
        """Start the AI training worker"""
        try:
            logging.info("Starting AI Training Worker...")
            
            # Schedule training tasks
            schedule.every(self.training_interval_hours).hours.do(self.scheduled_training)
            schedule.every(self.data_collection_interval_minutes).minutes.do(self.collect_training_data)
            
            # Run initial training if no model exists
            if not self.ml_pipeline.pattern_success_model:
                logging.info("No existing model found, running initial training...")
                self.run_training()
            
            # Start the scheduler
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logging.info("AI Training Worker stopped by user")
        except Exception as e:
            logging.error(f"AI Training Worker error: {e}")
            raise
    
    def run_training(self, force: bool = False) -> bool:
        """Run AI model training"""
        try:
            start_time = time.time()
            logging.info("Starting AI model training...")
            
            # Check if training is needed
            if not force and self._should_skip_training():
                logging.info("Skipping training - conditions not met")
                return False
            
            # Prepare training data
            logging.info("Preparing training data...")
            training_data = self.ml_pipeline.prepare_training_data()
            
            if training_data.empty:
                logging.warning("No training data available")
                return False
            
            logging.info(f"Training data prepared: {len(training_data)} samples")
            
            # Run training
            training_success = self.ml_pipeline.train_pattern_success_model(force_retrain=force)
            
            if training_success:
                # Evaluate new model performance
                performance_metrics = self.ml_pipeline.get_model_performance_metrics()
                
                # Update training statistics
                training_duration = time.time() - start_time
                self._update_training_stats(True, performance_metrics, training_duration)
                
                logging.info(f"Training completed successfully in {training_duration:.2f} seconds")
                logging.info(f"Model performance: {performance_metrics}")
                
                # Check if model improved
                if self._check_model_improvement(performance_metrics):
                    logging.info("Model performance improved! 🎉")
                    self.training_stats['model_improvement_count'] += 1
                
                self.last_training_date = datetime.now()
                return True
            else:
                self._update_training_stats(False, {}, time.time() - start_time)
                logging.error("Training failed")
                return False
                
        except Exception as e:
            logging.error(f"Error during training: {e}")
            self._update_training_stats(False, {}, time.time() - start_time)
            return False
    
    def scheduled_training(self):
        """Scheduled training task"""
        try:
            logging.info("Running scheduled training...")
            self.run_training()
        except Exception as e:
            logging.error(f"Error in scheduled training: {e}")
    
    def collect_training_data(self):
        """Collect new training data from completed strategies"""
        try:
            logging.info("Collecting training data...")
            
            with get_db() as db:
                # Get recently completed strategies
                cutoff_time = datetime.now() - timedelta(hours=1)
                recent_strategies = db.query(StrategyHistory).filter(
                    StrategyHistory.completion_time >= cutoff_time
                ).all()
                
                if recent_strategies:
                    logging.info(f"Collected {len(recent_strategies)} new strategy records")
                    
                    # Store data collection timestamp
                    self.last_data_collection = datetime.now()
                    
                    # Trigger training if we have enough new data
                    if len(recent_strategies) >= 10:  # Threshold for new training
                        logging.info("Sufficient new data collected, triggering training...")
                        self.run_training()
                else:
                    logging.debug("No new strategy data to collect")
                    
        except Exception as e:
            logging.error(f"Error collecting training data: {e}")
    
    def _should_skip_training(self) -> bool:
        """Determine if training should be skipped"""
        try:
            # Skip if we trained recently
            if self.last_training_date:
                time_since_training = datetime.now() - self.last_training_date
                if time_since_training.total_seconds() < self.training_interval_hours * 3600:
                    return True
            
            # Skip if model performance is already good
            if self.ml_pipeline.pattern_success_model:
                performance = self.ml_pipeline.get_model_performance_metrics()
                if not performance.get('error'):
                    current_accuracy = performance.get('performance_metrics', {}).get('success_rate', 0)
                    if current_accuracy >= self.performance_threshold:
                        logging.info(f"Model performance ({current_accuracy:.1%}) above threshold, skipping training")
                        return True
            
            return False
            
        except Exception as e:
            logging.error(f"Error checking if training should be skipped: {e}")
            return False
    
    def _update_training_stats(self, success: bool, performance_metrics: Dict[str, Any], duration: float):
        """Update training statistics"""
        try:
            self.training_stats['total_training_runs'] += 1
            
            if success:
                self.training_stats['successful_training_runs'] += 1
                
                # Update accuracy metrics
                if performance_metrics and not performance_metrics.get('error'):
                    current_accuracy = performance_metrics.get('performance_metrics', {}).get('success_rate', 0)
                    self.training_stats['last_training_accuracy'] = current_accuracy
                    
                    if current_accuracy > self.training_stats['best_training_accuracy']:
                        self.training_stats['best_training_accuracy'] = current_accuracy
            else:
                self.training_stats['failed_training_runs'] += 1
            
            self.training_stats['last_training_duration'] = duration
            
            # Log statistics
            logging.info(f"Training stats updated: {self.training_stats}")
            
        except Exception as e:
            logging.error(f"Error updating training stats: {e}")
    
    def _check_model_improvement(self, performance_metrics: Dict[str, Any]) -> bool:
        """Check if the new model shows improvement"""
        try:
            if not performance_metrics or performance_metrics.get('error'):
                return False
            
            current_accuracy = performance_metrics.get('performance_metrics', {}).get('success_rate', 0)
            previous_accuracy = self.training_stats['last_training_accuracy']
            
            # Check if accuracy improved by at least 1%
            if current_accuracy > previous_accuracy + 0.01:
                logging.info(f"Model improved: {previous_accuracy:.1%} -> {current_accuracy:.1%}")
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"Error checking model improvement: {e}")
            return False
    
    def get_training_status(self) -> Dict[str, Any]:
        """Get current training status and statistics"""
        try:
            return {
                'worker_status': 'active',
                'last_training_date': self.last_training_date.isoformat() if self.last_training_date else None,
                'last_data_collection': self.last_data_collection.isoformat() if self.last_data_collection else None,
                'training_interval_hours': self.training_interval_hours,
                'data_collection_interval_minutes': self.data_collection_interval_minutes,
                'training_statistics': self.training_stats,
                'model_status': self.ml_pipeline.get_model_performance_metrics(),
                'next_scheduled_training': self._get_next_training_time()
            }
        except Exception as e:
            logging.error(f"Error getting training status: {e}")
            return {'error': str(e)}
    
    def _get_next_training_time(self) -> str:
        """Get the next scheduled training time"""
        try:
            if self.last_training_date:
                next_training = self.last_training_date + timedelta(hours=self.training_interval_hours)
                return next_training.isoformat()
            return "Not scheduled"
        except Exception as e:
            logging.error(f"Error calculating next training time: {e}")
            return "Unknown"
    
    def force_training(self) -> bool:
        """Force immediate training regardless of conditions"""
        try:
            logging.info("Force training requested...")
            return self.run_training(force=True)
        except Exception as e:
            logging.error(f"Error in force training: {e}")
            return False
    
    def update_training_parameters(self, training_interval_hours: int = None, 
                                 data_collection_interval_minutes: int = None,
                                 performance_threshold: float = None):
        """Update training parameters"""
        try:
            if training_interval_hours is not None:
                self.training_interval_hours = training_interval_hours
                logging.info(f"Training interval updated to {training_interval_hours} hours")
            
            if data_collection_interval_minutes is not None:
                self.data_collection_interval_minutes = data_collection_interval_minutes
                logging.info(f"Data collection interval updated to {data_collection_interval_minutes} minutes")
            
            if performance_threshold is not None:
                self.performance_threshold = performance_threshold
                logging.info(f"Performance threshold updated to {performance_threshold}")
            
            # Reschedule tasks with new parameters
            schedule.clear()
            schedule.every(self.training_interval_hours).hours.do(self.scheduled_training)
            schedule.every(self.data_collection_interval_minutes).minutes.do(self.collect_training_data)
            
            logging.info("Training parameters updated and tasks rescheduled")
            
        except Exception as e:
            logging.error(f"Error updating training parameters: {e}")
    
    def stop(self):
        """Stop the AI training worker"""
        try:
            logging.info("Stopping AI Training Worker...")
            schedule.clear()
            logging.info("AI Training Worker stopped")
        except Exception as e:
            logging.error(f"Error stopping AI Training Worker: {e}")

# Global instance
ai_training_worker = AITrainingWorker()

if __name__ == "__main__":
    # Start the worker
    ai_training_worker.start()
