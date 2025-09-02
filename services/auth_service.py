import logging
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from core.db import get_db, User
from config import get_config
from core.db import MoomooAccount

config = get_config()

class AuthService:
    """Authentication service for user management"""
    
    def __init__(self):
        self.secret_key = config.SECRET_KEY
        self.token_expiry_hours = 24
        
    def _hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def _generate_token(self, user_id: int, email: str) -> str:
        """Generate JWT token for user"""
        payload = {
            'user_id': str(user_id),
            'email': email,
            'exp': datetime.utcnow() + timedelta(hours=self.token_expiry_hours),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def _verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logging.warning("Token has expired")
            return None
        except jwt.InvalidTokenError:
            logging.warning("Invalid token")
            return None
    
    def register_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new user"""
        try:
            with get_db() as db:
                # Check if user already exists
                existing_user = db.query(User).filter_by(email=user_data['email']).first()
                if existing_user:
                    return {
                        'success': False,
                        'error': 'User with this email already exists'
                    }
                # Hash password
                hashed_password = self._hash_password(user_data['password'])
                # Create user
                new_user = User(
                    firstName=user_data['firstName'],
                    lastName=user_data['lastName'],
                    email=user_data['email'],
                    password=hashed_password,
                    isAdmin=False,
                    createdAt=datetime.utcnow(),
                    updatedAt=datetime.utcnow(),
                    isActive=True,
                    lastLogin=None
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                # Generate token
                token = self._generate_token(new_user.id, new_user.email)
                return {
                    'success': True,
                    'user': {
                        'id': str(new_user.id),
                        'firstName': new_user.firstName,
                        'lastName': new_user.lastName,
                        'email': new_user.email,
                        'isAdmin': new_user.isAdmin
                    },
                    'token': token
                }
        except Exception as e:
            logging.error(f"Error registering user: {e}")
            return {
                'success': False,
                'error': 'Registration failed'
            }
    
    def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user login"""
        try:
            with get_db() as db:
                user = db.query(User).filter_by(email=email).first()
                if not user:
                    return {
                        'success': False,
                        'error': 'Invalid email or password'
                    }
                if not self._verify_password(password, user.password):
                    return {
                        'success': False,
                        'error': 'Invalid email or password'
                    }
                if not user.isActive:
                    return {
                        'success': False,
                        'error': 'Account is deactivated'
                    }
                user.lastLogin = datetime.utcnow()
                db.commit()
                # Get approved moomoo account if exists
                moomoo_account = db.query(MoomooAccount).filter_by(userId=user.id, status='approved').first()
                moomoo_account_info = None
                if moomoo_account:
                    moomoo_account_info = {
                        'id': str(moomoo_account.id),
                        'accountId': moomoo_account.accountId,
                        'host': moomoo_account.host,
                        'port': moomoo_account.port,
                        'tradingEnabled': moomoo_account.tradingEnabled,
                        'tradingAmount': moomoo_account.tradingAmount,
                        'status': moomoo_account.status
                    }
                token = self._generate_token(user.id, user.email)
                return {
                    'success': True,
                    'user': {
                        'id': str(user.id),
                        'firstName': user.firstName,
                        'lastName': user.lastName,
                        'email': user.email,
                        'isAdmin': user.isAdmin,
                        'moomooAccount': moomoo_account_info
                    },
                    'token': token
                }
        except Exception as e:
            logging.error(f"Error logging in user: {e}")
            return {
                'success': False,
                'error': 'Login failed'
            }
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return user data"""
        try:
            payload = self._verify_token(token)
            if not payload:
                return None
            with get_db() as db:
                user = db.query(User).filter_by(id=int(payload['user_id'])).first()
                moomoo_account = db.query(MoomooAccount).filter_by(userId=user.id, status='approved').first()
                moomoo_account_info = None
                if moomoo_account:
                    moomoo_account_info = {
                        'id': str(moomoo_account.id),
                        'accountId': moomoo_account.accountId,
                        'host': moomoo_account.host,
                        'port': moomoo_account.port,
                        'tradingEnabled': moomoo_account.tradingEnabled,
                        'tradingAmount': moomoo_account.tradingAmount,
                        'status': moomoo_account.status
                    }
                if not user or not user.isActive:
                    return None
                return {
                    'id': str(user.id),
                    'firstName': user.firstName,
                    'lastName': user.lastName,
                    'email': user.email,
                    'isAdmin': user.isAdmin,
                    'moomooAccount': moomoo_account_info
                }
        except Exception as e:
            logging.error(f"Error verifying token: {e}")
            return None
    
    def forgot_password(self, email: str) -> Dict[str, Any]:
        """Initiate password reset process"""
        try:
            with get_db() as db:
                user = db.query(User).filter_by(email=email).first()
                if not user:
                    # Don't reveal if user exists or not for security
                    return {
                        'success': True,
                        'message': 'If an account with this email exists, a reset link has been sent'
                    }
                # Generate reset token
                reset_token = jwt.encode(
                    {
                        'user_id': str(user.id),
                        'email': email,
                        'type': 'password_reset',
                        'exp': datetime.utcnow() + timedelta(hours=1),
                        'iat': datetime.utcnow()
                    },
                    self.secret_key,
                    algorithm='HS256'
                )
                # Store reset token in user (optional: add fields to User model)
                # user.resetToken = reset_token
                # user.resetTokenExpiry = datetime.utcnow() + timedelta(hours=1)
                # db.commit()
                # TODO: Send email with reset link
                logging.info(f"Password reset requested for user: {email}")
                return {
                    'success': True,
                    'message': 'If an account with this email exists, a reset link has been sent'
                }
        except Exception as e:
            logging.error(f"Error in forgot password: {e}")
            return {
                'success': False,
                'error': 'Failed to process password reset request'
            }
    
    def reset_password(self, token: str, new_password: str) -> Dict[str, Any]:
        """Reset password using reset token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            if payload.get('type') != 'password_reset':
                return {
                    'success': False,
                    'error': 'Invalid reset token'
                }
            with get_db() as db:
                user = db.query(User).filter_by(id=int(payload['user_id'])).first()
                if not user:
                    return {
                        'success': False,
                        'error': 'Invalid reset token'
                    }
                # Optionally check for token expiry if you store it in DB
                hashed_password = self._hash_password(new_password)
                user.password = hashed_password
                user.updatedAt = datetime.utcnow()
                # user.resetToken = None
                # user.resetTokenExpiry = None
                db.commit()
                return {
                    'success': True,
                    'message': 'Password has been reset successfully'
                }
        except jwt.ExpiredSignatureError:
            return {
                'success': False,
                'error': 'Reset token has expired'
            }
        except jwt.InvalidTokenError:
            return {
                'success': False,
                'error': 'Invalid reset token'
            }
        except Exception as e:
            logging.error(f"Error resetting password: {e}")
            return {
                'success': False,
                'error': 'Failed to reset password'
            }
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            with get_db() as db:
                user = db.query(User).filter_by(id=int(user_id)).first()
                if not user:
                    return None
                return {
                    'id': str(user.id),
                    'firstName': user.firstName,
                    'lastName': user.lastName,
                    'email': user.email,
                    'isAdmin': user.isAdmin,
                    'createdAt': user.createdAt,
                    'lastLogin': user.lastLogin
                }
        except Exception as e:
            logging.error(f"Error getting user by ID: {e}")
            return None

    def change_password(self, user_id: int, old_password: str, new_password: str) -> Dict[str, Any]:
        try:
            with get_db() as db:
                user = db.query(User).filter_by(id=user_id).first()
                if not user:
                    return {'error': 'User not found'}

                if not self._verify_password(old_password, user.password):
                    return {'error': 'Old password is incorrect'}

                hashed_password = self._hash_password(new_password)
                user.password = hashed_password
                user.updatedAt = datetime.utcnow()
                db.commit()
                return {'message': 'Password changed successfully'}
        except Exception as e:
            logging.error(f"Error changing password: {e}")
            return {'error': 'Failed to change password'}

# Create singleton instance
auth_service = AuthService() 