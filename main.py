import websockets
from websocket import create_connection
import requests
import asyncio

import fairyws
import fairy_firebase

listener = fairy_firebase.Listener()
listener.start()

asyncio.get_event_loop().run_until_complete(
    websockets.serve(fairyws.fairysocket, 'localhost', 7777))
asyncio.get_event_loop().run_forever()