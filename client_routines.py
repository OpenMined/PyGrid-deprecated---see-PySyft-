import torch as th
import syft as sy
import grid as gr
import requests
import time

addr = "http://localhost:5000"

hook = sy.TorchHook(th)
worker = gr.GridClient(addr=addr)


def main():
    x = th.tensor([1, 2, 3, 4]).send(worker)
    y = x + x
    print("Y = ", y.get())


if __name__ == "__main__":
    main()
# del x
# del y
