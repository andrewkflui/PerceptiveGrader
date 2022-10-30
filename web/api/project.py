import os, copy, shutil, json, orjson
from pathlib import Path

import sys
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..{}..{}'.format(os.sep, os.sep)))

from abc import ABC, ABCMeta, abstractmethod

import numpy as np

from datasets.datasets import Dataset, EncodedDataset, SubDataset
from basis import config, constants
from basis.logger import logger
from core import utils
from core.algorithms import Algorithm
from gal.core.algorithms import GAL, get_subspace_dimension_string
from gal.core.subspaces import GALSubspace

from dataset_processor import process_dataset
from text_encoder import get_model, encode_dataset

def create_subspace_param_list(encoder, original_subspace_weight, num_subspace, random_dimension):
	subspace_param_list = [{'encoder': encoder, 'weight': original_subspace_weight}]
	for i in range(num_subspace):
		subspace_param_list += [{'encoder': encoder, 'random_dimension': random_dimension,
			'random_reference_position': 0, 'id': i+1}]
	dimension_string, subspaceencoder = get_subspace_dimension_string(subspace_param_list)
	return {'{} {}'.format(subspaceencoder.upper(), dimension_string): subspace_param_list}

def create_mixed_subspace_param_list(encoders, random_dimension):
	subspace_param_list = [{'encoder': encoder[0], 'weight': 0} for encoder in encoders]
	for position in range(len(encoders)):
		encoder,  count = encoders[position]
		for i in range(0, count):
			subspace_param_list.append({'encoder': encoder, 'random_dimension': random_dimension,
				'random_reference_positions': [(position, 1)], 'random_selection_method': 'vertical',
				'id': len(subspace_param_list)-len(encoders)+1})
	dimension_string, subspaceencoder = get_subspace_dimension_string(subspace_param_list)
	return {'{} {}'.format(subspaceencoder.upper(), dimension_string): subspace_param_list}

def create_mixed_inside_subspace_param_list(encoders, random_dimension):
	subspace_param_list = [{'encoder': encoder, 'weight': 0} for encoder in encoders]
	for i in range(16):
		encoder = '_'.join(encoders)
		encoder = encoder.replace('google_universal_sentence_encoder', 'GUSE')
		subspace_param_list.append({'encoder': encoder, 'random_dimension': random_dimension,
			'random_reference_positions': [(0, 0.5), (1, 0.5)], 'random_selection_method': 'vertical',
			'id': i+1})
	dimension_string, subspaceencoder = get_subspace_dimension_string(subspace_param_list)
	return {'{} {}'.format(subspaceencoder.upper(), dimension_string): subspace_param_list}

POSSIBLE_GRADES_OPTIONS = {1: ['Correct', 'Wrong'], 2: ['2', '1', '0']}
ENCODERS = {'GUSE': 'google_universal_sentence_encoder', 'Skip Thoughts': 'skip_thoughts',
	'Bert': 'bert', 'GloVe': 'glove', 'TFIDF': 'tfifd'}
SUBSPACE_OPTION_LIST = {}
SUBSPACE_OPTION_LIST.update(create_subspace_param_list('google_universal_sentence_encoder', 0, 16, 64))
# SUBSPACE_OPTION_LIST.update(create_subspace_param_list('glove', 0, 16, 64))
# SUBSPACE_OPTION_LIST.update(create_mixed_subspace_param_list(
# 	[('google_universal_sentence_encoder', 12), ('glove', 4)], 64))
# SUBSPACE_OPTION_LIST.update(create_mixed_inside_subspace_param_list(
# 	['google_universal_sentence_encoder', 'glove'], 128))

