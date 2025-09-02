import logging
import argparse
from moomoo import *
from polygon import RESTClient
from datetime import datetime
import pytz
from config import get_config
from config.logging import setup_logging
from services.redis_manager import redis_manager
import pandas as pd
from multiprocessing import Process
import threading
import ticker_process_worker
import candlestick_process_worker
import orderbook_process_worker
import technical_indicators_worker
import fire_detection_worker
import explosion_detection_worker
import ema_detection_worker
import green_detection_worker
import pattern_evaluation_worker
from utils.util import get_current_time, get_short_ticker, get_current_session

# Moomoo configuration
SysConfig.enable_proto_encrypt(True)
SysConfig.set_init_rsa_file("moomoo1/rsa.txt")

class TickerHandler(TickerHandlerBase):
    def __init__(self):
        super(TickerHandler, self).__init__()
        self._last_batch_time = time.time()
        self._tick_queue = []
        self._batch_size = 100
        self._max_queue_size = 1000

    def on_recv_rsp(self, rsp_pb):
        ret_code, data = super(TickerHandler,self).on_recv_rsp(rsp_pb)
        if ret_code != RET_OK:
            print("TickerTest: error, msg: %s"% data)
            return RET_ERROR, data
        for _, row in data.iterrows():
            if len(self._tick_queue) >= self._max_queue_size:
                self._process_batch()

            tick_data = {
                'code': row['code'],
                'time': row['time'],
                'price': row['price'],
                'volume': row['volume'],
                'ticker_direction': row['ticker_direction'],
            }
            self._tick_queue.append((row['code'], tick_data))

        if len(self._tick_queue) >= self._batch_size or ((time.time() - self._last_batch_time >= 1) and len(self._tick_queue) > 0):
            self._process_batch()
            self._last_batch_time = time.time()

        return RET_OK, data
    
    def _process_batch(self):
        if len(self._tick_queue) == 0:
            return
        
        try:
            with redis_manager.redis_client.pipeline() as pipe:
                for code, tick_data in self._tick_queue:
                    pipe.rpush(f'moomoo:tick:{code}', json.dumps(tick_data))
                pipe.execute()
            logging.info(f"Ticker batch processed: {len(self._tick_queue)} last time: {tick_data['time']}")
        except Exception as e:
            logging.error(f"Error processing ticker batch: {e}")
        finally:
            self._tick_queue = []

class CandlestickHandler(CurKlineHandlerBase):
    def on_recv_rsp(self, rsp_pb) -> tuple:
        ret_code, data = super(CandlestickHandler, self).on_recv_rsp(rsp_pb)
        if ret_code != RET_OK:
            logging.error(f"TickerHandler error: {data}")
            return RET_ERROR, data

        for _, row in data.iterrows():
            candle = {
                'timestamp': row['time_key'],
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row['volume']
            }
            redis_manager.push_candlestick(row['code'], candle)
            logging.info(f"Candlestick pushed to Redis: open: {candle['open']}, high: {candle['high']}, low: {candle['low']}, close: {candle['close']}, volume: {candle['volume']}, timestamp: {candle['timestamp']}")
        
        return RET_OK, data

class OrderbookHandler(OrderBookHandlerBase):
    def on_recv_rsp(self, rsp_pb):
        ret_code, data = super(OrderbookHandler, self).on_recv_rsp(rsp_pb)
        if ret_code != RET_OK:
            logging.error(f"OrderBookHandler error: {data}")
            return RET_ERROR, data

        redis_manager.push_orderbook(data['code'], data)
        # logging.info(f"Orderbook pushed to Redis: {data}")

        return RET_OK, data

def get_previous_trading_day(quote_ctx):
    try:
        start = (get_current_time() - timedelta(days=7)).strftime('%Y-%m-%d')
        end = (get_current_time() - timedelta(days=1)).strftime('%Y-%m-%d')
        ret, data = quote_ctx.request_trading_days(TradeDateMarket.US, start=start, end=end)
        if ret == RET_OK:
            return data[-1]['time']
        else:
            logging.error(f"Error getting previous trading day: {data}")
            return None
    except Exception as e:
        logging.error(f"Error getting previous trading day: {e}")
        return None

def get_prev_close_price(candles):
    date = get_current_time().strftime('%Y-%m-%d')
    if get_current_session() == 'afterhours':
        date = get_previous_trading_day
    

def complete_intraday_candles_polygon(ticker, previous_trading_day):
    POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')
    client = RESTClient(POLYGON_API_KEY)
    current_date = get_current_time().strftime('%Y-%m-%d')
    start = previous_trading_day
    end = current_date
    candles = []
    for a in client.list_aggs(
        get_short_ticker(ticker),
        1,
        "minute",
        start,
        end,
        adjusted="true",
        sort="asc"
    ):
        utc_dt = datetime.fromtimestamp(a.timestamp/1000, tz=pytz.UTC) + timedelta(minutes=1)
        est_dt = utc_dt.astimezone(pytz.timezone('US/Eastern'))
        candles.append({
            'timestamp': est_dt.strftime('%Y-%m-%d %H:%M:%S'),
            'open': a.open,
            'high': a.high,
            'low': a.low,
            'close': a.close,
            'volume': a.volume
        })
    return candles

