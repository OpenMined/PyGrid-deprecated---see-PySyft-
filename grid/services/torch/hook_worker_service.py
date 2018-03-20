import torch
from ..base import BaseService


class HookWorkerService(BaseService):
	def __init__(self, worker):
		super().__init__(worker)

	def hook_tensor_serde(self, tensor_type):
		# TODO
		pass