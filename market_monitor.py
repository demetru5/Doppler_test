import os
import time
import logging
import threading
import pytz
import pandas as pd
from typing import List
from datetime import datetime, timedelta
from moomoo import *
from polygon import RESTClient
from polygon.websocket.models import WebSocketMessage
from polygon.rest.models import (
    TickerSnapshot,
    Agg,
    MinuteSnapshot,
    LastQuote,
    LastTrade
)
from config import get_config
from services.redis_manager import redis_manager
from services.polygon_manager import PolygonManager
from utils.util import get_moomoo_ticker, get_short_ticker, get_current_time, get_current_session
from services.market_context_service import intraday_macro_analysis
from config.logging import setup_logging

class MarketMonitor:
    def __init__(self):
        SysConfig.enable_proto_encrypt(True)
        SysConfig.set_init_rsa_file("moomoo1/rsa.txt")
        POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')
        self.polygon_client = RESTClient(POLYGON_API_KEY)
        self.quote_ctx = OpenQuoteContext(get_config().MOOMOO_HOST, get_config().MOOMOO_PORT1)
        self.snapshot_data = {}
        self.lock = threading.Lock()

    def _process_gainer(self, ticker, mode):
        moomoo_ticker = get_moomoo_ticker(ticker)
        if (
            moomoo_ticker in redis_manager.get_all_tickers()
        ):
            return

        logging.info(f"Processing gainer: {moomoo_ticker} in {mode}")

        redis_manager.publish('subscribe', {
            'tickers': [moomoo_ticker],
            'mode': mode,
        })

    def _detect_rapid_gainer(self):
        while True:
            try:
                with self.lock:
                    snapshot_data_copy = self.snapshot_data.copy()

                for moomoo_ticker in snapshot_data_copy:
                    if snapshot_data_copy[moomoo_ticker]['min'][-1]['close'] > 15:
                        continue

                    change = 0
                    change_pct = 0
                    recent_time = None
                    last_minute_data = snapshot_data_copy[moomoo_ticker]['min'][-1]
                    current_time = get_current_time()
                    trade_timestamp = pd.to_datetime(last_minute_data['timestamp']).tz_localize('US/Eastern')
                    if current_time - trade_timestamp > timedelta(minutes=1):
                        continue
                    if last_minute_data['close'] == 0 or last_minute_data['open'] == 0:
                        continue

                    change = last_minute_data['close'] - last_minute_data['open']
                    change_pct = (change / last_minute_data['open']) * 100
                    recent_time = last_minute_data['timestamp']

                    if change_pct > 10:
                        logging.info(f"🟢 {moomoo_ticker} detected {change_pct}% in 1m at {recent_time}")
                        self._process_gainer(moomoo_ticker, "rapid_gainer")
                    elif change_pct > 5:
                        logging.info(f"{moomoo_ticker} detected {change_pct}% in 1m at {recent_time}")
                        self._process_gainer(moomoo_ticker, "rapid_gainer")

                time.sleep(0.1)

            except Exception as e:
                logging.error(f"Error in rapid gainer detection: {e}")
                time.sleep(1)

    def _detect_five_minute_gainer(self):
        while True:
            try:
                gainers = []
                polygon_tickers = redis_manager.get_polygon_tickers()

                for ticker in polygon_tickers:
                    five_minutes_data = redis_manager.get_polygon_data(ticker)
                    if not five_minutes_data:  # Skip if no data
                        continue

                    if len(five_minutes_data) > 2:
                        start_time = five_minutes_data[0]['timestamp']
                        end_time = five_minutes_data[-1]['timestamp']
                        period = pd.to_datetime(end_time) - pd.to_datetime(start_time)
                        if period.total_seconds() > 3 * 60:
                            price_change = five_minutes_data[-1]['price'] - five_minutes_data[0]['price']
                            price_change_pct = (price_change / five_minutes_data[0]['price']) * 100
                            if price_change_pct > 5:
                                gainers.append({
                                    'ticker': ticker,
                                    'price': five_minutes_data[-1]['price'],
                                    'price_change_pct': price_change_pct
                                })

                if len(gainers) > 0:
                    gainers.sort(key=lambda x: x['price_change_pct'], reverse=True)
                    for gainer in gainers:
                        self._process_gainer(gainer['ticker'], 'five_minute_gainer')

                time.sleep(30)
            except Exception as e:
                logging.error(f"Error in five minute gainer detection: {e}")
                time.sleep(30)

    def _detect_session_gainer(self):
        while True:
            try:
                with self.lock:
                    snapshot_data_copy = self.snapshot_data.copy()

                current_session = get_current_session()
                gainers = []

                for ticker in snapshot_data_copy:
                    session_change = 0
                    session_change_pct = 0
                    session_price = 0
                    if current_session == 'afterhours':
                        prev_close_price = snapshot_data_copy[ticker]['day']['close']
                    else:
                        prev_close_price = snapshot_data_copy[ticker]['prev_day']['close']

                    if prev_close_price is None or prev_close_price < 0.01:
                        continue

                    session_price = snapshot_data_copy[ticker]['min'][-1]['close']
                    session_change = session_price - prev_close_price
                    session_change_pct = (session_change / prev_close_price) * 100

                    if session_change_pct > 0:
                        gainers.append({
                            'ticker': ticker,
                            'price': session_price,
                            'session_change_pct': session_change_pct
                        })
                
                if len(gainers) > 0:
                    gainers.sort(key=lambda x: x['session_change_pct'], reverse=True)
                    for gainer in gainers[:5]:
                        self._process_gainer(gainer['ticker'], "session_gainer")

                time.sleep(30)
            except Exception as e:
                logging.error(f"Error in session gainer detection: {e}")
                time.sleep(30)

    def _fetch_polygon_candles(self, ticker):
        current_date = get_current_time().strftime('%Y-%m-%d')
        candles = []
        for a in self.polygon_client.list_aggs(
            get_short_ticker(ticker),
            1,
            "minute",
            current_date,
            current_date,
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

    def _run_polygon_websocket(self):
        polygon_manager = PolygonManager()
        polygon_manager.run_websocket(self._handle_polygon_message)

    def _handle_polygon_message(self, msgs: List[WebSocketMessage]):
        try:
            for m in msgs:
                if redis_manager.check_prev_close_price(get_moomoo_ticker(m.symbol)):
                    utc_dt = datetime.fromtimestamp(m.end_timestamp/1000, tz=pytz.UTC)
                    est_dt = utc_dt.astimezone(pytz.timezone('US/Eastern'))
                    redis_manager.add_polygon_data(m.symbol, m.close, m.volume, est_dt.strftime('%Y-%m-%d %H:%M:%S'))

        except Exception as e:
            logging.error(f"Error handling polygon message: {e}")

    def _get_market_context(self):
        while True:
            try:
                market_context = intraday_macro_analysis()
                redis_manager.set_market_context(market_context)
                logging.info(f"Market context: {market_context}")
            except Exception as e:
                logging.error(f"Error getting market context: {e}")
            time.sleep(300)

    def _unsubscribe_stocks(self):
        while True:
            try:
                tickers_to_unsubscribe = []
                tickers = redis_manager.get_all_tickers()
                for ticker in tickers:
                    candles = redis_manager.get_candles(ticker)
                    subscribed_time = redis_manager.get_subscribed_time(ticker)
                    candles_after_subscribed = [candle for candle in candles if candle['timestamp'] >= subscribed_time]
                    if len(candles_after_subscribed) > 5:
                        zero_volume_candles_count = sum(1 for candle in candles_after_subscribed if candle['volume'] == 0)
                        if zero_volume_candles_count > 2:
                            tickers_to_unsubscribe.append(ticker)

                if len(tickers_to_unsubscribe) > 0:
                    redis_manager.publish('unsubscribe', {
                        'tickers': tickers_to_unsubscribe
                    })

            except Exception as e:
                logging.error(f"Error in unsubscribe stocks: {e}")

            time.sleep(2 * 60)

    def _start_polygon_monitors(self):
        while True:
            try:
                if get_current_session() == 'closed':
                    time.sleep(1)
                    continue

                logging.info("Fetching polygon snapshot")
                snapshot = self.polygon_client.get_snapshot_all(
                    "stocks",
                )
                with self.lock:
                    snapshot_data_copy = self.snapshot_data.copy()

                for item in snapshot:
                    if not isinstance(item, TickerSnapshot) or not isinstance(item.min, MinuteSnapshot) or not isinstance(item.day, Agg) or not isinstance(item.prev_day, Agg) or not isinstance(item.last_quote, LastQuote) or not isinstance(item.last_trade, LastTrade) or len(item.ticker) > 4:
                        continue
                    min_utc_dt = datetime.fromtimestamp(item.min.timestamp/1000, tz=pytz.UTC) + timedelta(minutes=1)
                    min_est_dt = min_utc_dt.astimezone(pytz.timezone('US/Eastern'))
                    last_trade_utc_dt = datetime.fromtimestamp(item.last_trade.sip_timestamp/1000000000, tz=pytz.UTC)
                    last_trade_est_dt = last_trade_utc_dt.astimezone(pytz.timezone('US/Eastern'))
                    if item.ticker not in snapshot_data_copy:
                        moomoo_ticker = get_moomoo_ticker(item.ticker)
                        snapshot_data_copy[moomoo_ticker] = {
                            'ticker': moomoo_ticker,
                            'min': [{
                                'timestamp': min_est_dt.strftime('%Y-%m-%d %H:%M:%S'),
                                'open': item.min.open,
                                'high': item.min.high,
                                'low': item.min.low,
                                'close': item.min.close,
                                'volume': item.min.volume,
                                'vwap': item.min.vwap,
                                'accumulated_volume': item.min.accumulated_volume,
                            }],
                            'day': {
                                'open': item.day.open,
                                'high': item.day.high,
                                'low': item.day.low,
                                'close': item.day.close,
                                'volume': item.day.volume,
                                'vwap': item.day.vwap,
                            },
                            'prev_day': {
                                'open': item.prev_day.open,
                                'high': item.prev_day.high,
                                'low': item.prev_day.low,
                                'close': item.prev_day.close,
                                'volume': item.prev_day.volume,
                                'vwap': item.prev_day.vwap,
                            },
                            'last_quote': {
                                'bid_price': item.last_quote.bid_price,
                                'bid_size': item.last_quote.bid_size,
                                'ask_price': item.last_quote.ask_price,
                                'ask_size': item.last_quote.ask_size,
                            },
                            'last_trade': [{
                                'price': item.last_trade.price,
                                'size': item.last_trade.size,
                                'timestamp': last_trade_est_dt.strftime('%Y-%m-%d %H:%M:%S'),
                            }]
                        }
                    else:
                        last_min_timestamp = snapshot_data_copy[moomoo_ticker]['min'][-1]['timestamp']
                        if last_min_timestamp != min_est_dt.strftime('%Y-%m-%d %H:%M:%S'):
                            snapshot_data_copy[moomoo_ticker]['min'].append({
                                'timestamp': min_est_dt.strftime('%Y-%m-%d %H:%M:%S'),
                                'open': item.min.open,
                                'high': item.min.high,
                                'low': item.min.low,
                                'close': item.min.close,
                                'volume': item.min.volume,
                                'vwap': item.min.vwap,
                                'accumulated_volume': item.min.accumulated_volume,
                            })
                        else:
                            snapshot_data_copy[moomoo_ticker]['min'][-1]['close'] = item.min.close
                            snapshot_data_copy[moomoo_ticker]['min'][-1]['volume'] = item.min.volume
                            snapshot_data_copy[moomoo_ticker]['min'][-1]['vwap'] = item.min.vwap
                            snapshot_data_copy[moomoo_ticker]['min'][-1]['accumulated_volume'] = item.min.accumulated_volume

                        if len(snapshot_data_copy[moomoo_ticker]['min']) > 5:
                            snapshot_data_copy[moomoo_ticker]['min'].pop(0)

                        snapshot_data_copy[moomoo_ticker]['day']['close'] = item.day.close
                        snapshot_data_copy[moomoo_ticker]['day']['volume'] = item.day.volume
                        snapshot_data_copy[moomoo_ticker]['day']['vwap'] = item.day.vwap
                        snapshot_data_copy[moomoo_ticker]['last_quote']['bid_price'] = item.last_quote.bid_price
                        snapshot_data_copy[moomoo_ticker]['last_quote']['bid_size'] = item.last_quote.bid_size
                        snapshot_data_copy[moomoo_ticker]['last_quote']['ask_price'] = item.last_quote.ask_price
                        snapshot_data_copy[moomoo_ticker]['last_quote']['ask_size'] = item.last_quote.ask_size
                        if snapshot_data_copy[moomoo_ticker]['last_trade'][-1]['timestamp'] != last_trade_est_dt.strftime('%Y-%m-%d %H:%M:%S'):
                            snapshot_data_copy[moomoo_ticker]['last_trade'].append({
                                'price': item.last_trade.price,
                                'size': item.last_trade.size,
                                'timestamp': last_trade_est_dt.strftime('%Y-%m-%d %H:%M:%S'),
                            })
                        if len(snapshot_data_copy[moomoo_ticker]['last_trade']) > 10:
                            snapshot_data_copy[moomoo_ticker]['last_trade'].pop(0)

                with self.lock:
                    self.snapshot_data = snapshot_data_copy

                logging.info(f"Polygon snapshot fetched {len(snapshot_data_copy)} tickers")

            except Exception as e:
                logging.error(f"Error in start polygon monitors: {e}")
            time.sleep(1)

    def _vwap_scanner(self):
        while True:
            try:
                with self.lock:
                    snapshot_data_copy = self.snapshot_data.copy()

                if len(snapshot_data_copy) == 0:
                    time.sleep(30)
                    continue

                candidates = []
                tickers = []
                for ticker, item in snapshot_data_copy.items():
                    if not (0.5 <= item['last_trade'][-1]['price'] <= 12.00):
                        continue

                    if item['min'][-1]['accumulated_volume'] < 50_000:
                        continue

                    if item['min'][-1]['accumulated_volume'] * item['last_trade'][-1]['price'] < 500_000:
                        continue

                    current_time = get_current_time()
                    last_trade_timestamp = pd.to_datetime(item['last_trade'][-1]['timestamp']).tz_localize('US/Eastern')
                    if current_time - last_trade_timestamp > timedelta(minutes=1):
                        continue

                    tickers.append(ticker)

                if len(tickers) > 0:
                    ret, data = self.quote_ctx.get_market_snapshot(tickers)
                    if ret == RET_OK:
                        tickers = data[data['outstanding_shares'] < 50_000_000]['code'].tolist()

                if len(tickers) > 0:
                    candidates = [item for ticker, item in snapshot_data_copy.items() if ticker in tickers]
                    candidates.sort(key=lambda x: (
                        -x['day']['volume'] * x['last_trade'][-1]['price']
                    ))

                logging.info(f"VWAP candidates {len(candidates)} {[c['ticker'] for c in candidates]}")

                for candidate in candidates[:10]:
                    self._process_gainer(candidate['ticker'], "vwap_candidate")

            except Exception as e:
                logging.error(f"Error in vwap scanner: {e}")
            time.sleep(30)

    def _validate_emas(self, EMA240s, EMA5s):
        try:
            if not len(EMA240s.values) == len(EMA5s.values) or not len(EMA240s.values) > 0 or not len(EMA5s.values) > 0:
                return False
            last_ema240_timestamp = datetime.fromtimestamp(EMA240s.values[0].timestamp/1000, tz=pytz.timezone('US/Eastern'))
            last_ema5_timestamp = datetime.fromtimestamp(EMA5s.values[0].timestamp/1000, tz=pytz.timezone('US/Eastern'))
            current_time = get_current_time()
            if current_time - last_ema240_timestamp > timedelta(minutes=10) or current_time - last_ema5_timestamp > timedelta(minutes=10):
                return False
            return True
        except Exception as e:
            logging.error(f"Error in validate emas: {e}")
            return False

    def _check_crossover(self, EMA240s, EMA5s):
        try:
            if EMA5s.values[-1].value < EMA5s.values[0].value and EMA5s.values[-1].value < EMA240s.values[-1].value and EMA5s.values[0].value >= EMA240s.values[0].value:
                return True
            return False
        except Exception as e:
            logging.error(f"Error in check crossover: {e}")
            return False

    def _dip_scanner(self):
        while True:
            try:
                with self.lock:
                    snapshot_data_copy = self.snapshot_data.copy()

                if len(snapshot_data_copy) == 0:
                    time.sleep(30)
                    continue

                candidates = []
                tickers = []
                # Price Filter between $0.5 and $12
                for ticker, item in snapshot_data_copy.items():
                    if not (0.5 <= item['last_trade'][-1]['price'] <= 12.00):
                        continue

                    current_time = get_current_time()
                    last_trade_timestamp = pd.to_datetime(item['last_trade'][-1]['timestamp']).tz_localize('US/Eastern')
                    if current_time - last_trade_timestamp > timedelta(minutes=1):
                        continue

                    tickers.append(ticker)

                # Float Filter less than 50M
                if len(tickers) > 0:
                    ret, data = self.quote_ctx.get_market_snapshot(tickers)
                    if ret == RET_OK:
                        tickers = data[data['outstanding_shares'] < 50_000_000]['code'].tolist()

                # EMA5 & EMA240 Filter for approach each other
                if len(tickers) > 0:
                    for ticker in tickers:
                        EMA240s = self.polygon_client.get_ema(
                            ticker=get_short_ticker(ticker),
                            timespan="minute",
                            adjusted="true",
                            window="240",
                            series_type="close",
                            order="desc",
                            limit="10",
                        )
                        EMA5s = self.polygon_client.get_ema(
                            ticker=get_short_ticker(ticker),
                            timespan="minute",
                            adjusted="true",
                            window="5",
                            series_type="close",
                            order="desc",
                            limit="10",
                        )
                        if not self._validate_emas(EMA240s, EMA5s):
                            logging.info(f"Invalid emas for {ticker}")
                            continue
                        if self._check_crossover(EMA240s, EMA5s):
                            logging.info(f"Crossover for {ticker}")
                            candidates.append(snapshot_data_copy[ticker])

                    candidates.sort(key=lambda x: (
                        -x['day']['volume'] * x['last_trade'][-1]['price']
                    ))

                    for candidate in candidates[:10]:
                        self._process_gainer(candidate['ticker'], "dip_candidate")
                else:
                    logging.warning(f"No Dip candidates found")

            except Exception as e:
                logging.error(f"Error in dip scanner: {e}")
            time.sleep(30)

    def run(self):
        polygon_monitors_thread = threading.Thread(target=self._start_polygon_monitors)
        polygon_monitors_thread.start()

        vwap_scanner_thread = threading.Thread(target=self._vwap_scanner)
        vwap_scanner_thread.start()

        dip_scanner_thread = threading.Thread(target=self._dip_scanner)
        dip_scanner_thread.start()

        rapid_gainer_thread = threading.Thread(target=self._detect_rapid_gainer)
        rapid_gainer_thread.start()

        # five_minute_gainer_thread = threading.Thread(target=self._detect_five_minute_gainer)
        # five_minute_gainer_thread.start()

        session_gainer_thread = threading.Thread(target=self._detect_session_gainer)
        session_gainer_thread.start()

        # polygon_websocket_thread = threading.Thread(target=self._run_polygon_websocket)
        # polygon_websocket_thread.start()

        unsubscribe_thread = threading.Thread(target=self._unsubscribe_stocks)
        unsubscribe_thread.start()

        market_context_thread = threading.Thread(target=self._get_market_context)
        market_context_thread.start()

if __name__ == "__main__":
    setup_logging(file_name=f'market_monitor.log')
    market_monitor = MarketMonitor()
    market_monitor.run()