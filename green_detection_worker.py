import logging
import time
from services.redis_manager import redis_manager
from config.logging import setup_logging
from utils.util import get_current_time
from services.technical_service import is_choppy_market

def run(ticker):
    setup_logging(file_name=f'{ticker}/green_detection_worker.log')

    detected_timestamp = None
    while True:
        try:
            if detected_timestamp and time.time() - detected_timestamp < 60:
                time.sleep(1)
                continue

            # Continuous extended-hours window without 30-min gap
            hour = get_current_time().hour
            if not (4 <= hour < 20):
                logging.info(f"{ticker} Not in trading hours")
                time.sleep(30)
                continue

            indicators = redis_manager.get_technical_indicators(ticker)
            scores = redis_manager.get_technical_scores(ticker)
            price = redis_manager.get_stock_price(ticker)

            # Chop veto using technical_service
            # if is_choppy_market(ticker):
            #     logging.info(f"{ticker} choppy market veto")
            #     time.sleep(0.25)
            #     continue

            is_all_green = False

            try:
                is_all_green = (
                    scores.get('technical_score') >= 0.7 and
                    indicators.get('RVol') >= 2.0 and
                    indicators.get('ATR_to_VWAP') >= 0.50 and
                    indicators.get('Volume_Ratio') >= 1.5 and
                    indicators.get('ATR_to_HOD') <= 1 and
                    indicators.get('VWAP_Slope') >= 0 and
                    indicators.get('ZenP') > 1 and
                    indicators.get('ATR_Spread') < 0.25
                )
            except Exception as e:
                logging.error(f'No efficient indicators: {e}')

            logging.info(f"{ticker}, {price}, technical score: {scores.get('technical_score')}{'✔' if scores.get('technical_score') >= 0.7 else '❌'}, RVol: {indicators.get('RVol')}{'✔' if indicators.get('RVol') >= 2.0 else '❌'}, ATR_to_VWAP: {indicators.get('ATR_to_VWAP')}{'✔' if indicators.get('ATR_to_VWAP') >= 0.50 else '❌'}, Volume Ratio: {indicators.get('Volume_Ratio')}{'✔' if indicators.get('Volume_Ratio') >= 1.5 else '❌'}, ATR_to_HOD: {indicators.get('ATR_to_HOD')}{'✔' if indicators.get('ATR_to_HOD') <= 1 else '❌'}, VWAP Slope: {indicators.get('VWAP_Slope')}{'✔' if indicators.get('VWAP_Slope') >= 0 else '❌'}, Zenp: {indicators.get('ZenP')}{'✔' if indicators.get('ZenP') > 1 else '❌'}, ATR_Spread: {indicators.get('ATR_Spread')}{'✔' if indicators.get('ATR_Spread') < 0.25 else '❌'}")

            if is_all_green:
                logging.info(f"🟢 {ticker} detected all green")
                redis_manager.publish('trade_signal', {
                    'type': 'green',
                    'ticker': ticker
                })
                detected_timestamp = time.time()
                continue

        except Exception as e:
            logging.error(f"Error in green detection worker: {e}")
        time.sleep(0.25)
