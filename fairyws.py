import json as encoder
import asyncio
import websockets
from websocket import create_connection
import requests

import rooms
import fairy_firebase

#constants
SUBSCRIBE_ON_CHAT_ROOM ='SUBSCRIBE_ON_CHAT'


async def subscribe_on_chat_room(ws):
    if ws not in rooms.chat:
        rooms.chat.add(ws)
        state = fairy_firebase.chat_ref.get()
        await ws.send(encoder.dumps({'type': 'chat', 'data': state}))

async def unsubscribe_from_chat_room(ws):
    if ws in rooms.chat:
        print('UNSUBSCRIBED FROM CHAT ROOM')
        rooms.chat.remove(ws)


async def register(ws):
    print('new websocket registered!')
    rooms.connections.add(ws)

async def unregister(ws):
    print('websocket unregistered!')
    rooms.connections.remove(ws)
    unsubscribe_from_chat_room(ws)

async def fairysocket(websocket, path):
    await register(websocket)
    try:
        async for message in websocket:
            data = encoder.loads(message)
            if data['action'] == SUBSCRIBE_ON_CHAT_ROOM:
                await subscribe_on_chat_room(websocket)
    finally:
        await unregister(websocket)