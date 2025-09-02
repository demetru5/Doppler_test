import logging
from flask import request, jsonify, g
from services.auth_service import auth_service
from utils.auth_decorators import require_auth
from core.db import get_db, User
from datetime import datetime

def register_auth_routes(app):
    """Register authentication routes with Flask app"""
    
    @app.route('/api/auth/register', methods=['POST'])
    def register():
        """Register a new user"""
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['firstName', 'lastName', 'email', 'password']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({
                        'success': False,
                        'error': f'{field} is required'
                    }), 400
            
            # Validate email format
            if '@' not in data['email'] or '.' not in data['email']:
                return jsonify({
                    'success': False,
                    'error': 'Invalid email format'
                }), 400
            
            # Validate password strength
            if len(data['password']) < 8:
                return jsonify({
                    'success': False,
                    'error': 'Password must be at least 8 characters long'
                }), 400
            
            # Register user
            result = auth_service.register_user(data)
            
            if result['success']:
                return jsonify(result), 201
            else:
                return jsonify(result), 400
                
        except Exception as e:
            logging.error(f"Registration error: {e}")
            return jsonify({
                'success': False,
                'error': 'Registration failed'
            }), 500
    
    @app.route('/api/auth/login', methods=['POST'])
    def login():
        """Authenticate user login"""
        try:
            data = request.get_json()
            
            # Validate required fields
            if not data.get('email') or not data.get('password'):
                return jsonify({
                    'success': False,
                    'error': 'Email and password are required'
                }), 400
            
            # Authenticate user
            result = auth_service.login_user(data['email'], data['password'])
            
            if result['success']:
                return jsonify(result), 200
            else:
                return jsonify(result), 401
                
        except Exception as e:
            logging.error(f"Login error: {e}")
            return jsonify({
                'success': False,
                'error': 'Login failed'
            }), 500
    
    @app.route('/api/auth/verify', methods=['GET'])
    @require_auth
    def verify_token():
        """Verify JWT token and return user data"""
        try:
            return jsonify({
                'success': True,
                'user': g.current_user
            }), 200
            
        except Exception as e:
            logging.error(f"Token verification error: {e}")
            return jsonify({
                'success': False,
                'error': 'Token verification failed'
            }), 500
    
    @app.route('/api/auth/forgot-password', methods=['POST'])
    def forgot_password():
        """Initiate password reset process"""
        try:
            data = request.get_json()
            
            if not data.get('email'):
                return jsonify({
                    'success': False,
                    'error': 'Email is required'
                }), 400
            
            # Process password reset request
            result = auth_service.forgot_password(data['email'])
            
            return jsonify(result), 200
                
        except Exception as e:
            logging.error(f"Forgot password error: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to process password reset request'
            }), 500
    
    @app.route('/api/auth/reset-password', methods=['POST'])
    def reset_password():
        """Reset password using reset token"""
        try:
            data = request.get_json()
            
            # Validate required fields
            if not data.get('token') or not data.get('newPassword'):
                return jsonify({
                    'success': False,
                    'error': 'Token and new password are required'
                }), 400
            
            # Validate password strength
            if len(data['newPassword']) < 8:
                return jsonify({
                    'success': False,
                    'error': 'Password must be at least 8 characters long'
                }), 400
            
            # Reset password
            result = auth_service.reset_password(data['token'], data['newPassword'])
            
            if result['success']:
                return jsonify(result), 200
            else:
                return jsonify(result), 400
                
        except Exception as e:
            logging.error(f"Password reset error: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to reset password'
            }), 500
    
    @app.route('/api/auth/profile', methods=['GET'])
    @require_auth
    def get_profile():
        """Get current user profile"""
        try:
            user_id = g.current_user['id']
            user = auth_service.get_user_by_id(user_id)
            
            if user:
                return jsonify({
                    'success': True,
                    'user': user
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': 'User not found'
                }), 404
                
        except Exception as e:
            logging.error(f"Get profile error: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to get profile'
            }), 500
    
    @app.route('/api/auth/profile', methods=['PUT'])
    @require_auth
    def update_profile():
        """Update current user profile"""
        try:
            data = request.get_json()
            user_id = g.current_user['id']
            
            # Only allow updating firstName and lastName
            allowed_fields = ['firstName', 'lastName']
            update_data = {k: v for k, v in data.items() if k in allowed_fields}
            
            if not update_data:
                return jsonify({
                    'success': False,
                    'error': 'No valid fields to update'
                }), 400
            
            with get_db() as db:
                user = db.query(User).filter_by(id=int(user_id)).first()
                if not user:
                    return jsonify({
                        'success': False,
                        'error': 'User not found'
                    }), 404
                for k, v in update_data.items():
                    setattr(user, k, v)
                user.updatedAt = datetime.utcnow()
                db.commit()
                # Get updated user
                user_data = auth_service.get_user_by_id(user_id)
                return jsonify({
                    'success': True,
                    'user': user_data
                }), 200
                
        except Exception as e:
            logging.error(f"Update profile error: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to update profile'
            }), 500
    
    @app.route('/api/auth/logout', methods=['POST'])
    @require_auth
    def logout():
        """Logout user (client-side token removal)"""
        try:
            # In a stateless JWT system, logout is handled client-side
            # by removing the token. This endpoint can be used for logging
            # logout events or future token blacklisting if needed.
            
            return jsonify({
                'success': True,
                'message': 'Logged out successfully'
            }), 200
                
        except Exception as e:
            logging.error(f"Logout error: {e}")
            return jsonify({
                'success': False,
                'error': 'Logout failed'
            }), 500 

    @app.route('/api/auth/change-password', methods=['POST'])
    @require_auth
    def change_password():
        """
        Change password for authenticated user
        """
        data = request.get_json()
        if not data.get('oldPassword') or not data.get('newPassword'):
            return jsonify({'error': 'Old and new password are required'}), 400

        # Validate new password strength
        if len(data['newPassword']) < 8:
            return jsonify({'error': 'Password must be at least 8 characters long'}), 400

        user_id = g.current_user['id']  # Provided by require_auth
        result = auth_service.change_password(user_id, data['oldPassword'], data['newPassword'])
        if 'error' in result:
            return jsonify(result), 400
        return jsonify(result), 200 