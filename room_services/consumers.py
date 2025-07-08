# room_services/consumers.py
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
import json

logger = logging.getLogger(__name__)

class OrderStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.order_id = self.scope["url_route"]["kwargs"]["order_id"]
        self.group_name = f"order_{self.order_id}"
        logger.info("WS CONNECT   group=%s channel=%s", self.group_name, self.channel_name)

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        logger.info("WS CONNECTED group=%s", self.group_name)

    async def disconnect(self, close_code):
        logger.info("WS DISCONNECT group=%s code=%s", self.group_name, close_code)
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def order_update(self, event):
        data = event["data"]
        logger.info("WS RECEIVED  group=%s data=%r", self.group_name, data)
        await self.send(text_data=json.dumps(data))
        logger.info("WS SENT      group=%s data=%r", self.group_name, data)
