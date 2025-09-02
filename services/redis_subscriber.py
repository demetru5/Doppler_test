import time
import threading
import logging
import json
from moomoo import OrderType

class RedisSubscriber:
    def __init__(self):
        self.running = False
        self.thread = None

    def start(self):
        """Start the redis subscriber thread"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.subscribe, daemon=True)
            self.thread.start()
            logging.info("Redis subscriber started")

    def stop(self):
        """Stop the redis subscriber thread"""
        self.running = False
        if self.thread:
            self.thread.join()
            logging.info("Redis subscriber stopped")

    def subscribe(self):
        from core.socketio_instance import socketio
        from services.redis_manager import redis_manager
        from services.moomoo_manager import moomoo_manager
        from services.moomoo_account import moomoo_accounts
        
        pubsub = redis_manager.redis_client.pubsub()
        pubsub.subscribe('socket_emit', 'subscribe', 'unsubscribe', 'trade_signal')
        while self.running:
            try:
                for message in pubsub.listen():
                    if message['type'] == 'message':
                        if message['channel'] == 'trade_signal':
                            logging.info(f"Received redis message: {message['channel']}, {message['data']}")
                            data = json.loads(message['data'])
                            if data['type'] == 'rapid_10_percent':
                                ticker = data['ticker']
                                price = redis_manager.get_stock_price(ticker)
                                for _, moomoo_account in moomoo_accounts.items():
                                    moomoo_account.place_buy_order(ticker, round(price*1.01, 2))
                            elif data['type'] == 'ema_cross_up':
                                ticker = data['ticker']
                                for _, moomoo_account in moomoo_accounts.items():
                                    moomoo_account.buy_with_smart_sell(ticker)
                            elif data['type'] == 'vwap_approach':
                                ticker = data['ticker']
                                for _, moomoo_account in moomoo_accounts.items():
                                    moomoo_account.buy_with_smart_sell(ticker)
                            elif data['type'] == 'green':
                                ticker = data['ticker']
                                for _, moomoo_account in moomoo_accounts.items():
                                    moomoo_account.buy_with_smart_sell(ticker)
                            # elif data['type'] == 'trading_coach':
                            #     ticker = data['ticker']
                            #     status = data['status']
                            #     price = redis_manager.get_stock_price(ticker)
                            #     if status == 'entry':
                            #         for _, moomoo_account in moomoo_accounts.items():
                            #             moomoo_account.buy_with_smart_sell(ticker)
                            #     elif status == 'target':
                            #         for _, moomoo_account in moomoo_accounts.items():
                            #             remaining_quantity = moomoo_account.quantity.get(ticker, 0)
                            #             sell_quantity = int(remaining_quantity * 0.5)
                            #             if sell_quantity > 0:
                            #                 moomoo_account.place_sell_order_with_retry(ticker, None, sell_quantity)
                            #     elif status == 'exit':
                            #         for _, moomoo_account in moomoo_accounts.items():
                            #             remaining_quantity = moomoo_account.quantity.get(ticker, 0)
                            #             if remaining_quantity > 0:
                            #                 moomoo_account.place_sell_order_with_retry(ticker, None, remaining_quantity)
                        elif message['channel'] == 'socket_emit':
                            data = json.loads(message['data'])
                            socketio.emit(data['event'], data['data'])
                        elif message['channel'] == 'subscribe':
                            data = json.loads(message['data'])
                            tickers = data['tickers']
                            mode = data['mode']
                            moomoo_manager.subscribe_stocks(tickers, mode)
                        elif message['channel'] == 'unsubscribe':
                            data = json.loads(message['data'])
                            tickers = data['tickers']
                            moomoo_manager.unsubscribe_stocks(tickers)
            except Exception as e:
                logging.error(f"Error in redis subscriber: {e}")
                time.sleep(1)

redis_subscriber = RedisSubscriber()