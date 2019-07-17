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
import requests

cred = credentials.Certificate('./serviceAccountKey.json')
firebase = firebase_admin.initialize_app(cred, {'databaseURL': 'https://fairy-db978.firebaseio.com'})
ADMIN_PATH = 'ZjRUkuNaS'

import threading
import time

PATH_SALT = 'FVa3vxsIjScs'
UNIQUE_IDENTIFY = 'SnHuLP5he6dnw36k'

# A variables that contains some data
user_presence = None
chat = None
messages = None
user_presence_2 = {}

#A variables with latest message for notifiers
messages_newest = None
chat_newest = None
user_presence_2_newest_online = None
user_presence_2_newest_offline = None

# A semaphore to indicate that an item is available
""" available = threading.Semaphore(0) """

# An event to indicate that processing is complete
user_presence_completed = threading.Event()
chat_completed = threading.Event()
messages_completed = threading.Event()

# A variables than contains database references
users_ref = db.reference('/users/')
user_presence_ref = db.reference('/presence/')
chat_ref = db.reference('/chat/')
messages_ref = db.reference('/messages/')

# List of whole running connections
CONNECTIONS = set()

# Lists of rooms, which must be subscribed
user_presence_room = set()
chat_room = set()
messages_room = set()

def user_presence_dump():
    return encoder.dumps({'type':'presence', 'data': user_presence})

async def user_presence_notify_online():
    global user_presence_2_newest_online
    #print('START!')
    #print(user_presence_2_newest_online)
    if user_presence_room:
        message = encoder.dumps({'type': 'user_is_online', 'data': user_presence_2_newest_online})
        await asyncio.wait([connection.send(message) for connection in user_presence_room])
    user_presence_2_newest_online = None

async def user_presence_notify_offline():
    global user_presence_2_newest_offline
    #print('START!')
    #print(user_presence_2_newest_offline)
    if user_presence_room:
        message = encoder.dumps({'type': 'user_is_offline', 'data': user_presence_2_newest_offline})
        await asyncio.wait([connection.send(message) for connection in user_presence_room])
    user_presence_2_newest_offline = None


async def messages_notify():
    #print('START NOTIFY!')
    if messages_room:
        message = encoder.dumps({'type': 'new_message', 'data': messages_newest})
        await asyncio.wait([connection.send(message) for connection in messages_room])

async def chat_notify():
    if chat_room:
        message = encoder.dumps({'type': 'new_chat_message', 'data': chat_newest})
        await asyncio.wait([connection.send(message) for connection in chat_room])


def messages_listener(event):
    global messages
    global messages_newest
    new_state = event.data
    #print('DATA: %s'  % new_state)

    """ check if..."""
    if new_state != None:
        if len(new_state) <= 1:
            messages_newest = new_state
        else:
            #print('VERY LONG!')
            messages = new_state
        messages_completed.set()

