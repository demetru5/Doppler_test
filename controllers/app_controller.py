from moomoo import *
from flask import jsonify
from flask import request
import time
from services.redis_manager import redis_manager
from utils.auth_decorators import require_auth
from services.moomoo_account import moomoo_accounts
from services.moomoo_account_service import moomoo_account_service
from core.db import get_db, MoomooAccount
from flask import g

def find_non_serializable(obj, path=""):
    """Recursively find non-JSON serializable objects and their paths"""
    non_serializable = []
    
    try:
        json.dumps(obj)
        return non_serializable
    except (TypeError, ValueError):
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                non_serializable.extend(find_non_serializable(value, current_path))
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                current_path = f"{path}[{i}]" if path else f"[{i}]"
                non_serializable.extend(find_non_serializable(item, current_path))
        else:
            non_serializable.append(f"{path}: {type(obj).__name__} = {str(obj)[:100]}")
    
    return non_serializable

def register_app_routes(app):
    @app.route('/api/get_market_context')
    def get_market_context():
        return jsonify(redis_manager.get_market_context())

    @app.route('/api/get_stock_data')
    def get_stock_data():
        stocks_data = []
        tickers = redis_manager.get_all_tickers()

        for ticker in tickers:
            ticker_stocks_data = redis_manager.get_stock_data(ticker)
            stocks_data.append(ticker_stocks_data)

        return jsonify(stocks_data)

    @app.route('/api/get_candles')
    def get_candles():
        ticker = request.args.get('ticker')
        return jsonify(redis_manager.get_candles(ticker))
    
    @app.route('/api/get_positions')
    @require_auth
    def get_positions():
        account = g.current_user['moomooAccount']
        if not account or not account['tradingEnabled'] or not account['id']:
            return jsonify({})
        account_id = account['id']
        
        positions = redis_manager.get_account_positions(account_id)
        orders = redis_manager.get_account_orders(account_id)
        for ticker, position in positions.items():
            each_orders = orders.get(ticker, [])
            each_orders.sort(key=lambda x: x['create_time'])
            position['orders'] = each_orders
        return jsonify(positions)

    @app.route('/api/toggle_buy_features', methods=['POST'])
    @require_auth
    def toggle_buy_features():
        account = g.current_user['moomooAccount']
        if not account:
            return jsonify({'success': False, 'error': 'No moomoo account found'})
        enabled = request.json['enabled']
        result = moomoo_account_service.update_trading_settings(account['id'], {'tradingEnabled': enabled})
        moomoo_accounts[int(account['id'])].trading_enabled = enabled
        return jsonify({'success': result['success'], 'enabled': enabled})

    @app.route('/api/get_buy_features_status')
    @require_auth
    def get_buy_features_status():
        user_id = g.current_user['id']
        with get_db() as db:
            account = db.query(MoomooAccount).filter_by(userId=int(user_id), status='approved').first()
            enabled = account.tradingEnabled if account else False
            return jsonify({'enabled': enabled})
    
    @app.route('/api/exit_position', methods=['POST'])
    @require_auth
    def exit_position():
        account = g.current_user['moomooAccount']
        positions = redis_manager.get_account_positions(account['id'])
        if not positions:
            return jsonify({'success': False, 'error': 'No positions found'})
        ticker = request.json['ticker']
        if ticker not in positions:
            return jsonify({'success': False, 'error': 'Ticker not found in positions'})
        position = positions[ticker]
        if position['qty'] == 0:
            return jsonify({'success': False, 'error': 'Position already exited'})
        price = redis_manager.get_stock_price(ticker)
        if not price:
            return jsonify({'success': False, 'error': 'No price found'})
        ret, data = moomoo_accounts[int(account['id'])].place_sell_order(ticker, price, position['qty'])
        if ret != RET_OK:
            return jsonify({'success': False, 'error': data})
        return jsonify({'success': True})
    
    @app.route('/api/sell_stock', methods=['POST'])
    @require_auth
    def sell_stock():
        account = g.current_user['moomooAccount']
        if not account:
            return jsonify({'success': False, 'error': 'No moomoo account found'})