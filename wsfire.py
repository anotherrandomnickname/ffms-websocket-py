import rooms
import asyncio
from asgiref.sync import async_to_sync
import json as encoder



class WebsocketFireClass():
    @async_to_sync
    async def new_chat_message(self, state):
        encoded_state = encoder.dumps({'type': 'new_chat_message', 'data': state})
        print("NEW CHAT MESSAGE, START FIRING...")
        if rooms.chat:
            await asyncio.wait([connection.send(encoded_state) for connection in rooms.chat])

    @async_to_sync
    async def new_chat_message2(self, state):
        await asyncio.sleep(2)