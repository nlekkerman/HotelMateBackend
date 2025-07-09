from channels.generic.websocket import AsyncWebsocketConsumer
import json

class OrderStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.order_id = self.scope["url_route"]["kwargs"]["order_id"]
        self.group_name = f"order_{self.order_id}"
        
        print(f"🟢 [CONNECT] WebSocket connecting to order group: {self.group_name}")
        
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        print(f"✅ [CONNECTED] WebSocket successfully joined: {self.group_name}")

    async def disconnect(self, close_code):
        print(f"🔴 [DISCONNECT] WebSocket leaving group: {self.group_name}")
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def order_update(self, event):
        print(f"📦 [RECEIVED] Update for {self.group_name}: {event['data']}")
        await self.send(text_data=json.dumps(event["data"]))
        print(f"🚀 [SENT] Payload delivered to WebSocket: {event['data']}")
