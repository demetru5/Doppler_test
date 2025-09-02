import logging
from flask import request, jsonify, g
from services.moomoo_account_service import moomoo_account_service
from utils.auth_decorators import require_auth, require_admin
from typing import Dict, Any
from datetime import datetime
from core.db import MoomooAccount
from services.redis_manager import redis_manager

def register_moomoo_account_routes(app):
    """Register moomoo account management routes with Flask app"""
    
    @app.route('/api/moomoo/connect', methods=['POST'])
    @require_auth
    def request_account_connection():
        """Request to connect a moomoo account"""
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['accountId', 'password', 'tradingPassword']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({
                        'success': False,
                        'error': f'{field} is required'
                    }), 400
            
            # At least one of email or phone should be provided
            if not data.get('email') and not data.get('phone'):
                return jsonify({
                    'success': False,
                    'error': 'Either email or phone number is required'
                }), 400
            
            # Request account connection
            result = moomoo_account_service.request_account_connection(
                g.current_user['id'], 
                data
            )
            
            if result['success']:
                return jsonify(result), 201
            else:
                return jsonify(result), 400
                
        except Exception as e:
            logging.error(f"Account connection request error: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to submit account connection request'
            }), 500
    
    @app.route('/api/moomoo/account', methods=['GET'])
    @require_auth
    def get_user_account():
        """Get current user's moomoo account"""
        try:
            account = moomoo_account_service.get_user_account(g.current_user['id'])
            
            if account:
                return jsonify({
                    'success': True,
                    'account': account
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': 'No moomoo account found'
                }), 404
                
        except Exception as e:
            logging.error(f"Get user account error: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to get account information'
            }), 500
    
    @app.route('/api/moomoo/settings', methods=['PUT'])
    @require_auth
    def update_trading_settings():
        """Update trading settings for user's moomoo account"""
        try:
            data = request.get_json()
            
            # Validate trading percentage if provided
            if 'tradingAmount' in data:
                amount = data['tradingAmount']
                if not isinstance(amount, (int, float)) or not (amount > 0):
                    return jsonify({
                        'success': False,
                        'error': 'Trading amount must be a number greater than 0'
                    }), 400
            
            # Update settings
            result = moomoo_account_service.update_trading_settings(
                g.current_user['id'], 
                data
            )
            
            if result['success']:
                from services.moomoo_account import moomoo_accounts
                moomoo_account = moomoo_accounts[int(g.current_user['moomooAccount']['id'])]
                if 'tradingEnabled' in data:
                    moomoo_account.trading_enabled = data['tradingEnabled']
                if 'tradingAmount' in data:
                    moomoo_account.trading_amount = data['tradingAmount']
                if 'tradingAccount' in data:
                    moomoo_account.update_trading_account(data['tradingAccount'])
                return jsonify(result), 200
            else:
                return jsonify(result), 400
                
        except Exception as e:
            logging.error(f"Update trading settings error: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to update trading settings'
            }), 500
    
    @app.route('/api/moomoo/account', methods=['DELETE'])
    @require_auth
    def delete_account():
        """Delete user's moomoo account connection"""
        try:
            # Get user's account
            account = moomoo_account_service.get_user_account(g.current_user['id'])
            
            if not account:
                return jsonify({
                    'success': False,
                    'error': 'No moomoo account found'
                }), 404
            
            # Delete account
            result = moomoo_account_service.delete_account(account['id'])
            
            if result['success']:
                return jsonify(result), 200
            else:
                return jsonify(result), 400
                
        except Exception as e:
            logging.error(f"Delete account error: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to delete account'
            }), 500
    
    # Admin endpoints
    @app.route('/api/admin/moomoo/pending', methods=['GET'])
    @require_auth
    @require_admin
    def get_pending_requests():
        """Get all pending account connection requests (admin only)"""
        try:
            requests = moomoo_account_service.get_pending_requests()
            
            return jsonify({
                'success': True,
                'requests': requests
            }), 200
                
        except Exception as e:
            logging.error(f"Get pending requests error: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to get pending requests'
            }), 500
    
    @app.route('/api/admin/moomoo/assign/<account_id>', methods=['POST'])
    @require_admin
    def assign_open_configuration(account_id):
        """Assign open configuration to a moomoo account (admin only)"""
        try:
            data = request.get_json()
            result = moomoo_account_service.assign_opend_configuration(account_id, data['host'], data['port'])

            if result['success']:
                return jsonify(result), 200
            else:
                return jsonify(result), 400
        except Exception as e:
            logging.error(f"Assign open configuration error: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to assign open configuration'
            }), 500

    @app.route('/api/admin/moomoo/approve/<account_id>', methods=['POST'])
    @require_admin
    def approve_account(account_id):
        """Approve a moomoo account connection request (admin only)"""
        try:
            result = moomoo_account_service.approve_account(
                account_id, 
                g.current_user['id']
            )
            if result['success']:
                account = moomoo_account_service.get_account_by_id(account_id)
                from services.moomoo_account import add_moomoo_account
                add_moomoo_account(account)
                return jsonify(result), 200
            else:
                return jsonify(result), 400
        except Exception as e:
            logging.error(f"Approve account error: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to approve account'
            }), 500
    
    @app.route('/api/admin/moomoo/reject/<account_id>', methods=['POST'])
    @require_admin
    def reject_account(account_id):
        """Reject a moomoo account connection request (admin only)"""
        try:
            data = request.get_json()
            
            if not data.get('reason'):
                return jsonify({
                    'success': False,
                    'error': 'Rejection reason is required'
                }), 400
            
            result = moomoo_account_service.reject_account(
                account_id, 
                g.current_user['id'],
                data['reason']
            )
            
            if result['success']:
                return jsonify(result), 200
            else:
                return jsonify(result), 400
                
        except Exception as e:
            logging.error(f"Reject account error: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to reject account'
            }), 500
    
    @app.route('/api/admin/moomoo/accounts', methods=['GET'])
    @require_admin
    def get_all_accounts():
        """Get all moomoo accounts (admin only)"""
        try:
            accounts = moomoo_account_service.get_all_accounts()
            
            return jsonify({
                'success': True,
                'accounts': accounts
            }), 200
                
        except Exception as e:
            logging.error(f"Get all accounts error: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to get accounts'
            }), 500 

    @app.route('/api/admin/daily-overview', methods=['GET'])
    @require_admin
    def get_daily_overview():
        """Get daily trading overview for all accounts (admin only)"""
        try:
            overview = moomoo_account_service.get_daily_overview()
            
            return jsonify({
                'success': True,
                'overview': overview
            }), 200
                
        except Exception as e:
            logging.error(f"Get daily overview error: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to get daily overview'
            }), 500 

    @app.route('/api/admin/moomoo/accounts/<account_id>/trading-settings', methods=['PUT'])
    @require_auth
    @require_admin
    def update_account_trading_settings(account_id):
        """Update trading settings for any account (admin only)"""
        try:
            data = request.get_json()
            
            # Validate required fields
            if 'trading_enabled' not in data and 'trading_amount' not in data:
                return jsonify({
                    'success': False,
                    'error': 'At least one setting must be provided'
                }), 400
            
            # Update settings
            result = moomoo_account_service.update_account_trading_settings(
                account_id, data, g.current_user['id']
            )
            
            if result['success']:
                return jsonify(result), 200
            else:
                return jsonify(result), 400
                
        except Exception as e:
            logging.error(f"Update trading settings error: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to update trading settings'
            }), 500

    @app.route('/api/admin/moomoo/accounts/<account_id>/account-type', methods=['PUT'])
    @require_auth
    @require_admin
    def switch_account_type(account_id):
        """Switch account type between cash and margin (admin only)"""
        try:
            data = request.get_json()
            new_account_type = data.get('account_type')
            
            if new_account_type not in ['cash', 'margin']:
                return jsonify({
                    'success': False,
                    'error': 'Invalid account type. Must be "cash" or "margin"'
                }), 400
            
            result = moomoo_account_service.switch_account_type(
                account_id, new_account_type, g.current_user['id']
            )
            
            if result['success']:
                # Update live account instance
                from services.moomoo_account import moomoo_accounts
                if int(account_id) in moomoo_accounts:
                    account = moomoo_accounts[int(account_id)]
                    account.switch_trading_account(new_account_type)
                
                return jsonify(result), 200
            else:
                return jsonify(result), 400
                
        except Exception as e:
            logging.error(f"Switch account type error: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to switch account type'
            }), 500

    @app.route('/api/admin/moomoo/accounts/<account_id>/suspend', methods=['POST'])
    @require_auth
    @require_admin
    def suspend_account(account_id):
        """Suspend trading for an account (admin only)"""
        try:
            data = request.get_json()
            reason = data.get('reason', 'Admin suspension')
            duration_hours = data.get('duration_hours', 24)
            
            result = moomoo_account_service.suspend_account(
                account_id, reason, duration_hours, g.current_user['id']
            )
            
            if result['success']:
                # Update live account instance
                from services.moomoo_account import moomoo_accounts
                if int(account_id) in moomoo_accounts:
                    account = moomoo_accounts[int(account_id)]
                    account.suspend_trading(reason, duration_hours)
                
                return jsonify(result), 200
            else:
                return jsonify(result), 400
                
        except Exception as e:
            logging.error(f"Suspend account error: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to suspend account'
            }), 500

    @app.route('/api/admin/moomoo/accounts/<account_id>/resume', methods=['POST'])
    @require_auth
    @require_admin
    def resume_account(account_id):
        """Resume trading for a suspended account (admin only)"""
        try:
            result = moomoo_account_service.resume_account(
                account_id, g.current_user['id']
            )
            
            if result['success']:
                # Update live account instance
                from services.moomoo_account import moomoo_accounts
                if int(account_id) in moomoo_accounts:
                    account = moomoo_accounts[int(account_id)]
                    account.resume_trading()
                
                return jsonify(result), 200
            else:
                return jsonify(result), 400
                
        except Exception as e:
            logging.error(f"Resume account error: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to resume account'
            }), 500

    @app.route('/api/admin/moomoo/accounts/<account_id>/force-exit', methods=['POST'])
    @require_auth
    @require_admin
    def force_exit_positions(account_id):
        """Force exit all positions for an account (admin only)"""
        try:
            data = request.get_json()
            reason = data.get('reason', 'Admin force exit')
            
            result = moomoo_account_service.force_exit_positions(
                account_id, reason, g.current_user['id']
            )
            
            if result['success']:
                # Execute force exit on live account
                from services.moomoo_account import moomoo_accounts
                if int(account_id) in moomoo_accounts:
                    account = moomoo_accounts[int(account_id)]
                    account.force_exit_all_positions(reason)
                
                return jsonify(result), 200
            else:
                return jsonify(result), 400
                
        except Exception as e:
            logging.error(f"Force exit positions error: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to force exit positions'
            }), 500

    @app.route('/api/admin/moomoo/accounts/<account_id>/risk-limits', methods=['PUT'])
    @require_auth
    @require_admin
    def update_risk_limits(account_id):
        """Update risk management limits (admin only)"""
        try:
            data = request.get_json()
            
            # Validate risk parameters
            if 'max_daily_loss' in data and data['max_daily_loss'] < 0:
                return jsonify({
                    'success': False,
                    'error': 'Max daily loss cannot be negative'
                }), 400
            
            if 'risk_per_trade' in data and not (0 < data['risk_per_trade'] <= 0.1):
                return jsonify({
                    'success': False,
                    'error': 'Risk per trade must be between 0 and 10%'
                }), 400
            
            result = moomoo_account_service.update_risk_limits(
                account_id, data, g.current_user['id']
            )
            
            if result['success']:
                # Update live account instance
                from services.moomoo_account import moomoo_accounts
                if int(account_id) in moomoo_accounts:
                    account = moomoo_accounts[int(account_id)]
                    account.update_risk_limits(data)
                
                return jsonify(result), 200
            else:
                return jsonify(result), 400
                
        except Exception as e:
            logging.error(f"Update risk limits error: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to update risk limits'
            }), 500

    @app.route('/api/admin/moomoo/accounts/<account_id>/trading-history', methods=['GET'])
    @require_auth
    @require_admin
    def get_account_trading_history(account_id):
        """Get detailed trading history for an account (admin only)"""
        try:
            days = request.args.get('days', 30, type=int)
            
            result = moomoo_account_service.get_account_trading_history(
                account_id, days
            )
            
            return jsonify(result), 200
                
        except Exception as e:
            logging.error(f"Get trading history error: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to get trading history'
            }), 500

    @app.route('/api/admin/moomoo/accounts/<account_id>/performance', methods=['GET'])
    @require_auth
    @require_admin
    def get_account_performance(account_id):
        """Get performance metrics for an account (admin only)"""
        try:
            period = request.args.get('period', '30d')  # 7d, 30d, 90d, 1y
            
            result = moomoo_account_service.get_account_performance(
                account_id, period
            )
            
            return jsonify(result), 200
                
        except Exception as e:
            logging.error(f"Get performance error: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to get performance metrics'
            }), 500

    @app.route('/api/admin/moomoo/accounts/<account_id>/bulk-operations', methods=['POST'])
    @require_auth
    @require_admin
    def execute_bulk_operations(account_id):
        """Execute bulk operations on an account (admin only)"""
        try:
            data = request.get_json()
            operations = data.get('operations', [])
            
            if not operations:
                return jsonify({
                    'success': False,
                    'error': 'No operations specified'
                }), 400
            
            result = moomoo_account_service.execute_bulk_operations(
                account_id, operations, g.current_user['id']
            )
            
            return jsonify(result), 200
                
        except Exception as e:
            logging.error(f"Bulk operations error: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to execute bulk operations'
            }), 500

    @app.route('/api/admin/system/status', methods=['GET'])
    @require_auth
    @require_admin
    def get_system_status():
        """Get overall system status (admin only)"""
        try:
            from services.system_initializer import system_initializer
            status = system_initializer.get_system_status()
            
            return jsonify({
                'success': True,
                'status': status
            }), 200
                
        except Exception as e:
            logging.error(f"Get system status error: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to get system status'
            }), 500

    @app.route('/api/admin/moomoo/accounts/<account_id>/reconnect', methods=['POST'])
    @require_auth
    @require_admin
    def reconnect_account(account_id):
        """Reconnect a Moomoo account (admin only)"""
        try:
            result = moomoo_account_service.reconnect_account(
                account_id, g.current_user['id']
            )
            
            if result['success']:
                return jsonify(result), 200
            else:
                return jsonify(result), 400
                
        except Exception as e:
            logging.error(f"Reconnect account error: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to reconnect account'
            }), 500

    @app.route('/api/admin/moomoo/accounts/<account_id>/refresh', methods=['POST'])
    @require_auth
    @require_admin
    def refresh_account_data(account_id):
        """Refresh account data (admin only)"""
        try:
            result = moomoo_account_service.refresh_account_data(
                account_id, g.current_user['id']
            )
            
            if result['success']:
                return jsonify(result), 200
            else:
                return jsonify(result), 400
                
        except Exception as e:
            logging.error(f"Refresh account data error: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to refresh account data'
            }), 500
