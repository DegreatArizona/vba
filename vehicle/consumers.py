import json
from channels.generic.websocket import AsyncWebsocketConsumer

class MechanicLocationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.mechanic_id = self.scope['url_route']['kwargs']['mechanic_id']
        await self.channel_layer.group_add(
            f"mechanic_{self.mechanic_id}",
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            f"mechanic_{self.mechanic_id}",
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        await self.channel_layer.group_send(
            f"mechanic_{self.mechanic_id}",
            {
                'type': 'send_location',
                'latitude': data['latitude'],
                'longitude': data['longitude'],
            }
        )

    async def send_location(self, event):
        await self.send(text_data=json.dumps({
            'latitude': event['latitude'],
            'longitude': event['longitude'],
        }))
