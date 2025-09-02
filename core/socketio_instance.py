from flask_socketio import SocketIO

# Create a global socketio instance that can be imported by other modules
socketio = SocketIO(
    cors_allowed_origins="*", 
    async_mode='threading',
) 