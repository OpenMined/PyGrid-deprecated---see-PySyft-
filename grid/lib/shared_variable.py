import torch
from torch.autograd import Variable, Function
import inspect
import random
import copy

BASE = 10
KAPPA = 3  # ~29 bits

# TODO set these intelligently
PRECISION_INTEGRAL = 2
PRECISION_FRACTIONAL = 5
PRECISION = PRECISION_INTEGRAL + PRECISION_FRACTIONAL
BOUND = BASE**PRECISION

# Q field
field = 2**41  # < 64 bits
#Q = 2147483648
Q_MAXDEGREE = 1


def encode(rational, precision_fractional=PRECISION_FRACTIONAL):
    upscaled = (rational * BASE**precision_fractional).long()
    upscaled.remainder_(field)
    return upscaled


def decode(field_element, precision_fractional=PRECISION_FRACTIONAL):
    field_element = field_element.data
    neg_values = field_element.gt(field)
    #pos_values = field_element.le(field)
    #upscaled = field_element*(neg_valuese+pos_values)
    field_element[neg_values] = field-field_element[neg_values]
    rational = field_element.float() / BASE**precision_fractional
    return rational


def share(secret):
    first = torch.LongTensor(secret.shape).random_(field)
    second = (secret - first) % field
    return [first, second]


def reconstruct(shares):
    return sum(shares) % field


def swap_shares(share, party, interface):
    if (party == 0):
        interface.send(share)
        share_other = interface.receive()
    elif (party == 1):
        share_other = interface.receive()
        interface.send(share)
    return share_other