class Project():
	def __init__(self, temp_path=None, **kwargs):
		self.kwargs = kwargs
		# self.random_seed = None
		self.random_seed = 0	# Fixed for testing

		self.temp_path = temp_path
		self.project_path = None
		
		# self.processed_dataset: Dataset = None
		self.dataset: Dataset = None
		self.selected_answer_index = None

		self.algorithm_args = dict()
		self.algorithm: Algorithm = None
		self.tsne_data = None

		self.state = None
		self.initialized = False
		self.saved = False

		self.name = self.path = self.possible_grades_option = self.possible_grades = None
		self.subspace_param_list_key = self.subspace_param_list = None
		self.encoders, self.model_string_list = [], []
		self.encodings = {}

		self.ordered_answer_list, self.pgv_values, self.results = None, None, None

		self._exclude_copy_list = []
		self._set_empty_copy_list = ['processed_dataset', 'dataset', 'algorithm']
	
	def __str__(self):
		string = '[Project]\n'
		string += 'Name: {}\n'.format(self.name)
		string += 'Encoders: {}\n'.format(self.encoders)
		string += 'Models: {}\n'.format(self.model_string_list)
		string += str(self.dataset)
		return string

	def __copy__(self):
		clone = self.__class__.__new__(self.__class__)
		for k, v in self.__dict__.items():
			if k in self._exclude_copy_list:
				continue
			clone.__dict__[k] = v if not k in self._set_empty_copy_list else ([] if type(v) == list else None)
		return clone

	# def initialize(self, name, path, encoder, possible_grades_option, subspace_param_list_key):
	def initialize(self, name, path, possible_grades_option, subspace_param_list_key):
		try:
			# self.create(name, path, encoder, possible_grades_option, subspace_param_list_key)
			self.create(name, path, possible_grades_option, subspace_param_list_key)
			self.state = 'Processing Dataset'
			processed_dataset = self.process_dataset(path=path)
			self.state = 'Encoding Dataset'
			# self.dataset = self.encode_dataset(processed_dataset=self.processed_dataset)
			datasets, self.encodings = self.get_encodings(processed_dataset)
			for key, value in self.encodings.items():
				logger.debug(f'Project.get_encodings, encodings, keys: {key}, value.shape: {np.array(value).shape}')
			self.dataset = datasets[0]
			self.state = None
			self.initialized = True
			logger.info(str(self))
		except Exception as e:
			self.state = 'Error{}: {}'.format(' while ' + self.state if self.state is not None else '', e)
			logger.error('Project.initialize, {}'.format(self.state))
			raise Exception(f'Project.initialize, {self.state}')

	# def create(self, name, path, encoder, possible_grades_option, subspace_param_list_key):
	def create(self, name, path, possible_grades_option, subspace_param_list_key):
		self.name = name
		self.path = path
		# self.encoder = encoder
		# self.source_model, self.model, self.model_string = get_model(encoder, None)
		self.possible_grades_option = possible_grades_option
		self.possible_grades = POSSIBLE_GRADES_OPTIONS[self.possible_grades_option]
		self.subspace_param_list_key = subspace_param_list_key
		self.subspace_param_list = SUBSPACE_OPTION_LIST[self.subspace_param_list_key]
		self.encoders = [param.get('encoder') for param in self.subspace_param_list \
			if param.get('random_dimension') is None]
		for encoder in self.encoders:
			self.model_string_list.append(get_model(encoder, None)[2])
		# self.saved = False

	def save(self, path):
		# if self.saved:
		# 	self.state = None
		# 	return
		if path is None:
			return

		try:
			self.state = 'Saving'
			self.saved = True
			# self.project_path = self.project_path or os.path.join(path, self.name)
			self.project_path = self.project_path or path
			clone = copy.copy(self)
			clone.state = None
			utils.save(clone, self.project_path, 'project.dat')
			self.state = 'Saving Datasets'
			# utils.save(self.processed_dataset, self.project_path, 'processed_dataset.dat')
			utils.save(self.dataset, self.project_path, 'dataset.dat')
			utils.save(self.algorithm, self.project_path, 'algorithm.dat')
			self.state = None
		except Exception as e:
			self.state = 'Error{}: {}'.format(' while ' + self.state if self.state is not None else '', e)
			self.saved = False
			logger.error('Project.save, {}'.format(self.state))
			raise Exception(self.state)
		
	def load(self, project_path):
		try:
			self.state = 'Loading'
			self.project_path = project_path
			clone = utils.load(os.path.join(self.project_path, 'project.dat'))
			self.__dict__.update(clone.__dict__)
			self.state = 'Loading Datasets'
			# self.processed_dataset = utils.load(os.path.join(self.project_path, 'processed_dataset.dat'))
			self.dataset = utils.load(os.path.join(self.project_path, 'dataset.dat'))
			self.algorithm = utils.load(os.path.join(self.project_path, 'algorithm.dat'))
			
			# TO-DO: check again
			self.get_valuable_answer_indices(batch_size=self.algorithm.reduced_num_data)
			self.tsne_data = utils.get_tsne_data(self.algorithm.subspaces[0].data, mode='2d', perplexity=5.)

			self.saved = True
			self.state = None
			self.initialized = True
		except Exception as e:
			self.state = 'Error{}: {}'.format(' while ' + self.state if self.state is not None else '', e)
			logger.error('Project.load, {}'.format(self.state))

	def process_dataset(self, path):
		processed_dataset = process_dataset(name=None, root=None, file_path=path, save=False)
		self._question_id = processed_dataset.questions[0].id
		logger.debug('Project.process_dataset, question_id: {}'.format(self._question_id))
		return processed_dataset

	def encode_dataset(self, processed_dataset, encoder, model_string, cache=False):
		dataset, encodings = None, None
		if cache and self.temp_path is not None:
			# dataset_path = os.path.join(config.ROOT_PATH, 'web', 'api', 'temp')
			dataset_path = self.temp_path
			dataset_file_name = self.name + '_dataset.dat'
			encodings_file_name = '{}_{}_{}_encodings.dat'.format(self.name, encoder, model_string.replace(os.sep, '_'))
		else:
			dataset_path = dataset_file_name = encodings_file_name = None
		if dataset_path is not None and os.path.exists(os.path.join(dataset_path, dataset_file_name)) \
			and os.path.exists(os.path.join(dataset_path, encodings_file_name)):
			dataset = utils.load(os.path.join(dataset_path, dataset_file_name))
			encodings = utils.load(os.path.join(dataset_path, encodings_file_name))
		else:
			# self.dataset = encode_dataset(name=None, question_id=None, encoder=self.encoder,
			# 	model=self.model_string, dataset=self.processed_dataset, save=False)
			# for i in range(len(self.encoders)):
			# 	dataset = encode_dataset(name=None, question_id=None, encoder=self.encoders[i],
			# 		model=self.model_string_list[i], dataset=processed_dataset, save=False)
				# self.encodings[self.encoders[i]] = [a.encoding for a in d.answers]
			dataset = encode_dataset(name=None, question_id=None, encoder=encoder,
					model=model_string, dataset=processed_dataset, save=False)
			encodings = [a.encoding for a in dataset.answers]

			if cache and dataset_path is not None:
				utils.save(dataset, dataset_path, dataset_file_name)
				utils.save(encodings, dataset_path, encodings_file_name)
		return dataset, encodings

	def get_encodings(self, processed_dataset, cache=True):
		datasets, encodings = [], {}
		for i in range(len(self.encoders)):
			d, e = self.encode_dataset(processed_dataset, self.encoders[i],
				self.model_string_list[i], cache=cache)
			datasets.append(d)
			encodings[self.encoders[i]] = e
		return datasets, encodings
	
	def add_data(self, new_data_file_path):
		new_data_list = {}
		processed_dataset = self.process_dataset(path=new_data_file_path)
		# for i in range(len(self.encoders)):
		# 	# dataset = encode_dataset(name=None, question_id=None, encoder=self.encoders[i],
		# 	# 	model=self.model_string_list[i], dataset=processed_dataset, save=False)
		# 	dataset, encodings = self.encode_dataset(processed_dataset=processed_dataset, cache=False)
		# 	if i == 0:
		# 		self.dataset.add_data(dataset.answers)
		# 	# self.encodings[self.encoders[i]] += [a.encoding for a in dataset.answers]
		# 	new_data = np.copy([a.encoding for a in dataset.answers])
		# 	self.encodings[self.encoders[i]] += new_data
		# 	new_data_list[self.encoders[i]] = new_data
		
		# if self.temp_path is not None:
		# 	# dataset_path = os.path.join(config.ROOT_PATH, 'web', 'api', 'temp')
		# 	dataset_path = self.temp_path
		# 	dataset_file_name = self.name + '_dataset.dat'
		# 	encodings_file_name = '{}_{}_encodings.dat'.format(self.name, self.subspace_param_list_key)
		# 	utils.save(self.dataset, dataset_path, dataset_file_name)
		# 	utils.save(self.encodings, dataset_path, encodings_file_name)

		datasets, new_data_list = self.get_encodings(processed_dataset, cache=False)
		self.dataset.add_data(datasets[0].answers)
		for key, value in new_data_list.items():
			self.encodings[key] += value

		self.algorithm.add_data(new_data_list, additional_grading_actions=0, additional_batch_sizes=None)
		self.get_valuable_answer_indices(batch_size=self.algorithm.reduced_num_data)
		self.tsne_data = utils.get_tsne_data(self.algorithm.subspaces[0].data, mode='2d', perplexity=5.)
	
	# def select_answer(self, answer_index):
	# 	self.selected_answer_index = answer_index
	# 	self.saved = False

	def answer_markup(self, answer_index, value):
		# self.dataset.answers[answer_index].markup = value
		self.dataset.answers[answer_index].markup_class = value
		self.save(self.project_path)

	def initialize_algorithm(self):
		for params in self.subspace_param_list:
			random_dimension = params.get('random_dimension')
			if random_dimension is None:
				encoder, model = params.get('encoder'), params.get('model', None),
				compress_factor = params.get('compress_factor', None)
				compress_method = params.get('compress_method', 'pca')

				data, reference_data = [], []
				# for a in self.dataset.answers:
				# 	if a.is_reference:
				# 		reference_data.append(a.encoding)
				# 	else:
				# 		data.append(a.encoding)
				for a in range(len(self.dataset.answers)):
					if self.dataset.answers[a].is_reference:
						reference_data.append(self.encodings[encoder][a])
					else:
						data.append(self.encodings[encoder][a])
				data = np.array(data)
				reference_data = np.array(reference_data)
				if compress_factor is not None:
					data, reference_data = utils.compress_data(data, reference_data, compress_factor,
						file_path=None, save_to_file=False, method=compress_method)
				params['data'] = data

		self.algorithm = GAL(subspace_param_list=self.subspace_param_list,
			possible_grades=self.possible_grades, random_seed=self.random_seed)
		self.get_valuable_answer_indices(batch_size=self.algorithm.reduced_num_data)
		self.tsne_data = utils.get_tsne_data(self.algorithm.subspaces[0].data, mode='2d', perplexity=5.)

	def get_valuable_answer_indices(self, batch_size):
		indices, reduced_indices, selection_param_dict, informations, nearest_ground_truth_distances, \
		local_nearest_ground_truth_distance_list, local_nearest_ground_truth_index_map_list, \
		local_marginalness_list, global_marginalness, outlier_indices_list \
			= self.algorithm.run(batch_size=batch_size)
		# self.ordered_answer_list = [(i, self.dataset.answers[i]) for i in indices]
		# self.ordered_answer_list = indices
		# return self.ordered_answer_list
		self.pgv_values = informations.tolist()
		self.get_ordered_answer_list(reduced_indices)

	def get_ordered_answer_list(self, reduced_indices):
		# remaining_indices = list(range(self.algorithm.reduced_num_data))
		# self.ordered_answer_list = []
		# for reduced_index in reduced_indices:
		# 	self.ordered_answer_list += self.algorithm.get_original_data_indices([reduced_index])
		# 	remaining_indices.remove(reduced_index)
		# for reduced_index in remaining_indices:
		# 	self.ordered_answer_list += self.algorithm.get_original_data_indices([reduced_index])
		self.ordered_answer_list = reduced_indices \
			+ [i for i in range(self.algorithm.reduced_num_data) if i not in reduced_indices]

	def adjust_cutoff(self, adjust_type, value):
		if self.algorithm is None:
			return
		self.algorithm.adjust_cutoff(adjust_type, value)
		self.get_valuable_answer_indices(batch_size=self.algorithm.reduced_num_data)
		self.results = self.algorithm.get_result().tolist() if self.results is not None else None
		self.save(self.project_path)

	def run(self, answer_index_label_dict):
		if self.algorithm is None:
			return None, None, None
		self.algorithm.mark_answers(answer_index_label_dict)
		self.get_valuable_answer_indices(batch_size=self.algorithm.reduced_num_data)
		self.results = self.algorithm.get_result().tolist()
		self.save(self.project_path)
		return self.ordered_answer_list, self.pgv_values, self.results

