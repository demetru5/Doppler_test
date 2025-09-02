import os
import logging
from polygon import WebSocketClient
from polygon.websocket.models import Feed, Market

POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')

class PolygonManager:
    def __init__(self):
        self.websocket_client = WebSocketClient(
            api_key=POLYGON_API_KEY,
            feed=Feed.RealTime,
            market=Market.Stocks
        )
        self.websocket_client.subscribe("A.*")

    def run_websocket(self, handle_msg):
        logging.info("Starting polygon websocket")
        self.websocket_client.run(handle_msg)