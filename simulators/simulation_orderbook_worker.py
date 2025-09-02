#!/usr/bin/env python3
"""
Simulation Orderbook Worker
Generates realistic orderbook data synchronized with tick prices for testing the Doppler Bot system
"""

import logging
import time
import json
import random
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
import numpy as np
from config.logging import setup_logging
from services.redis_manager import redis_manager

class OrderbookSimulator:
    def __init__(self, ticker: str, base_price: float = 100.0, volatility: float = 0.02):
        self.ticker = ticker
        self.base_price = base_price
        self.current_price = base_price
        self.volatility = volatility
        self.orderbook_count = 0
        
        # Orderbook parameters
        self.depth_levels = 10  # Number of bid/ask levels
        self.min_tick_size = 0.01
        self.update_interval = 0.1  # Update every 100ms
        
        # Market microstructure parameters
        self.base_spread = 0.02  # 2 cent base spread
        self.spread_volatility = 0.005  # Spread variation
        self.volume_decay = 0.7  # Volume decreases with distance from mid
        
        # Market session parameters
        self.market_open = datetime.now().replace(hour=9, minute=30, second=0, microsecond=0)
        self.market_close = datetime.now().replace(hour=16, minute=0, second=0, microsecond=0)
        
        # Initialize orderbook
        self.bids = []
        self.asks = []
        self._initialize_orderbook()
        
        # Track last tick price for synchronization
        self.last_tick_price = base_price
        self.last_tick_time = None
        
    def _initialize_orderbook(self):
        """Initialize the orderbook with realistic bid/ask levels"""
        mid_price = self.current_price
        
        # Generate bid levels (below mid price)
        for i in range(self.depth_levels):
            price_offset = (i + 1) * self.min_tick_size
            bid_price = mid_price - price_offset
            
            # Volume decreases with distance from mid
            base_volume = random.randint(100, 1000)
            volume = int(base_volume * (self.volume_decay ** i))
            
            self.bids.append((round(bid_price, 2), volume))
        
        # Generate ask levels (above mid price)
        for i in range(self.depth_levels):
            price_offset = (i + 1) * self.min_tick_size
            ask_price = mid_price + price_offset
            
            # Volume decreases with distance from mid
            base_volume = random.randint(100, 1000)
            volume = int(base_volume * (self.volume_decay ** i))
            
            self.asks.append((round(ask_price, 2), volume))
        
        # Sort bids (descending) and asks (ascending)
        self.bids.sort(key=lambda x: x[0], reverse=True)
        self.asks.sort(key=lambda x: x[0])
    
    def _get_latest_tick_price(self) -> float:
        """Get the latest tick price from Redis to synchronize orderbook"""
        try:
            tick_data = redis_manager.get_tick(self.ticker)
            if not tick_data:
                return self.current_price
            
            # Get the most recent tick
            latest_tick = tick_data[-1]
            latest_price = latest_tick.get('price', self.current_price)
            latest_time = latest_tick.get('time', None)
            
            # Only update if we have a new tick
            if latest_time != self.last_tick_time:
                self.last_tick_time = latest_time
                self.last_tick_price = latest_price
                return latest_price
            
            return self.last_tick_price
            
        except Exception as e:
            logging.debug(f"Error getting latest tick price: {e}")
            return self.current_price
    
    def _calculate_spread(self) -> float:
        """Calculate current bid-ask spread"""
        if not self.bids or not self.asks:
            return self.base_spread
        
        best_bid = self.bids[0][0]
        best_ask = self.asks[0][0]
        return best_ask - best_bid
    
    def _update_orderbook_to_price(self, new_price: float):
        """Update orderbook to match the new tick price"""
        if abs(new_price - self.current_price) < self.min_tick_size:
            return  # No significant price change
        
        old_mid = (self.bids[0][0] + self.asks[0][0]) / 2 if self.bids and self.asks else self.current_price
        price_change = new_price - old_mid
        
        # Adjust all bid prices
        self.bids = [(round(bid[0] + price_change, 2), bid[1]) for bid in self.bids]
        
        # Adjust all ask prices
        self.asks = [(round(ask[0] + price_change, 2), ask[1]) for ask in self.asks]
        
        # Remove negative prices
        self.bids = [bid for bid in self.bids if bid[0] > 0]
        self.asks = [ask for ask in self.asks if ask[0] > 0]
        
        # Ensure we have enough levels
        while len(self.bids) < self.depth_levels:
            lowest_bid = self.bids[-1][0] if self.bids else new_price - self.min_tick_size
            new_bid_price = lowest_bid - self.min_tick_size
            if new_bid_price > 0:
                volume = random.randint(100, 1000)
                self.bids.append((round(new_bid_price, 2), volume))
        
        while len(self.asks) < self.depth_levels:
            highest_ask = self.asks[-1][0] if self.asks else new_price + self.min_tick_size
            new_ask_price = highest_ask + self.min_tick_size
            volume = random.randint(100, 1000)
            self.asks.append((round(new_ask_price, 2), volume))
        
        # Sort and maintain depth
        self.bids.sort(key=lambda x: x[0], reverse=True)
        self.asks.sort(key=lambda x: x[0])
        self.bids = self.bids[:self.depth_levels]
        self.asks = self.asks[:self.depth_levels]
        
        self.current_price = new_price
    
    def _simulate_order_flow(self):
        """Simulate realistic order flow patterns"""
        # Randomly add new orders
        if random.random() < 0.3:  # 30% chance to add new order
            side = random.choice(['bid', 'ask'])
            if side == 'bid':
                # Add new bid level
                if len(self.bids) < self.depth_levels + 2:
                    lowest_bid = self.bids[-1][0] if self.bids else self.current_price - self.min_tick_size
                    new_price = lowest_bid - self.min_tick_size
                    if new_price > 0:
                        volume = random.randint(100, 1000)
                        self.bids.append((round(new_price, 2), volume))
            else:
                # Add new ask level
                if len(self.asks) < self.depth_levels + 2:
                    highest_ask = self.asks[-1][0] if self.asks else self.current_price + self.min_tick_size
                    new_price = highest_ask + self.min_tick_size
                    volume = random.randint(100, 1000)
                    self.asks.append((round(new_price, 2), volume))
        
        # Randomly modify existing orders
        if random.random() < 0.2:  # 20% chance to modify order
            if self.bids and random.random() < 0.5:
                # Modify random bid
                idx = random.randint(0, min(len(self.bids) - 1, 4))  # Top 5 levels
                old_price, old_volume = self.bids[idx]
                new_volume = max(1, int(old_volume * random.uniform(0.5, 1.5)))
                self.bids[idx] = (old_price, new_volume)
            
            if self.asks and random.random() < 0.5:
                # Modify random ask
                idx = random.randint(0, min(len(self.asks) - 1, 4))  # Top 5 levels
                old_price, old_volume = self.asks[idx]
                new_volume = max(1, int(old_volume * random.uniform(0.5, 1.5)))
                self.asks[idx] = (old_price, new_volume)
        
        # Sort and maintain depth
        self.bids.sort(key=lambda x: x[0], reverse=True)
        self.asks.sort(key=lambda x: x[0])
        self.bids = self.bids[:self.depth_levels]
        self.asks = self.asks[:self.depth_levels]
    
    def _maintain_spread(self):
        """Ensure spread stays within reasonable bounds"""
        current_spread = self._calculate_spread()
        target_spread = self.base_spread + np.random.normal(0, self.spread_volatility)
        
        if current_spread < target_spread * 0.5:  # Spread too tight
            # Widen spread by adjusting ask prices up
            spread_adjustment = (target_spread - current_spread) / 2
            self.asks = [(round(ask[0] + spread_adjustment, 2), ask[1]) for ask in self.asks]
        
        elif current_spread > target_spread * 2:  # Spread too wide
            # Tighten spread by adjusting bid prices up
            spread_adjustment = (current_spread - target_spread) / 2
            self.bids = [(round(bid[0] + spread_adjustment, 2), bid[1]) for bid in self.bids]
    
    def generate_orderbook(self) -> Dict[str, Any]:
        """Generate a single orderbook snapshot synchronized with tick data"""
        # Get latest tick price and update orderbook
        latest_tick_price = self._get_latest_tick_price()
        self._update_orderbook_to_price(latest_tick_price)
        
        # Simulate order flow (add/remove orders)
        self._simulate_order_flow()
        
        # Maintain spread within reasonable bounds
        self._maintain_spread()
        
        # Create orderbook data in the format expected by the system
        orderbook_data = {
            'code': self.ticker,
            'Bid': self.bids.copy(),
            'Ask': self.asks.copy(),
            'timestamp': time.time(),
            'simulated': True,
            'tick_price': latest_tick_price
        }
        
        self.orderbook_count += 1
        return orderbook_data
    
    def run_simulation(self, duration_hours: float = 8):
        """Run the orderbook simulation for specified duration"""
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=duration_hours)
        
        logging.info(f"Starting orderbook simulation for {self.ticker}")
        logging.info(f"Base price: ${self.base_price:.2f}, Volatility: {self.volatility:.4f}")
        logging.info(f"Update interval: {self.update_interval}s, Duration: {duration_hours}h")
        logging.info(f"Depth levels: {self.depth_levels}")
        logging.info(f"Synchronizing with tick data...")
        
        try:
            while datetime.now() < end_time:
                orderbook_data = self.generate_orderbook()
                
                # Push to Redis using the same format as real system
                redis_manager.push_orderbook(self.ticker, orderbook_data)
                
                # Log every 100 updates
                if self.orderbook_count % 100 == 0:
                    best_bid = orderbook_data['Bid'][0][0] if orderbook_data['Bid'] else 0
                    best_ask = orderbook_data['Ask'][0][0] if orderbook_data['Ask'] else 0
                    spread = best_ask - best_bid if best_bid and best_ask else 0
                    tick_price = orderbook_data.get('tick_price', 0)
                    logging.info(f"Generated {self.orderbook_count} orderbooks, Tick: ${tick_price:.2f}, Mid: ${(best_bid + best_ask) / 2:.2f}, Spread: ${spread:.3f}")
                
                time.sleep(self.update_interval)
                
        except KeyboardInterrupt:
            logging.info("Simulation interrupted by user")
        except Exception as e:
            logging.error(f"Error in orderbook simulation: {e}")
        finally:
            logging.info(f"Orderbook simulation completed. Total orderbooks generated: {self.orderbook_count}")

def run(ticker: str, base_price: float = 100.0, volatility: float = 0.02, duration_hours: float = 8):
    """Main function to run orderbook simulation"""
    setup_logging(file_name=f'{ticker}/simulation_orderbook_worker.log')
    
    simulator = OrderbookSimulator(ticker, base_price, volatility)
    simulator.run_simulation(duration_hours)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate orderbook data synchronized with ticks for testing")
    parser.add_argument("ticker", type=str, help="Ticker symbol to simulate")
    parser.add_argument("--base-price", type=float, default=100.0, help="Base price for simulation")
    parser.add_argument("--volatility", type=float, default=0.02, help="Price volatility (0.01 = 1%)")
    parser.add_argument("--duration", type=float, default=8.0, help="Simulation duration in hours")
    
    args = parser.parse_args()
    
    run(args.ticker, args.base_price, args.volatility, args.duration)