def complete_intraday_candles(quote_ctx, ticker, previous_trading_day):
    current_date = get_current_time().strftime('%Y-%m-%d')
    completed = False
    while not completed:
        logging.info(f"Completing intraday candles for {ticker}")
        ret, data, _ = quote_ctx.request_history_kline(ticker, start=previous_trading_day, end=current_date, ktype=KLType.K_1M, extended_time=True, max_count=None)
        if ret != RET_OK:
            logging.error(f"Error completing intraday candles for {ticker}: {data}")
            candles = complete_intraday_candles_polygon(ticker, previous_trading_day)
            if len(candles) > 0:
                redis_manager.merge_candles(ticker, candles)
                logging.info(f"Completed intraday candles for {ticker}: {len(candles)}")
                completed = True
            continue
        
        data['timestamp'] = data['time_key']
        candles_data = data[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        candles = candles_data.to_dict(orient='records')
        redis_manager.merge_candles(ticker, candles)
        logging.info(f"Completed intraday candles for {ticker}: {len(candles)}")
        completed = True
    
    if not redis_manager.check_prev_close_price(ticker):
        candle_timestamp = f'{current_date} 16:00:00' if get_current_session() == 'afterhours' else f'{previous_trading_day} 16:00:00'
        candle = [c for c in candles if c['timestamp'] == candle_timestamp]
        if len(candle) > 0:
            redis_manager.set_prev_close_price(ticker, candle[0]['close'])
            logging.info(f"Set previous close price for {ticker}: {candle[0]['close']}")

def run(ticker, mode):
    """Main application entry point"""
    quote_ctx = None
    config = get_config()
    try:
        # Initialize quote context
        quote_ctx = OpenQuoteContext(host=config.MOOMOO_HOST, port=config.MOOMOO_PORT1)
        previous_trading_day = get_previous_trading_day(quote_ctx)
        if not previous_trading_day:
            previous_trading_day = get_current_time().strftime('%Y-%m-%d')
        ticker_handler = TickerHandler()
        candlestick_handler = CandlestickHandler()
        orderbook_handler = OrderbookHandler()
        quote_ctx.set_handler(ticker_handler)
        quote_ctx.set_handler(candlestick_handler)
        quote_ctx.set_handler(orderbook_handler)
        ret, data = quote_ctx.subscribe(
            [ticker], 
            [SubType.TICKER, SubType.K_1M, SubType.ORDER_BOOK],
            is_first_push=True,
            subscribe_push=True,
            extended_time=True,
            session=Session.ALL
        )
        if ret == RET_OK:
            logging.info(f"Subscribed to {ticker}")
            redis_manager.set_subscribed_time(ticker)
            redis_manager.set_mode(ticker, mode)

            complete_candles_thread = threading.Thread(target=complete_intraday_candles, args=(quote_ctx, ticker, previous_trading_day))
            complete_candles_thread.start()
            
            # Data processing
            ticker_process = Process(target=ticker_process_worker.run, args=(ticker,))
            ticker_process.start()
            candlestick_process = Process(target=candlestick_process_worker.run, args=(ticker,))
            candlestick_process.start()
            orderbook_process = Process(target=orderbook_process_worker.run, args=(ticker,))
            orderbook_process.start()
            indicators_process = Process(target=technical_indicators_worker.run, args=(ticker,))
            indicators_process.start()
            fire_detection_process = Process(target=fire_detection_worker.run, args=(ticker,))
            fire_detection_process.start()
            explosion_detection_process = Process(target=explosion_detection_worker.run, args=(ticker,))
            explosion_detection_process.start()

            # Pattern and Strategy Evaluation
            pattern_evaluation_process = Process(target=pattern_evaluation_worker.run, args=(ticker,))
            pattern_evaluation_process.start()

            # Auto trading signal analyzer
            ema_detection_process = Process(target=ema_detection_worker.run, args=(ticker,))
            ema_detection_process.start()
            green_detection_process = Process(target=green_detection_worker.run, args=(ticker,))
            green_detection_process.start()
        else:
            logging.error(f"Subscription error: {data}")
    except Exception as e:
        logging.error(f"Fatal error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("ticker", type=str, help="Ticker to subscribe to")
    parser.add_argument("--mode", type=str, help="Subscription mode", required=True)
    args = parser.parse_args()
    setup_logging(file_name=f'{args.ticker}/subscribe_worker.log')
    run(args.ticker, args.mode)
