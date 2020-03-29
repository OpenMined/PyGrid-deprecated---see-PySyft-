import syft as sy
from syft.execution.state import State
from syft.execution.plan import Plan
from syft.execution.translation.torchscript import PlanTranslatorTorchscript
from syft.serde import protobuf
from syft_proto.execution.v1.state_pb2 import State as StatePB
from syft_proto.execution.v1.plan_pb2 import Plan as PlanPB
from syft.execution.placeholder import PlaceHolder

# assume _diff_state produced the same as here
# https://github.com/OpenMined/PySyft/blob/ryffel/syft-core/examples/experimental/FL%20Training%20Plan/Execute%20Plan.ipynb
# see step 7
# This serialization format will likely to change

# Make fake local worker for serialization
worker = sy.VirtualWorker(hook=None)


def unserialize_model_params(bin: bin):
    """Unserializes model or checkpoint or diff stored in db to list of tensors"""
    state = StatePB()
    state.ParseFromString(bin)
    state = protobuf.serde._unbufferize(worker, state)
    model_params = state.tensors()
    return model_params


def serialize_model_params(params: tuple):
    """Serializes list of tensors into State/protobuf"""
    model_params_state = State(
        owner=None,
        state_placeholders=[PlaceHolder().instantiate(param) for param in params],
    )
    pb = protobuf.serde._bufferize(worker, model_params_state)
    serialized_state = pb.SerializeToString()
    return serialized_state


def unserialize_plan(bin: bin):
    """Unserializes a Plan"""
    pb = PlanPB()
    pb.ParseFromString(bin)
    plan = protobuf.serde._unbufferize(worker, pb)
    return plan


def serialize_plan(plan: "Plan"):
    """Serializes a Plan"""
    pb = protobuf.serde._bufferize(worker, plan)
    serialized_plan = pb.SerializeToString()
    return serialized_plan


def translate_plan(plan: "Plan", variant: str):
    """Translate Plan to specified variant"""
    translators = {"torchscript": PlanTranslatorTorchscript}
    translator_cls = translators.get(variant, None)

    if translator_cls is None:
        return plan

    return plan.translate_with(translator_cls)
