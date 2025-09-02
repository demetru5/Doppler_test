import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logging(log_level=logging.INFO, file_name=None):
    """Configure application logging with rotation and proper formatting"""
    # Create logs directory if it doesn't exist
    current_date = datetime.now().strftime('%Y_%m_%d')
    log_dir = f"logs/{current_date}"
    os.makedirs(log_dir, exist_ok=True)
    
    # Generate log filename with date
    log_file = os.path.join(log_dir, f"app.log") if file_name is None else os.path.join(log_dir, f"{file_name}")
    # Ensure the full directory for the log file exists
    log_file_dir = os.path.dirname(log_file)
    os.makedirs(log_file_dir, exist_ok=True)
    # check exists and create if not
    if not os.path.exists(log_file):
        with open(log_file, 'w') as f:
            f.write('')
    
    # Create formatters
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )
    
    # Create and configure file handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(log_level)
    
    # Create and configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(log_level)
    
    # Get the root logger and configure it
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove any existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add the handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Log the setup
    root_logger.info(f"Logging configured with level {logging.getLevelName(log_level)}")
    root_logger.info(f"Log file: {log_file}")
    
    return root_logger
