import logging
import time
import pandas as pd
from config.logging import setup_logging
from services.redis_manager import redis_manager

def run(ticker):
    setup_logging(file_name=f'{ticker}/candlestick_process_worker.log')

    while True:
        try:
            candlestick_data = redis_manager.pop_candlestick(ticker)
            if not candlestick_data:
                time.sleep(0.1)
                continue
            
            df = pd.DataFrame(candlestick_data)
            agg_df = df.groupby('timestamp').agg(
                open=('open', 'last'),
                high=('high', 'last'),
                low=('low', 'last'),
                close=('close', 'last'), 
                volume=('volume', 'last'),
                timestamp=('timestamp', 'last')
            )
            
            if agg_df.empty:
                time.sleep(0.1)
                continue

            for _, row in agg_df.iterrows():
                redis_manager.update_candle_by_timestamp(ticker, {
                    'timestamp': row['timestamp'],
                    'open': row['open'],
                    'high': row['high'],
                    'low': row['low'],
                    'close': row['close'],
                    'volume': row['volume']
                })
                logging.info(f"Candlestick processed: {row['timestamp']} {row['open']} {row['high']} {row['low']} {row['close']} {row['volume']}")
                
        except Exception as e:
            logging.error(f"Error in aggregate worker: {e}", exc_info=True)
        
        time.sleep(0.1)