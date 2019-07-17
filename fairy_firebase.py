import threading
import firebase_admin
from firebase_admin import credentials
from firebase_admin import auth
from firebase_admin import db
import json as encoder
from websocket import create_connection
import asyncio
import wsfire

cred = credentials.Certificate('./serviceAccountKey.json')
firebase = firebase_admin.initialize_app(cred, {'databaseURL': 'https://fairy-db978.firebaseio.com'})

chat_ref = db.reference('/chat/')

chat_ex2_ref = db.reference('/chat_ex2/')


class Listener(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.fire = wsfire.WebsocketFireClass()

    def chat_listener(self, event):
        state = event.data
        print('DATA %s' % state)
        result = self.fire.new_chat_message(state)

    def chat_ex2_listener(self, event):
        state = event.data
        print('DATA EX2: %s' % state)
        result = self.fire.new_chat_message2(state)
    

    def run(self):
        global chat_ex_ref
        chat_state = chat_ref.get()
        chat_ref.listen(self.chat_listener)
        chat_ex2_ref.listen(self.chat_ex2_listener)
        print('LISTEN: %s' % chat_state)
