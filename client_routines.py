import torch as th
import syft as sy
import grid as gr
hook = sy.TorchHook(th)
worker = gr.GridClient(addr='http://localhost:5000')
x = th.tensor([1,2,3,4]).send(worker)
y = x + x
y
print(y)

