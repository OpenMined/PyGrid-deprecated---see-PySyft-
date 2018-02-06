from . import ipfsapi
from grid.lib import OutputPipe, utils
from grid.dataset import get_dataset

import base64
import random
import keras
import json
import numpy as np
import torch
from torch.autograd import Variable
import sys
from colorama import Fore, Back, Style

"""
TODO: modify Client to store the source code for the model in IPFS.
            (think through logistics; introduces hurdles for packaging model source code)
TODO: figure out a convenient way to make robust training procedure for torch -- will probably want to use ignite for this
"""


class Grid(object):

    def __init__(self, ipfs_addr='127.0.0.1', port=5001):
        self.api = utils.get_ipfs_api()
        self.encoded_id = self.get_encoded_id()
        self.id = self.api.config_show()['Identity']['PeerID']

    def get_encoded_id(self):

        """Currently a workaround because we can't figure out how to decode the 'from'
        side of messages sent across the wire. However, we can check to see if two messages
        are equal. Thus, by sending a random message to ourselves we can figure out what
        our own encoded id is. TODO: figure out how to decode it."""

        rand_channel = random.randint(0,1000000)
        try:
            temp_channel = self.api.pubsub_sub(topic=rand_channel,stream=True)
        except:
            print(f'\n{Fore.RED}ERROR: {Style.RESET_ALL}could not connect to IPFS PUBSUB.  Did you run the daemon with {Fore.GREEN}--enable-pubsub-experiment{Style.RESET_ALL} ?')
            sys.exit()

        secret = random.randint(0,1000000)
        self.api.pubsub_pub(topic=rand_channel,payload="id:" + str(secret))

        for encoded in temp_channel:

            # decode message
            decoded = self.decode_message(encoded)

            if(decoded is not None):
                if(str(decoded['data'].split(":")[-1]) == str(secret)):
                    return str(decoded['from'])

    def decode_message(self,encoded):
        if('from' in encoded):
            decoded = {}
            decoded['from'] = base64.standard_b64decode(encoded['from'])
            decoded['data'] = base64.standard_b64decode(encoded['data']).decode('ascii')
            decoded['seqno'] = base64.standard_b64decode(encoded['seqno'])
            decoded['topicIDs'] = encoded['topicIDs']
            decoded['encoded'] = encoded
            return decoded
        else:
            return None



    def serialize_torch_model(self, model, **kwargs):
        """
        kwargs are the arguments needed to instantiate the model
        """
        state = {'state_dict':model.state_dict(), 'kwargs':kwargs}
        torch.save(state, 'temp_model.pth.tar')
        with open('temp_model.pth.tar', 'rb') as f:
            model_bin = f.read()
            f.close()
        return model_bin

    def deserialize_torch_model(self, model_bin, model_class, **kwargs):
        """
        model_class is needed since PyTorch uses pickle for serialization
            see https://discuss.pytorch.org/t/loading-pytorch-model-without-a-code/12469/2 for details
        kwargs are the arguments needed to instantiate the model from model_class
        """
        with open('temp_model2.pth.tar', 'wb') as g:
            g.write(model_bin)
            g.close()
        state = torch.load()
        model = model_class(**state['kwargs'])
        model.load_state_dict(state['state_dict'])
        return model

    def serialize_numpy(self, tensor):
        return json.dumps(tensor.tolist()) # nested lists with same data, indices

    def deserialize_numpy(self,json_array):
        return np.array(json.loads(json_array)).astype('float')

    def publish(self,channel,dict_message):
        self.api.pubsub_pub(topic=channel,payload=json.dumps(dict_message))


    # TODO: framework = 'torch'
    def generate_fit_spec(self, model,request,batch_size=1,epochs=1,log_interval=1, framework = 'keras', model_class = None):

        model_bin = utils.serialize_keras_model(model)
        model_addr = self.api.add_bytes(model_bin)

        if model_class is not None:
            self.api.add_bytes(model_class)

        spec = {}
        spec['model_addr'] = model_addr
        spec['data_addr'] = request
        spec['batch_size'] = batch_size
        spec['epochs'] = epochs
        spec['log_interval'] = log_interval
        spec['framework'] = framework
        spec['train_channel'] = 'openmined_train_'+str(model_addr)
        return spec

    def listen_to_channel(self,handle_message,channel):
        new_models = self.api.pubsub_sub(topic=channel,stream=True)


        for m in new_models:
            message = self.decode_message(m)
            if(message is not None):
                out = handle_message(message)
                if(out is not None):
                    return out

    # TODO: torch
    def receive_model(self,message, verbose=True):
        msg = json.loads(message['data'])
        if(msg is not None):
            if(msg['type'] == 'transact'):
                return utils.ipfs2keras(msg['model_addr']),msg
            elif(msg['type'] == 'log'):
                if(verbose):
                    output = "Worker:" + msg['worker_id'][-5:]
                    output += " - Epoch " + str(msg['epoch_id']) + " of " + str(msg['num_epochs'])
                    output += " - Valid Loss: " + str(msg['eval_loss'])[0:8]
                    print(output)


    # TODO: torch
    def fit_worker(self,message):

        decoded = json.loads(message['data'])

        if(decoded['framework'] == 'keras'):

            model = utils.ipfs2keras(decoded['model_addr'])

            dataset = get_dataset(decoded['data_addr'])
            if dataset is None:
                raise Exception("Dataset could not be found. This should fail gracefully.")

            input, target = dataset.train_data, dataset.train_labels
            valid_input, valid_target = dataset.test_data, dataset.test_labels

            pipe = OutputPipe(
                id=self.id,
                publisher=self.publish,
                channel=decoded['train_channel'],
                epochs=decoded['epochs'],
                model_addr=decoded['model_addr'],
                model=model
            )

            model.fit(
                input,
                target,
                batch_size=decoded['batch_size'],
                validation_data=(valid_input, valid_target),
                verbose=False,
                epochs=decoded['epochs'],
                callbacks=[pipe]
            )

        else:
            raise NotImplementedError("Only compatible with Keras at the moment")


    def fit(self, model,request,batch_size=1,epochs=1,log_interval=1,message_handler=None):

        if(message_handler is None):
            message_handler = self.receive_model
        spec = self.generate_fit_spec(model,request,batch_size,epochs,log_interval)
        self.publish('openmined',spec)

        trained = self.listen_to_channel(message_handler,spec['train_channel'])
        return trained

    def work(self):
        self.listen_to_channel(self.fit_worker,'openmined')
