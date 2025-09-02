#!/usr/bin/env python3
"""
Simulation Master Controller
Coordinates all simulation workers for comprehensive testing of the Doppler Bot system
"""

import logging
import argparse
import time
import signal
import sys
from multiprocessing import Process
from config.logging import setup_logging
from simulators.simulation_tick_worker import run as run_tick_simulation
from simulators.simulation_candlestick_worker import run as run_candlestick_simulation
from simulators.simulation_orderbook_worker import run as run_orderbook_simulation

class SimulationMaster:
    def __init__(self, ticker: str, base_price: float = 100.0, volatility: float = 0.02):
        self.ticker = ticker
        self.base_price = base_price
        self.volatility = volatility
        self.processes = []
        self.running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logging.info(f"Received signal {signum}, shutting down simulation...")
        self.stop_simulation()
        sys.exit(0)
    
    def start_simulation(self, duration_hours: float = 8):
        """Start all simulation workers in the correct order"""
        if self.running:
            logging.warning("Simulation is already running")
            return
        
        logging.info(f"Starting comprehensive simulation for {self.ticker}")
        logging.info(f"Base price: ${self.base_price:.2f}, Volatility: {self.volatility:.4f}")
        logging.info(f"Duration: {duration_hours} hours")
        logging.info(f"Architecture: Tick → Candlestick (aggregation) + Orderbook (sync)")
        
        try:
            # Start tick simulation worker FIRST (data source)
            logging.info("Starting tick simulation worker (data source)...")
            tick_process = Process(
                target=run_tick_simulation,
                args=(self.ticker, self.base_price, self.volatility, 0.1, duration_hours),
                name=f"TickSim-{self.ticker}"
            )
            tick_process.start()
            self.processes.append(tick_process)
            logging.info("Tick simulation worker started successfully")
            
            # Wait a moment for tick data to start flowing
            time.sleep(2)
            
            # Start candlestick aggregation worker (depends on tick data)
            logging.info("Starting candlestick aggregation worker...")
            candle_process = Process(
                target=run_candlestick_simulation,
                args=(self.ticker, duration_hours),
                name=f"CandleAgg-{self.ticker}"
            )
            candle_process.start()
            self.processes.append(candle_process)
            logging.info("Candlestick aggregation worker started successfully")
            
            # Start orderbook simulation worker (synchronized with tick data)
            logging.info("Starting orderbook simulation worker...")
            orderbook_process = Process(
                target=run_orderbook_simulation,
                args=(self.ticker, self.base_price, self.volatility, duration_hours),
                name=f"OrderbookSim-{self.ticker}"
            )
            orderbook_process.start()
            self.processes.append(orderbook_process)
            logging.info("Orderbook simulation worker started successfully")
            
            self.running = True
            logging.info("All simulation workers started successfully")
            logging.info("Data flow: Tick → Candlestick (1-min aggregation) + Orderbook (price sync)")
            
            # Monitor processes
            self._monitor_processes()
            
        except Exception as e:
            logging.error(f"Error starting simulation: {e}")
            self.stop_simulation()
            raise
    
    def _monitor_processes(self):
        """Monitor all simulation processes"""
        try:
            while self.running and any(p.is_alive() for p in self.processes):
                # Check process status
                for i, process in enumerate(self.processes):
                    if not process.is_alive():
                        logging.warning(f"Process {process.name} died unexpectedly")
                        # Restart the process
                        self._restart_process(i)
                
                time.sleep(5)  # Check every 5 seconds
                
        except KeyboardInterrupt:
            logging.info("Simulation interrupted by user")
        finally:
            self.stop_simulation()
    
    def _restart_process(self, process_index: int):
        """Restart a specific simulation process"""
        if process_index >= len(self.processes):
            return
        
        old_process = self.processes[process_index]
        process_name = old_process.name
        
        logging.info(f"Restarting {process_name}")
        
        # Determine which simulation to restart
        if "TickSim" in process_name:
            new_process = Process(
                target=run_tick_simulation,
                args=(self.ticker, self.base_price, self.volatility, 0.1, 8),
                name=process_name
            )
        elif "CandleAgg" in process_name:
            new_process = Process(
                target=run_candlestick_simulation,
                args=(self.ticker, 8),
                name=process_name
            )
        elif "OrderbookSim" in process_name:
            new_process = Process(
                target=run_orderbook_simulation,
                args=(self.ticker, self.base_price, self.volatility, 8),
                name=process_name
            )
        else:
            logging.error(f"Unknown process type: {process_name}")
            return
        
        # Start new process
        new_process.start()
        self.processes[process_index] = new_process
        logging.info(f"{process_name} restarted successfully")
    
    def stop_simulation(self):
        """Stop all simulation workers"""
        if not self.running:
            return
        
        logging.info("Stopping all simulation workers...")
        self.running = False
        
        # Terminate all processes
        for process in self.processes:
            if process.is_alive():
                logging.info(f"Terminating {process.name}")
                process.terminate()
                process.join(timeout=5)
                
                # Force kill if still alive
                if process.is_alive():
                    logging.warning(f"Force killing {process.name}")
                    process.kill()
                    process.join()
        
        self.processes.clear()
        logging.info("All simulation workers stopped")
    
    def get_status(self):
        """Get current status of all simulation workers"""
        status = {
            'running': self.running,
            'ticker': self.ticker,
            'architecture': 'Tick → Candlestick (aggregation) + Orderbook (sync)',
            'processes': []
        }
        
        for process in self.processes:
            status['processes'].append({
                'name': process.name,
                'alive': process.is_alive(),
                'pid': process.pid if process.is_alive() else None
            })
        
        return status

