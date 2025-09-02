import redis
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from config import get_config
from typing import Dict, Any, List
from utils.util import get_moomoo_ticker, get_current_time

class RedisManager:
    def __init__(self):
        config = get_config()
        self.redis_client = redis.from_url(config.REDIS_URL, decode_responses=True)

    def publish(self, channel: str, message: Dict[str, Any]):
        """Publish a message to a channel"""
        try:
            self.redis_client.publish(channel, json.dumps(message))
            return True
        except Exception as e:
            logging.error(f"Failed to publish message to Redis: {e}")
            return False
        
    def set_allow_buy(self, enabled):
        """Set the allow_buy state in Redis"""
        try:
            self.redis_client.set('moomoo:allow_buy', json.dumps(enabled))
            logging.info(f"Set allow_buy to {enabled} in Redis")
            return True
        except Exception as e:
            logging.error(f"Failed to set allow_buy in Redis: {e}")
            return False
    def get_allow_buy(self):
        """Get the allow_buy state from Redis"""
        try:
            value = self.redis_client.get('moomoo:allow_buy')
            if value is None:
                return False
            return json.loads(value)
        except Exception as e:
            logging.error(f"Failed to get allow_buy from Redis: {e}")
            return False
    
    def set_account_positions(self, account_id, positions):
        """Set account state in Redis"""
        try:
            key = f'moomoo:account:{account_id}:positions'
            self.redis_client.set(key, json.dumps(positions))
            return True
        except Exception as e:
            logging.error(f"Failed to set account positions in Redis: {e}")
            return False
    def get_account_positions(self, account_id):
        """Get account positions from Redis"""
        try:
            key = f'moomoo:account:{account_id}:positions'
            value = self.redis_client.get(key)
            if value is None:
                return {}
            return json.loads(value)
        except Exception as e:
            logging.error(f"Failed to get account positions from Redis: {e}")
            return {}
    
    def set_account_orders(self, account_id, orders):
        """Set account orders in Redis"""
        try:
            key = f'moomoo:account:{account_id}:orders'
            self.redis_client.set(key, json.dumps(orders))
            return True
        except Exception as e:
            logging.error(f"Failed to set account orders in Redis: {e}")
            return False
    def get_account_orders(self, account_id):
        """Get account orders from Redis"""
        try:
            key = f'moomoo:account:{account_id}:orders'
            value = self.redis_client.get(key)
            if value is None:
                return {}
            return json.loads(value)
        except Exception as e:
            logging.error(f"Failed to get account orders from Redis: {e}")
            return {}

    def set_account_cash_balance(self, account_id, cash_balance):
        """Set account cash balance in Redis"""
        try:
            self.redis_client.set(f'moomoo:account:{account_id}:cash_balance', cash_balance)
            return True
        except Exception as e:
            logging.error(f"Failed to set account cash balance in Redis: {e}")
    def get_account_cash_balance(self, account_id):
        """Get account cash balance from Redis"""
        try:
            data = self.redis_client.get(f'moomoo:account:{account_id}:cash_balance')
            if data is None:
                return None
            return json.loads(data)
        except Exception as e:
            logging.error(f"Failed to get account cash balance from Redis: {e}")
            return None
    
    def set_account_cash_settled_balance(self, account_id, cash_settled_balance):
        """Set account cash settled balance in Redis"""
        try:
            self.redis_client.set(f'moomoo:account:{account_id}:cash_settled_balance', cash_settled_balance)
            return True
        except Exception as e:
            logging.error(f"Failed to set account cash settled balance in Redis: {e}")
    def get_account_cash_settled_balance(self, account_id):
        """Get account cash settled balance from Redis"""
        try:
            return self.redis_client.get(f'moomoo:account:{account_id}:cash_settled_balance')
        except Exception as e:
            logging.error(f"Failed to get account cash settled balance from Redis: {e}")
            return None
        
    def set_account_margin_balance(self, account_id, margin_balance):
        """Set account margin balance in Redis"""
        try:
            self.redis_client.set(f'moomoo:account:{account_id}:margin_balance', margin_balance)
            return True
        except Exception as e:
            logging.error(f"Failed to set account margin balance in Redis: {e}")
    def get_account_margin_balance(self, account_id):
        """Get account margin balance from Redis"""
        try:
            data = self.redis_client.get(f'moomoo:account:{account_id}:margin_balance')
            if data is None:
                return None
            return json.loads(data)
        except Exception as e:
            logging.error(f"Failed to get account margin balance from Redis: {e}")
            return None

    def set_account_margin_settled_balance(self, account_id, margin_settled_balance):
        """Set account margin settled balance in Redis"""
        try:
            self.redis_client.set(f'moomoo:account:{account_id}:margin_settled_balance', margin_settled_balance)
            return True
        except Exception as e:
            logging.error(f"Failed to set account margin settled balance in Redis: {e}")
    def get_account_margin_settled_balance(self, account_id):
        """Get account margin settled balance from Redis"""
        try:
            return self.redis_client.get(f'moomoo:account:{account_id}:margin_settled_balance')
        except Exception as e:
            logging.error(f"Failed to get account margin settled balance from Redis: {e}")
            return None

    def set_float_share(self, ticker: str, float_share: int):
        """Set the float share in Redis"""
        try:
            self.redis_client.set(f'float_share:{ticker}', float_share)
            return True
        except Exception as e:
            logging.error(f"Failed to set float share in Redis: {e}")
    def get_float_share(self, ticker: str):
        """Get the float share from Redis"""
        try:
            data = self.redis_client.get(f'float_share:{ticker}')
            if data is None:
                return None
            # Convert bytes to string, then to float
            return float(data)
        except Exception as e:
            logging.error(f"Failed to get float share from Redis: {e}")
            return None
    def check_float_share(self, ticker: str):
        """Check if the float share exist for the ticker"""
        try:
            return self.redis_client.exists(f'float_share:{ticker}')
        except Exception as e:
            logging.error(f"Failed to check float share in Redis: {e}")
            return False
    def get_tickers_in_float_share(self):
        """Get the tickers in float share"""
        try:
            return [item.split(':')[1] for item in self.redis_client.keys('float_share:*')]
        except Exception as e:
            logging.error(f"Failed to get tickers in float share in Redis: {e}")
            return []
        
    def set_avg_30d_volume(self, ticker: str, avg_30d_volume: float):
        """Set the avg 30d volume in Redis"""
        try:
            self.redis_client.set(f'avg_30d_volume:{ticker}', avg_30d_volume)
            return True
        except Exception as e:
            logging.error(f"Failed to set avg 30d volume in Redis: {e}")
    def get_avg_30d_volume(self, ticker: str) -> float:
        """Get the avg 30d volume from Redis"""
        try:
            data = self.redis_client.get(f'avg_30d_volume:{ticker}')
            if data is None:
                return 0
            return float(data)
        except Exception as e:
            logging.error(f"Failed to get avg 30d volume from Redis: {e}")
            return 0
    def check_avg_30d_volume(self, ticker: str):
        """Check if the avg 30d volume exist for the ticker"""
        try:
            return self.redis_client.exists(f'avg_30d_volume:{ticker}')
        except Exception as e:
            logging.error(f"Failed to check avg 30d volume in Redis: {e}")
            return False
    def get_tickers_in_avg_30d_volume(self):
        """Get the tickers in avg 30d volume"""
        try:
            return [item.split(':')[1] for item in self.redis_client.keys('avg_30d_volume:*')]
        except Exception as e:
            logging.error(f"Failed to get tickers in avg 30d volume in Redis: {e}")
            return []

    def set_prev_close_price(self, ticker: str, prev_close_price: float):
        """Set the prev close price in Redis"""
        try:
            self.redis_client.set(f'prev_close_price:{ticker}', prev_close_price)
            self.publish('socket_emit', {
                'event': 'prev_close_price',
                'data': {
                    'ticker': ticker,
                    'prev_close_price': prev_close_price
                }
            })
            return True
        except Exception as e:
            logging.error(f"Failed to set prev close price in Redis: {e}")
    def get_prev_close_price(self, ticker: str):
        """Get the prev close price from Redis"""
        try:
            data = self.redis_client.get(f'prev_close_price:{ticker}')
            if data is None:
                return None
            # Convert bytes to string, then to float
            return float(data) if isinstance(data, bytes) else float(data)
        except Exception as e:
            logging.error(f"Failed to get prev close price from Redis: {e}")
            return None
    def check_prev_close_price(self, ticker: str):
        """Check if the prev close price exist for the ticker"""
        try:
            return self.redis_client.exists(f'prev_close_price:{ticker}')
        except Exception as e:
            logging.error(f"Failed to check prev close price in Redis: {e}")
            return False
    def get_tickers_in_prev_close_price(self):
        """Get the tickers in prev close price"""
        try:
            return [item.split(':')[1] for item in self.redis_client.keys('prev_close_price:*')]
        except Exception as e:
            logging.error(f"Failed to get tickers in prev close price in Redis: {e}")
            return []

    def add_polygon_data(self, ticker: str, close: float, volume: int, timestamp: str):
        """Add a polygon message to Redis"""
        try:
            moomoo_ticker = get_moomoo_ticker(ticker)
            key = f'polygon:{moomoo_ticker}'
            self.redis_client.rpush(key, json.dumps({
                'price': close,
                'volume': volume,
                'timestamp': timestamp
            }))
            self.redis_client.ltrim(key, -500, -1)
            return True
        except Exception as e:
            logging.error(f"Failed to add polygon message to Redis: {e}")
    def get_polygon_data(self, ticker: str):
        """Get the polygon data from Redis"""
        try:
            moomoo_ticker = get_moomoo_ticker(ticker)
            data = self.redis_client.lrange(f'polygon:{moomoo_ticker}', 0, -1)
            if data is None:
                return []
            return [json.loads(item) for item in data]
        except Exception as e:
            logging.error(f"Failed to get polygon data from Redis: {e}")
            return []
    def get_polygon_tickers(self):
        """Get the polygon tickers from Redis"""
        try:
            return [item.split(':')[1] for item in self.redis_client.keys('polygon:*')]
        except Exception as e:
            logging.error(f"Failed to get polygon tickers from Redis: {e}")
            return []

    # moomoo tick data queue
    def push_tick(self, ticker: str, data: Dict[str, Any]):
        """Push tick data to Redis"""
        try:
            self.redis_client.rpush(f'moomoo:tick:{ticker}', json.dumps(data))
            return True
        except Exception as e:
            logging.error(f"Failed to push tick data to Redis: {e}")
            return False
    def get_tick(self, ticker: str):
        """Get tick data from Redis"""
        try:
            data = self.redis_client.lrange(f'moomoo:tick:{ticker}', 0, -1)
            if data is None:
                return []
            return [json.loads(item) for item in data]
        except Exception as e:
            logging.error(f"Failed to get tick data from Redis: {e}")
            return []
    def remove_old_tick(self, ticker: str):
        """Remove tick which is older than 60 seconds"""
        try:
            data = self.redis_client.lrange(f'moomoo:tick:{ticker}', 0, -1)
            if data is None:
                return False, None
            tick_data = [json.loads(item) for item in data]
            for index, item in enumerate(tick_data):
                if pd.to_datetime(item['time']) >= pd.to_datetime(tick_data[-1]['time']) - timedelta(seconds=60):
                    self.redis_client.ltrim(f'moomoo:tick:{ticker}', index, -1)
                    return True, index
            self.redis_client.delete(f'moomoo:tick:{ticker}')
            return True, len(tick_data)
        except Exception as e:
            logging.error(f"Failed to remove old tick from Redis: {e}")
            return False

    # moomoo realtime data queue
    def push_realtime(self, ticker: str, data: Dict[str, Any]):
        """Push data to Redis"""
        try:
            self.redis_client.rpush(f'moomoo:realtime:{ticker}', json.dumps(data))
            return True
        except Exception as e:
            logging.error(f"Failed to push data to Redis: {e}")
    def pop_realtime(self, ticker: str):
        """Pop data from Redis"""
        try:
            data = self.redis_client.lrange(f'moomoo:realtime:{ticker}', 0, -1)
            self.redis_client.delete(f'moomoo:realtime:{ticker}')
            if data is None:
                return []
            return [json.loads(item) for item in data]
        except Exception as e:
            logging.error(f"Failed to pop data from Redis: {e}")
            return []

    # moomoo candlestick queue
    def push_candlestick(self, ticker: str, data: Dict[str, Any]):
        """Push candlestick data to Redis"""
        try:
            self.redis_client.rpush(f'moomoo:candlestick:{ticker}', json.dumps(data))
            return True
        except Exception as e:
            logging.error(f"Failed to push candlestick data to Redis: {e}")
            return False
    def pop_candlestick(self, ticker: str):
        """Pop candlestick data from Redis"""
        try:
            data = self.redis_client.lrange(f'moomoo:candlestick:{ticker}', 0, -1)
            self.redis_client.delete(f'moomoo:candlestick:{ticker}')
            if data is None:
                return []
            return [json.loads(item) for item in data]
        except Exception as e:
            logging.error(f"Failed to pop candlestick data from Redis: {e}")
            return []    

    # moomoo orderbook queue
    def push_orderbook(self, ticker: str, data: Dict[str, Any]):
        """Push orderbook data to Redis"""
        try:
            self.redis_client.rpush(f'moomoo:orderbook:{ticker}', json.dumps(data))
            return True
        except Exception as e:
            logging.error(f"Failed to push orderbook data to Redis: {e}")
            return False
    def pop_orderbook(self, ticker: str):
        """Pop orderbook data from Redis"""
        try:
            data = self.redis_client.lrange(f'moomoo:orderbook:{ticker}', 0, -1)
            self.redis_client.delete(f'moomoo:orderbook:{ticker}')
            if data is None:
                return []
            return [json.loads(item) for item in data]
        except Exception as e:
            logging.error(f"Failed to pop orderbook data from Redis: {e}")
            return []

    def blpop_orderbook(self, ticker: str, timeout: int = 1):
        """Blocking pop for orderbook stream to enable event-driven loops."""
        try:
            key = f'moomoo:orderbook:{ticker}'
            result = self.redis_client.blpop(key, timeout=timeout)
            if not result:
                return None
            _, raw = result
            try:
                return json.loads(raw)
            except Exception:
                return None
        except Exception as e:
            logging.error(f"Failed to BLPOP orderbook from Redis: {e}")
            return None

    # stock orderbook data
    def get_orderbook(self, ticker: str):
        """Get the orderbook data from Redis"""
        try:
            orderbook = self.redis_client.lrange(f'stocks:{ticker}:orderbook', 0, -1)
            if orderbook is None:
                return []
            return [json.loads(item) for item in orderbook]
        except Exception as e:
            logging.error(f"Failed to get orderbook data from Redis: {e}")
            return []
    def update_orderbook(self, ticker: str, data: Dict[str, Any]):
        """Update the latest orderbook data in Redis"""
        try:
            self.redis_client.lset(f'stocks:{ticker}:orderbook', -1, json.dumps(data))
            return True
        except Exception as e:
            logging.error(f"Failed to update orderbook data in Redis: {e}")
            return False
    def append_orderbook(self, ticker: str, data: Dict[str, Any]):
        """Append orderbook data to Redis & Keep only last 60 seconds of data"""
        try:
            self.redis_client.rpush(f'stocks:{ticker}:orderbook', json.dumps(data))
            self.redis_client.ltrim(f'stocks:{ticker}:orderbook', -60, -1)
            self.publish('socket_emit', {
                'event': 'orderbook',
                'data': {
                    'ticker': ticker,
                    'orderbook': data
                }
            })
            return True
        except Exception as e:
            logging.error(f"Failed to append orderbook data to Redis: {e}")
            return False
    def get_last_orderbook_snapshot(self, ticker: str):
        """Get the last orderbook snapshot from Redis"""
        try:
            data = self.redis_client.lindex(f'stocks:{ticker}:orderbook', -1)
            if data is None:
                return None
            return json.loads(data)
        except Exception as e:
            logging.error(f"Failed to get last orderbook snapshot from Redis: {e}")
            return None

    def get_fast_snapshot(self, ticker: str) -> Dict[str, Any]:
        """Batch-fetch critical indicators and last orderbook snapshot via a single pipeline."""
        try:
            p = self.redis_client.pipeline()
            # Scalars (lindex -1), except ATR_Spread which uses get
            scalar_keys = ['VWAP','ATR','ADX','VWAP_Slope','EMA5','EMA4','EMA9','RVol','Volume_Ratio','ATR_to_VWAP','ATR_to_HOD','ZenP','HOD']
            for k in scalar_keys:
                p.lindex(f'stocks:{ticker}:{k}', -1)
            p.get(f'stocks:{ticker}:ATR_Spread')
            # ROC last two
            p.lrange(f'stocks:{ticker}:ROC', -2, -1)
            # Last orderbook snapshot
            p.lindex(f'stocks:{ticker}:orderbook', -1)
            results = p.execute()

            out: Dict[str, Any] = {}
            idx = 0
            for k in scalar_keys:
                val = results[idx]
                idx += 1
                try:
                    out[k] = float(val) if val is not None else 0.0
                except Exception:
                    out[k] = 0.0
            # ATR_Spread
            try:
                out['ATR_Spread'] = float(results[idx]) if results[idx] is not None else 0.0
            except Exception:
                out['ATR_Spread'] = 0.0
            idx += 1
            # ROC2
            try:
                roc_vals = results[idx] or []
                out['ROC2'] = [float(x) for x in roc_vals]
            except Exception:
                out['ROC2'] = []
            idx += 1
            # Orderbook
            try:
                ob_raw = results[idx]
                out['orderbook'] = json.loads(ob_raw) if ob_raw else None
            except Exception:
                out['orderbook'] = None
            # Current price
            out['price'] = self.get_stock_price(ticker)
            return out
        except Exception as e:
            logging.error(f"Failed to get fast snapshot for {ticker}: {e}")
            return {}

    def get_latest_snapshot(self, ticker: str) -> Dict[str, Any]:
        """Alias to get_fast_snapshot for clarity in callers that gate heavy snapshot work."""
        return self.get_fast_snapshot(ticker)

    def get_subscribed_time(self, ticker: str):
        """Get the subscribed time of a ticker"""
        try:
            return self.redis_client.get(f'stocks:{ticker}:subscribed_time')
        except Exception as e:
            logging.error(f"Failed to get subscribed time of a ticker in Redis: {e}")
            return None
    def set_subscribed_time(self, ticker: str):
        """Add a ticker to subscribed"""
        try:
            self.redis_client.set(f'stocks:{ticker}:subscribed_time', get_current_time().strftime('%Y-%m-%d %H:%M:%S'))
            self.publish('socket_emit', {
                'event': 'stock_update',
                'data': self.get_stock_data(ticker)
            })
            return True
        except Exception as e:
            logging.error(f"Failed to add ticker to subscribed in Redis: {e}")


    def set_mode(self, ticker, mode):
        try:
            return self.redis_client.sadd(f'stocks:{ticker}:mode', mode)
        except Exception as e:
            logging.error(f"Failed to set mode of stocks in Redis: {e}")
    def get_mode(self, ticker):
        try:
            mode = []
            data = self.redis_client.smembers(f'stocks:{ticker}:mode')
            if data is None:
                return []
            for item in data:
                mode.append(str(item))
            return mode
        except Exception as e:
            logging.error(f"Failed to get mode of stocks in Redis: {e}")
            return []

    def remove_all_stock_data(self, ticker: str):
        """Remove all stock data from Redis"""
        try:
            keys = self.redis_client.keys(f'stocks:{ticker}:*')
            if keys:
                self.redis_client.delete(*keys)

            self.publish('socket_emit', {
                'event': 'unsubscribe',
                'data': {
                    'ticker': ticker
                }
            })
            return True
        except Exception as e:
            logging.error(f"Failed to remove all stock data from Redis: {e}")
            return False

    def get_candles(self, ticker: str):
        """Get the candles from Redis"""
        try:
            candles = self.redis_client.lrange(f'stocks:{ticker}:candles', 0, -1)
            if candles is None:
                return []

            return [json.loads(item) for item in candles]
        except Exception as e:
            logging.error(f"Failed to get candles from Redis: {e}")
            return []
    def get_last_minute_candle(self, ticker: str):
        """Get the last minute candle from Redis"""
        try:
            data = self.redis_client.lindex(f'stocks:{ticker}:candles', -1)
            if data is None:
                return None
            return json.loads(data)
        except Exception as e:
            logging.error(f"Failed to get last minute candle from Redis: {e}")
            return None
    def push_minute_candle(self, ticker: str, data: Dict[str, Any]):
        """Push the minute candle to the buffer"""
        try:
            self.redis_client.rpush(f'stocks:{ticker}:candles', json.dumps(data))
            self.set_stock_price(ticker, data['close'])
            original_volume = self.get_stock_volume(ticker)
            self.set_stock_volume(ticker, original_volume + data['volume'])
            self.publish('socket_emit', {
                'event': 'candle',
                'data': {
                    'ticker': ticker,
                    'candle': data
                }
            })
            return True
        except Exception as e:
            logging.error(f"Failed to push minute candle to buffer in Redis: {e}")
            return False
    def update_last_minute_candle(self, ticker: str, data: Dict[str, Any]):
        """Update the last minute candle in Redis"""
        try:
            original_candle = self.get_last_minute_candle(ticker)
            self.redis_client.lset(f'stocks:{ticker}:candles', -1, json.dumps(data))
            self.set_stock_price(ticker, data['close'])
            original_volume = self.get_stock_volume(ticker) - original_candle['volume']
            self.set_stock_volume(ticker, original_volume + data['volume'])
            self.publish('socket_emit', {
                'event': 'candle',
                'data': {
                    'ticker': ticker,
                    'candle': data
                }
            })
            return True
        except Exception as e:
            logging.error(f"Failed to update last minute candle in Redis: {e}")
            return False
    def get_last_n_candles(self, ticker: str, n: int):
        """Get the last n candles from Redis"""
        try:
            data = self.redis_client.lrange(f'stocks:{ticker}:candles', -n, -1)
            if data is None:
                return []
            return [json.loads(item) for item in data]
        except Exception as e:
            logging.error(f"Failed to get last n candles from Redis: {e}")
            return []
    def merge_candles(self, ticker: str, candles: List[Dict[str, Any]]):
        """Merge candles into original candles"""
        try:
            original_candles = self.get_candles(ticker)
            for original_candle in original_candles:
                if original_candle['timestamp'] not in [c['timestamp'] for c in candles]:
                    candles.append(original_candle)
            self.redis_client.delete(f'stocks:{ticker}:candles')
            self.redis_client.rpush(f'stocks:{ticker}:candles', *[json.dumps(candle) for candle in candles])
            self.set_stock_price(ticker, candles[-1]['close'])
            self.set_stock_volume(ticker, sum([candle['volume'] for candle in candles]))
            return True
        except Exception as e:
            logging.error(f"Failed to merge candles into Redis: {e}")
            return False
    def update_candle_by_timestamp(self, ticker: str, data: Dict[str, Any]):
        """Update a specific candle in Redis by matching its timestamp, searching from most recent"""
        try:
            # Get all candles for the ticker
            candles_key = f'stocks:{ticker}:candles'
            candles = self.redis_client.lrange(candles_key, 0, -1)
            if not candles:
                return
            else:
                candles = [json.loads(item) for item in candles]

            # If no candles or the new candle is more recent than the last candle, append the new candle
            if not candles or (len(candles) > 0 and pd.to_datetime(data['timestamp']) > pd.to_datetime(candles[-1]['timestamp'])):
                self.redis_client.rpush(candles_key, json.dumps(data))
                volume = self.get_stock_volume(ticker) + data['volume']
                self.set_stock_price(ticker, data['close'])
                self.set_stock_volume(ticker, volume)
                self.publish('socket_emit', {
                    'event': 'candle',
                    'data': {
                        'ticker': ticker,
                        'candle': data
                    }
                })
                self.publish(f'stocks:{ticker}:candles', json.dumps(data))
                return True
            
            # Search from the end of the list
            original_candle = None
            for i in range(len(candles)-1, -1, -1):
                candle = candles[i]
                if candle['timestamp'] == data['timestamp']:
                    # Found matching candle - update it
                    original_candle = candle
                    
                    # Update volume calculations
                    original_volume = self.get_stock_volume(ticker) - original_candle['volume']
                    new_volume = original_volume + data['volume']
                    
                    # Perform updates
                    self.redis_client.lset(candles_key, i, json.dumps(data))

                    if i == len(candles) - 1:
                        self.set_stock_price(ticker, data['close'])
                    self.set_stock_volume(ticker, new_volume)
                    
                    # Publish update
                    self.publish('socket_emit', {
                        'event': 'candle',
                        'data': {
                            'ticker': ticker,
                            'candle': data
                        }
                    })
                    self.publish(f'stocks:{ticker}:candles', json.dumps(data))
                    return True
            return False
        except Exception as e:
            logging.error(f"Failed to update candle by timestamp in Redis: {e}")
            return False
    def get_candles_after_timestamp(self, ticker: str, timestamp: str):
        """Get the candles after a specific timestamp"""
        try:
            candles = self.redis_client.lrange(f'stocks:{ticker}:candles', 0, -1)
            if candles is None:
                return []
            return [
                json.loads(item)
                for item in candles
                if pd.to_datetime(json.loads(item)['timestamp']) > pd.to_datetime(timestamp)
            ]
        except Exception as e:
            logging.error(f"Failed to get candles after timestamp in Redis: {e}")
            return []

    def get_last_candle_time(self, ticker:str):
        """Get the last candle time from Redis"""
        try:
            data = self.redis_client.get(f'stocks:{ticker}:last_candle_time')
            if data is None:
                return None
            return data if isinstance(data, bytes) else str(data)
        except Exception as e:
            logging.error(f"Failed to get last candle time from Redis: {e}")
            return None
    def set_last_candle_time(self, ticker: str, timestamp: str):
        """Set the last candle time in Redis"""
        try:
            self.redis_client.set(f'stocks:{ticker}:last_candle_time', timestamp)
            return True
        except Exception as e:
            logging.error(f"Failed to set last candle time in Redis: {e}")
            return False

    def get_stock_price(self, ticker: str):
        """Get the current stock price from Redis"""
        try:
            price = self.redis_client.get(f'stocks:{ticker}:price')
            if price is None:
                return 0.0
            # Convert bytes to string, then to float
            return float(price) if isinstance(price, bytes) else float(price)
        except Exception as e:
            logging.error(f"Failed to get stock price from Redis: {e}")
            return 0.0
    def set_stock_price(self, ticker: str, price: float):
        """Set the current stock price in Redis"""
        try:
            self.redis_client.set(f'stocks:{ticker}:price', price)
            self.publish('socket_emit', {
                'event': 'stock_price',
                'data': {
                    'ticker': ticker,
                    'price': price
                }
            })
            return True
        except Exception as e:
            logging.error(f"Failed to set stock price in Redis: {e}")
            return False
    
    def get_stock_volume(self, ticker: str):
        """Get the current stock volume from Redis"""
        try:
            volume = self.redis_client.get(f'stocks:{ticker}:volume')
            if volume is None:
                return 0
            # Convert bytes to string, then to int
            return int(volume) if isinstance(volume, bytes) else int(volume)
        except Exception as e:
            logging.error(f"Failed to get stock volume from Redis: {e}")
            return 0
    def set_stock_volume(self, ticker: str, volume: int):
        """Set the current stock volume in Redis"""
        try:
            self.redis_client.set(f'stocks:{ticker}:volume', volume)
            self.publish('socket_emit', {
                'event': 'stock_volume',
                'data': {
                    'ticker': ticker,
                    'volume': volume
                }
            })
            return True
        except Exception as e:
            logging.error(f"Failed to set stock volume in Redis: {e}")
            return False
        
    def get_all_tickers(self):
        """Get all stocks with their complete data from Redis"""
        try:
            stock_keys = self.redis_client.keys('stocks:*:candles')
            if not stock_keys:
                return []
            
            tickers = []
            for key in stock_keys:
                try:
                    ticker = key.split(':')[1]
                    tickers.append(ticker)
                except Exception as e:
                    logging.error(f"Failed to parse stock key {key}: {e}")
                    continue
            
            return tickers
        except Exception as e:
            logging.error(f"Failed to get all stocks data from Redis: {e}")
            return []
    def get_stock_data(self, ticker: str):
        """Get all stock data from Redis"""
        try:
            mode = self.get_mode(ticker)
            price = self.get_stock_price(ticker)
            volume = self.get_stock_volume(ticker)
            float_share = self.get_float_share(ticker)
            avg_30d_volume = self.get_avg_30d_volume(ticker)
            prev_close_price = self.get_prev_close_price(ticker)
            indicators = self.get_technical_indicators(ticker)
            scores = self.get_technical_scores(ticker)
            fire_emoji_status = self.get_fire_emoji_status(ticker)
            explosion_emoji_status = self.get_explosion_emoji_status(ticker)
            stock_data = {
                'mode': mode,
                'ticker': ticker,
                'price': price,
                'volume': volume,
                'float_share': float_share,
                'avg_30d_volume': avg_30d_volume,
                'prev_close_price': prev_close_price,
                'indicators': indicators,
                'scores': scores,
                'fire_emoji_status': fire_emoji_status,
                'explosion_emoji_status': explosion_emoji_status,
            }
            return stock_data
        except Exception as e:
            logging.error(f"Failed to get stock data from Redis: {e}")
            return {}

    def get_technical_indicator(self, ticker: str, key: str, period: int):
        if period == 1:
            try:
                indicator = self.redis_client.lindex(f'stocks:{ticker}:{key}', -1)
                if not indicator:
                    return None
                return float(indicator)
            except Exception as e:
                logging.error(f"Failed to get indicator data from Redis {ticker}, {key}, {period}: {e}")
                return None
        else:
            try:
                indicators = self.redis_client.lrange(f'stocks:{ticker}:{key}', -period, -1)
                if not indicators:
                    return []
                return [float(value) for value in indicators]
            except Exception as e:
                logging.error(f"Failed to get indicator data from Redis {ticker}, {key}, {period}: {e}")
                return []
    def get_atr_spread(self, ticker: str):
        try:
            data = self.redis_client.get(f'stocks:{ticker}:ATR_Spread')
            if not data:
                return None
            return float(data)
        except Exception as e:
            logging.error(f"Failed to get ATR spread {ticker}: {e}")
            return None
    def get_key_levels(self, ticker: str):
        try:
            data = self.redis_client.get(f'stocks:{ticker}:key_levels')
            if not data:
                return []
            return json.loads(data)
        except Exception as e:
            logging.error(f"Failed to get key levels from Redis {ticker}: {e}")
            return []
    def get_support_resistance(self, ticker: str):
        try:
            data = self.redis_client.get(f'stocks:{ticker}:support_resistance')
            if not data:
                return []
            return json.loads(data)
        except Exception as e:
            logging.error(f"Failed to get support resistance from Redis {ticker}: {e}")
            return []
    def get_technical_scores(self, ticker: str):
        default_scores = {
            'technical_score': 0,
            'confirmation_score': 0,
            'volume_score': 0,
            'momentum_score': 0,
            'trend_score': 0,
            'volatility_score': 0
        }
        try:
            technical_score = self.redis_client.get(f'stocks:{ticker}:technical_score')
            confirmation_score = self.redis_client.get(f'stocks:{ticker}:confirmation_score')
            volume_score = self.redis_client.get(f'stocks:{ticker}:volume_score')
            momentum_score = self.redis_client.get(f'stocks:{ticker}:momentum_score')
            trend_score = self.redis_client.get(f'stocks:{ticker}:trend_score')
            volatility_score = self.redis_client.get(f'stocks:{ticker}:volatility_score')
            return {
                'technical_score': float(technical_score) if technical_score else 0,
                'confirmation_score': float(confirmation_score) if confirmation_score else 0,
                'volume_score': float(volume_score) if volume_score else 0,
                'momentum_score': float(momentum_score) if momentum_score else 0,
                'trend_score': float(trend_score) if trend_score else 0,
                'volatility_score': float(volatility_score) if volatility_score else 0,
            }
        except Exception as e:
            logging.error(f"Failed to get technical scores from Redis {ticker}: {e}")
            return default_scores
    def get_technical_indicators(self, ticker: str):
        default_indicators = {
            'VWAP': 0,
            'RSI': 0,
            'StochRSI_K': 0,
            'StochRSI_D': 0,
            'MACD': 0,
            'MACD_signal': 0,
            'MACD_hist': 0,
            'ADX': 0,
            'DMP': 0,
            'DMN': 0,
            'Supertrend': 0,
            'Trend': 0,
            'PSAR_L': 0,
            'PSAR_S': 0,
            'PSAR_R': 0,
            'EMA200': 0,
            'EMA21': 0,
            'EMA9': 0,
            'EMA4': 0,
            'EMA5': 0,
            'VWAP_Slope': 0,
            'Volume_Ratio': 0,
            'ROC': 0,
            'Williams_R': 0,
            'ATR': 0,
            'HOD': 0,
            'ATR_to_HOD': 0,
            'ATR_to_VWAP': 0,
            'ZenP': 0,
            'RVol': 0,
            'BB_lower': 0,
            'BB_mid': 0,
            'BB_upper': 0,
            'ATR_Spread': 0,
        }
        try:
            return {
                'VWAP': self.get_technical_indicator(ticker, 'VWAP', 1),
                'RSI': self.get_technical_indicator(ticker, 'RSI', 1),
                'StochRSI_K': self.get_technical_indicator(ticker, 'StochRSI_K', 1),
                'StochRSI_D': self.get_technical_indicator(ticker, 'StochRSI_D', 1),
                'MACD': self.get_technical_indicator(ticker, 'MACD', 1),
                'MACD_signal': self.get_technical_indicator(ticker, 'MACD_signal', 1),
                'MACD_hist': self.get_technical_indicator(ticker, 'MACD_hist', 1),
                'ADX': self.get_technical_indicator(ticker, 'ADX', 1),
                'DMP': self.get_technical_indicator(ticker, 'DMP', 1),
                'DMN': self.get_technical_indicator(ticker, 'DMN', 1),
                'Supertrend': self.get_technical_indicator(ticker, 'Supertrend', 1),
                'Trend': self.get_technical_indicator(ticker, 'Trend', 1),
                'PSAR_L': self.get_technical_indicator(ticker, 'PSAR_L', 1),
                'PSAR_S': self.get_technical_indicator(ticker, 'PSAR_S', 1),
                'PSAR_R': self.get_technical_indicator(ticker, 'PSAR_R', 1),
                'EMA200': self.get_technical_indicator(ticker, 'EMA200', 1),
                'EMA21': self.get_technical_indicator(ticker, 'EMA21', 1),
                'EMA9': self.get_technical_indicator(ticker, 'EMA9', 1),
                'EMA4': self.get_technical_indicator(ticker, 'EMA4', 1),
                'EMA5': self.get_technical_indicator(ticker, 'EMA5', 1),
                'VWAP_Slope': self.get_technical_indicator(ticker, 'VWAP_Slope', 1),
                'Volume_Ratio': self.get_technical_indicator(ticker, 'Volume_Ratio', 1),
                'ROC': self.get_technical_indicator(ticker, 'ROC', 1),
                'Williams_R': self.get_technical_indicator(ticker, 'Williams_R', 1),
                'ATR': self.get_technical_indicator(ticker, 'ATR', 1),
                'HOD': self.get_technical_indicator(ticker, 'HOD', 1),
                'ATR_to_HOD': self.get_technical_indicator(ticker, 'ATR_to_HOD', 1),
                'ATR_to_VWAP': self.get_technical_indicator(ticker, 'ATR_to_VWAP', 1),
                'ZenP': self.get_technical_indicator(ticker, 'ZenP', 1),
                'RVol': self.get_technical_indicator(ticker, 'RVol', 1),
                'BB_lower': self.get_technical_indicator(ticker, 'BB_lower', 1),
                'BB_mid': self.get_technical_indicator(ticker, 'BB_mid', 1),
                'BB_upper': self.get_technical_indicator(ticker, 'BB_upper', 1),
                'ATR_Spread': self.get_atr_spread(ticker),
            }
        except Exception as e:
            logging.error(f"Failed to get technical indicators from Redis {ticker}, {e}")
            return default_indicators

    def set_last_order_time(self, ticker: str, timestamp: str):
        """Set the last order time in Redis"""
        try:
            self.redis_client.set(f'stocks:{ticker}:last_order_time', timestamp)
            return True
        except Exception as e:
            logging.error(f"Failed to set last order time in Redis: {e}")
            return False
    def get_last_order_time(self, ticker: str):
        """Get the last order time from Redis"""
        try:
            return self.redis_client.get(f'stocks:{ticker}:last_order_time')
        except Exception as e:
            logging.error(f"Failed to get last order time from Redis: {e}")
    def set_last_order_price(self, ticker: str, price: float):
        """Set the last order price in Redis"""
        try:
            self.redis_client.set(f'stocks:{ticker}:last_order_price', price)
            return True
        except Exception as e:
            logging.error(f"Failed to set last order price in Redis: {e}")
    def get_last_order_price(self, ticker: str):
        """Get the last order price from Redis"""
        try:
            return self.redis_client.get(f'stocks:{ticker}:last_order_price')
        except Exception as e:
            logging.error(f"Failed to get last order price from Redis: {e}")
            return None
    
    def get_buffer_rows(self, ticker: str):
        """Get the buffer rows from Redis"""
        try:
            data = self.redis_client.get(f'stocks:{ticker}:buffer_rows')
            if data is None:
                return []
            return json.loads(data)
        except Exception as e:
            logging.error(f"Failed to get buffer rows from Redis: {e}")
            return []
    def set_buffer_rows(self, ticker: str, rows: List[Dict[str, Any]]):
        """Set the buffer rows in Redis"""
        try:
            self.redis_client.set(f'stocks:{ticker}:buffer_rows', json.dumps(rows))
            return True
        except Exception as e:
            logging.error(f"Failed to set buffer rows in Redis: {e}")

    def get_buffer_data(self, ticker: str):
        """Get the buffer data from Redis"""
        try:
            data = self.redis_client.get(f'stocks:{ticker}:buffer_data')
            if data is None:
                return []
            return json.loads(data)
        except Exception as e:
            logging.error(f"Failed to get buffer data from Redis: {e}")
            return []
    def set_buffer_data(self, ticker: str, data: Dict[str, Any]):
        """Set the buffer data in Redis"""
        try:
            self.redis_client.set(f'stocks:{ticker}:buffer_data', json.dumps(data))
            return True
        except Exception as e:
            logging.error(f"Failed to set buffer data in Redis: {e}")
            return False

    def push_second_candle(self, ticker: str, data: Dict[str, Any]):
        """Push the second candle to the buffer"""
        try:
            self.redis_client.rpush(f'stocks:{ticker}:buffer_data', json.dumps(data))
            self.redis_client.ltrim(f'stocks:{ticker}:buffer_data', -60, -1)
            return True
        except Exception as e:
            logging.error(f"Failed to push second candle to buffer in Redis: {e}")

    def get_last_second_candle(self, ticker: str):
        """Get the last second candle from the buffer"""
        try:
            data = self.redis_client.lindex(f'stocks:{ticker}:buffer_data', -1)
            if data is None:
                return None
            return json.loads(data)
        except Exception as e:
            logging.error(f"Failed to get last second candle from buffer in Redis: {e}")
            return None

    def push_realtime_data(self, ticker: str, data: Dict[str, Any]):
        """Push the realtime data to the buffer"""
        try:
            self.redis_client.rpush(f'stocks:{ticker}:realtime_data', json.dumps(data))
            return True
        except Exception as e:
            logging.error(f"Failed to push realtime data to buffer in Redis: {e}")
            return False
    def pop_realtime_data(self, ticker: str):
        """Pop the realtime data from the buffer"""
        try:
            data = self.redis_client.lrange(f'stocks:{ticker}:realtime_data', 0, -1)
            self.redis_client.delete(f'stocks:{ticker}:realtime_data')
            if data is None:
                return []
            return [json.loads(item) for item in data]
        except Exception as e:
            logging.error(f"Failed to get realtime data from buffer in Redis: {e}")
            return []

    def get_market_context(self):
        """Get the market context from Redis"""
        try:
            data = self.redis_client.get('market_context')
            if data is None:
                return None
            return json.loads(data)
        except Exception as e:
            logging.error(f"Failed to get market context from Redis: {e}")
            return None
    def set_market_context(self, market_context: Dict[str, Any]):
        """Set the market context in Redis"""
        try:
            self.redis_client.set('market_context', json.dumps(market_context))
            self.publish('socket_emit', {
                'event': 'market_context',
                'data': market_context
            })
            return True
        except Exception as e:
            logging.error(f"Failed to set market context in Redis: {e}")

    def set_fire_emoji_status(self, ticker: str, fire_emoji_status: bool):
        """Set the fire emoji in Redis"""
        try:
            original_fire_emoji_status = self.get_fire_emoji_status(ticker)
            self.redis_client.set(f'stocks:{ticker}:fire_emoji_status', json.dumps(fire_emoji_status))
            if original_fire_emoji_status != fire_emoji_status:
                self.publish('socket_emit', {
                    'event': 'fire_emoji_status',
                    'data': {
                        'ticker': ticker,
                        'fire_emoji_status': fire_emoji_status
                    }
                })
            return True
        except Exception as e:
            logging.error(f"Failed to set fire emoji in Redis: {e}")
    def get_fire_emoji_status(self, ticker: str):
        """Get the fire emoji from Redis"""
        try:
            data = self.redis_client.get(f'stocks:{ticker}:fire_emoji_status')
            if data is None:
                return False
            return json.loads(data)
        except Exception as e:
            logging.error(f"Failed to get fire emoji from Redis: {e}")
            return False

    def set_explosion_emoji_status(self, ticker: str, explosion_emoji_status: bool):
        """Set the explosion emoji status in Redis"""
        try:
            original_explosion_emoji_status = self.get_explosion_emoji_status(ticker)
            self.redis_client.set(f'stocks:{ticker}:explosion_emoji_status', json.dumps(explosion_emoji_status))
            if original_explosion_emoji_status != explosion_emoji_status:
                self.publish('socket_emit', {
                    'event': 'explosion_emoji_status',
                    'data': {
                        'ticker': ticker,
                        'explosion_emoji_status': explosion_emoji_status
                    }
                })
            return True
        except Exception as e:
            logging.error(f"Failed to set explosion emoji status in Redis: {e}")
    def get_explosion_emoji_status(self, ticker: str):
        """Get the explosion emoji status from Redis"""
        try:
            data = self.redis_client.get(f'stocks:{ticker}:explosion_emoji_status')
            if data is None:
                return False
            return json.loads(data)
        except Exception as e:
            logging.error(f"Failed to get explosion emoji status from Redis: {e}")
            return False

    def get_current_strategy(self, ticker: str):
        """Get the current strategy from Redis"""
        try:
            data = self.redis_client.get(f'stocks:{ticker}:strategy')
            if data is None:
                return None
            return json.loads(data)
        except Exception as e:
            logging.error(f"Failed to get current strategy from Redis: {e}")
            return None
    def set_current_strategy(self, ticker: str, strategy: Dict[str, Any]):
        """Set the current strategy in Redis"""
        try:
            self.redis_client.set(f'stocks:{ticker}:strategy', json.dumps(strategy))
            self.publish('socket_emit', {
                'event': 'strategy',
                'data': {
                    'ticker': ticker,
                    'strategy': strategy
                }
            })
            return True
        except Exception as e:
            logging.error(f"Failed to set current strategy in Redis: {e}")

    def get_strategy_history(self, ticker: str):
        """Get the strategy history from Redis"""
        try:
            data = self.redis_client.lrange(f'stocks:{ticker}:strategy_history', 0, -1)
            if data is None:
                return []
            return [json.loads(item) for item in data]
        except Exception as e:
            logging.error(f"Failed to get strategy history from Redis: {e}")
            return []
    def add_strategy_to_history(self, ticker: str, strategy: Dict[str, Any]):
        """Add a strategy to the history in Redis"""
        try:
            self.redis_client.rpush(f'stocks:{ticker}:strategy_history', json.dumps(strategy))
            return True
        except Exception as e:
            logging.error(f"Failed to add strategy to history in Redis: {e}")
            return False

    def check_choppy_market(self, ticker: str):
        """Check if the market is choppy"""
        try:
            return self.redis_client.get(f'stocks:{ticker}:choppy_market')
        except Exception as e:
            logging.error(f"Failed to check choppy market in Redis: {e}")
            return False

# Global Redis manager instance
redis_manager = RedisManager() 