def truncate(x, party, amount=PRECISION_FRACTIONAL):
    if (x.party == 0):
        return x//BASE**amount
    return field-((field-x)//BASE**amount)


def public_add(x, y, party):
    if (party == 0):
        return x+y
    elif(party == 1):
        return x


def spdz_add(a, b):
    return (a+b % field)


def generate_mul_triple(m, n):
    r = torch.LongTensor(m, n).random_(field)
    s = torch.LongTensor(m, m).random_(field)
    t = r * s
    return r, s, t


def generate_mul_triple_communication(m, n, party, interface):
    if (party == 0):
        r, s, t = generate_mul_triple(m, n)

        r_alice, r_bob = share(r)
        s_alice, s_bob = share(s)
        t_alice, t_bob = share(t)

        swap_shares(r_bob, party, interface)
        swap_shares(s_bob, party, interface)
        swap_shares(t_bob, party, interface)

        triple_alice = [r_alice, s_alice, t_alice]
        return triple_alice
    elif (party == 1):
        r_bob = swap_shares(torch.LongTensor(m, n).zero_(), party, interface)
        s_bob = swap_shares(torch.LongTensor(m, n).zero_(), party, interface)
        t_bob = swap_shares(torch.LongTensor(m, n).zero_(), party, interface)
        triple_bob = [r_bob, s_bob, t_bob]
        return triple_bob


def spdz_mul(x, y, party, interface):
    if x.shape != y.shape:
        raise ValueError()
    m, n = x.shape
    triple = generate_mul_triple_communication(m, n, party, interface)
    a, b, c = triple
    d = x - a
    e = y - b

    d_other = swap_shares(d, party, interface)
    e_other = swap_shares(e, party, interface)
    delta = reconstruct([d, d_other])
    epsilon = reconstruct([e, e_other])
    r = delta * epsilon
    s = a * epsilon
    t = b * delta
    share = s + t + c
    share = public_add(share, r, party)
    share = truncate(share, party)
    return share


def generate_matmul_triple(m, n, k):
    r = torch.LongTensor(m, k).random_(field)
    s = torch.LongTensor(k, n).random_(field)
    t = (r @ s) % field
    return r, s, t


def generate_matmul_triple_communication(m, n, k, party, interface):
    if(party == 0):
        r, s, t = generate_matmul_triple(m, n, k)
        r_alice, r_bob = share(r)
        s_alice, s_bob = share(s)
        t_alice, t_bob = share(t)

        swap_shares(r_bob, party, interface)
        swap_shares(s_bob, party, interface)
        swap_shares(t_bob, party, interface)

        triple_alice = [r_alice, s_alice, t_alice]
        return triple_alice
    elif (party == 1):
        r_bob = swap_shares(torch.LongTensor(m, k).zero_(), party, interface)
        s_bob = swap_shares(torch.LongTensor(k, n).zero_(), party, interface)
        t_bob = swap_shares(torch.LongTensor(m, n).zero_(), party, interface)
        triple_bob = [r_bob, s_bob, t_bob]
        return triple_bob


def spdz_matmul(x, y, party, interface):
    x_height = x.shape[0]
    x_width = x.shape[1]

    y_height = y.shape[0]
    y_width = y.shape[1]

    assert x_width == y_height

    r, s, t = generate_matmul_triple_communication(
        x_height, y_width, x_width, party, interface)

    rho_local = x - r
    sigma_local = y - s

    # Communication
    rho_other = swap_shares(rho_local, party, interface)
    sigma_other = swap_shares(sigma_local, party, interface)

    # They both add up the shares locally
    rho = reconstruct([rho_local, rho_other])
    sigma = reconstruct([sigma_local, sigma_other])

    r_sigma = r @ sigma
    rho_s = rho @ s

    share = r_sigma + rho_s + t

    rs = rho @ sigma

    share = public_add(share, rs, party)
    share = truncate(share, party)
    return share


def generate_sigmoid_shares_communication(x, party, interface):
    if (party == 0):
        W0 = encode(torch.FloatTensor(x.shape).one_()*1/2)
        W1 = encode(torch.FloatTensor(x.shape).one_()*1/4)
        W3 = encode(torch.FloatTensor(x.shape).one_()*-1/48)
        W5 = encode(torch.FloatTensor(x.shape).one_()*1/480)

        W0_alice, W0_bob = share(W0)
        W1_alice, W1_bob = share(W1)
        W3_alice, W3_bob = share(W3)
        W5_alice, W5_bob = share(W5)

        swap_shares(W0_bob, party, interface)
        swap_shares(W1_bob, party, interface)
        swap_shares(W3_bob, party, interface)
        swap_shares(W5_bob, party, interface)

        quad_alice = [W0_alice, W1_alice, W3_alice, W5_alice]
        return quad_alice
    elif (party == 1):
        W0_bob = swap_shares(torch.LongTensor(
            x.shape).zero_(), party, interface)
        W1_bob = swap_shares(torch.LongTensor(
            x.shape).zero_(), party, interface)
        W3_bob = swap_shares(torch.LongTensor(
            x.shape).zero_(), party, interface)
        W5_bob = swap_shares(torch.LongTensor(
            x.shape).zero_(), party, interface)
        quad_bob = [W0_bob, W1_bob, W3_bob, W5_bob]
        return quad_bob


def spdz_sigmoid(x, party, interface):
    W0, W1, W3, W5 = generate_sigmoid_shares_communication(x, party, interface)
    x2 = spdz_mul(x, x, party, interface)
    x3 = spdz_mul(x, x2, party, interface)
    x5 = spdz_mul(x3, x2, party, interface)
    temp5 = spdz_mul(x5, W5, party, interface)
    temp3 = spdz_mul(x3, W3, party, interface)
    temp1 = spdz_mul(x, W1, party, interface)
    temp53 = spdz_add(temp5, temp3)
    temp531 = spdz_add(temp53, temp1)
    return spdz_add(W0, temp531)


class SharedAdd(Function):

    @staticmethod
    def forward(ctx, a, b):
        return spdz_add(a, b)

    @staticmethod
    def backward(ctx, grad_out):
        grad_out = grad_out.data
        return grad_out, grad_out


class SharedMult(Function):

    @staticmethod
    def forward(ctx, a, b, party, interface):
        ctx.save_for_backward(a, b)
        return spdz_mul(a, b, party, interface)

    @staticmethod
    def backward(ctx, grad_out, party, interface):
        a, b = ctx.saved_tensors
        grad_out = grad_out
        return Variable(spdz_mul(grad_out.data, b, party, interface)), Variable(spdz_mul(grad_out.data, a, party, interface))


class SharedMatmul(Function):

    @staticmethod
    def forward(ctx, a, b, party, interface):
        ctx.save_for_backward(a, b)
        return spdz_matmul(a, b, party, interface)

    @staticmethod
    def backward(ctx, grad_out, party, interface):
        a, b = ctx.saved_tensors
        return spdz_matmul(grad_out,  b.t_(), party, interface), spdz_matmul(grad_out, a.t_(), party, interface)


class SharedSigmoid(Function):

    @staticmethod
    def forward(ctx, a, party, interface):
        ctx.save_for_backwards(a)
        return spdz_sigmoid(a, party, interface)

    @staticmethod
    def backward(ctx, grad_out, party, interface):
        a = ctx.saved_tensors
        ones = encode(torch.FloatTensor(a.shape).one_())
        return spdz_mul(a, public_add(ones, -a, party), party, interface)


class SharedVariable(object):

    def __init__(self, var, party, interface, requires_grad=True):
        self.requires_grad = requires_grad
        if not isinstance(var, Variable):
            raise ValueError('Var must be a variable')
        else:
            self.var = var
        self.party = party
        self.interface = interface

    def __neg__(self):
        return SharedVariable(torch.Tensor.neg(self.var), self.party, self.requires_grad)

    def __add__(self, other):
        return self.add(other)

    def __mul__(self, other):
        return self.mul(other)

    def __matmul__(self, other):
        return self.matmul(other)

    def sigmoid(self):
        return SharedVariable(SharedSigmoid.apply(self.var, self.party, self.interface), self.party, self.interface)

    def add(self, other):
        return SharedVariable(SharedAdd.apply(self.var, other.var), self.party, self.interface, self.requires_grad)

    def mul(self, other):
        return SharedVariable(SharedMult.apply(self.var, other.var, self.party, self.interface), self.party, self.interface, self.requires_grad)

    def matmul(self, other):
        return SharedVariable(SharedMatmul.apply(self.var, other.var, self.party, self.interface), self.party, self.interface, self.requires_grad)

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
