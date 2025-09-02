import os
import logging
from dotenv import load_dotenv
import subprocess
from config.logging import setup_logging
from core.app import create_app

load_dotenv()

# Set environment
os.environ.setdefault('FLASK_ENV', 'production')

# Setup logging
setup_logging()

# Initialize system with proper error handling
from services.system_initializer import system_initializer
if not system_initializer.initialize_system():
    logging.error("System initialization failed, exiting...")
    exit(1)

# Create the app and socketio
app, socketio = create_app()

# Run market monitor in a separate process
market_monitor_path = os.path.join(os.path.dirname(__file__), "./market_monitor.py")
market_monitor_process = subprocess.Popen(["python", market_monitor_path])

# WSGI application
application = app

if __name__ == "__main__":
    # Run the app (for development only)
    # In production, use: gunicorn --worker-class eventlet -w 1 wsgi:application
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False) 