def run_master_simulation(ticker: str, base_price: float = 100.0, volatility: float = 0.02, 
                         duration_hours: float = 8):
    """Main function to run master simulation"""
    setup_logging(file_name=f'{ticker}/simulation_master.log')
    
    master = SimulationMaster(ticker, base_price, volatility)
    
    try:
        master.start_simulation(duration_hours)
    except KeyboardInterrupt:
        logging.info("Simulation interrupted by user")
    except Exception as e:
        logging.error(f"Error in master simulation: {e}")
    finally:
        master.stop_simulation()

def run_individual_simulation(simulation_type: str, ticker: str, base_price: float = 100.0, 
                            volatility: float = 0.02, duration_hours: float = 8):
    """Run individual simulation worker"""
    setup_logging(file_name=f'{ticker}/simulation_{simulation_type}.log')
    
    if simulation_type == 'tick':
        run_tick_simulation(ticker, base_price, volatility, 0.1, duration_hours)
    elif simulation_type == 'candlestick':
        run_candlestick_simulation(ticker, duration_hours)
    elif simulation_type == 'orderbook':
        run_orderbook_simulation(ticker, base_price, volatility, duration_hours)
    else:
        logging.error(f"Unknown simulation type: {simulation_type}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Master controller for Doppler Bot simulation")
    parser.add_argument("ticker", type=str, help="Ticker symbol to simulate")
    parser.add_argument("--mode", type=str, choices=['master', 'tick', 'candlestick', 'orderbook'], 
                       default='master', help="Simulation mode")
    parser.add_argument("--base-price", type=float, default=100.0, help="Base price for simulation")
    parser.add_argument("--volatility", type=float, default=0.02, help="Price volatility (0.01 = 1%)")
    parser.add_argument("--duration", type=float, default=8.0, help="Simulation duration in hours")
    
    args = parser.parse_args()
    
    if args.mode == 'master':
        run_master_simulation(args.ticker, args.base_price, args.volatility, args.duration)
    else:
        run_individual_simulation(args.mode, args.ticker, args.base_price, args.volatility, args.duration)