def users_listener(event):
    path = event.path
    event_type = event.event_type
    state = event.data
    global user_presence_2_newest_online
    global user_presence_2_newest_offline

    print('USERS DATA: %s' % state)
    print('EVENT TYPE: %s' % event_type)
    print('USERS PATH: %s' % path)

    # Do not refractor this code, please. 
    if path != '/':
        uid = path.split('/')[1]
        #print('UID: %s' % uid)
        ref_path = '/users/' + uid
        user_ref = db.reference(ref_path)
        check_connections = user_ref.get()
        #print('CHECK CONNECTIONS: %s' % check_connections)
        if 'connections' in check_connections:
            # Check if user has more connections
            if len(check_connections['connections']) == 1:
                # First connection
                user_info = check_connections['info']
                user_key = user_info['pk']
                new_user = {str(user_key): user_info}
                uid = path.split('/')[1]
                #print('USER INFO: %s' % user_info)
                #print('USER KEY: %s' % user_key)
                user_presence_2.update(new_user)
                user_presence_2_newest_online = new_user
                #print('NEW STATE: %s' % user_presence_2)
                print ('NEW CONNECTION!')
                print('UID: %s' % uid)
                try: 
                    URL = 'http://localhost:8010/set_user_online/' + PATH_SALT
                    data_json = {
                        'uid': uid,
                    }
                    r = requests.post(url=URL, json=data_json)
                except:
                    print('ERROR!')
            else:
                # Still connected
                print('STILL CONNECTED!')
        else:
            # Clean disconnection
            uid = path.split('/')[1]
            ref_path = '/users/' + uid + '/info'
            user_ref = db.reference(ref_path)
            user_info = user_ref.get()
            user_key = str(user_info['pk'])
            user_presence_2_newest_offline = user_key
            if user_key in user_presence_2:
                user_presence_2.pop(user_key)
            try: 
                URL = 'http://localhost:8010/set_user_offline/' + PATH_SALT
                data_json = {
                    'uid': uid,
                }
                r = requests.post(url=URL, json=data_json)
            except:
                print('ERROR!')

            
    elif event_type == 'patch':
        local_path = state.keys()
        uid = list(local_path)[0].split('/')[0]
        ref_path = '/users/' + uid
        user_ref = db.reference(ref_path)
        check_connections = user_ref.get()
        #print('UID: %s' % uid)
        #print('CHECK CONNECTIONS: %s' % check_connections)
        # Check if user has more connections
        if 'connections' in check_connections:
            # Still connected
            print('STILL CONNECTED!')
        else:
            user_info = check_connections['info']
            user_key = str(user_info['pk'])
            user_presence_2_newest_offline = user_key
            #print('USER INFO: %s' % user_info)
            #print('USER KEY: %s' % user_key)
            if user_key in user_presence_2:
                user_presence_2.pop(user_key)
            #print('NEW STATE: %s' % user_presence_2)
            # connection is disconnected
            print('UID: %s' % uid)
            print('DISCONNECTED!!')
            try: 
                URL = 'http://localhost:8010/set_user_offline/' + PATH_SALT
                data_json = {
                    'uid': uid,
                }
                r = requests.post(url=URL, json=data_json)
            except:
                print('ERROR!')
                
    #print('END!')
    elif not isinstance(state, bool) and event_type == 'put' and path == '/':
        try:
            URL = 'http://localhost:8010/setonlineinitial/' + PATH_SALT
            print('URL: %s' % URL)
            r = requests.post(url=URL, json=state)
            data = r.json()
            print('DATA: %s' %data)
        except: 
            print('WOOPS EROR')

    user_presence_completed.set()

def chat_listener(event):
    path = event.path
    event_type = event.event_type
    state = event.data
    global chat_newest

    print('CHAT DATA: %s' % state)
    print('EVENT TYPE: %s' % event_type)
    print('CHAT PATH: %s' % path)

    chat_newest = state
    chat_completed.set()

# A producer thread
def user_presence_producer():
    while True:
        user_presence_completed.wait()
        message = 'DEFAULT'
        #print('START NOTIFY!! %s' % message)
        #print(user_presence_2_newest_offline)
        #print(user_presence_2_newest_online)
        if user_presence_2_newest_offline != None:
            #print('OFFLINE!')
            message = 'NOTIFY_USER_IS_OFFLINE'
        if user_presence_2_newest_online != None:
            message = 'NOTIFY_USER_IS_ONLINE'
        ws = create_connection('ws://127.0.0.1:7777/')
        ws.send(encoder.dumps({'action': message}))
        ws.close()
        user_presence_completed.clear()


def chat_producer():
    while True:
        chat_completed.wait()
        ws = create_connection('ws://127.0.0.1:7777/')
        ws.send(encoder.dumps({'action': 'NOTIFY_NEW_CHAT_MESSAGE'}))
        ws.close()
        chat_completed.clear()


def messages_producer():
    while True:
        messages_completed.wait()
        ws = create_connection('ws://127.0.0.1:7777/')
        ws.send(encoder.dumps({'action': 'NOTIFY_ABOUT_NEW_MESSAGE'}))
        ws.close()
        #print('NEW MESSAGE DEPLOYED: %s' % messages_newest)
        messages_completed.clear()


