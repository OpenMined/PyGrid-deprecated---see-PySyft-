import torch
from torch.autograd import Variable, Function
import sys
for x in sys.path:
    print(x)
from grid.lib import spdz


class SharedAdd(Function):

    @staticmethod
    def forward(ctx, a, b):
        return spdz.spdz_add(a, b)

    @staticmethod
    def backward(ctx, grad_out):
        grad_out = grad_out.data
        return grad_out, grad_out


class SharedMult(Function):

    @staticmethod
    def forward(ctx, a, b, interface):
        ctx.save_for_backward(a, b)
        ctx.interface = interface
        return spdz.spdz_mul(a, b, interface)

    @staticmethod
    def backward(ctx, grad_out):
        a, b = ctx.saved_tensors
        interface = ctx.interface
        grad_out = grad_out
        return Variable(spdz.spdz_mul(grad_out.data, b, interface)), Variable(spdz.spdz_mul(grad_out.data, a, interface))


class SharedMatmul(Function):

    @staticmethod
    def forward(ctx, a, b, interface):
        ctx.save_for_backward(a, b)
        ctx.interface = interface
        return spdz.spdz_matmul(a, b, interface)

    @staticmethod
    def backward(ctx, grad_out):
        a, b = ctx.saved_tensors
        interface = ctx.interface
        return spdz.spdz_matmul(grad_out,  b.t_(), interface), spdz.spdz_matmul(grad_out, a.t_(), interface)


class SharedSigmoid(Function):

    @staticmethod
    def forward(ctx, a, interface):
        ctx.save_for_backwards(a)
        ctx.interface = interface
        return spdz.spdz_sigmoid(a, interface)

    @staticmethod
    def backward(ctx, grad_out):
        a = ctx.saved_tensors
        interface = ctx.interface
        ones = spdz.encode(torch.FloatTensor(a.shape).one_())
        return spdz.spdz_mul(a, spdz.public_add(ones, -a, interface), interface)


class SharedVariable(object):

    def __init__(self, var, interface, requires_grad=True):
        self.requires_grad = requires_grad
        if not isinstance(var, Variable):
            raise ValueError('Var must be a variable')
        else:
            self.var = var
        self.interface = interface

    def __neg__(self):
        return SharedVariable(torch.Tensor.neg(self.var), self.requires_grad)

    def __add__(self, other):
        return self.add(other)

    def __mul__(self, other):
        return self.mul(other)

    def __matmul__(self, other):
        return self.matmul(other)

    def sigmoid(self):
        return SharedVariable(SharedSigmoid.apply(self.var, self.interface), self.interface)

    def add(self, other):
        return SharedVariable(SharedAdd.apply(self.var, other.var), self.interface, self.requires_grad)

    def mul(self, other):
        return SharedVariable(SharedMult.apply(self.var, other.var, self.interface), self.interface, self.requires_grad)

    def matmul(self, other):
        return SharedVariable(SharedMatmul.apply(self.var, other.var, self.interface), self.interface, self.requires_grad)

    @property
    def grad(self):
        return self.var.grad

    @property
    def data(self):
        return self.var.data

    def t_(self):
        self.var = self.var.t_()

    def __repr__(self):
        return self.var.__repr__()

    def type(self):
        return 'SharedVariable'
