import firebase_admin
from firebase_admin import credentials
from firebase_admin import auth
from firebase_admin import db
import json as encoder
import websocket
import threading

cred = credentials.Certificate('./serviceAccountKey.json')
firebase = firebase_admin.initialize_app(cred, {'databaseURL': 'https://fairy-db978.firebaseio.com'})
ADMIN_PATH = 'ZjRUkuNaS'


user_presence = None
user_presence_available = threading.Semaphore(0)
user_presence_completed = threading.Event()

class Firebase_Thread(threading.Thread):

    def __init__(self, ws):
        print('FIREBASE THREAD IS RUNNING')

    def __run__(self):
        global user_presence
        user_presence_ref = db.reference('/presence/')
        user_presence = user_presence_ref.get()
        user_presence_ref.listen(self.user_presence_listener)
        """ self.ws.send({'type': 'user_presence', 'data': new_user_presence}) """

    def user_presence_listener(event):
        global user_presence
        new_user_presence = event.data
        user_presence = new_user_presence
        user_presence_available.release()
        print("NEW STATE! %s" % new_user_presence)

class Websocket_Thread(threading.Thread):

    def __init__(self):
        print('WEBSOCKET THREAD IS RUNNING!')
        self.daemon = True

    def __run__(self):
        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp('ws://127.0.0.1:7777/',
            on_message = self.on_message,
            on_error = self.on_error,
            on_close = self.on_close)
        self.ws.on_open = self.run
        self.ws.run_forever()

    def on_message(ws, message):
        print('MESSAGE! %s' % message)

    def on_error(ws, error):
        print(error)

    def on_close(ws):
        print("### closed ###")

    def run(ws):
        print('opened')


if __name__ == "__main__":

    firebase = Firebase_Thread()
    ws = Websocket_Thread()

    firebase.__run__()
    ws.__run__()

