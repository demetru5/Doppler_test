import logging
import threading
import time
import pandas as pd
from moomoo import *
from core.socketio_instance import socketio
from services.redis_manager import redis_manager

class TradeOrderHandler(TradeOrderHandlerBase):
    """ order update push"""
    def __init__(self, account_id):
        super().__init__()
        self.account_id = account_id

    def on_recv_rsp(self, rsp_pb):
        ret, data = super(TradeOrderHandler, self).on_recv_rsp(rsp_pb)
        if ret != RET_OK:
            print(f"Failed to handle order: {data}")
            return ret, data

        if self.account_id in moomoo_accounts:
            for _, row in data.iterrows():
                moomoo_accounts[self.account_id].process_order(row)

        return ret, data

class MoomooAccount:
    def __init__(self, id, host, port, unlock_password, trading_account='cash', trading_enabled=False, trading_amount=10):
        self.logger = self._setup_account_logger(id)
        SysConfig.enable_proto_encrypt(True)
        SysConfig.set_init_rsa_file("moomoo1/rsa.txt")

        self.lock = threading.Lock()

        self.id = id
        self.host = host
        self.port = port
        self.unlock_password = unlock_password
        self.is_correct_password = False
        self.trading_account = trading_account
        self.trading_enabled = trading_enabled
        self.trading_amount = trading_amount

        self.trade_ctx = None
        self.cash_account_id = None
        self.margin_account_id = None
        self.cash_balance = None
        self.margin_balance = None
        self.cash_settled_balance = None
        self.margin_settled_balance = None
        self.cash_orders = {}
        self.margin_orders = {}
        self.cash_positions = {}
        self.margin_positions = {}
        self.buy_timestamps = {}
        self.quantity = {}

        self.trade_order_handler = TradeOrderHandler(self.id)
        self._init_trade_ctx(host, port, unlock_password)

    def _setup_account_logger(self, account_id):
        """Create a separate logger for this account"""
        import os
        from datetime import datetime
        
        # Create logs directory if it doesn't exist
        current_date = datetime.now().strftime('%Y_%m_%d')
        log_dir = f"logs/{current_date}"
        os.makedirs(log_dir, exist_ok=True)
        
        # Create account-specific log file
        log_file = os.path.join(log_dir, f"moomoo_account_{account_id}.log")
        
        # Create logger for this account
        logger = logging.getLogger(f"moomoo_account_{account_id}")
        logger.setLevel(logging.INFO)
        
        # Avoid duplicate handlers
        if not logger.handlers:
            # Create file handler
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            
            # Create formatter
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(formatter)
            
            # Add handler to logger
            logger.addHandler(file_handler)
            
            # Prevent propagation to root logger to avoid duplicate logs
            logger.propagate = False
        
        return logger

    def _init_trade_ctx(self, host, port, unlock_password):
        self.trade_ctx = OpenSecTradeContext(
            filter_trdmarket=TrdMarket.US,
            host=host,
            port=port,
            is_encrypt=True,
            security_firm=SecurityFirm.FUTUINC
        )
        self.trade_ctx.set_handler(self.trade_order_handler)
        ret, data = self.trade_ctx.unlock_trade(unlock_password)
        if ret != RET_OK:
            raise Exception(f"Failed to unlock trade: {data}")

        self.is_correct_password = True
        self._sync_account_data()

    def _sync_account_data(self):
        """Sync account data from Moomoo"""
        try:
            # Get account list
            ret, acc_list_data = self.trade_ctx.get_acc_list()
            if ret != RET_OK:
                raise Exception(f"Failed to get account list: {acc_list_data}")

            cash_account_id = acc_list_data.loc[(acc_list_data['acc_type'] == 'CASH') & (acc_list_data['trd_env'] == TrdEnv.REAL), 'acc_id']
            margin_account_id = acc_list_data.loc[(acc_list_data['acc_type'] == 'MARGIN') & (acc_list_data['trd_env'] == TrdEnv.REAL), 'acc_id']
            if len(cash_account_id) > 0:
                self.cash_account_id = cash_account_id.iloc[0]
            if len(margin_account_id) > 0:
                self.margin_account_id = margin_account_id.iloc[0]

            # Sync account balance
            self.refresh_account_balance()
            self.refresh_positions()

        except Exception as e:
            self.logger.error(f"Error syncing account data: {e}")
            raise

    def update_trading_account(self, trading_account):
        self.trading_account = trading_account
        self.refresh_account_balance()

    def update_trading_enabled(self, trading_enabled):
        self.trading_enabled = trading_enabled
        self.refresh_account_balance()

    def update_trading_amount(self, trading_amount):
        self.trading_amount = trading_amount
        self.refresh_account_balance()

    def refresh_account_balance(self):
        if self.cash_account_id:
            ret, cash_acc_info_data = self.trade_ctx.accinfo_query(trd_env=TrdEnv.REAL, acc_id=self.cash_account_id, currency=Currency.USD)
            if ret == RET_OK:
                self.cash_balance = float(cash_acc_info_data['cash'][0])
                self.cash_settled_balance = float(cash_acc_info_data['avl_withdrawal_cash'][0])
                self.logger.info(f"Synced cash balance: ${self.cash_balance:.2f} and settled cash: ${self.cash_settled_balance:.2f}")
            else:
                self.logger.error(f"Failed to sync account data: {cash_acc_info_data}")

        if self.margin_account_id:
            ret, margin_acc_info_data = self.trade_ctx.accinfo_query(trd_env=TrdEnv.REAL, acc_id=self.margin_account_id, currency=Currency.USD)
            if ret == RET_OK:
                self.margin_balance = float(margin_acc_info_data['cash'][0])
                self.margin_settled_balance = float(margin_acc_info_data['avl_withdrawal_cash'][0])
                self.logger.info(f"Synced margin balance: ${self.margin_balance:.2f} and settled margin: ${self.margin_settled_balance:.2f}")
            else:
                self.logger.error(f"Failed to sync account data: {margin_acc_info_data}")

    def can_buy(self, ticker):
        if not self.trading_enabled:
            return False, f"🔴 {self.id} No buy for {ticker}: Trading is disabled"

        if ticker in self.buy_timestamps:
            if time.time() - self.buy_timestamps[ticker] < 60:
                return False, f"🔴 {self.id} No buy for {ticker}: Already bought in the last 60 seconds"

        # if self.has_position(ticker):
        #     return False, f"🔴 {self.id} No buy for {ticker}: Already has position"

        if ticker in self.quantity and self.quantity[ticker] > 0:
            return False, f"🔴 {self.id} No buy for {ticker}: Already has position"

        # if price <= 0:
        #     return False, 'Price is invalid'

        if self.trading_account == 'cash':
            if self.trading_amount > self.cash_settled_balance:
                return False, f"🔴 {self.id} No buy for {ticker}: Trading amount is exceed settled cash"
        elif self.trading_account == 'margin':
            if self.trading_amount > self.margin_settled_balance:
                return False, f"🔴 {self.id} No buy for {ticker}: Trading amount is exceed settled margin"
        else:
            return False, f"🔴 {self.id} No buy for {ticker}: Invalid trading account"

        return True, ''

    def can_sell(self, ticker, sell_qty):
        if not self.trading_enabled:
            return False, 'System sell feature is disabled'

        positions = self.cash_positions if self.trading_account == 'cash' else self.margin_positions
        if ticker not in positions:
            return False, f'No position for {ticker}'

        if positions[ticker]['qty'] < sell_qty:
            return False, f'Insufficient position quantity: {positions[ticker]["qty"]}'

        return True, ''

    def process_order(self, row):
        self.logger.info(f"🟢 {self.id} {row['code']} {row['order_status']} {row['trd_side']} order({row['order_id']}) at {row['price']} - {row['create_time']} with quantity {row['qty']}")

        self.refresh_account_balance()
        self.refresh_positions()

    def refresh_positions(self):
        self.refresh_orders()
        if self.cash_account_id:
            ret, data = self.trade_ctx.position_list_query(acc_id=self.cash_account_id, trd_env=TrdEnv.REAL)
            if ret == RET_OK:
                cash_positions = {}
                for _, row in data.iterrows():
                    ticker = row['code']
                    cash_positions[ticker] = {
                        'ticker': ticker,
                        'qty': row['qty'],
                        'can_sell_qty': row['can_sell_qty'],
                        'average_cost': row['average_cost'],
                        'pl_ratio': row['pl_ratio'],
                        'pl_val': row['pl_val'],
                        'today_pl_val': row['today_pl_val'],
                        'today_trd_val': row['today_trd_val'],
                        'today_buy_qty': row['today_buy_qty'],
                        'today_buy_val': row['today_buy_val'],
                        'today_sell_qty': row['today_sell_qty'],
                        'today_sell_val': row['today_sell_val'],
                        'orders': self.cash_orders[ticker] if ticker in self.cash_orders else []
                    }
                with self.lock:
                    self.cash_positions = cash_positions
                try:
                    socketio.emit(f'cash_positions_{self.id}', cash_positions)
                except Exception as e:
                    self.logger.error(f"socketio is not initialized: {e}")
            else:
                self.logger.error(f"Failed to get cash positions: {data}")
        if self.margin_account_id:
            ret, data = self.trade_ctx.position_list_query(acc_id=self.margin_account_id, trd_env=TrdEnv.REAL)
            if ret == RET_OK:
                margin_positions = {}
                for _, row in data.iterrows():
                    ticker = row['code']
                    margin_positions[ticker] = {
                        'ticker': ticker,
                        'qty': row['qty'],
                        'can_sell_qty': row['can_sell_qty'],
                        'average_cost': row['average_cost'],
                        'pl_ratio': row['pl_ratio'],
                        'pl_val': row['pl_val'],
                        'today_pl_val': row['today_pl_val'],
                        'today_trd_val': row['today_trd_val'],
                        'today_buy_qty': row['today_buy_qty'],
                        'today_buy_val': row['today_buy_val'],
                        'today_sell_qty': row['today_sell_qty'],
                        'today_sell_val': row['today_sell_val'],
                        'orders': self.margin_orders[ticker] if ticker in self.margin_orders else []
                    }
                with self.lock:
                    self.margin_positions = margin_positions
                try:
                    socketio.emit(f'margin_positions_{self.id}', margin_positions)
                except Exception as e:
                    self.logger.error(f"socketio is not initialized: {e}")
            else:
                self.logger.error(f"Failed to get margin positions: {data}")

    def refresh_orders(self):
        if self.cash_account_id:
            ret, data = self.trade_ctx.order_list_query(acc_id=self.cash_account_id, trd_env=TrdEnv.REAL)
            if ret == RET_OK:
                cash_orders = {}
                for _, row in data.iterrows():
                    ticker = row['code']
                    if ticker not in cash_orders:
                        cash_orders[ticker] = []
                    cash_orders[ticker].append({
                        'ticker': ticker,
                        'trd_side': row['trd_side'],
                        'order_type': row['order_type'],
                        'order_status': row['order_status'],
                        'order_id': row['order_id'],
                        'qty': row['qty'],
                        'price': row['price'],
                        'create_time': row['create_time'],
                        'updated_time': row['updated_time'],
                        'dealt_qty': row['dealt_qty'],
                        'dealt_avg_price': row['dealt_avg_price'],
                        'session': row['session']
                    })
                with self.lock:
                    self.cash_orders = cash_orders
                try:
                    socketio.emit(f'cash_orders_{self.id}', cash_orders)
                except Exception as e:
                    self.logger.error(f"socketio is not initialized: {e}")
            else:
                self.logger.error(f"Failed to get cash orders: {data}")
        if self.margin_account_id:
            ret, data = self.trade_ctx.order_list_query(acc_id=self.margin_account_id, trd_env=TrdEnv.REAL)
            if ret == RET_OK:
                margin_orders = {}
                for _, row in data.iterrows():
                    ticker = row['code']
                    if ticker not in margin_orders:
                        margin_orders[ticker] = []
                    margin_orders[ticker].append({
                        'ticker': ticker,
                        'trd_side': row['trd_side'],
                        'order_type': row['order_type'],
                        'order_status': row['order_status'],
                        'order_id': row['order_id'],
                        'qty': row['qty'],
                        'price': row['price'],
                        'create_time': row['create_time'],
                        'updated_time': row['updated_time'],
                        'dealt_qty': row['dealt_qty'],
                        'dealt_avg_price': row['dealt_avg_price'],
                        'session': row['session']
                    })
                with self.lock:
                    self.margin_orders = margin_orders
                try:
                    socketio.emit(f'margin_orders_{self.id}', margin_orders)
                except Exception as e:
                    self.logger.error(f"socketio is not initialized: {e}")
            else:
                self.logger.error(f"Failed to get margin orders: {data}")

    def place_buy_order(self, ticker, price, quantity=1, with_trailing_stop=True):
        can_buy, reason = self.can_buy(ticker, price)
        if not can_buy:
            self.logger.info(f"🔴 {self.id} No place buy order for {ticker}: {reason}")
            return RET_ERROR, reason

        quantity = int(self.trading_amount / price)

        ret, data = self.trade_ctx.place_order(
            price=price,
            qty=quantity,
            code=ticker,
            trd_side=TrdSide.BUY,
            order_type=OrderType.NORMAL,
            acc_id=self.cash_account_id if self.trading_account == 'cash' else self.margin_account_id,
            fill_outside_rth=True,
            trd_env=TrdEnv.REAL,
            time_in_force=TimeInForce.DAY,
            session=Session.ETH,
        )

        if ret != RET_OK:
            self.logger.error(f"Failed to place buy order: {data}")
            return RET_ERROR, data

        if with_trailing_stop:
            self.place_trailing_stop_order(ticker, quantity)

        return RET_OK, data

    def place_sell_order(self, ticker, price, quantity=1):
        can_sell, reason = self.can_sell(ticker, quantity)
        if not can_sell:
            self.logger.info(f"🔴 {self.id} No place sell order for {ticker}: {reason}")
            return RET_ERROR, reason

        ret, data = self.trade_ctx.place_order(
            price=price,
            qty=quantity,
            code=ticker,
            trd_side=TrdSide.SELL,
            order_type=OrderType.NORMAL,
            acc_id=self.cash_account_id if self.trading_account == 'cash' else self.margin_account_id,
            fill_outside_rth=True,
            trd_env=TrdEnv.REAL,
            time_in_force=TimeInForce.DAY,
            session=Session.ETH
        )

        if ret != RET_OK:
            self.logger.error(f"Failed to place sell order: {data}")
            return RET_ERROR, data

        return RET_OK, data

    def place_sell_order_with_retry(self, ticker, initial_price, quantity):
        can_sell, reason = self.can_sell(ticker, quantity)
        if not can_sell:
            self.logger.info(f"🔴 {self.id} No place sell order for {ticker}: {reason}")
            return RET_ERROR, reason

        current_price = initial_price
        if current_price is None:
            orderbook = redis_manager.get_last_orderbook_snapshot(ticker)
            if orderbook and 'best_bid_price' in orderbook:
                current_price = orderbook['best_bid_price']
                self.logger.info(f"🟡 {self.id} Updated sell price for {ticker} to ${current_price:.2f} based on current bid")
            else:
                self.logger.warning(f"🟡 {self.id} Orderbook unavailable for {ticker}, Retrying with original price")
        
        while True:
            self.logger.info(f"🟡 {self.id} Attempting to sell {ticker} at ${current_price:.2f}")
            
            ret, data = self.trade_ctx.place_order(
                price=current_price,
                qty=quantity,
                code=ticker,
                trd_side=TrdSide.SELL,
                order_type=OrderType.NORMAL,
                acc_id=self.cash_account_id if self.trading_account == 'cash' else self.margin_account_id,
                fill_outside_rth=True,
                trd_env=TrdEnv.REAL,
                time_in_force=TimeInForce.DAY,
                session=Session.ETH
            )

            if ret != RET_OK:
                self.logger.error(f"🔴 {self.id} Failed to place sell order at ${current_price:.2f}: {data}")
                orderbook = redis_manager.get_last_orderbook_snapshot(ticker)
                if orderbook and 'best_bid_price' in orderbook:
                    current_price = orderbook['best_bid_price']
                    self.logger.info(f"🟡 {self.id} Updated sell price for {ticker} to ${current_price:.2f} based on current bid")
                else:
                    current_price = None
                    self.logger.warning(f"🟡 {self.id} Orderbook unavailable for {ticker}, Retrying with original price")
                continue

            order = data.iloc[0]
            order_id = order['order_id']
            
            if self._monitor_sell_order_execution(ticker, order_id, current_price, quantity):
                self.logger.info(f"🟢 {self.id} Sell order for {ticker} executed successfully at ${current_price:.2f}")
                self.quantity[ticker] -= quantity
                return RET_OK, data
            else:
                cancelled = False
                while not cancelled:
                    ret, data = self.cancel_order(order_id)
                    if ret == RET_OK:
                        cancelled = True
                    time.sleep(0.5)
                
                orderbook = redis_manager.get_last_orderbook_snapshot(ticker)
                if orderbook and 'best_bid_price' in orderbook:
                    current_price = orderbook['best_bid_price']
                    self.logger.info(f"🟡 {self.id} Updated sell price for {ticker} to ${current_price:.2f} based on current bid")
                else:
                    current_price = None
                    self.logger.warning(f"🟡 {self.id} Orderbook unavailable for {ticker}, Retrying with original price")

    def _monitor_sell_order_execution(self, ticker, order_id, price, quantity, timeout=30):
        """Monitor sell order execution with timeout"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            self.refresh_orders()
            with self.lock:
                all_orders = self.cash_orders if self.trading_account == 'cash' else self.margin_orders
            
            if ticker not in all_orders:
                time.sleep(1)
                continue
                
            tick_orders = all_orders[ticker]
            current_order = None
            
            for order in tick_orders:
                if order['order_id'] == order_id:
                    current_order = order
                    break
                    
            if not current_order:
                time.sleep(1)
                continue
                
            # Check order status
            if current_order['order_status'] == 'FILLED_ALL':
                return True
            elif current_order['order_status'] in ['CANCELLED_ALL', 'FAILED']:
                return False
            elif current_order['order_status'] == 'PARTIAL_FILLED':
                # Check if we have partial fills
                filled_qty = current_order.get('dealt_qty', 0)
                if filled_qty > 0:
                    self.logger.info(f"🟡 {self.id} Partial fill for {ticker}: {filled_qty}/{quantity} shares")
                    # Continue monitoring for remaining quantity
                    quantity = quantity - filled_qty
                    if quantity <= 0:
                        return True
                        
            time.sleep(1)
            
        self.logger.warning(f"🟡 {self.id} Sell order monitoring timeout for {ticker}")
        return False

    def modify_sell_price(self, order_id, price):
        ret, data = self.trade_ctx.modify_order(
            modify_order_op=ModifyOrderOp.NORMAL,
            order_id=order_id,
            price=price,
            trd_env=TrdEnv.REAL,
            acc_id=self.cash_account_id if self.trading_account == 'cash' else self.margin_account_id
        )

        if ret != RET_OK:
            self.logger.error(f"Failed to modify sell price: {data}")
            return RET_ERROR, data

        return RET_OK, data

    def cancel_order(self, order_id):
        try:
            ret, data = self.trade_ctx.modify_order(
                price=0,
                qty=0,
                modify_order_op=ModifyOrderOp.CANCEL,
                order_id=order_id,
                trd_env=TrdEnv.REAL,
                acc_id=self.cash_account_id if self.trading_account == 'cash' else self.margin_account_id
            )

            if ret != RET_OK:
                self.logger.error(f"Failed to cancel order: {data}")
                return RET_ERROR, data

            return RET_OK, data

        except Exception as e:
            self.logger.error(f"Failed to cancel order: {e}")
            return RET_ERROR, str(e)

    def place_trailing_stop_order(self, ticker, quantity):
        ret2, data2 = self.trade_ctx.place_order(
            price=0,
            qty=quantity,
            code=ticker,
            trd_side=TrdSide.SELL,
            order_type=OrderType.TRAILING_STOP_LIMIT,
            trail_type=TrailType.RATIO,
            trail_value=5,
            trail_spread=0.01,
            trd_env=TrdEnv.REAL,
            acc_id=self.cash_account_id if self.trading_account == 'cash' else self.margin_account_id,
            time_in_force=TimeInForce.DAY,
            fill_outside_rth=True
        )

        if ret2 != RET_OK:
            self.logger.error(f"Failed to place trailing stop order: {data2}")
            return RET_ERROR, data2

        return RET_OK, data2

    def dynamic_trailing_stop_order(self, ticker, order_id):
        while True:
            orders = redis_manager.get_account_orders(self.id)
            if ticker not in orders:
                break

            order = [item for item in orders[ticker] if item['order_id'] == order_id][0] if [item for item in orders[ticker] if item['order_id'] == order_id] else None
            if not order:
                break

            if order['order_status'] == OrderStatus.FILLED_ALL or order['order_status'] == OrderStatus.CANCELLED_ALL or order['order_status'] == OrderStatus.FAILED:
                break

            atr = redis_manager.get_technical_indicator(ticker, 'ATR', 1)
            if not atr:
                time.sleep(10)
                continue

            trail_value = atr * 1.5
            self.trade_ctx.modify_order(
                modify_order_op=ModifyOrderOp.NORMAL,
                price=order['price'],
                qty=order['qty'],
                order_id=order_id,
                acc_id=self.cash_account_id if self.trading_account == 'cash' else self.margin_account_id,
                trail_type=TrailType.AMOUNT,
                trail_value=trail_value,
            )
            self.logger.info(f"🟢 {self.id} Modified trailing stop order for {ticker} at {trail_value}")
            time.sleep(10)

    def has_position(self, ticker):
        if self.trading_account == 'cash':
            positions = self.cash_positions
        else:
            positions = self.margin_positions
        has_hold_position = ticker in positions and positions[ticker]['qty'] > 0
        return has_hold_position

    def buy_with_smart_sell(self, ticker, with_smart_sell = True):
        status, reason = self.can_buy(ticker)
        if not status:
            self.logger.error(f"Failed to buy {ticker}, {reason}")
            return False

        orderbook = redis_manager.get_last_orderbook_snapshot(ticker)
        if not orderbook:
            return False, f"🔴 {self.id} No buy for {ticker}: No orderbook snapshot"

        ask_price = orderbook['best_ask_price']
        qty = int(self.trading_amount / ask_price)
        if qty == 0:
            return False, f"🔴 {self.id} No buy for {ticker}: Qty is 0"

        ret, data = self.trade_ctx.place_order(
            price=ask_price,
            qty=qty,
            code=ticker,
            trd_side=TrdSide.BUY,
            order_type=OrderType.NORMAL,
            acc_id=self.cash_account_id if self.trading_account == 'cash' else self.margin_account_id,
            fill_outside_rth=True,
            trd_env=TrdEnv.REAL,
            time_in_force=TimeInForce.DAY,
            session=Session.ETH,
        )

        if ret != RET_OK:
            self.logger.error(f"🔴 {self.id} Failed to place buy order: {data}")
            return False

        order = data.iloc[0]
        self.buy_timestamps[ticker] = time.time()

        cancel_unfilled_thread = threading.Thread(target=self.cancel_unfilled_order, args=(ticker, order['order_id'], order['price'], order['qty'], with_smart_sell))
        cancel_unfilled_thread.start()

        return True

    def cancel_unfilled_order(self, ticker, order_id, price, qty, with_smart_sell):
        """Cancel order if it is not filled within 5 seconds"""
        time.sleep(5)
        self.refresh_orders()
        with self.lock:
            all_orders = self.cash_orders if self.trading_account == 'cash' else self.margin_orders
        if ticker not in all_orders:
            self.logger.info(f"🟡 {self.id} No order for {ticker}")
            return
        tick_orders = all_orders[ticker]
        if order_id not in [item['order_id'] for item in tick_orders]:
            self.logger.info(f"🟡 {self.id} No order {order_id} for {ticker}")
            return
        order = [item for item in tick_orders if item['order_id'] == order_id][0]
        is_filled = order['order_status'] == OrderStatus.FILLED_ALL
        if not is_filled:
            while True:
                self.logger.info(f"🟡 {self.id} Cancelling unfilled order {order_id} for {ticker}")
                ret, data = self.trade_ctx.modify_order(
                    modify_order_op=ModifyOrderOp.CANCEL,
                    order_id=order_id,
                    price=price,
                    qty=qty,
                    trd_env=TrdEnv.REAL,
                    acc_id=self.cash_account_id if self.trading_account == 'cash' else self.margin_account_id
                )
                if ret == RET_OK:
                    self.buy_timestamps.pop(ticker, None)
                    self.logger.info(f"🟢 {self.id} Cancelled unfilled order {order_id} for {ticker}")
                    break
                time.sleep(0.5)
        else:
            self.quantity[ticker] = qty
            if with_smart_sell:
                self.logger.info(f"🟢 {self.id} Starting smart sell for {ticker}")
                sell_thread = threading.Thread(target=self.smart_sell, args=(ticker, order['price'], order['qty'], order['updated_time']))
                sell_thread.start()

    def smart_sell(self, ticker, price, qty, order_filled_time):
        buy_price = price
        highest_price = price
        remaining_qty = qty
        while remaining_qty > 0:
            try:
                tick_data = redis_manager.get_tick(ticker)[-10:]
                order_filled_time_dt = pd.to_datetime(order_filled_time)
                prices_after_order = [tick['price'] for tick in tick_data if pd.to_datetime(tick['time']) > order_filled_time_dt]
                if prices_after_order:
                    highest_price = max(highest_price, max(prices_after_order))
                
                # Backup safeguard - disaster circuit breaker
                current_price = redis_manager.get_stock_price(ticker)
                if current_price < buy_price * 0.90:  # 10% drop from buy price
                    self.logger.warning(f"🚨 {ticker} Disaster circuit breaker triggered: {current_price} < {buy_price * 0.90}")
                    ret, data = self.place_sell_order_with_retry(ticker, current_price, remaining_qty)
                    if ret == RET_OK:
                        self.logger.info(f"🟢 {self.id} Emergency sell order placed for {ticker} at ${current_price}")
                        remaining_qty = 0
                        break
                    else:
                        self.logger.error(f"🔴 {self.id} Failed to place emergency sell order {ticker}: {data}")
                
                is_sell_condition, sell_price, sell_qty = self.check_sell_condition(ticker, buy_price, highest_price, remaining_qty)
                if is_sell_condition and sell_qty > 0 and sell_qty <= remaining_qty:
                    ret, data = self.place_sell_order_with_retry(ticker, sell_price, sell_qty)
                    if ret != RET_OK:
                        self.logger.error(f"🔴 {self.id} Failed to place sell order {ticker} at ${sell_price}: {data}")
                        continue
                    self.logger.info(f"🟢 {self.id} Placed sell order for {ticker} at ${sell_price}")
                    # substract sold qty from remaining qty
                    remaining_qty -= sell_qty
                    # update buy price to the sell price
                    if remaining_qty > 0:
                        buy_price = sell_price
            except Exception as e:
                self.logger.error(f"Failed while smart selling {ticker}: {e}")
            time.sleep(0.2)
            continue
    
    def check_sell_condition(self, ticker, buy_price, highest_price, remaining_qty):
        """Check if the sell condition is met"""
        try:
            price = redis_manager.get_stock_price(ticker)
            
            # 1. Dynamic profit threshold
            atr = redis_manager.get_technical_indicator(ticker, 'ATR', 1)
            if atr is not None and atr > 0:
                profit_threshold = buy_price + max(atr * 1.5, buy_price * 0.03)
            else:
                profit_threshold = buy_price * 1.05  # Fallback to 5%
            
            self.logger.info(f"{ticker} price: ${price}")
            if price > profit_threshold:
                orderbook = redis_manager.get_last_orderbook_snapshot(ticker)
                bid_price = orderbook['best_bid_price']
                sell_price = min(price, bid_price)
                sell_qty = remaining_qty//2 if remaining_qty//2 > 0 else remaining_qty
                self.logger.info(f"✅ {ticker} Price reached dynamic profit threshold: {price} > {profit_threshold}, buy_price: {buy_price}, bid_price: {bid_price}, sell_qty: {sell_qty}")
                return True, sell_price, sell_qty

            self.logger.info(f"{ticker} highest_price: ${highest_price}")
            self.logger.info(f"{ticker} remaining_qty: {remaining_qty}")

            if not atr or atr <= 0:
                self.logger.warning(f"{ticker} ATR not available, using fallback")
                atr = buy_price * 0.02  # Fallback ATR

            # 2. Adaptive ATR trailing stop based on ADX
            adx = redis_manager.get_technical_indicator(ticker, 'ADX', 1)
            if adx is not None and adx > 0:
                if adx > 30:  # Strong trend - looser stop
                    atr_multiplier = 2.0
                    self.logger.info(f"{ticker} Strong trend (ADX: {adx}), using loose stop: ATR × {atr_multiplier}")
                elif adx < 20:  # Choppy market - tighter stop
                    atr_multiplier = 1.0
                    self.logger.info(f"{ticker} Choppy market (ADX: {adx}), using tight stop: ATR × {atr_multiplier}")
                else:  # Normal market
                    atr_multiplier = 1.5
                    self.logger.info(f"{ticker} Normal market (ADX: {adx}), using standard stop: ATR × {atr_multiplier}")
            else:
                atr_multiplier = 1.5  # Default fallback
                self.logger.info(f"{ticker} ADX not available, using default stop: ATR × {atr_multiplier}")

            limit_line = highest_price - atr * atr_multiplier
            is_below_limit_line = price <= limit_line
            
            # 3. VWAP check for failed breakouts
            vwap = redis_manager.get_technical_indicator(ticker, 'VWAP', 1)
            vwap_breakdown = False
            if vwap is not None and vwap > 0:
                vwap_threshold = vwap - atr * 0.75  # 0.75 ATR below VWAP
                vwap_breakdown = price < vwap_threshold
                if vwap_breakdown:
                    self.logger.info(f"⚠️ {ticker} VWAP breakdown detected: {price} < {vwap_threshold} (VWAP: {vwap})")
            
            if is_below_limit_line or vwap_breakdown:
                orderbook = redis_manager.get_last_orderbook_snapshot(ticker)
                self.logger.info(f"{ticker} orderbook: {orderbook}")
                bid_price = orderbook['best_bid_price']
                
                # Skip imbalance check if VWAP breakdown
                if vwap_breakdown:
                    self.logger.info(f"✅ {ticker} VWAP breakdown exit triggered: {price} < {vwap_threshold}")
                    return True, bid_price, remaining_qty
                
                is_bid_dominating = orderbook['imbalance'] >= 0.6
                if is_bid_dominating:
                    self.logger.info(f"❌{ticker} Bid dominating {orderbook['imbalance']}")
                    return False, None, 0

                tick_data = redis_manager.get_tick(ticker)[-10:]
                is_strong_buy_volume = sum([tick['volume'] for tick in tick_data if tick['ticker_direction'] == 'BUY']) > sum([tick['volume'] for tick in tick_data if tick['ticker_direction'] == 'SELL'])
                self.logger.info(f"{ticker} tick_data: {tick_data}")
                if is_strong_buy_volume:
                    self.logger.info(f"❌ {ticker} is_strong_buy_volume: {is_strong_buy_volume} {sum([tick['volume'] for tick in tick_data if tick['ticker_direction'] == 'BUY'])} > {sum([tick['volume'] for tick in tick_data if tick['ticker_direction'] == 'SELL'])}")
                    return False, None, 0

                self.logger.info(f"✅ {ticker} is_below_limit_line: {is_below_limit_line}: {price} <= {limit_line}, highest_price: {highest_price}, atr: {atr}, atr_multiplier: {atr_multiplier}")
                return True, bid_price, remaining_qty

            self.logger.info(f"❌ {ticker} is_below_limit_line: {is_below_limit_line}: {price} <= {limit_line}, highest_price: {highest_price}, atr: {atr}, atr_multiplier: {atr_multiplier}")
            return False, None, 0
        except Exception as e:
            self.logger.error(f"Failed to check sell condition {ticker}: {e}")
            return False, None, 0

moomoo_accounts = {}

def load_moomoo_accounts():
    from core.db import get_db, MoomooAccount as DBMoomooAccount
    with get_db() as db:
        records = db.query(DBMoomooAccount).filter(DBMoomooAccount.status == 'approved').all()
        for record in records:
            moomoo_accounts[record.id] = MoomooAccount(record.id, record.host, record.port, record.tradingPassword, record.tradingAccount, record.tradingEnabled, record.tradingAmount)

def add_moomoo_account(account):
    try:
        moomoo_accounts[account.id] = MoomooAccount(account.id, account.host, account.port, account.tradingPassword, account.tradingAccount, account.tradingEnabled, account.tradingAmount)
        logging.info(f"Added moomoo account: {account.id} {account.host} {account.port} {account.tradingPassword} {account.tradingAccount} {account.tradingEnabled} {account.tradingAmount}")
        return True
    except Exception as e:
        logging.error(f"Error adding moomoo account: {e}")
        return False

def get_all_accounts():
    return moomoo_accounts.copy()