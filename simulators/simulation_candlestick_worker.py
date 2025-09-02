#!/usr/bin/env python3
"""
Simulation Candlestick Worker
Aggregates tick data into 1-minute candlesticks and updates current candle in real-time
"""

import logging
import time
import json
import random
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, List
import pandas as pd
from config.logging import setup_logging
from services.redis_manager import redis_manager

class CandlestickAggregator:
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.current_candle = None
        self.candle_count = 0
        self.last_candle_time = None
        self.last_tick_time = None
        
    def _aggregate_ticks_to_candle(self, ticks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate tick data into a candlestick"""
        if not ticks:
            return None
        
        # Extract price and volume data
        prices = [tick['price'] for tick in ticks]
        volumes = [tick['volume'] for tick in ticks]
        timestamps = [tick['time'] for tick in ticks]
        
        # Calculate OHLCV
        open_price = prices[0]
        close_price = prices[-1]
        high_price = max(prices)
        low_price = min(prices)
        total_volume = sum(volumes)
        
        # Use the first tick's timestamp as candle timestamp
        candle_timestamp = pd.to_datetime(timestamps[0]).replace(second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
        
        # Create candlestick data
        candle_data = {
            'timestamp': candle_timestamp,
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': total_volume,
            'simulated': True,
            'ticker': self.ticker,
            'tick_count': len(ticks)
        }
        
        return candle_data
    
    def _get_current_minute_ticks(self) -> List[Dict[str, Any]]:
        """Get all ticks for the current minute from Redis"""
        try:
            # Get all tick data for this ticker
            tick_data = redis_manager.get_tick(self.ticker)
            if not tick_data:
                return []
            
            current_time = datetime.now()
            current_minute = current_time.replace(second=0, microsecond=0)
            next_minute = current_minute + timedelta(minutes=1)
            
            # Filter ticks for current minute
            current_minute_ticks = []
            for tick in tick_data:
                try:
                    tick_time = pd.to_datetime(tick['time'])
                    if current_minute <= tick_time < next_minute:
                        current_minute_ticks.append(tick)
                except Exception as e:
                    logging.debug(f"Error parsing tick time: {e}")
                    continue
            
            # Sort by timestamp
            current_minute_ticks.sort(key=lambda x: x['time'])
            
            return current_minute_ticks
            
        except Exception as e:
            logging.error(f"Error getting current minute ticks: {e}")
            return []
    
    def run_aggregation(self, duration_hours: float = 8):
        """Run the candlestick aggregation for specified duration"""
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=duration_hours)
        
        logging.info(f"Starting candlestick aggregation for {self.ticker}")
        logging.info(f"Duration: {duration_hours} hours")
        logging.info(f"Candle interval: 1 minute")
        logging.info(f"Real-time updates: Current candle updates with each tick")
        logging.info(f"Waiting for tick data to aggregate...")
        
        try:
            while datetime.now() < end_time:
                current_minute_ticks = self._get_current_minute_ticks()
                if current_minute_ticks:
                    self.current_candle = self._aggregate_ticks_to_candle(current_minute_ticks)
                    redis_manager.push_candlestick(self.ticker, self.current_candle)
                
                time.sleep(1)  # Check every 100ms for real-time updates
                
        except KeyboardInterrupt:
            logging.info("Aggregation interrupted by user")
        except Exception as e:
            logging.error(f"Error in candlestick aggregation: {e}")
        finally:
            # Finalize the last candle if it exists
            if self.current_candle and self.current_candle['tick_count'] > 0:
                self._finalize_current_candle()
            
            logging.info(f"Candlestick aggregation completed. Total candles created: {self.candle_count}")

def run(ticker: str, duration_hours: float = 8):
    """Main function to run candlestick aggregation"""
    setup_logging(file_name=f'{ticker}/simulation_candlestick_worker.log')
    
    aggregator = CandlestickAggregator(ticker)
    aggregator.run_aggregation(duration_hours)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aggregate tick data into candlesticks with real-time updates")
    parser.add_argument("ticker", type=str, help="Ticker symbol to aggregate")
    parser.add_argument("--duration", type=float, default=8.0, help="Aggregation duration in hours")
    
    args = parser.parse_args()
    
    run(args.ticker, args.duration)
