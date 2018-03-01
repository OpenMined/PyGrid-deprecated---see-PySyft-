from ... import channels
from ..base import BaseService
from bitcoin import base58
import torch

import torch
from torch.autograd import Variable
import inspect
import random
import copy
from ...lib import utils
from ...lib import serde
import json

class TorchService(BaseService):

    # this service just listens on the general "openmined" channel so that other nodes
    # on the network know its there.

    def __init__(self,worker):
        super().__init__(worker)

        self.worker = worker

        self.objects = {}

        self.hook_float_tensor_add()
        self.hook_float_tensor___init__()
        self.hook_float_tensor_serde()
        self.hook_float_tensor_send()
        self.hook_float_tensor_process_command()
        self.hook_float_tensor_get()

        def print_messages(message):
            fr = base58.encode(msg['from'])
            print(fr)
            print(message['data'])
            return message

        listen_for_obj_callback_channel = channels.torch_listen_for_obj_callback(self.worker.id)
        self.worker.listen_to_channel(listen_for_obj_callback_channel,self.receive_obj)

        listen_for_obj_callback_channel = channels.torch_listen_for_obj_req_callback(self.worker.id)
        self.worker.listen_to_channel(listen_for_obj_callback_channel,self.receive_obj_request)

        # listen_for_obj_response_callback_channel = channels.torch_listen_for_obj_response_callback(self.worker.id)
        # self.worker.listen_to_channel(listen_for_obj_response_callback_channel,print_messages)

    def receive_obj(self,msg):
        print("received obj:" + str(msg))
        dic = json.loads(msg['data'])

        if(dic['type'] == 'torch.FloatTensor'):
            obj = torch.FloatTensor.de(dic)
            obj.is_pointer_to_remote = False
            obj.owner = self.worker
            self.objects[obj.id] = obj
            return obj


    def register_object(self,obj,is_pointer_to_remote):
        obj.id = random.randint(0, 1e10)
        obj.owner = self.worker
        obj.is_pointer_to_remote = False
        self.objects[obj.id] = obj
        return obj
    
    def send_obj(self,obj,to):
        g.publish(channels.torch_listen_for_obj_callback(to),message=obj.ser())
        obj.is_pointer_to_remote = True
        obj.owner = to
        return obj

    def send_command(self,command,to):
        return to.receive_command(command)
    
    def request_obj(self,obj):
        response = obj.owner.receive_obj_request(obj.id)
        return self.receive_obj(response)
    
    def receive_obj_request(self,msg):
        print("receive_obj_request:" + str(msg))
        obj_ids = json.loads(msg['data'])
        fr = base58.encode(msg['from'])

        response = list()
        for obj_id in obj_ids:
            if(obj_id in self.objects.keys()):
                response.append(self.objects[obj_id].ser())
            else:
                response.append('n/a - tensor not found')
        response_str = json.dumps(response)

        response_channel = channels.torch_listen_for_obj_req_response_callback(fr)
        self.worker.publish(channel=response_channel,message=response_str)
    
    
    def receive_command(self,command):
        if(command['base_type'] == 'torch.FloatTensor'):
            raw_response = torch.FloatTensor.process_command(self,command)
        
        return json.dumps(raw_response)
    
    def process_response(self,response):
        response = json.loads(response)
        tensor_ids = response
        out_tensors = list()
        for raw_msg in tensor_ids:
            msg = json.loads(raw_msg)
            if(msg["type"] == "torch.FloatTensor"):
                obj = torch.FloatTensor.de(msg)
            out_tensors.append(obj)
            
        if(len(out_tensors) > 1):
            return out_tensors
        elif(len(out_tensors) == 1):
            return out_tensors[0]
        else:
            return None
    
    def function2json(self, obj, name, frame, ix):
        
        args, varargs, keywords, values = inspect.getargvalues(frame)
        
        command = {}
        command['id'] = ix # This id is assigned as a placeholder for the data that the worker has
        command['command'] = name
        command['base_type'] = obj.type()
        command['args'] = args
        command['varargs'] =  varargs
        command['keywords'] = keywords
        command['values'] = [values[arg].id for arg in args]
        command['types'] = [type(val) for val in command['values']]
        
        return command

    # GENERIC

    def assign_workers(self):
        def decorate(func):
            def send_to_workers(*args, **kwargs):
                if(args[0].is_pointer_to_remote):
                    command = func(*args, **kwargs)
                    response = self.send_command(command,args[0].owner)
                    return self.process_response(response)
                    
                else:
                    return func(*args, **kwargs)
            return send_to_workers
        return decorate


    # FLOAT TENSOR FUNCTIONS
    def hook_float_tensor___init__(self):
        def new___init__(self,tensor,owner=self, *args, **kwargs):
            super(torch.FloatTensor, self).__init__(*args, **kwargs)
            self = owner.register_object(self,False)
         
        torch.FloatTensor.__init__ = new___init__


    def hook_float_tensor_add(self2):
        @self2.assign_workers()
        def new_add(self, other):
            if(self.is_pointer_to_remote):
                frame = inspect.currentframe()
                command = self.owner.function2json(self,'add', frame, self.id)
                return command
            else:
                result = self.old_add(other)
                return self2.register_object(result,True)

        try:
            torch.FloatTensor.old_add
        except:
            torch.FloatTensor.old_add = torch.FloatTensor.add
            
        torch.FloatTensor.add = new_add
        
    def hook_float_tensor_serde(self):
        def ser(self, include_data=True):

            msg = {}
            msg['type'] = 'torch.FloatTensor'
            if(include_data):
                msg['data'] = self.tolist()
            msg['id'] = self.id
            msg['owner'] = self.owner.id
            
            return json.dumps(msg)

        def de(msg):
            if(type(msg) == str):
                msg = json.loads(msg)
            if('data' in msg.keys()):
                v = torch.FloatTensor(msg['data'])
                v.owner = msg['owner']
            else:
                v = torch.zeros(0)
                v.owner = msg['owner']
                
            v.id = msg['id']
            return v

        torch.FloatTensor.ser = ser
        torch.FloatTensor.de = de 
        
    def hook_float_tensor_send(self):
        def send(self,new_owner):
            self.owner.send_obj(self,new_owner)
            return self

        torch.FloatTensor.send = send
        
    def hook_float_tensor_get(self):
        def get(self):
            self = self.request_obj(self)
            return self
        torch.FloatTensor.get = get
        
    def hook_float_tensor_process_command(self):
        def process_command(worker,command):
            if(command['command'] == 'add'):
                a = worker.objects[int(command['values'][0])]
                b = worker.objects[int(command['values'][1])]
                c = a.add(b)
                return [c.ser(False)]
            else:
                return "command not found"
            ""
            
        torch.FloatTensor.process_command = process_command