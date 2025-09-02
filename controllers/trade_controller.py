import logging
from flask import request, jsonify, g
from services.moomoo_account import moomoo_accounts
from utils.auth_decorators import require_auth, require_admin

def register_trade_routes(app):
    """Register trade routes with Flask app"""
    
    @app.route('/api/trade/buy-with-smart-sell', methods=['POST'])
    @require_auth
    @require_admin
    def buy_with_smart_sell():
        """Request to buy a stock with smart sell"""
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['ticker', 'account_id']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({
                        'success': False,
                        'error': f'{field} is required'
                    }), 400
            
            moomoo_account = moomoo_accounts.get(data['account_id'])
            if not moomoo_account:
                return jsonify({
                    'success': False,
                    'error': 'Account not found'
                }), 404
            
            result = moomoo_account.buy_with_smart_sell(data['ticker'])
            
            return jsonify(result), 201
                
        except Exception as e:
            logging.error(f"Buy with smart sell error: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to buy with smart sell'
            }), 500
    