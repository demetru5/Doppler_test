import logging
import threading
import time
import pytz
import pandas as pd
import subprocess
import os
import psutil
from datetime import datetime, timedelta
from moomoo import *
from config import get_config
from utils.util import get_current_session, get_current_time
from services.redis_manager import redis_manager

class MoomooManager:
    def __init__(self, host, port):
        SysConfig.enable_proto_encrypt(True)
        SysConfig.set_init_rsa_file("moomoo1/rsa.txt")

        self.quote_ctx = None
        
        # Process management
        self.subscribe_processes = {}  # {ticker: subprocess.Popen}
        
        self.market_filter_timestamps = []
        self.market_snapshot_timestamps = []
        self.MAX_MARKET_FILTER_IN_THIRTY_SECONDS = 10
        self.MAX_MARKET_SNAPSHOT_IN_THIRTY_SECONDS = 60

        self.lock = threading.Lock()
        
        self._init_quote_ctx(host, port)

    def _init_quote_ctx(self, host, port):
        self.quote_ctx = OpenQuoteContext(host, port)
        back_data_thread = threading.Thread(target=self._init_back_data, daemon=True)
        back_data_thread.start()

    def get_subscription_status(self):
        ret, data = self.quote_ctx.query_subscription()
        if ret == RET_OK:
            return data
        else:
            logging.error(f"Failed to get subscription status: {data}")
            return {}
    
    def _get_market_filter_sleep_time(self):
        if len(self.market_filter_timestamps) == 0:
            return 0
        current_time = time.time()
        self.market_filter_timestamps = [ts for ts in self.market_filter_timestamps if ts > current_time - 30]
        if len(self.market_filter_timestamps) < self.MAX_MARKET_FILTER_IN_THIRTY_SECONDS:
            return 0
        wait_time = self.market_filter_timestamps[0] + 30 - current_time
        return wait_time
    
    def _record_market_filter_timestamp(self):
        self.market_filter_timestamps.append(time.time())
    
    def _get_market_snapshot_sleep_time(self):
        if len(self.market_snapshot_timestamps) == 0:
            return 0
        current_time = time.time()
        self.market_snapshot_timestamps = [ts for ts in self.market_snapshot_timestamps if ts > current_time - 30]
        if len(self.market_snapshot_timestamps) < self.MAX_MARKET_SNAPSHOT_IN_THIRTY_SECONDS:
            return 0
        wait_time = self.market_snapshot_timestamps[0] + 30 - current_time
        return wait_time
    
    def _record_market_snapshot_timestamp(self):
        self.market_snapshot_timestamps.append(time.time())

    def market_filter(self, filters):
        all_results = []
        page = 0
        page_size = 200

        while True:
            sleep_time = self._get_market_filter_sleep_time()
            if sleep_time > 0:
                time.sleep(sleep_time)
            
            ret, ls = self.quote_ctx.get_stock_filter(
                market=Market.US,
                filter_list=filters,
                begin=page * page_size
            )
            self._record_market_filter_timestamp()

            if ret != RET_OK:
                logging.error(f"Failed to get market filter: {ls}")
                continue

            last_page, all_count, ret_list = ls
            all_results.extend(ret_list)

            logging.info(f"Page {page} of {all_count} results")

            if last_page or len(ret_list) < page_size:
                break

            page += 1
            time.sleep(0.1)

        # Get basic info to filter for main exchanges
        stock_ret, stock_data = self.quote_ctx.get_stock_basicinfo(Market.US, SecurityType.STOCK, [item.stock_code for item in all_results])    
        if stock_ret != RET_OK:
            logging.error(f"Error getting stock basic info: {stock_ret}")
            return []
    
        main_exchange_stocks = stock_data[stock_data['exchange_type'].isin([ExchType.US_NASDAQ, ExchType.US_NYSE, ExchType.US_AMEX])]['code'].tolist()

        # Filter for main exchanges
        all_results = [{
            "ticker": item.stock_code,
            **{filter.stock_field: item[filter] for filter in filters}
        } for item in all_results if item.stock_code in main_exchange_stocks]

        return all_results

    def market_snapshot(self, tickers):
        batch_size = 400
        all_snapshots = []

        for i in range(0, len(tickers), batch_size):
            batch_codes = tickers[i:i + batch_size]
            sleep_time = self._get_market_snapshot_sleep_time()
            if sleep_time > 0:
                time.sleep(sleep_time)
            ret, snapshot = self.quote_ctx.get_market_snapshot(batch_codes)
            self._record_market_snapshot_timestamp()

            if ret != RET_OK:
                logging.error(f"Error getting market snapshot for batch {i//batch_size + 1}: {ret}")
                continue

            all_snapshots.append(snapshot)
            logging.info(f"Retrieved {len(all_snapshots)} snapshots out of {len(tickers)} total")
            time.sleep(0.1)

        return pd.concat(all_snapshots)

    def get_candles(self, ticker, date=None):
        try:
            if not ticker.startswith('US.'):
                ticker = 'US.' + ticker

            if date is None:
                est = pytz.timezone('US/Eastern')
                date = datetime.now(est).strftime('%Y-%m-%d')

            ret, data, _ = self.quote_ctx.request_history_kline(ticker, start=date, end=date, ktype=KLType.K_1M, extended_time=True, max_count=None)
            
            if ret != RET_OK:
                return False, []
            
            data['timestamp'] = data['time_key']
            candles_data = data[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            candles = candles_data.to_dict(orient='records')

            return True, candles
        except Exception as e:
            logging.error(f"Error getting candles for {ticker}: {e}")
            return False, []

    def subscribe_stocks(self, tickers, mode):
        subscribe_worker_path = os.path.join(os.path.dirname(__file__), "../subscribe_worker.py")
            
        for ticker in tickers:
            if ticker not in self.subscribe_processes:
                try:
                    process = subprocess.Popen(["python", subscribe_worker_path, ticker, "--mode", str(mode)])
                    with self.lock:
                        self.subscribe_processes[ticker] = {
                            'process': process,
                            'parent_pid': process.pid
                        }
                    logging.info(f"Started subscribe process for {ticker} with PID {process.pid}")
                except Exception as e:
                    logging.error(f"Error subscribing to {ticker}: {e}")

    def unsubscribe_stocks(self, tickers):
        """Unsubscribe from stocks and terminate their processes"""
        with self.lock:
            for ticker in tickers:
                if ticker in self.subscribe_processes:
                    process_info = self.subscribe_processes[ticker]
                    parent_process = process_info['process']
                    parent_pid = process_info['parent_pid']
                    
                    try:
                        # Get all child processes
                        parent = psutil.Process(parent_pid)
                        children = parent.children(recursive=True)
                        
                        # Terminate children first
                        for child in children:
                            try:
                                child.terminate()
                            except psutil.NoSuchProcess:
                                pass
                        
                        # Wait for children to terminate
                        gone, alive = psutil.wait_procs(children, timeout=5)
                        
                        # Force kill remaining children
                        for child in alive:
                            try:
                                child.kill()
                            except psutil.NoSuchProcess:
                                pass
                        
                        # Terminate parent process
                        parent_process.terminate()
                        parent_process.wait(timeout=5)
                        
                        logging.info(f"Terminated process tree for {ticker}")
                    except Exception as e:
                        logging.error(f"Error terminating process tree for {ticker}: {e}")
                    finally:
                        del self.subscribe_processes[ticker]
                        redis_manager.remove_all_stock_data(ticker)

    def get_subscribe_processes(self):
        """Get information about all running subscribe processes"""
        with self.lock:
            process_info = {}
            for ticker, process in self.subscribe_processes.items():
                process_info[ticker] = {
                    'pid': process.pid,
                    'returncode': process.returncode,
                    'alive': process.poll() is None
                }
            return process_info

    def cleanup_dead_processes(self):
        """Remove references to processes that have died"""
        with self.lock:
            dead_tickers = []
            for ticker, process in self.subscribe_processes.items():
                if process.poll() is not None:  # Process has terminated
                    dead_tickers.append(ticker)
                    logging.info(f"Process for {ticker} has died with return code {process.returncode}")
            
            for ticker in dead_tickers:
                del self.subscribe_processes[ticker]
                redis_manager.remove_all_stock_data(ticker)

    def _init_back_data(self):
        while True:
            try:
                price_filter = SimpleFilter()
                price_filter.filter_max = 12
                price_filter.stock_field = StockField.CUR_PRICE
                price_filter.is_no_filter = False
            
                float_filter = SimpleFilter()
                float_filter.filter_min = 100_000 / 1000
                float_filter.filter_max = 100_000_000 / 1000
                float_filter.stock_field = StockField.FLOAT_SHARE
                float_filter.is_no_filter = False

                avg_volume_filter = AccumulateFilter()
                avg_volume_filter.filter_min = 0
                avg_volume_filter.stock_field = StockField.VOLUME
                avg_volume_filter.days = 30
                avg_volume_filter.is_no_filter = False

                filtered_stocks = self.market_filter([price_filter, float_filter, avg_volume_filter])
                logging.info(f"Filtered stocks: {[stock['ticker'] for stock in filtered_stocks]}")

                for stock in filtered_stocks:
                    moomoo_ticker = stock['ticker']
                    redis_manager.set_float_share(moomoo_ticker, stock[float_filter.stock_field] * 1000)
                    redis_manager.set_avg_30d_volume(moomoo_ticker, stock[avg_volume_filter.stock_field])

                self._init_prev_close_prices()
                
                logging.info("Initialized back data")
            except Exception as e:
                logging.error(f"Error initializing back data: {e}")
                time.sleep(60)
                continue
            
            current_est_time = get_current_time()
            sleep_seconds = 60
            if current_est_time.hour < 16:
                post_market_start_time = current_est_time.replace(hour=16, minute=0, second=0, microsecond=0)
                sleep_seconds = (post_market_start_time - current_est_time).total_seconds()
            else:
                post_market_start_time = current_est_time.replace(hour=16, minute=0, second=0, microsecond=0) + timedelta(days=1)
                sleep_seconds = (post_market_start_time - current_est_time).total_seconds()
            logging.info(f"Sleeping for {sleep_seconds} seconds until {post_market_start_time}")
            time.sleep(sleep_seconds)

    def _init_prev_close_prices(self):
        snapshots = self.market_snapshot([ticker for ticker in redis_manager.get_tickers_in_float_share()])
        field_name = 'last_price'
        if get_current_session() == 'regular':
            field_name = 'prev_close_price'

        for _, row in snapshots.iterrows():
            redis_manager.set_prev_close_price(row['code'], row[field_name])

moomoo_manager = MoomooManager(get_config().MOOMOO_HOST, get_config().MOOMOO_PORT1)