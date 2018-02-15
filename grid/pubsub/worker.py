from grid.lib import OutputPipe, utils
from . import base
from grid.pubsub import commands
from grid.pubsub import channels
from colorama import Fore, Back, Style

import json
import threading
from bitcoin import base58
import os

"""
TODO: modify Client to store the source code for the model in IPFS.
      (think through logistics; introduces
      hurdles for packaging model source code)
TODO: figure out a convenient way to make robust training procedure for torch
      -- will probably want to use ignite for this
"""


class Worker(base.PubSub):

    def train_meta(self, message):
        decoded = json.loads(message['data'])
        if 'op_code' not in decoded:
            return

        self.learner_callback.stop_training = decoded['op_code'] == 'quit'

    # TODO: torch
    def fit_worker(self, message):

        decoded = json.loads(message['data'])

        if(decoded['framework'] == 'keras'):

            model = utils.ipfs2keras(decoded['model_addr'])

            try:
                np_strings = json.loads(self.api.cat(decoded['data_addr']))
            except NotImplementedError:
                raise NotImplementedError("The IPFS API only supports Python 3.6. Please modify your environment.")

            input, target, valid_input, valid_target = list(map(lambda x: self.deserialize_numpy(x),np_strings))
            train_channel = decoded['train_channel']

            self.learner_callback = OutputPipe(
                id=self.id,
                publisher=self.publish,
                channel=train_channel,
                epochs=decoded['epochs'],
                model_addr=decoded['model_addr'],
                model=model
            )

            args = (self.train_meta, train_channel + ':' + self.id)
            monitor_thread = threading.Thread(target=self.listen_to_channel,
                                              args=args)
            monitor_thread.start()

            print('training model')

            model.fit(
                input,
                target,
                batch_size=decoded['batch_size'],
                validation_data=(valid_input, valid_target),
                verbose=False,
                epochs=decoded['epochs'],
                callbacks=[self.learner_callback]
            )

            print('done')

        else:
            raise NotImplementedError("Only compatible with Keras at the moment")

    """
    Grid Tree Implementation

    Methods for Grid tree down here
    """

    def work(self):
        self.listen_to_channel(channels.openmined, self.fit_worker)
        self.listen_to_channel(channels.list_tasks, self.list_tasks)
        self.listen_to_channel(channels.add_task, self.discovered_tasks)
        self.listen_to_channel(channels.list_tasks_callback(self.id),
                               self.discovered_tasks)
        self.publish(channels.list_tasks, commands.list_all)

    def listen_for_models(self, model_name):
        self.listen_to_channel(channels.add_model(model_name), self.added_model)

    def list_tasks(self, message):
        fr = base58.encode(message['from'])

        print("listing tasks to " + fr)

        with open(".openmined/tasks.json", "r") as task_list:
            string_list = task_list.read()
            tasks = json.loads(string_list)
            for t in tasks:
                self.listen_for_models(t['name'])

        callback_channel = channels.list_tasks_callback(fr)

        self.publish(callback_channel, string_list)

    def added_model(self, info):
        info = self.api.get_json(info['data'])

        task_addr = info['task']
        model_addr = info['model']

        task_info = self.api.get_json(task_addr)
        data_dir = task_info['data_dir']
        name = task_info['name']

        print(f'FOUND NEW MODEL: {task_addr}, {model_addr}, {data_dir}, {name}')

        """
        if os.path.exists(f'data/{data_dir}'):
            model = utils.ipfs2keras(model_addr)

            input = []
            target = []

            model.fit(
                input,
                target,
                batch_size=100, # TODO config?!?!?!?!
                verbose=False,
                epochs=100, # TODO config?!??!??!?
                validation_split=0.1 # TODO config??!?!?!?!?!?
            )

            self.add_model(name, model, parent=info)
            """

    def discovered_tasks(self, tasks):
        print(f'{Fore.WHITE}{Back.BLACK} TASKS {Style.RESET_ALL}')
        print(f'From\t\t\t\tName\t\t\t\tAddress')
        print('==================================================================')

        data = json.loads(tasks['data'])
        fr = base58.encode(tasks['from'])

        for task in data:
            name = task['name']
            addr = task['address']

            # TODO should only listen on task channels that which i have data for
            self.listen_for_models(name)
            utils.store_task(name, addr)

            print(f'{fr}\t{name}\t{addr}')
