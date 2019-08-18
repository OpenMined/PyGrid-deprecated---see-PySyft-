import torch as th
import syft as sy
import binascii
import requests
import os
from syft.workers import BaseWorker

from grid import utils as gr_utils


class GridClient(BaseWorker):
    """GridClient."""

    def __init__(self, addr: str, verbose: bool = True, hook=None, id="grid", **kwargs):
        hook = sy.hook if hook is None else hook
        super().__init__(hook=hook, id=id, verbose=verbose, **kwargs)
        print(
            "WARNING: Grid nodes publish datasets online and are for EXPERIMENTAL use only."
            "Deploy nodes at your own risk. Do not use OpenGrid with any data/models you wish to "
            "keep private.\n"
        )
        self.addr = addr
        self._verify_identity()

    def _verify_identity(self):
        r = requests.get(self.addr + "/identity/")
        if r.text != "OpenGrid":
            raise PermissionError("App is not an OpenGrid app.")

    def _send_msg(self, message: bin, location: BaseWorker) -> bin:
        raise NotImplementedError

    def _send_post(self, route, data, N: int = 10):
        url = os.path.join(self.addr, "{}/".format(route))
        r = requests.post(url, data=data)
        response = r.text
        # Try to request the message `N` times.
        for _ in range(N - 1):
            try:
                response = binascii.unhexlify(response[2:-1])
            except:
                if self.verbose:
                    print(response)
                response = None
                continue

            r = requests.post(url, data=data)
            response = r.text

        return response

    def _recv_msg(self, message: bin, N: int = 10) -> bin:
        message = str(binascii.hexlify(message))
        return self._send_post("cmd", data={"message": message}, N=N)

    def destroy(self):
        grid_name = self.addr.split("//")[1].split(".")[0]
        gr_utils.exec_os_cmd("heroku destroy " + grid_name + " --confirm " + grid_name)
        if self.verbose:
            print("Destroyed node: " + str(grid_name))
