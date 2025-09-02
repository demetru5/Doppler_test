import logging
from flask import Flask
from flask_cors import CORS
from config import get_config
from core.socketio_instance import socketio

def create_app():
    # Get configuration
    config = get_config()
    
    # Application Setup
    app = Flask(__name__)
    app.config.from_object(config)

    # CORS setup
    logging.info(f"CORS_ORIGINS: {config.CORS_ORIGINS}")
    CORS(app, resources={r"/*": {"origins": config.CORS_ORIGINS}})
    
    # Initialize socketio with the app
    socketio.init_app(app, cors_allowed_origins=config.CORS_ORIGINS)
    
    # Import and register routes
    from controllers.app_controller import register_app_routes
    from controllers.auth_controller import register_auth_routes
    from controllers.moomoo_account_controller import register_moomoo_account_routes
    from controllers.trade_controller import register_trade_routes
    
    register_app_routes(app)
    register_auth_routes(app)
    register_moomoo_account_routes(app)
    register_trade_routes(app)
    
    # Import and register controllers after app is created
    from controllers.websocket_controller import register_websocket_handlers
    register_websocket_handlers(socketio)
    
    return app, socketio