async def subscribe_on_chat(ws):
    if ws not in chat_room:
        chat_room.add(ws)
        state = chat_ref.get()
        await ws.send(encoder.dumps({'type': 'chat', 'data': state}))

async def unsubscribe_from_chat(ws):
    if ws in chat_room:
        chat_room.remove(ws)


async def subscribe_on_messages(ws):
    if ws not in messages_room:
        messages_room.add(ws)
        #print('SUBSCRIBED ON MESSAGES')
        state = messages_ref.get()
        await ws.send(encoder.dumps({'type': 'messages', 'data': state}))

async def unsubscribe_from_messages(ws):
    if ws in messages_room:
        #print('UNSUBSCRIBED FROM MESSAGES')
        messages_room.remove(ws)

async def subscribe_on_user_presence(ws):
    #print('SUBSCRIBED ON USER_PRESENCE')
    user_presence_room.add(ws)
    state = user_presence_2
    print('USER PRESENCE: %s' % user_presence_2)
    await ws.send(encoder.dumps({'type': 'user_presence', 'data': state}))

async def unsubscribe_from_user_presence(ws):
    if ws in user_presence_room:
        #print('UNSUBSCRIBED FROM USER PRESENCE')
        user_presence_room.remove(ws)

async def register(ws):
    print('new websocket registered!')
    CONNECTIONS.add(ws)

async def unregister(ws):
    print('websocket unregistered!')
    CONNECTIONS.remove(ws)


class ChatClass
    def __init__(self):
        threading.Thread.__init__(self)
        self.event = threading.Event()

    def run(self):
        while not self.event.is_set()

# Websocket thread
async def websocket(websocket, path):
    await register(websocket)
    try:
        async for message in websocket:
            data = encoder.loads(message)
            if data['action'] == 'NOTIFY_ABOUT_NEW_MESSAGE':
                await messages_notify()
            if data['action'] == 'NOTIFY_USER_IS_ONLINE':
                await user_presence_notify_online()
            if data['action'] == 'NOTIFY_USER_IS_OFFLINE':
                await user_presence_notify_offline()
            if data['action'] == 'NOTIFY_NEW_CHAT_MESSAGE':
                await chat_notify()
            if data['action'] == 'SUBSCRIBE_ON_CHAT':
                await subscribe_on_chat(websocket)
            if data['action'] == 'UNSUBSCRIBE_FROM_CHAT':
                await unsubscribe_from_chat(websocket)
            if data['action'] == 'SUBSCRIBE_ON_USER_PRESENCE':
                await subscribe_on_user_presence(websocket)
            if data['action'] == 'UNSUBSCRIBE_FROM_USER_PRESENCE':
                await unsubscribe_from_user_presence(websocket)
            if data['action'] == 'SUBSCRIBE_ON_MESSAGES':
                await subscribe_on_messages(websocket)
            if data['action'] == 'UNSUBSCRIBE_FROM_MESSAGES':
                await unsubscribe_from_messages(websocket)
    finally:
        await unregister(websocket)
        await unsubscribe_from_messages(websocket)
        await unsubscribe_from_user_presence(websocket)
        await unsubscribe_from_chat(websocket)


# A listener thread
def listen():
    global user_presence
    global messages

    global users_ref
    global user_presence_ref
    global messages_ref
    global chat_ref

    user_presence_state = user_presence_ref.get()
    messages_state = messages_ref.get()

    user_presence = user_presence_state
    messages = messages_state

    messages_ref.listen(messages_listener)
    users_ref.listen(users_listener) 
    chat_ref.listen(chat_listener)

    """ user_presence_completed.set()
    messages_completed.set() """
        

t1 = threading.Thread(target=listen)
t1.start()
t2 = threading.Thread(target=user_presence_producer)
t3 = threading.Thread(target=messages_producer)
t4 = threading.Thread(target=chat_producer)
t2.setDaemon(True)
t3.setDaemon(True)
t4.setDaemon(True)
t2.start()
t3.start()
t4.start()
asyncio.get_event_loop().run_until_complete(
    websockets.serve(websocket, 'localhost', 7777))
asyncio.get_event_loop().run_forever()