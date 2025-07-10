# your_app/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class OrderStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.hotel_slug = self.scope["url_route"]["kwargs"]["hotel_slug"]
        self.order_id   = self.scope["url_route"]["kwargs"]["order_id"]

        self.order_group = f"order_{self.order_id}"
        self.count_group = f"orders_{self.hotel_slug}"

        # join both groups
        await self.channel_layer.group_add(self.order_group, self.channel_name)
        await self.channel_layer.group_add(self.count_group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.order_group, self.channel_name)
        await self.channel_layer.group_discard(self.count_group, self.channel_name)

    # existing per-order update
    async def order_update(self, event):
        await self.send(text_data=json.dumps(event["data"]))

    # new counts handler
    async def count_update(self, event):
        await self.send(text_data=json.dumps(event["data"]))
