import logging

def register_websocket_handlers(socketio):
    """Register all WebSocket event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        logging.info('Client connected with server')

    return socketio