class ProjectManager(object):
	def __init__(self, temp_path=None):
		super().__init__()
		self.temp_path = temp_path
		self.projects = dict()

	def load_saved_project_names(self, directory):
		try:
			if not os.path.exists(directory):
				utils.create_directories(directory)
				return
			for subdirectory in os.listdir(directory):
				if os.path.isdir(os.path.join(directory, subdirectory)):
					# self.projects[subdirectory] = None
					self.projects[subdirectory] = Project()
					self.projects[subdirectory].project_path = os.path.join(directory, subdirectory)
		except Exception as e:
			logger.error(f'ProjectManager.load_saved_project_names, error: {e}')

	def get_project(self, name):
		# return self.projects[name] if name in self.projects else None
		if not name in self.projects:
			return None
		elif not self.projects[name].initialized:
			self.projects[name].load(self.projects[name].project_path)
		return self.projects[name]
	
	# def create_project(self, name, path, encoder, possible_grades_option, subspace_param_list_key):
	def create_project(self, name, path, possible_grades_option, subspace_param_list_key):
		try:
			project = Project(temp_path=self.temp_path)
			# project.initialize(name, path, encoder, possible_grades_option, subspace_param_list_key)
			project.initialize(name, path, possible_grades_option, subspace_param_list_key)
			project.initialize_algorithm()
			self.projects[name] = project
			return project
		except Exception as e:
			logger.error(f'ProjectManager.create_project, error: {e}')
			return None

	def load_project(self, project_path):
		try:
			project = Project()
			project.load(project_path)
			self.projects[project.name] = project
			return project
		except Exception as e:
			logger.error(f'ProjectManager.load_project, error: {e}')
			return None

	def save_project(self, name, project_path):
		try:
			self.projects[name].save(project_path)
			return self.projects[name]
		except Exception as e:
			logger.error(f'ProjectManager.save_project, error: {e}')
			return None

	def delete_project(self, name):
		try:
			if name not in self.projects:
				return
			if self.projects[name].project_path is not None:
				try:
					shutil.rmtree(self.projects[name].project_path)
				except Exception as e:
					pass
			del self.projects[name]
		except Exception as e:
			logger.error(f'ProjectManager.delete_project, error: {e}')

