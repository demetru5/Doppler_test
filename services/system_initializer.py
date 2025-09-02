import logging
import threading
import time
from typing import Dict, Any
from core.db import init_db

class SystemInitializer:
    """System initialization service for managing startup and shutdown"""
    
    def __init__(self):
        self.initialization_complete = False
        self.initialization_lock = threading.Lock()
    
    def initialize_system(self) -> bool:
        """Initialize the entire system on startup"""
        try:
            with self.initialization_lock:
                if self.initialization_complete:
                    logging.info("System already initialized")
                    return True
                
                logging.info("Starting system initialization...")

                # Step 1: Initialize database
                init_db()

                # Step 2: Initialize Redis
                self._init_redis_manager()

                # Step 3: Initialize Moomoo manager
                self._init_moomoo_manager()
                
                # Step 4: Load and initialize Moomoo accounts
                self._init_moomoo_accounts()

                # Step 5: Initialize Redis subscriber
                self._init_redis_subscriber()
                
                self.initialization_complete = True
                logging.info("System initialization completed successfully")
                return True
                
        except Exception as e:
            logging.error(f"System initialization failed: {e}")
            return False
    
    def _init_redis_manager(self):
        """Initialize Redis connection"""
        try:
            from services.redis_manager import redis_manager
            redis_manager.redis_client.flushall()
            logging.info("Redis connection established and flushed")
        except Exception as e:
            logging.error(f"Redis initialization failed: {e}")
            raise
    
    def _init_moomoo_manager(self):
        """Initialize Moomoo manager"""
        try:
            from services.moomoo_manager import moomoo_manager
            logging.info("Moomoo manager initialized")
        except Exception as e:
            logging.error(f"Moomoo manager initialization failed: {e}")
            raise

    def _init_moomoo_accounts(self):
        """Initialize Moomoo accounts from database"""
        try:
            from services.moomoo_account import load_moomoo_accounts, get_all_accounts
            
            # Load accounts from database
            logging.info("Loading Moomoo accounts from database...")
            load_moomoo_accounts()
            
            # Verify loaded accounts
            loaded_accounts = get_all_accounts()
            logging.info(f"Loaded {len(loaded_accounts)} Moomoo accounts")
            
            # Log account details
            for account_id, account in loaded_accounts.items():
                logging.info(f"Account {account_id}: {account.trading_account} account, "
                           f"Trading: {'enabled' if account.trading_enabled else 'disabled'}, "
                           f"Amount: ${account.trading_amount:.2f}")

        except Exception as e:
            logging.error(f"Moomoo accounts initialization failed: {e}")
            raise

    def _init_redis_subscriber(self):
        """Initialize Redis subscriber"""
        try:
            from services.redis_subscriber import redis_subscriber
            redis_subscriber.start()
            logging.info("Redis subscriber initialized")
        except Exception as e:
            logging.error(f"Redis subscriber initialization failed: {e}")
            raise

    def shutdown_system(self):
        """Gracefully shutdown the system"""
        try:
            logging.info("Starting system shutdown...")

            # Shutdown all Moomoo accounts
            from services.moomoo_account import shutdown_all_accounts
            shutdown_all_accounts()

            # Close Redis connection
            from services.redis_manager import redis_manager
            redis_manager.redis_client.close()

            logging.info("System shutdown completed")

        except Exception as e:
            logging.error(f"System shutdown failed: {e}")

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        try:
            from services.moomoo_account import get_all_accounts
            accounts = get_all_accounts()

            status = {
                'initialized': self.initialization_complete,
                'total_accounts': len(accounts),
                'active_accounts': len([a for a in accounts.values() if a.status.value == 'active']),
                'trading_enabled': len([a for a in accounts.values() if a.trading_config.trading_enabled]),
                'account_details': []
            }

            for account_id, account in accounts.items():
                status['account_details'].append({
                    'id': account_id,
                    'status': account.status.value,
                    'trading_enabled': account.trading_enabled,
                    'account_type': account.trading_account,
                    'trading_amount': account.trading_amount,
                    'connected': account.is_correct_password,
                    'cash_balance': getattr(account, 'cash_balance', 0),
                    'margin_balance': getattr(account, 'margin_balance', 0)
                })
            
            return status
            
        except Exception as e:
            logging.error(f"Error getting system status: {e}")
            return {'error': str(e)}

# Create singleton instance
system_initializer = SystemInitializer()
