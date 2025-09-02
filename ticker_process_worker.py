import logging
import time
from config.logging import setup_logging
from services.redis_manager import redis_manager

def run(ticker):
    setup_logging(file_name=f'{ticker}/ticker_process_worker.log')

    while True:
        try:
            ret, data = redis_manager.remove_old_tick(ticker)
            if not ret:
                time.sleep(1)
                continue
            if data:
                logging.info(f"Removed {data} old tick data from {ticker}")
                
        except Exception as e:
            logging.error(f"Error in aggregate worker: {e}", exc_info=True)
        
        time.sleep(1)