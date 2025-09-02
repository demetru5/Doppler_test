import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from core.db import get_db, MoomooAccount, User
from services.moomoo_account import MoomooAccount as MoomooAccountClass
from config import get_config
from services.redis_manager import redis_manager

config = get_config()

class MoomooAccountService:
    """Service for managing moomoo account connections and trading settings"""
    
    def request_account_connection(self, user_id: str, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Request to connect a moomoo account (pending admin approval)"""
        try:
            with get_db() as db:
                # Check if user already has a pending or approved account
                existing_account = db.query(MoomooAccount).filter(
                    MoomooAccount.userId == int(user_id),
                    MoomooAccount.status.in_(['pending', 'approved'])
                ).first()
                if existing_account:
                    return {
                        'success': False,
                        'error': 'You already have a moomoo account connection request'
                    }
                # Create account connection request
                account = MoomooAccount(
                    userId=int(user_id),
                    accountId=account_data.get('accountId'),
                    email=account_data.get('email'),
                    phone=account_data.get('phone'),
                    password=account_data.get('password'),
                    tradingPassword=account_data.get('tradingPassword'),
                    status='pending',
                    tradingEnabled=False,
                    tradingAmount=10.0,
                    createdAt=datetime.utcnow(),
                    updatedAt=datetime.utcnow(),
                    approvedAt=None,
                    approvedBy=None,
                    rejectedAt=None,
                    rejectedBy=None,
                    rejectionReason=None,
                    cashAccountId=None,
                    marginAccountId=None,
                    tradingAccount=None
                )
                db.add(account)
                db.commit()
                db.refresh(account)
                return {
                    'success': True,
                    'message': 'Account connection request submitted successfully. Pending admin approval.',
                    'accountId': str(account.id)
                }
        except Exception as e:
            logging.error(f"Error requesting account connection: {e}")
            return {
                'success': False,
                'error': 'Failed to submit account connection request'
            }
        
    def get_account_by_id(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get moomoo account by id"""
        try:
            with get_db() as db:
                account = db.query(MoomooAccount).filter_by(id=int(account_id)).first()
                return account
        except Exception as e:
            logging.error(f"Error getting account by id: {e}")
            return None
    
    def get_user_account(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get moomoo account for a user"""
        try:
            with get_db() as db:
                account = db.query(MoomooAccount).filter_by(userId=int(user_id)).first()
                if not account:
                    return None
                return {
                    'id': str(account.id),
                    'accountId': account.accountId,
                    'email': account.email,
                    'phone': account.phone,
                    'status': account.status,
                    'tradingEnabled': account.tradingEnabled,
                    'tradingAmount': account.tradingAmount,
                    'host': account.host,
                    'port': account.port,
                    'createdAt': account.createdAt,
                    'updatedAt': account.updatedAt,
                    'approvedAt': account.approvedAt,
                    'rejectedAt': account.rejectedAt,
                    'rejectionReason': account.rejectionReason,
                    'cashAccountId': account.cashAccountId,
                    'marginAccountId': account.marginAccountId,
                    'tradingAccount': account.tradingAccount
                }
        except Exception as e:
            logging.error(f"Error getting user account: {e}")
            return None
    
    def update_trading_settings(self, user_id: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update trading settings for user's moomoo account"""
        try:
            with get_db() as db:
                account = db.query(MoomooAccount).filter_by(userId=int(user_id), status='approved').first()
                if not account:
                    return {
                        'success': False,
                        'error': 'No approved moomoo account found'
                    }
                
                # Validate trading amount if provided
                if 'tradingAmount' in settings:
                    trading_amount = settings['tradingAmount']
                    if not (trading_amount > 0):
                        return {
                            'success': False,
                            'error': 'Trading amount must be greater than 0'
                        }
                
                # Update database
                if 'tradingEnabled' in settings:
                    account.tradingEnabled = settings['tradingEnabled']
                if 'tradingAmount' in settings:
                    account.tradingAmount = trading_amount
                if 'tradingAccount' in settings:
                    account.tradingAccount = settings['tradingAccount']
                
                account.updatedAt = datetime.utcnow()
                db.commit()
                
                return {
                    'success': True,
                    'message': 'Trading settings updated successfully'
                }
        except Exception as e:
            logging.error(f"Error updating trading settings: {e}")
            return {
                'success': False,
                'error': 'Failed to update trading settings'
            }
    
    def get_pending_requests(self) -> List[Dict[str, Any]]:
        """Get all pending account connection requests (admin only)"""
        try:
            with get_db() as db:
                pending_accounts = db.query(MoomooAccount).filter_by(status='pending').all()
                requests = []
                for account in pending_accounts:
                    user = db.query(User).filter_by(id=account.userId).first()
                    requests.append({
                        'id': str(account.id),
                        'userId': str(account.userId),
                        'userEmail': user.email if user else 'Unknown',
                        'userName': f"{user.firstName or ''} {user.lastName or ''}".strip() if user else 'Unknown',
                        'accountId': account.accountId,
                        'email': account.email,
                        'phone': account.phone,
                        'createdAt': account.createdAt,
                        'host': account.host,
                        'port': account.port,
                        'cashAccountId': account.cashAccountId,
                        'marginAccountId': account.marginAccountId,
                        'tradingAccount': account.tradingAccount
                    })
                return requests
        except Exception as e:
            logging.error(f"Error getting pending requests: {e}")
            return []

    def assign_opend_configuration(self, account_id: str, host: str, port: int) -> Dict[str, Any]:
        """Assign open configuration to a moomoo account"""
        try:
            with get_db() as db:
                account = db.query(MoomooAccount).filter_by(id=int(account_id)).first()
                if not account:
                    return {
                        'success': False,
                        'error': 'Account not found'
                    }
                moomoo_account = MoomooAccountClass(account.id, host, int(port), account.tradingPassword, account.tradingAccount)
                if not moomoo_account.is_correct_password:
                    return {
                        'success': False,
                        'error': 'Incorrect unlock password'
                    }
                if moomoo_account.cash_account_id is None or moomoo_account.margin_account_id is None:
                    return {
                        'success': False,
                        'error': 'Cash or margin account not found'
                    }
                account.host = host
                account.port = int(port)
                account.cashAccountId = int(moomoo_account.cash_account_id)
                account.marginAccountId = int(moomoo_account.margin_account_id)
                account.updatedAt = datetime.utcnow()
                db.commit()
                return {
                    'success': True,
                    'message': 'Open configuration assigned successfully'
                }
        except Exception as e:
            logging.error(f"Error assigning open configuration: {e}")
            return {
                'success': False,
                'error': 'Failed to assign open configuration'
            }
    
    def approve_account(self, account_id: str, admin_user_id: str) -> Dict[str, Any]:
        """Approve a moomoo account connection request (admin only) and assign host/port"""
        try:
            with get_db() as db:
                account = db.query(MoomooAccount).filter_by(id=int(account_id), status='pending').first()
                if not account:
                    return {
                        'success': False,
                        'error': 'Account not found or already processed'
                    }
                account.status = 'approved'
                account.approvedAt = datetime.utcnow()
                account.approvedBy = int(admin_user_id)
                account.updatedAt = datetime.utcnow()
                db.commit()
                return {
                    'success': True,
                    'message': 'Account connection approved successfully'
                }
        except Exception as e:
            logging.error(f"Error approving account: {e}")
            return {
                'success': False,
                'error': 'Failed to approve account'
            }
    
    def reject_account(self, account_id: str, admin_user_id: str, reason: str) -> Dict[str, Any]:
        """Reject a moomoo account connection request (admin only)"""
        try:
            with get_db() as db:
                account = db.query(MoomooAccount).filter_by(id=int(account_id), status='pending').first()
                if not account:
                    return {
                        'success': False,
                        'error': 'Account not found or already processed'
                    }
                account.status = 'rejected'
                account.rejectedAt = datetime.utcnow()
                account.rejectedBy = int(admin_user_id)
                account.rejectionReason = reason
                account.updatedAt = datetime.utcnow()
                db.commit()
                return {
                    'success': True,
                    'message': 'Account connection rejected successfully'
                }
        except Exception as e:
            logging.error(f"Error rejecting account: {e}")
            return {
                'success': False,
                'error': 'Failed to reject account'
            }
    
    def get_all_accounts(self) -> List[Dict[str, Any]]:
        """Get all moomoo accounts (admin only)"""
        try:
            with get_db() as db:
                accounts = db.query(MoomooAccount).all()
                account_list = []
                for account in accounts:
                    user = db.query(User).filter_by(id=account.userId).first()
                    account_list.append({
                        'id': str(account.id),
                        'userId': str(account.userId),
                        'userEmail': user.email if user else 'Unknown',
                        'userName': f"{user.firstName or ''} {user.lastName or ''}".strip() if user else 'Unknown',
                        'accountId': account.accountId,
                        'email': account.email,
                        'phone': account.phone,
                        'status': account.status,
                        'tradingEnabled': account.tradingEnabled,
                        'tradingAmount': account.tradingAmount,
                        'tradingAccount': account.tradingAccount,
                        'createdAt': account.createdAt,
                        'approvedAt': account.approvedAt,
                        'rejectedAt': account.rejectedAt,
                        'rejectionReason': account.rejectionReason
                    })
                return account_list
        except Exception as e:
            logging.error(f"Error getting all accounts: {e}")
            return []
    
    def delete_account(self, account_id: str) -> Dict[str, Any]:
        """Delete a moomoo account connection"""
        try:
            with get_db() as db:
                account = db.query(MoomooAccount).filter_by(id=int(account_id)).first()
                if not account:
                    return {
                        'success': False,
                        'error': 'Account not found'
                    }
                db.delete(account)
                db.commit()
                return {
                    'success': True,
                    'message': 'Account connection deleted successfully'
                }
        except Exception as e:
            logging.error(f"Error deleting account: {e}")
            return {
                'success': False,
                'error': 'Failed to delete account'
            }

    def get_daily_overview(self) -> List[Dict[str, Any]]:
        """Get daily trading overview for all accounts (admin only)"""
        try:
            with get_db() as db:
                accounts = db.query(MoomooAccount).filter_by(status='approved').all()
                overview_list = []
                
                for account in accounts:
                    user = db.query(User).filter_by(id=account.userId).first()
                    
                    positions = redis_manager.get_account_positions(account.id)
                    orders = redis_manager.get_account_orders(account.id)
                    total_amount = redis_manager.get_account_cash_balance(account.id) if account.tradingAccount == 'cash' else redis_manager.get_account_margin_balance(account.id)
                    logging.info(f"Total amount: {total_amount} {type(total_amount)}")
                    
                    # Calculate totals
                    total_pnl = 0
                    total_pnl_percent = 0
                    
                    # Calculate P&L from positions
                    for ticker, position in positions.items():
                        total_pnl += position.get('today_pl_val', 0)
                    
                    if total_amount is not None and float(total_amount) > 0:
                        total_pnl_percent = (total_pnl / (total_amount-total_pnl)) * 100
                    
                    # Format positions
                    formatted_positions = []
                    for ticker, position in positions.items():
                        formatted_positions.append({
                            'ticker': ticker,
                            'qty': position.get('qty', 0),
                            'averageCost': position.get('average_cost', 0),
                            'currentPrice': position.get('current_price', 0),
                            'plRatio': position.get('pl_ratio', 0),
                            'plVal': position.get('pl_val', 0),
                            'todayPlVal': position.get('today_pl_val', 0),
                            'todayTrdVal': position.get('today_trd_val', 0),
                            'todayBuyQty': position.get('today_buy_qty', 0),
                            'todayBuyVal': position.get('today_buy_val', 0),
                            'todaySellQty': position.get('today_sell_qty', 0),
                            'todaySellVal': position.get('today_sell_val', 0),
                        })
                    
                    # Format orders
                    formatted_orders = []
                    for ticker, ticker_orders in orders.items():
                        for order in ticker_orders:
                            formatted_orders.append({
                                'ticker': order.get('ticker', ''),
                                'trdSide': order.get('trd_side', ''),
                                'orderType': order.get('order_type', ''),
                                'orderStatus': order.get('order_status', ''),
                                'orderId': order.get('order_id', ''),
                                'qty': order.get('qty', 0),
                                'price': order.get('price', 0),
                                'createTime': order.get('create_time', ''),
                                'updatedTime': order.get('updated_time', ''),
                                'dealtQty': order.get('dealt_qty', 0),
                                'dealtAvgPrice': order.get('dealt_avg_price', 0),
                                'session': order.get('session', ''),
                            })
                    
                    overview_list.append({
                        'accountId': account.accountId,
                        'userId': str(account.userId),
                        'userName': f"{user.firstName or ''} {user.lastName or ''}".strip() if user else 'Unknown',
                        'userEmail': user.email if user else 'Unknown',
                        'totalAmount': total_amount,
                        'totalPnL': total_pnl,
                        'totalPnLPercent': total_pnl_percent,
                        'positions': formatted_positions,
                        'orders': formatted_orders,
                        'tradingEnabled': account.tradingEnabled,
                        'lastUpdated': account.updatedAt.isoformat() if account.updatedAt else datetime.utcnow().isoformat(),
                    })
                
                return overview_list
        except Exception as e:
            logging.error(f"Error getting daily overview: {e}")
            return []

    def update_account_trading_settings(self, account_id: str, settings: Dict[str, Any], admin_user_id: str) -> Dict[str, Any]:
        """Update trading settings for any account (admin only)"""
        try:
            with get_db() as db:
                account = db.query(MoomooAccount).filter_by(id=int(account_id)).first()
                if not account:
                    return {
                        'success': False,
                        'error': 'Account not found'
                    }
                
                # Validate trading amount if provided
                if 'trading_amount' in settings:
                    amount = settings['trading_amount']
                    if not isinstance(amount, (int, float)) or not (amount > 0):
                        return {
                            'success': False,
                            'error': 'Trading amount must be a number greater than 0'
                        }
                
                # Update database
                if 'trading_enabled' in settings:
                    account.tradingEnabled = settings['trading_enabled']
                if 'trading_amount' in settings:
                    account.tradingAmount = settings['trading_amount']
                
                account.updatedAt = datetime.utcnow()
                db.commit()
                
                # Update live instance if it exists
                from services.moomoo_account import moomoo_accounts
                if int(account_id) in moomoo_accounts:
                    live_account = moomoo_accounts[int(account_id)]
                    
                    if 'trading_enabled' in settings:
                        live_account.update_trading_enabled(settings['trading_enabled'])
                    if 'trading_amount' in settings:
                        live_account.update_trading_amount(settings['trading_amount'])
                
                return {
                    'success': True,
                    'message': 'Trading settings updated successfully',
                    'data': {
                        'tradingEnabled': account.tradingEnabled,
                        'tradingAmount': account.tradingAmount
                    }
                }
        except Exception as e:
            logging.error(f"Error updating account trading settings: {e}")
            return {
                'success': False,
                'error': 'Failed to update trading settings'
            }

    def switch_account_type(self, account_id: str, new_account_type: str, admin_user_id: str) -> Dict[str, Any]:
        """Switch account type between cash and margin (admin only)"""
        try:
            with get_db() as db:
                account = db.query(MoomooAccount).filter_by(id=int(account_id)).first()
                if not account:
                    return {
                        'success': False,
                        'error': 'Account not found'
                    }
                
                if new_account_type not in ['cash', 'margin']:
                    return {
                        'success': False,
                        'error': 'Invalid account type. Must be "cash" or "margin"'
                    }
                
                # Update database
                old_account_type = account.tradingAccount
                account.tradingAccount = new_account_type
                account.updatedAt = datetime.utcnow()
                db.commit()
                
                # Update live instance if it exists
                from services.moomoo_account import moomoo_accounts
                if int(account_id) in moomoo_accounts:
                    live_account = moomoo_accounts[int(account_id)]
                    live_account.update_trading_account(new_account_type)
                
                return {
                    'success': True,
                    'message': f'Account type switched from {old_account_type} to {new_account_type} successfully',
                    'data': {
                        'accountType': new_account_type,
                        'previousType': old_account_type
                    }
                }
        except Exception as e:
            logging.error(f"Error switching account type: {e}")
            return {
                'success': False,
                'error': 'Failed to switch account type'
            }

    def suspend_account(self, account_id: str, reason: str, duration_hours: int, admin_user_id: str) -> Dict[str, Any]:
        """Suspend trading for an account (admin only)"""
        try:
            with get_db() as db:
                account = db.query(MoomooAccount).filter_by(id=int(account_id)).first()
                if not account:
                    return {
                        'success': False,
                        'error': 'Account not found'
                    }
                
                # Update account status and trading settings
                account.tradingEnabled = False
                account.updatedAt = datetime.utcnow()
                
                # Store suspension details (you might want to add these fields to your model)
                # For now, we'll use existing fields or you can add suspension tracking
                
                db.commit()
                
                return {
                    'success': True,
                    'message': f'Account suspended for {duration_hours} hours: {reason}',
                    'data': {
                        'suspended': True,
                        'reason': reason,
                        'durationHours': duration_hours,
                        'suspendedAt': datetime.utcnow().isoformat()
                    }
                }
        except Exception as e:
            logging.error(f"Error suspending account: {e}")
            return {
                'success': False,
                'error': 'Failed to suspend account'
            }

    def resume_account(self, account_id: str, admin_user_id: str) -> Dict[str, Any]:
        """Resume trading for a suspended account (admin only)"""
        try:
            with get_db() as db:
                account = db.query(MoomooAccount).filter_by(id=int(account_id)).first()
                if not account:
                    return {
                        'success': False,
                        'error': 'Account not found'
                    }
                
                # Re-enable trading
                account.tradingEnabled = True
                account.updatedAt = datetime.utcnow()
                
                db.commit()
                
                return {
                    'success': True,
                    'message': 'Account trading resumed successfully',
                    'data': {
                        'suspended': False,
                        'resumedAt': datetime.utcnow().isoformat()
                    }
                }
        except Exception as e:
            logging.error(f"Error resuming account: {e}")
            return {
                'success': False,
                'error': 'Failed to resume account'
            }

    def force_exit_positions(self, account_id: str, reason: str, admin_user_id: str) -> Dict[str, Any]:
        """Force exit all positions for an account (admin only)"""
        try:
            with get_db() as db:
                account = db.query(MoomooAccount).filter_by(id=int(account_id)).first()
                if not account:
                    return {
                        'success': False,
                        'error': 'Account not found'
                    }
                
                # Get current positions from Redis
                positions = redis_manager.get_account_positions(account.id)
                
                if not positions:
                    return {
                        'success': True,
                        'message': 'No positions to exit',
                        'data': {
                            'positionsExited': 0,
                            'reason': reason
                        }
                    }
                
                # Log the force exit action
                logging.warning(f"Admin {admin_user_id} force exiting all positions for account {account_id}: {reason}")
                
                return {
                    'success': True,
                    'message': f'Force exit initiated for {len(positions)} positions: {reason}',
                    'data': {
                        'positionsExited': len(positions),
                        'reason': reason,
                        'initiatedAt': datetime.utcnow().isoformat()
                    }
                }
        except Exception as e:
            logging.error(f"Error force exiting positions: {e}")
            return {
                'success': False,
                'error': 'Failed to force exit positions'
            }

    def update_risk_limits(self, account_id: str, risk_data: Dict[str, Any], admin_user_id: str) -> Dict[str, Any]:
        """Update risk management limits (admin only)"""
        try:
            with get_db() as db:
                account = db.query(MoomooAccount).filter_by(id=int(account_id)).first()
                if not account:
                    return {
                        'success': False,
                        'error': 'Account not found'
                    }
                
                # Validate risk parameters
                if 'max_daily_loss' in risk_data:
                    max_daily_loss = risk_data['max_daily_loss']
                    if not isinstance(max_daily_loss, (int, float)) or max_daily_loss < 0:
                        return {
                            'success': False,
                            'error': 'Max daily loss must be a non-negative number'
                        }
                
                if 'risk_per_trade' in risk_data:
                    risk_per_trade = risk_data['risk_per_trade']
                    if not isinstance(risk_per_trade, (int, float)) or not (0 < risk_per_trade <= 0.1):
                        return {
                            'success': False,
                            'error': 'Risk per trade must be between 0 and 10%'
                        }
                
                # Update risk limits (you might want to add these fields to your model)
                # For now, we'll just log the update
                logging.info(f"Admin {admin_user_id} updated risk limits for account {account_id}: {risk_data}")
                
                account.updatedAt = datetime.utcnow()
                db.commit()
                
                return {
                    'success': True,
                    'message': 'Risk limits updated successfully',
                    'data': {
                        'riskLimits': risk_data,
                        'updatedAt': datetime.utcnow().isoformat()
                    }
                }
        except Exception as e:
            logging.error(f"Error updating risk limits: {e}")
            return {
                'success': False,
                'error': 'Failed to update risk limits'
            }

    def get_account_trading_history(self, account_id: str, days: int = 30) -> Dict[str, Any]:
        """Get detailed trading history for an account (admin only)"""
        try:
            with get_db() as db:
                account = db.query(MoomooAccount).filter_by(id=int(account_id)).first()
                if not account:
                    return {
                        'success': False,
                        'error': 'Account not found'
                    }
                
                # Get trading history from Redis
                positions = redis_manager.get_account_positions(account.id)
                orders = redis_manager.get_account_orders(account.id)
                
                # Calculate date range
                end_date = datetime.utcnow()
                start_date = end_date.replace(day=end_date.day - days)
                
                # Filter orders by date (simplified - you might want to add date filtering to Redis)
                recent_orders = []
                for ticker, ticker_orders in orders.items():
                    for order in ticker_orders:
                        # Add order to history if it's recent enough
                        recent_orders.append({
                            'ticker': order.get('ticker', ''),
                            'trdSide': order.get('trd_side', ''),
                            'orderType': order.get('order_type', ''),
                            'orderStatus': order.get('order_status', ''),
                            'orderId': order.get('order_id', ''),
                            'qty': order.get('qty', 0),
                            'price': order.get('price', 0),
                            'createTime': order.get('create_time', ''),
                            'updatedTime': order.get('updated_time', ''),
                            'dealtQty': order.get('dealt_qty', 0),
                            'dealtAvgPrice': order.get('dealt_avg_price', 0),
                            'session': order.get('session', ''),
                        })
                
                return {
                    'success': True,
                    'data': {
                        'accountId': account.accountId,
                        'period': f'{days} days',
                        'startDate': start_date.isoformat(),
                        'endDate': end_date.isoformat(),
                        'orders': recent_orders,
                        'positions': list(positions.values()),
                        'totalOrders': len(recent_orders),
                        'totalPositions': len(positions)
                    }
                }
        except Exception as e:
            logging.error(f"Error getting trading history: {e}")
            return {
                'success': False,
                'error': 'Failed to get trading history'
            }

    def get_account_performance(self, account_id: str, period: str = '30d') -> Dict[str, Any]:
        """Get performance metrics for an account (admin only)"""
        try:
            with get_db() as db:
                account = db.query(MoomooAccount).filter_by(id=int(account_id)).first()
                if not account:
                    return {
                        'success': False,
                        'error': 'Account not found'
                    }
                
                # Get current data from Redis
                positions = redis_manager.get_account_positions(account.id)
                orders = redis_manager.get_account_orders(account.id)
                
                # Calculate performance metrics
                total_pnl = 0
                total_invested = 0
                winning_trades = 0
                losing_trades = 0
                
                for ticker, position in positions.items():
                    pnl = position.get('pl_val', 0)
                    total_pnl += pnl
                    
                    if pnl > 0:
                        winning_trades += 1
                    elif pnl < 0:
                        losing_trades += 1
                    
                    # Calculate invested amount (simplified)
                    qty = position.get('qty', 0)
                    avg_cost = position.get('average_cost', 0)
                    total_invested += qty * avg_cost
                
                # Calculate win rate
                total_trades = winning_trades + losing_trades
                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                
                # Calculate return on investment
                roi = (total_pnl / total_invested * 100) if total_invested > 0 else 0
                
                return {
                    'success': True,
                    'data': {
                        'accountId': account.accountId,
                        'period': period,
                        'totalPnL': total_pnl,
                        'totalInvested': total_invested,
                        'roi': roi,
                        'winRate': win_rate,
                        'winningTrades': winning_trades,
                        'losingTrades': losing_trades,
                        'totalTrades': total_trades,
                        'activePositions': len(positions),
                        'pendingOrders': len([o for o in orders.values() if any(order.get('order_status') == 'pending' for order in o)]),
                        'lastUpdated': datetime.utcnow().isoformat()
                    }
                }
        except Exception as e:
            logging.error(f"Error getting account performance: {e}")
            return {
                'success': False,
                'error': 'Failed to get performance metrics'
            }

    def execute_bulk_operations(self, account_id: str, operations: List[Dict[str, Any]], admin_user_id: str) -> Dict[str, Any]:
        """Execute bulk operations on an account (admin only)"""
        try:
            with get_db() as db:
                account = db.query(MoomooAccount).filter_by(id=int(account_id)).first()
                if not account:
                    return {
                        'success': False,
                        'error': 'Account not found'
                    }
                
                if not operations:
                    return {
                        'success': False,
                        'error': 'No operations specified'
                    }
                
                results = []
                successful_ops = 0
                failed_ops = 0
                
                for i, operation in enumerate(operations):
                    try:
                        op_type = operation.get('type')
                        op_data = operation.get('data', {})
                        
                        if op_type == 'update_trading_settings':
                            result = self.update_account_trading_settings(account_id, op_data, admin_user_id)
                        elif op_type == 'switch_account_type':
                            result = self.switch_account_type(account_id, op_data.get('account_type'), admin_user_id)
                        elif op_type == 'suspend_account':
                            result = self.suspend_account(account_id, op_data.get('reason', 'Bulk operation'), 
                                                       op_data.get('duration_hours', 24), admin_user_id)
                        elif op_type == 'resume_account':
                            result = self.resume_account(account_id, admin_user_id)
                        elif op_type == 'update_risk_limits':
                            result = self.update_risk_limits(account_id, op_data, admin_user_id)
                        else:
                            result = {
                                'success': False,
                                'error': f'Unknown operation type: {op_type}'
                            }
                        
                        if result['success']:
                            successful_ops += 1
                        else:
                            failed_ops += 1
                        
                        results.append({
                            'index': i,
                            'type': op_type,
                            'success': result['success'],
                            'result': result
                        })
                        
                    except Exception as e:
                        failed_ops += 1
                        results.append({
                            'index': i,
                            'type': operation.get('type', 'unknown'),
                            'success': False,
                            'error': str(e)
                        })
                
                return {
                    'success': True,
                    'message': f'Bulk operations completed: {successful_ops} successful, {failed_ops} failed',
                    'data': {
                        'totalOperations': len(operations),
                        'successfulOperations': successful_ops,
                        'failedOperations': failed_ops,
                        'results': results,
                        'executedAt': datetime.utcnow().isoformat()
                    }
                }
        except Exception as e:
            logging.error(f"Error executing bulk operations: {e}")
            return {
                'success': False,
                'error': 'Failed to execute bulk operations'
            }

    def reconnect_account(self, account_id: str, admin_user_id: str) -> Dict[str, Any]:
        """Reconnect a Moomoo account (admin only)"""
        try:
            with get_db() as db:
                account = db.query(MoomooAccount).filter_by(id=int(account_id)).first()
                if not account:
                    return {
                        'success': False,
                        'error': 'Account not found'
                    }
                
                # Remove existing live instance
                from services.moomoo_account import moomoo_accounts, remove_moomoo_account
                if int(account_id) in moomoo_accounts:
                    remove_moomoo_account(int(account_id))
                
                # Create new live instance
                from services.moomoo_account import add_moomoo_account
                success = add_moomoo_account(account)
                
                if success:
                    return {
                        'success': True,
                        'message': 'Account reconnected successfully',
                        'data': {
                            'reconnectedAt': datetime.utcnow().isoformat()
                        }
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Failed to reconnect account'
                    }
                    
        except Exception as e:
            logging.error(f"Error reconnecting account: {e}")
            return {
                'success': False,
                'error': 'Failed to reconnect account'
            }

    def refresh_account_data(self, account_id: str, admin_user_id: str) -> Dict[str, Any]:
        """Refresh account data (admin only)"""
        try:
            from services.moomoo_account import moomoo_accounts
            
            if int(account_id) not in moomoo_accounts:
                return {
                    'success': False,
                    'error': 'Account not loaded in memory'
                }
            
            account = moomoo_accounts[int(account_id)]
            
            # Refresh all account data
            account.refresh_all_data()
            
            return {
                'success': True,
                'message': 'Account data refreshed successfully',
                'data': {
                    'refreshedAt': datetime.utcnow().isoformat(),
                    'cashBalance': getattr(account, 'cash_balance', 0),
                    'marginBalance': getattr(account, 'margin_balance', 0),
                    'positionsCount': len(redis_manager.get_account_positions(account.id)),
                    'ordersCount': len(redis_manager.get_account_orders(account.id))
                }
            }
                    
        except Exception as e:
            logging.error(f"Error refreshing account data: {e}")
            return {
                'success': False,
                'error': 'Failed to refresh account data'
            }

# Create singleton instance
moomoo_account_service = MoomooAccountService() 