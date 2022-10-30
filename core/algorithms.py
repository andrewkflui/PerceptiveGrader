from abc import ABC, ABCMeta, abstractmethod

class Algorithm(ABC):
	def __init__(self, name, data, version=None):
		self.name = name
		self.data = data
		self.version = version
		self.result = None

	def __str__(self):
		if self.version is None:
			return '[{}]'.format(self.name.upper())
		else:
			return '[{}V{}]'.format(self.name.upper(), self.version)

	def set_attributes(self, args):
		for k, v in args.items():
			if k[0] == '_' or k[len(k)-1] == '_' or k in ['name', 'data', 'result', 'args']:
				continue
			
			if hasattr(self, k):
				setattr(self, k, v)

	@abstractmethod
	def run(self):
		raise NotImplementedError('run is not implemented')

	@abstractmethod
	def get_result(self):
		raise NotImplementedError('get_result not implemented')