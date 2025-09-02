from flask import request, jsonify, g
from functools import wraps
from services.auth_service import auth_service
import logging

def require_auth(f):
    """Decorator to require authentication for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization header required'}), 401
        try:
            token = auth_header.split(' ')[1] if len(auth_header.split(' ')) == 2 else auth_header
            user = auth_service.verify_token(token)
            if not user:
                return jsonify({'error': 'Invalid or expired token'}), 401
            g.current_user = user
            return f(*args, **kwargs)
        except Exception as e:
            logging.error(f"Authentication error: {e}")
            return jsonify({'error': 'Authentication failed'}), 401
    return decorated_function

def require_admin(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization header required'}), 401
        try:
            token = auth_header.split(' ')[1] if len(auth_header.split(' ')) == 2 else auth_header
            user = auth_service.verify_token(token)
            if not user:
                return jsonify({'error': 'Invalid or expired token'}), 401
            g.current_user = user
            if not user.get('isAdmin', False):
                return jsonify({'error': 'Admin privileges required'}), 403
            return f(*args, **kwargs)
        except Exception as e:
            logging.error(f"Admin authentication error: {e}")
            return jsonify({'error': 'Authentication failed'}), 401
    return decorated_function