import logging
import time
from typing import List, Tuple
import pandas as pd
from config.logging import setup_logging
from services.redis_manager import redis_manager

def run(ticker):
    setup_logging(file_name=f'{ticker}/orderbook_process_worker.log')

    while True:
        try:
            orderbook_data = redis_manager.pop_orderbook(ticker)
            if not orderbook_data:
                time.sleep(0.1)
                continue
            
            orderbook = orderbook_data[-1]
            prev_orderbook = orderbook_data[-2] if len(orderbook_data) >= 2 else None
            
            if orderbook is None:
                time.sleep(0.1)
                continue
            
            bids: List[Tuple[float, float]] = orderbook['Bid']
            asks: List[Tuple[float, float]] = orderbook['Ask']

            if not bids or not asks:
                logging.debug("Empty L2 snapshot; skipping.")
                time.sleep(0.05)
                continue

            bid_volume = bids[0][1]
            best_bid_price = bids[0][0]
            ask_volume = asks[0][1]
            best_ask_price = asks[0][0]

            # Tape microstructure from recent ticks (~3s window)
            aggressor_ratio = 0.5
            uptick_seq = 0
            ticks = redis_manager.get_tick(ticker)
            if ticks:
                try:
                    now_ts = pd.to_datetime(ticks[-1]['time'])
                    recent_ticks = [t for t in reversed(ticks) if pd.to_datetime(t['time']) >= now_ts - pd.Timedelta(seconds=3)]
                    buy_vol = sum(t.get('volume', 0) for t in recent_ticks if t.get('ticker_direction') == 'BUY')
                    sell_vol = sum(t.get('volume', 0) for t in recent_ticks if t.get('ticker_direction') == 'SELL')
                    total = buy_vol + sell_vol
                    aggressor_ratio = (buy_vol / total) if total > 0 else 0.5
                    for t in recent_ticks:
                        td = t.get('ticker_direction')
                        if td == 'BUY':
                            uptick_seq += 1
                        elif td == 'SELL':
                            break
                        else:
                            continue
                except Exception:
                    aggressor_ratio = 0.5
                    uptick_seq = 0

            # Ask sweep/depletion and bid reload from last two snapshots
            sweep_flag = False
            reload_flag = False
            if prev_orderbook:
                try:
                    prev_asks: List[Tuple[float, float]] = prev_orderbook.get('Ask', [])
                    prev_bids: List[Tuple[float, float]] = prev_orderbook.get('Bid', [])
                    if not prev_asks or not prev_bids:
                        raise ValueError("Previous L2 snapshot empty")
                    prev_best_ask_price = prev_asks[0][0]
                    prev_best_bid_price = prev_bids[0][0]
                    prev_top5_ask = sum(x[1] for x in prev_asks[:5])
                    curr_top5_ask = sum(x[1] for x in asks[:5])
                    depletion = 0.0
                    if prev_top5_ask > 0:
                        depletion = (prev_top5_ask - curr_top5_ask) / prev_top5_ask
                    # Sweep if top-of-book ask depleted materially OR best ask hopped with shrink
                    if depletion >= 0.5 or (best_ask_price > prev_best_ask_price and depletion > 0):
                        sweep_flag = True
                    prev_best_bid_size = prev_bids[0][1]
                    curr_best_bid_size = bids[0][1]
                    # Reload if same price OR slight defensive step-down but size grows ≥50%
                    if prev_best_bid_size > 0 and ((best_bid_price <= prev_best_bid_price) and ((curr_best_bid_size - prev_best_bid_size) / prev_best_bid_size) >= 0.5):
                        growth = (curr_best_bid_size - prev_best_bid_size) / prev_best_bid_size
                        reload_flag = growth >= 0.5
                except Exception:
                    sweep_flag = False
                    reload_flag = False

            data = {
                'timestamp': time.time(),
                # bids
                'bids': [(bid[0], bid[1]) for bid in bids],
                'best_bid_price': best_bid_price,
                'avg_bid_price': sum(bid[0] for bid in bids) / len(bids) if len(bids) > 0 else 0,
                'bid_volume': bid_volume,
                # asks
                'asks': [(ask[0], ask[1]) for ask in asks],
                'best_ask_price': best_ask_price,
                'avg_ask_price': sum(ask[0] for ask in asks) / len(asks) if len(asks) > 0 else 0,
                'ask_volume': ask_volume,
                # total
                'imbalance': bid_volume / (bid_volume + ask_volume) if (bid_volume + ask_volume) > 0 else 0,
                'total_volume': bid_volume + ask_volume,
                # microstructure
                'aggressor_ratio': aggressor_ratio,
                'uptick_seq': uptick_seq,
                'sweep_flag': sweep_flag,
                'reload_flag': reload_flag,
            }

            redis_manager.append_orderbook(ticker, data)
            # logging.info(f"Orderbook processed: {data}")
                
        except Exception as e:
            logging.error(f"Error in aggregate worker: {e}", exc_info=True)
        
        time.sleep(0.05)