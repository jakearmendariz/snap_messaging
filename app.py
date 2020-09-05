#!/usr/bin/env python
from threading import Lock
from flask import Flask, render_template, session, request, \
    copy_current_request_context
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
    
import time

async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'not_gonna_add_this_to_github_so_haha_i_wont_do_it'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()

messages = []


def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        update_messages()
        socketio.sleep(0.3)

def update_messages():
    global messages
    copy = messages.copy()
    before = len(copy)
    for message in copy:
        if time.time() > message['delay']:
            print('\n\n\nDeleting message', message['data'])
            messages.remove(message)
    if before > len(messages):
        socketio.emit('update_chat',
            messages,
            namespace='/test')
            

@app.route('/', methods=['POST', 'GET'])
def index():
    if(request.method == 'POST'):
        print('Posted name',  request.form['name'])
        session['name'] = request.form['name']
    global messages
    if 'name' in session:
        return render_template('index.html', name = session['name'], messages=messages)
    return render_template('index.html', name = '', messages=messages)


@socketio.on('my_broadcast_event', namespace='/test')
def test_broadcast_message(message):
    print("\n\n\nmessage", message)
    global messages
    messages.append({'data':message['data'], 'delay': int(message['delay']) + time.time(), 'user':session['name']})
    emit('update_chat',
         messages,
         broadcast=True)


@socketio.on('my_ping', namespace='/test')
def ping_pong():
    emit('my_pong')


@socketio.on('connect', namespace='/test')
def test_connect():
    if 'name' not in session:
        session['name'] = ''
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)


if __name__ == '__main__':
    socketio.run(app, debug=True)
