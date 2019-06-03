# event_notify.py
#
# An example of using a semaphore and an event to have a thread
# signal completion of some task
import firebase_admin
from firebase_admin import credentials
from firebase_admin import auth
from firebase_admin import db
import json as encoder
import asyncio
import websockets
from websocket import create_connection

cred = credentials.Certificate('./serviceAccountKey.json')
firebase = firebase_admin.initialize_app(cred, {'databaseURL': 'https://fairy-db978.firebaseio.com'})
ADMIN_PATH = 'ZjRUkuNaS'

import threading
import time

# A variables that contains some data
user_presence = None
chat = None
messages = None

# A semaphore to indicate that an item is available
""" available = threading.Semaphore(0) """

# An event to indicate that processing is complete
user_presence_completed = threading.Event()
chat_completed = threading.Event()
messages_completed = threading.Event()

# A variables than contains database references
user_presence_ref = db.reference('/presence/')
chat_ref = db.reference('/chat/')
messages_ref = db.reference('/messages/')

# List of whole running connections
CONNECTIONS = set()

# Lists of rooms, which must be subscribed
user_presense_room = set()
chat_room = set()

def user_presence_dump():
    return encoder.dumps({'type':'presence', 'data': user_presence})

async def user_presence_notifier():
    if CONNECTIONS:
        message = user_presence_dump()
        print('state sent for every connection!')
        await asyncio.wait([connection.send(message) for connection in CONNECTIONS])

def user_presence_listener(event):
    global user_presence
    new_state = event.data
    event_type = event.event_type
    if event_type == 'put' and new_state != None:
        key2 = str(key1)
        if key2 != None:
            if key2 in user_presence:
                new_state_to_update = user_presence[key2]
                user_presence[key2] = event.data
    elif event_type == 'patch':
        user_presence.update(new_state)
    print("new state received: %s" % new_state)
    user_presence_completed.set()

def messages_listener(event):
    global messages
    new_state = event.data
    event_type = event.event_type
    print('NEW EVENT!')
    print('DATA: %s'  % new_state)
    print('TYPE: %s ' % event_type)

# A listener thread
def run():
    global user_presence
    global messages

    global user_presence_ref
    global messages_ref

    """ user_presence_ref = db.reference('/presence/') """

    user_presence_state = user_presence_ref.get()
    messages_state = messages_ref.get()

    user_presence = user_presence_state
    messages = messages_state

    user_presence_ref.listen(user_presence_listener)
    messages_ref.listen(messages_listener)

    user_presence_completed.set()
    messages_completed.set()
    """ self.ws.send({'type': 'user_presence', 'data': new_user_presence}) """


# A producer thread
def user_presence_producer():
    while True:
        user_presence_completed.wait()
        ws = create_connection('ws://127.0.0.1:7777/')
        ws.send(encoder.dumps({'action': 'NOTIFY_NEW_USER_IS_ONLINE'}))
        result =  ws.recv()
        """ print("Received '%s'" % result) """
        ws.close()
        print("new state deployed: %s" % user_presence)
        user_presence_completed.clear()


def messages_producer():
    while True:
        messages_completed.wait()
        ws = create_connection('ws://127.0.0.1:7777/')
        ws.send(encoder.dumps({'action': 'NOTIFY_ABOUT_NEW_MESSAGE'}))
        result = ws.recv()
        ws.close()
        print('NEW MESSAGE DEPLOYED: %s' % messages)
        messages_completed.clear()



async def register(ws):
    print('new websocket registered!')
    CONNECTIONS.add(ws)

async def unregister(ws):
    print('websocket unregistered!')
    CONNECTIONS.remove(ws)

# Websocket thread
async def websocket(websocket, path):
    await register(websocket)
    try:
        async for message in websocket:
            data = encoder.loads(message)
            if data['action'] == 'NOTIFY_NEW_USER_IS_ONLINE':
                await user_presence_notifier()
            if data['action'] == 'FETCH_ONLINE_USERS':
                response = user_presence_dump()
                await websocket.send(response)
            if data['action'] == 'NOTIFY_ABOUT_NEW_MESSAGE':
                print('NEW MESSAGE NOTIFIED!')
    finally:
        await unregister(websocket)
        

t1 = threading.Thread(target=run)
t1.start()
t2 = threading.Thread(target=user_presence_producer)
t3 = threading.Thread(target=messages_producer)
t2.setDaemon(True)
t3.setDaemon(True)
t2.start()
t3.start()
asyncio.get_event_loop().run_until_complete(
    websockets.serve(websocket, 'localhost', 7777))
asyncio.get_event_loop().run_forever()