import logging
import time
from services.redis_manager import redis_manager
from config.logging import setup_logging
from services.technical_service import update_technical_indicators

def run(ticker):
    setup_logging(file_name=f'{ticker}/technical_indicators_worker.log')

    prev_last_candle = None
    prev_timestamp = None
    while True:
        try:
            last_candle = redis_manager.get_last_minute_candle(ticker)

            if last_candle is None:
                time.sleep(1)
                continue

            #
            if (
                (prev_last_candle and last_candle['close'] == prev_last_candle['close'] and last_candle['volume'] == prev_last_candle['volume']) or
                (prev_timestamp and time.time() - prev_timestamp < 5)
            ):
                time.sleep(1)
                continue
            
            prev_last_candle = last_candle
            prev_timestamp = time.time()

            update_technical_indicators(ticker)
            redis_manager.publish('socket_emit', {
                'event': 'indicators',
                'data': {
                    'ticker': ticker,
                    'indicators': redis_manager.get_technical_indicators(ticker)
                }
            })
            redis_manager.publish('socket_emit', {
                'event': 'scores',
                'data': {
                    'ticker': ticker,
                    'scores': redis_manager.get_technical_scores(ticker)
                }
            })
            logging.info(f"Technical indicators updated for {ticker} for {last_candle}")
        except Exception as e:
            logging.error(f"Error in technical indicators worker {ticker}: {e}")
        time.sleep(1)
