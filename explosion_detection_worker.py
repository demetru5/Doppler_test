import logging
import time
import pandas as pd
from services.redis_manager import redis_manager
from config.logging import setup_logging

def run(ticker):
    setup_logging(file_name=f'{ticker}/explosion_detection_worker.log')

    while True:
        try:
            tick_data = redis_manager.get_tick(ticker)

            tick_data_20_sec = [tick for tick in tick_data if pd.to_datetime(tick['time']) > pd.to_datetime(tick_data[-1]['time']) - pd.Timedelta(seconds=20)]
            if not tick_data_20_sec or len(tick_data) < 10:
                logging.info(f"No sufficient tick data")
                redis_manager.set_explosion_emoji_status(ticker, False)
                time.sleep(1)
                continue
            price_change_rate = (tick_data_20_sec[-1]['price'] - tick_data_20_sec[0]['price']) / tick_data_20_sec[0]['price'] if tick_data_20_sec[0]['price'] != 0 else 0
            
            # 1. Price change rate
            if price_change_rate < 0.05:
                logging.info(f"No extreme price change rate: {price_change_rate * 100}%")
                redis_manager.set_explosion_emoji_status(ticker, False)
                time.sleep(1)
                continue

            # 2. Volume acceleration rate
            first_half_volume = sum([tick['volume'] for tick in tick_data[-10:-5]])
            second_half_volume = sum([tick['volume'] for tick in tick_data[-5:]])
            if first_half_volume == 0 or second_half_volume / first_half_volume < 2:
                logging.info(f"No extreme volume")
                redis_manager.set_explosion_emoji_status(ticker, False)
                time.sleep(1)
                continue

            # 3. RVOL
            if redis_manager.get_technical_indicator(ticker, 'RVol', 1) < 5.0:
                logging.info(f"No extreme volume change rate: {redis_manager.get_technical_indicator(ticker, 'RVol', 1)}")
                redis_manager.set_explosion_emoji_status(ticker, False)
                time.sleep(1)
                continue
            
            # 4. Bid dominating
            orderbook = redis_manager.get_last_orderbook_snapshot(ticker)
            if not orderbook or orderbook.get('imbalance') < 0.8:
                logging.info(f"No bid dominating: {orderbook.get('imbalance')}")
                redis_manager.set_explosion_emoji_status(ticker, False)
                time.sleep(1)
                continue

            # 5. Price above VWAP
            if not (redis_manager.get_stock_price(ticker) > redis_manager.get_technical_indicator(ticker, 'VWAP', 1) > 0):
                logging.info(f"No price above vwap {redis_manager.get_stock_price(ticker)} {redis_manager.get_technical_indicator(ticker, 'VWAP', 1)}")
                redis_manager.set_explosion_emoji_status(ticker, False)
                time.sleep(1)
                continue
            
            # 6. ATR to VWAP
            if redis_manager.get_technical_indicator(ticker, 'ATR_to_VWAP') <= 0:
                logging.info(f"No atr to vwap {redis_manager.get_technical_indicator(ticker, 'ATR_to_VWAP')}")
                redis_manager.set_explosion_emoji_status(ticker, False)
                time.sleep(1)
                continue
            
            # 7. ATR to HOD
            if not (0 < redis_manager.get_technical_indicator(ticker, 'ATR_to_HOD') < 1):
                logging.info(f"No atr to hod {redis_manager.get_technical_indicator(ticker, 'ATR_to_HOD')}")
                redis_manager.set_explosion_emoji_status(ticker, False)
                time.sleep(1)
                continue
            
            # 8. VWAP slope
            if redis_manager.get_technical_indicator(ticker, 'VWAP_Slope') < 0:
                logging.info(f"No vwap slope {redis_manager.get_technical_indicator(ticker, 'VWAP_Slope')}")
                redis_manager.set_explosion_emoji_status(ticker, False)
                time.sleep(1)
                continue

            # 9. Technical Score
            if redis_manager.get_technical_scores(ticker).get('technical_score') < 0.7:
                logging.info(f"No final score {redis_manager.get_technical_scores(ticker).get('technical_score')}")
                redis_manager.set_explosion_emoji_status(ticker, False)
                time.sleep(1)
                continue
            
            redis_manager.set_explosion_emoji_status(ticker, True)
            logging.info(f"💥 Explosion status: {ticker} {redis_manager.get_explosion_status(ticker)}")

        except Exception as e:
            logging.error(f"Error in explosion detection worker: {e}")
        time.sleep(1)
