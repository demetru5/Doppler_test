import logging
import time
from services.redis_manager import redis_manager
from services.trading_coach_service import trading_coach_service
from services.strategy_service import strategy_service
from config.logging import setup_logging

def run(ticker):
    setup_logging(file_name=f'{ticker}/pattern_evaluation_worker.log')
    
    previous_close = 0
    previous_volume = 0
    while True:
        try:
            price = redis_manager.get_stock_price(ticker)
            volume = redis_manager.get_stock_volume(ticker)

            if price is None or volume is None:
                time.sleep(1)
                continue
            
            if price == previous_close and volume == previous_volume:
                time.sleep(1)
                continue

            previous_close = price
            previous_volume = volume
            logging.info(f"Price: {price}, Volume: {volume}")

            strategy_service.evaluate_strategy_lock(ticker)

            coaching_narrative = trading_coach_service.generate_narrative(ticker)
            redis_manager.publish('socket_emit', {
                'event': 'coaching_narrative',
                'data': {
                    'ticker': ticker,
                    'narrative': coaching_narrative.to_dict()
                }
            })
                        
        except Exception as e:
            logging.error(f"Fatal error in pattern evaluation worker for {ticker}: {e}")

        time.sleep(1)