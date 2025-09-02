import logging
import time
from services.redis_manager import redis_manager
from config.logging import setup_logging

def run(ticker):
    setup_logging(file_name=f'{ticker}/fire_detection_worker.log')

    while True:
        try:
            if not (
                redis_manager.get_technical_scores(ticker).get('technical_score') > 0.6 and
                redis_manager.get_technical_indicator(ticker, 'Volume_Ratio', 1) > 1.5 and
                redis_manager.get_technical_indicator(ticker, 'ROC', 1) > 0
            ):
                logging.info(f"No fire emoji status for {ticker} with technical score: {redis_manager.get_technical_scores(ticker).get('technical_score')} and volume ratio: {redis_manager.get_technical_indicator(ticker, 'Volume_Ratio', 1)} and roc: {redis_manager.get_technical_indicator(ticker, 'ROC', 1)}")
                redis_manager.set_fire_emoji_status(ticker, False)
                time.sleep(1)
                continue

            count = 0
            tick_data = redis_manager.get_tick(ticker)
            if tick_data and len(tick_data) > 10:
                first_half_volume = sum([tick['volume'] for tick in tick_data[:5]])
                second_half_volume = sum([tick['volume'] for tick in tick_data[5:]])
                if first_half_volume > 0 and second_half_volume / first_half_volume > 0.6:
                    count += 1
                    logging.info(f"Met volume acceleration first half: {first_half_volume} second half: {second_half_volume}")
            
            orderbook = redis_manager.get_last_orderbook_snapshot(ticker)
            if orderbook and orderbook.get('imbalance') > 0.6:
                count += 1
                logging.info(f"Met bid dominating {orderbook.get('imbalance')}")
            
            if redis_manager.get_technical_indicator(ticker, 'MACD_hist', 1) > 0 and redis_manager.get_technical_indicator(ticker, 'MACD', 1) > redis_manager.get_technical_indicator(ticker, 'MACD_signal', 1):
                count += 1
                logging.info(f"Met macd momentum {redis_manager.get_technical_indicator(ticker, 'MACD_hist', 1)} {redis_manager.get_technical_indicator(ticker, 'MACD', 1)} {redis_manager.get_technical_indicator(ticker, 'MACD_signal', 1)}")

            if redis_manager.get_technical_indicator(ticker, 'StochRSI_K', 1) > 50:
                count += 1
                logging.info(f"Met stoch rsi momentum {redis_manager.get_technical_indicator(ticker, 'StochRSI_K', 1)}")

            if redis_manager.get_technical_indicator(ticker, 'ADX', 1) > 20:
                count += 1
                logging.info(f"Met adx momentum {redis_manager.get_technical_indicator(ticker, 'ADX', 1)}")
            
            if redis_manager.get_stock_price(ticker) > redis_manager.get_technical_indicator(ticker, 'VWAP', 1) > 0:
                count += 1
                logging.info(f"Met price above vwap {redis_manager.get_stock_price(ticker)} {redis_manager.get_technical_indicator(ticker, 'VWAP', 1)}")

            if redis_manager.get_technical_indicator(ticker, 'ATR_to_VWAP', 1) > 0:
                count += 1
                logging.info(f"Met atr to vwap {redis_manager.get_technical_indicator(ticker, 'ATR_to_VWAP', 1)}")

            if redis_manager.get_technical_indicator(ticker, 'ATR_to_HOD', 1) < 1:
                count += 1
                logging.info(f"Met atr to hod {redis_manager.get_technical_indicator(ticker, 'ATR_to_HOD', 1)}")

            if redis_manager.get_technical_indicator(ticker, 'VWAP_Slope', 1) >= 0:
                count += 1
                logging.info(f"Met vwap slope {redis_manager.get_technical_indicator(ticker, 'ATR_to_VWAP', 1)}")

            if count >= 2:
                logging.info(f"🔥 Met fire emoji status {count}")
                redis_manager.set_fire_emoji_status(ticker, True)
            else:
                logging.info(f"No fire emoji status for {ticker} with count: {count}")
                redis_manager.set_fire_emoji_status(ticker, False)

        except Exception as e:
            logging.error(f"Error in fire detection worker: {e}")
        time.sleep(1)
