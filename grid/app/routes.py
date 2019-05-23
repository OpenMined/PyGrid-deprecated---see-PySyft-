import binascii
import json
import os

from flask import Flask, session, request
from app import app
import redis
import syft as sy
import torch as th


hook = sy.TorchHook(th)

app.secret_key = b'keepmesecret'

try:
    db = redis.from_url(os.environ['REDISCLOUD_URL'])
except:
    db = redis.from_url('redis://localhost:6379')

def _maybe_create_worker(worker_name: str = 'worker', virtual_worker_id: str = 'grid'):
    worker = db.get(worker_name)

    if worker is None:
        worker = sy.VirtualWorker(hook, virtual_worker_id, auto_add=False)
        print("\t \nCREATING NEW WORKER!!")
    else:
        worker = sy.serde.deserialize(worker)
        print("\t \nFOUND OLD WORKER!! " + str(worker._objects.keys()))

    return worker

def _request_message(worker):
    message = request.form['message']
    message = binascii.unhexlify(message[2:-1])
    response = worker._recv_msg(message)
    response = str(binascii.hexlify(response))
    return response

def _store_worker(worker, worker_name: str = 'worker'):
    db.set(worker_name, sy.serde.serialize(worker, force_full_simplification=True))

@app.route('/')
def hello_world():
#    name = db.get('name') or'World'
#    db.set('del_ctr', 0)
    return 'Howdy!'

@app.route("/identity/")
def is_this_an_opengrid_node():
    """This exists because in the automation scripts which deploy nodes,
    there's an edge case where the 'node already exists' but sometimes it
    can be an app that does something totally different. So we want to have
    some endpoint which just casually identifies this server as an OpenGrid
    server."""
    return "OpenGrid"

@app.route('/cmd/', methods=['POST'])
def cmd():
    try:
        worker = _maybe_create_worker("worker", "grid")

        worker.verbose = True
        sy.torch.hook.local_worker.add_worker(worker)

        print("WORKER", worker)

        response = _request_message(worker)

        print("\t NEW WORKER STATE:" + str(worker._objects.keys()) + "\n\n")

        _store_worker(worker, "worker")
        return response
    except Exception as e:
        return str(e)

