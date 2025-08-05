from channels.generic.websocket import AsyncWebsocketConsumer
import json

class OrderStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.hotel_slug = self.scope["url_route"]["kwargs"]["hotel_slug"]
        self.order_id = self.scope["url_route"]["kwargs"]["order_id"]
        self.group_name = f"order_{self.hotel_slug}_{self.order_id}"
        
        # Join the group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Leave the group
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def order_update(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event["data"]))
