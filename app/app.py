import binascii
import json
import os

import redis
import syft as sy
import torch as th
from gevent import pywsgi
from flask import Flask, render_template
import socketio

try:
    db = redis.from_url(os.environ['REDISCLOUD_URL'])
except:
    db = redis.from_url('redis://localhost:6379')


hook = sy.TorchHook(th)
async_mode = 'gevent'
sio = socketio.Server(async_mode=async_mode)
app = Flask(__name__)
app.wsgi_app = socketio.WSGIApp(sio, app.wsgi_app)


def _maybe_create_worker(worker_name: str = 'worker', virtual_worker_id: str = 'grid'):
    worker = db.get(worker_name)

    if worker is None:
        worker = sy.VirtualWorker(hook, virtual_worker_id, auto_add=False)
        print("\t \nCREATING NEW WORKER!!")
    else:
        worker = sy.serde.deserialize(worker)
        print("\t \nFOUND OLD WORKER!! " + str(worker._objects.keys()))
    return worker

def _store_worker(worker, worker_name: str = 'worker'):
    db.set(worker_name, sy.serde.serialize(worker, force_full_simplification=True))


@app.route('/')
def hello_world():
    name = db.get('name') or'World'
    db.set('del_ctr', 0)
    return 'Websocket Howdy %s!' % str(name)


@sio.on("/identity/")
def is_this_an_opengrid_node():
    """This exists because in the automation scripts which deploy nodes,
    there's an edge case where the 'node already exists' but sometimes it
    can be an app that does something totally different. So we want to have
    some endpoint which just casually identifies this server as an OpenGrid
    server."""
    sio.emit('/identity', "Websocket OpenGrid")


@sio.on('/cmd/')
def cmd(sid, message):
    try:
        worker = _maybe_create_worker("worker", "grid")

        worker.verbose = True
        sy.torch.hook.local_worker.add_worker(worker)

        response = worker._recv_msg(message)

        print("\t NEW WORKER STATE:" + str(worker._objects.keys()) + "\n\n")

        _store_worker(worker, "worker")

        sio.emit("/cmd/", response)
    except Exception as e:
        print("Error: ", e)
        sio.emit("/cmd/", str(e))



if __name__ == '__main__':
<<<<<<< HEAD
    if sio.async_mode == 'gevent':
        # deploy with gevent
        from gevent import pywsgi
        try:
            from geventwebsocket.handler import WebSocketHandler
            websocket = True
        except ImportError:
            websocket = False
        if websocket:
            pywsgi.WSGIServer(('', 5000),
                              handler_class=WebSocketHandler).serve_forever()
        else:
            pywsgi.WSGIServer(('', 5000), app).serve_forever()
    else:
        print('Unknown async_mode: ' + sio.async_mode)
=======
    app.run()
>>>>>>> origin/dev
