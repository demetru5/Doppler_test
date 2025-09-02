#!/usr/bin/env python3
"""
Simulation Tick Worker
Generates realistic tick data for testing the Doppler Bot system
"""

import logging
import time
import json
import random
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any
import numpy as np
from config.logging import setup_logging
from services.redis_manager import redis_manager

class TickSimulator:
    def __init__(self, ticker: str, base_price: float = 100.0, volatility: float = 0.02):
        self.ticker = ticker
        self.base_price = base_price
        self.current_price = base_price
        self.volatility = volatility
        self.last_tick_time = datetime.now()
        self.tick_count = 0
        
        # Market microstructure parameters
        self.bid_ask_spread = 0.01  # 1 cent spread
        self.min_tick_size = 0.01
        self.volume_range = (1, 100)
        
        # Time-based patterns
        self.market_open = datetime.now().replace(hour=9, minute=30, second=0, microsecond=0)
        self.market_close = datetime.now().replace(hour=16, minute=0, second=0, microsecond=0)
        
        # Volatility clustering (higher volatility during open/close)
        self.volatility_multiplier = 1.0
        
    def _calculate_volatility(self, current_time: datetime) -> float:
        """Calculate time-based volatility"""
        time_diff = (current_time - self.market_open).total_seconds()
        market_hours = (self.market_close - self.market_open).total_seconds()
        
        # Higher volatility at market open and close
        if time_diff < 1800 or time_diff > market_hours - 1800:  # First/last 30 minutes
            return self.volatility * 2.0
        elif time_diff < 3600 or time_diff > market_hours - 3600:  # First/last hour
            return self.volatility * 1.5
        else:
            return self.volatility * 0.8
    
    def _generate_price_movement(self) -> float:
        """Generate realistic price movement using random walk with mean reversion"""
        # Random walk component
        random_component = np.random.normal(0, self.volatility_multiplier * self.volatility)
        
        # Mean reversion component (tendency to return to base price)
        mean_reversion = (self.base_price - self.current_price) * 0.001
        
        # Combine components
        price_change = random_component + mean_reversion
        
        # Apply minimum tick size
        price_change = round(price_change / self.min_tick_size) * self.min_tick_size
        
        return price_change
    
    def _generate_volume(self) -> int:
        """Generate realistic volume based on price movement and time"""
        base_volume = random.randint(*self.volume_range)
        
        # Higher volume for larger price movements
        price_change_abs = abs(self.current_price - self.base_price)
        volume_multiplier = 1 + (price_change_abs / self.base_price) * 10
        
        # Time-based volume patterns
        current_time = datetime.now()
        if current_time.hour in [9, 10, 15, 16]:  # Market open/close hours
            volume_multiplier *= 1.5
        
        return int(base_volume * volume_multiplier)
    
    def _determine_tick_direction(self, price_change: float) -> str:
        """Determine if tick represents buy or sell pressure"""
        if price_change > 0:
            return "BUY"
        elif price_change < 0:
            return "SELL"
        else:
            # Random direction for no price change
            return random.choice(["BUY", "SELL"])
    
    def generate_tick(self) -> Dict[str, Any]:
        """Generate a single tick data point"""
        current_time = datetime.now()
        
        # Update volatility based on time
        self.volatility_multiplier = self._calculate_volatility(current_time)
        
        # Generate price movement
        price_change = self._generate_price_movement()
        self.current_price += price_change
        
        # Ensure price doesn't go negative
        if self.current_price <= 0:
            self.current_price = self.base_price * 0.1
        
        # Generate volume
        volume = self._generate_volume()
        
        # Determine tick direction
        tick_direction = self._determine_tick_direction(price_change)
        
        # Create tick data
        tick_data = {
            'code': self.ticker,
            'time': current_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'price': round(self.current_price, 2),
            'volume': volume,
            'ticker_direction': tick_direction,
            'simulated': True,
            'timestamp': current_time.timestamp()
        }
        
        self.tick_count += 1
        self.last_tick_time = current_time
        
        return tick_data
    
    def run_simulation(self, tick_interval: float = 0.1, duration_hours: float = 8):
        """Run the tick simulation for specified duration"""
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=duration_hours)
        
        logging.info(f"Starting tick simulation for {self.ticker}")
        logging.info(f"Base price: ${self.base_price:.2f}, Volatility: {self.volatility:.4f}")
        logging.info(f"Tick interval: {tick_interval}s, Duration: {duration_hours}h")
        
        try:
            while datetime.now() < end_time:
                tick_data = self.generate_tick()
                
                # Push to Redis using the same format as real system
                redis_manager.redis_client.rpush(f'moomoo:tick:{self.ticker}', json.dumps(tick_data))
                
                # Log every 100 ticks
                if self.tick_count % 100 == 0:
                    logging.info(f"Generated {self.tick_count} ticks, Current price: ${tick_data['price']:.2f}")
                
                time.sleep(tick_interval)
                
        except KeyboardInterrupt:
            logging.info("Simulation interrupted by user")
        except Exception as e:
            logging.error(f"Error in tick simulation: {e}")
        finally:
            logging.info(f"Tick simulation completed. Total ticks generated: {self.tick_count}")

def run(ticker: str, base_price: float = 100.0, volatility: float = 0.02, 
        tick_interval: float = 0.1, duration_hours: float = 8):
    """Main function to run tick simulation"""
    setup_logging(file_name=f'{ticker}/simulation_tick_worker.log')
    
    simulator = TickSimulator(ticker, base_price, volatility)
    simulator.run_simulation(tick_interval, duration_hours)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate tick data for testing")
    parser.add_argument("ticker", type=str, help="Ticker symbol to simulate")
    parser.add_argument("--base-price", type=float, default=100.0, help="Base price for simulation")
    parser.add_argument("--volatility", type=float, default=0.02, help="Price volatility (0.01 = 1%)")
    parser.add_argument("--tick-interval", type=float, default=0.1, help="Tick generation interval in seconds")
    parser.add_argument("--duration", type=float, default=8.0, help="Simulation duration in hours")
    
    args = parser.parse_args()
    
    run(args.ticker, args.base_price, args.volatility, args.tick_interval, args.duration)