class Serializer(ABC):
	param_list = []
	serializable_object_params = {}

	@classmethod
	def serialize(cls, obj):
		param_dict = dict()
		if obj is None:
			return None
		try:
			param_list = cls.param_list + list(cls.serializable_object_params.keys())
			param_list = param_list if len(param_list) > 0 else obj.__dict__
			for k in param_list:
				v = getattr(obj, k)
				if k in cls.serializable_object_params:
					if type(v) == list:
						param_dict[k] = [cls.serializable_object_params[k].serialize(o) for o in v]
					else:
						param_dict[k] = cls.serializable_object_params[k].serialize(v)
				elif k in param_list:
					# param_dict[k] = v if not isinstance(v, np.ndarray) else v.tolist()
					# param_dict[k] = v if not isinstance(v, np.ndarray) else str(v)
					param_dict[k] = v
					# param_dict[k] = cls.serialize_recusive(k, v)
			# data = json.loads(json.dumps(param_dict, sort_keys=True))
			data = orjson.loads(orjson.dumps(param_dict,
				option=orjson.OPT_SERIALIZE_NUMPY | orjson.OPT_SORT_KEYS | orjson.OPT_NON_STR_KEYS))
			return data
		except Exception as e:
			logger.error('Serializer.serialize, obj.type: {}, param_list: {}, e: {}'.format(
				type(obj), param_list, e))
			# return {'error': str(e)}
			raise Exception(e)

