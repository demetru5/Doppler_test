import logging
import time
from services.redis_manager import redis_manager
from services.technical_service import is_choppy_market
from config.logging import setup_logging

def run(ticker):
    setup_logging(file_name=f'{ticker}/ema_detection_worker.log')

    detected_timestamp = None
    while True:
        try:
            if detected_timestamp and time.time() - detected_timestamp < 60:
                time.sleep(1)
                continue

            price = redis_manager.get_stock_price(ticker)

            # orderbook confirmation
            orderbook = redis_manager.get_last_orderbook_snapshot(ticker)
            if not orderbook:
                logging.warning(f'No orderbook snapshot')
                time.sleep(1)
                continue

            # check spread
            bid_price = orderbook.get('best_bid_price', 0)
            ask_price = orderbook.get('best_ask_price', 0)
            if not bid_price >= price * 0.99 or not ask_price <= price * 1.01:
                logging.warning(f'No 1% bid and ask price spread bid:{bid_price}, ask:{ask_price}')
                time.sleep(1)
                continue

            # check imbalance
            imbalance = orderbook.get('imbalance', 0)
            if not imbalance > 0.6:
                logging.warning(f'No imbalance {imbalance}')
                time.sleep(1)
                continue

            # check tape is green
            tick_data = redis_manager.get_tick(ticker)
            buy_ticks = sum(1 for tick in tick_data[-10:] if tick['ticker_direction'] == 'BUY')
            sell_ticks = sum(1 for tick in tick_data[-10:] if tick['ticker_direction'] == 'SELL')
            if not buy_ticks > sell_ticks:
                logging.warning(f'No buy tick({buy_ticks}) > sell tick({sell_ticks})')
                time.sleep(1)
                continue

            # Adaptive volume gate with tape override
            candles = redis_manager.get_last_n_candles(ticker, 11)
            recent = candles[:-1]
            if len(recent) < 10:
                logging.warning(f'No 10 candles {len(candles)}')
                time.sleep(1)
                continue

            avg10_vol = (sum(c['volume'] for c in recent) / len(recent)) if recent else 0
            min_gate = max(5000, 1.2 * avg10_vol)
            vol_ok = candles[-1]['volume'] >= min_gate
            if not vol_ok:
                logging.warning(f'No volume ok last volume: {candles[-1]}')
                time.sleep(1)
                continue

            VWAPs = redis_manager.get_technical_indicator(ticker, 'VWAP', 6)
            EMA4s = redis_manager.get_technical_indicator(ticker, 'EMA4', 6)
            EMA5s = redis_manager.get_technical_indicator(ticker, 'EMA5', 6)
            is_cross_up = False
            for i in range(len(VWAPs) - 1):
                if EMA4s[i] < VWAPs[i] and EMA4s[i+1] >= VWAPs[i+1] and EMA5s[i] < VWAPs[i] and EMA5s[i+1] >= VWAPs[i+1]:
                    is_cross_up = True
                    break
            if not is_cross_up:
                logging.warning(f'No cross up')
                time.sleep(1)
                continue

            # if is_choppy_market(ticker):
            #     logging.info(f"🟡 {ticker} detected choppy market")
            #     time.sleep(0.25)
            #     continue

            logging.info(f"🟢 {ticker} detected EMA strategy")
            redis_manager.publish('trade_signal', {
                'type': 'ema_cross_up',
                'ticker': ticker
            })
            detected_timestamp = time.time()
            continue

        except Exception as e:
            logging.error(f"Error in ema detection worker: {e}")

        time.sleep(0.25)