class GALSubspaceSerializer(Serializer):
	# param_list = ['weight', 'random_selections', 'random_selection_method',
	# 	'horizontal_random_selection_number', 'compress_method', 'distance_function', 'epsilon',
	# 	'spaciousness_neighbour_number', 'num_data', 'reduced_num_data', 'reduced_data', 'rd_cutoff',
	# 	'rd_deriving_factor', 'delta_link_threshold', 'default_rd_cutoff', 'default_delta_link_threshold',
	# 	'rd_cutoff_adjustment', 'delta_link_threshold_adjustment', 'max_delta', 'reduced_data_distances',
	# 	'densities', 'normalized_densities', 'max_density_indices', 'spaciousness', 'normalized_spaciousness',
	# 	'nearest_neighbours', 'original_to_reduced_index_map']
	param_list = ['weight', 'compress_method', 'distance_function', 'epsilon',
		'spaciousness_neighbour_number', 'num_data', 'reduced_num_data', 'rd_cutoff',
		'rd_deriving_factor', 'delta_link_threshold', 'default_rd_cutoff', 'default_delta_link_threshold',
		'rd_cutoff_adjustment', 'delta_link_threshold_adjustment', 'max_delta', 'nearest_neighbours']

class GALSerializer(Serializer):
	param_list = ['num_data', 'reduced_num_data', 'default_grade', 'current_iteration',
		'data', 'rd_cutoff', 'delta_link_threshold', 'default_rd_cutoff',
		'default_delta_link_threshold', 'rd_cutoff_adjustment', 'delta_link_threshold_adjustment',
		'known_data_labels', 'reduced_known_data_labels', 'reduced_data_distances', 'densities',
		'spaciousness', 'averaged_spaciousness', 'original_to_reduced_index_map']
	# serializable_object_params = {'subspaces': GALSubspaceSerializer}

class EncoderSerializer(Serializer):
	param_list = ['name']

class AnswerSerializer(Serializer):
	param_list = ['id', 'text', 'is_reference', 'markup_class']

class QuestionSerializer(Serializer):
	param_list = ['id', 'text']

class DatasetSerializer(Serializer):
	param_list = ['name']
	serializable_object_params = {'encoder': EncoderSerializer, 'question': QuestionSerializer,
		'answers': AnswerSerializer}

class ProjectSerializer(Serializer):
	param_list = ['name', 'encoders', 'possible_grades', 'subspace_param_list_key',
		'random_seed', 'selected_answer_index', 'ordered_answer_list', 'pgv_values', 'results', 'tsne_data',
		'state', 'saved']
	# serializable_object_params = {'dataset': DatasetSerializer, 'algorithm': GALSerializer}
	serializable_object_params = {'dataset': DatasetSerializer}



