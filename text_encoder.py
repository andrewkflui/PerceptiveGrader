import os, argparse, datetime
from pathlib import Path

import numpy as np

from core import utils
from basis import constants
from basis.logger import logger
from datasets.datasets import *

def get_model(encoder, model=None):
	if model is None:
		model = constants.ENCODERS[encoder]['default_model']
	
	# if '/' in model:
	if os.sep in model:
		# parts = model.split('/')
		parts = os.path.split(model)
		source_model = parts[0]
		model = parts[1]
	else:
		source_model = None

	return source_model, model, os.path.join(source_model, model) if source_model is not None else model

def load_processed_dataset(name, question_id, **kwargs):
	path = Path(config.ROOT_PATH) / 'data' / 'datasets' / 'processed'
	if name in constants.DATASETS:
		path /= constants.DATASETS[name]['processed_folder']
	else:
		path /= name.lower()

	if not os.path.exists(path):
		raise utils.InvalidNameError('dataset', name)
	
	# dataset = utils.load(path / 'data.txt')
	if question_id is not None:
		dataset = utils.load(path / question_id / 'data.txt')
	else:
		dataset = utils.load(path / 'data.txt')
	logger.info('text_encoder.load_processed_dataset: {}'.format(str(dataset)))

	return dataset

def encode_dataset(name, question_id, encoder, model=None, save=True, **kwargs):
	checkpoint_name = kwargs.get('checkpoint_name', None)
	dimension = kwargs.get('dimension', None)
	mapping = kwargs.get('mapping', None)
	scale = 0.7 if name == 'USCIS' or (name == 'SEB3' and mapping == '2way') \
		else (0.6 if (name == 'ASAPSAS' and mapping == '2way') else 0.5)

	min_frequency = kwargs.get('min_frequency', 0)
	lemmatize = not kwargs.get('not_lemmatize', False)
	remove_stop_words = not kwargs.get('not_remove_stop_words', False)

	# path = Path(config.ROOT_PATH) / 'data' / 'datasets' / 'processed'
	# if name in constants.DATASETS:
	# 	path /= constants.DATASETS[name]['processed_folder']
	# else:
	# 	path /= name.lower()

	# if not os.path.exists(path):
	# 	raise utils.InvalidNameError('dataset', name)

	# source_model, model, _ = get_model(encoder, model=model)
	
	# start_time = datetime.datetime.now()
	# # dataset = utils.load(path / 'data.txt')
	# if question_id is not None:
	# 	dataset = utils.load(path / question_id / 'data.txt')
	# else:
	# 	dataset = utils.load(path / 'data.txt')
	# logger.info(str(dataset))

	start_time = datetime.datetime.now()
	source_model, model, _ = get_model(encoder, model=model)
	dataset = kwargs.get('dataset', None) or load_processed_dataset(name, question_id, **kwargs)

	# output_path = 'data/datasets/encoded/{}/{}'.format(encoder, dataset.name)
	if encoder == 'skip_thoughts':
		from datasets.encoders import SkipThoughts
		checkpoint_name = checkpoint_name if checkpoint_name is not None else constants.ENCODERS[encoder]['default_checkpoint_name']
		encoded_dataset = SkipThoughts(model=model, checkpoint_name=checkpoint_name).encode(dataset)
	# elif encoder == 'google_universal_sentence_encoder':
	elif 'google_universal_sentence_encoder' in encoder:
		from datasets.encoders import GoogleUniversalSentenceEncoder
		encoded_dataset = GoogleUniversalSentenceEncoder(
			model=model, multilingual='multilingual' in encoder).encode(dataset)
	elif encoder == 'glove':
		from datasets.encoders import Glove
		encoded_dataset = Glove(source_model=source_model, ngram_range=(1, 3), min_frequency=min_frequency,
			lemmatize=lemmatize, remove_stop_words=remove_stop_words).encode(dataset)
	elif encoder == 'bert':
		from datasets.encoders import Bert
		encoded_dataset = Bert(source_model=source_model, dataset_name=model,
			ngram_range=(1, 3), min_frequency=min_frequency, lemmatize=lemmatize,
			remove_stop_words=remove_stop_words, oov_handler='avg').encode(dataset)
	elif encoder == 'fasttext':
		from datasets.encoders import FastText
		encoded_dataset = FastText(remove_stop_words=remove_stop_words).encode(dataset)
	elif encoder == 'tfidf':
		from datasets.encoders import TFIDF
		encoded_dataset = TFIDF(ngram_range=(1, 3), min_frequency=min_frequency, retrain=False).encode(dataset)
	elif encoder == 'count':
		from datasets.encoders import Count
		encoded_dataset = Count(ngram_range=(1, 3), min_frequency=min_frequency, retrain=False).encode(dataset)
	elif encoder == 'lsa':
		from datasets.encoders import LSA
		encoded_dataset = LSA(ngram_range=(1, 3), min_frequency=min_frequency, n_components=100, retrain=False).encode(dataset)
	elif encoder == 'jaccard_similarity':
		from datasets.encoders import JaccardSimilarity
		encoded_dataset = JaccardSimilarity(lemmatize=lemmatize, remove_stop_words=remove_stop_words).encode(dataset)
	else:
		raise utils.InvalidNameError('encoder', encoder)

	if save:
		output_path = Path(config.ROOT_PATH) / 'data' / 'datasets' / 'encoded' \
			/ encoded_dataset.encoder.name / encoded_dataset.encoder.model
		if name in constants.DATASETS:
			output_path /= constants.DATASETS[name]['processed_folder']
		else:
			output_path /= encoded_dataset.name.lower()

		utils.save(encoded_dataset, output_path, 'dataset.txt')

		is_preset = isinstance(dataset, PresetDataset)
		for question in encoded_dataset.questions:
			question_folder_path = output_path / question.id

			dataset = SubDataset(encoded_dataset=encoded_dataset, question=question)
			utils.save(dataset, question_folder_path, 'dataset.dat')
			if not os.path.exists(question_folder_path):
				utils.create_directories(question_folder_path)
			np.save(question_folder_path / 'data', dataset.data, allow_pickle=True)

			if not is_preset:
				continue

			if name == 'USCIS':
				mapping = '2way'
			elif name.startswith('SEB'):
				if name == 'SEB2':
					mapping = '2way'
				elif name == 'SEB3' and (mapping is None or (mapping not in ['2way', '3way'])):
					mapping = '3way'
				elif name == 'SEB5' and (mapping is None or (mapping not in ['2way', '3way', '5way'])):
					mapping = '5way'
			
			labels = np.array([a.get_answer_class(mapping, scale, dataset=dataset,
				question=question) for a in dataset.answers])

			if (name == 'SEB3' and mapping != '3way') or (name == 'SEB5' and mapping != '5way') \
				or (name == 'ASAPSAS' and mapping is not None):
				# labels_path = '{}/{}/{}'.format(output_path, question.id, mapping)
				labels_path = question_folder_path / mapping
			else:
				# labels_path = '{}/{}'.format(output_path, question.id)
				labels_path = question_folder_path
			
			rows = []
			for i in range(dataset.num_data):
				rows.append([dataset.answers[i].text, labels[i]])
			utils.write_csv_file(labels_path, 'labels.tsv', rows, delimiter='\t')

			# save reference answers separately
			np.save(Path(output_path) / question.id / 'reference_answer_data', dataset.reference_answer_data, allow_pickle=True)
			reference_answer_labels = np.array([a.get_answer_class(mapping, scale, dataset=dataset,
				question=question) for a in dataset.reference_answers])
			rows = []
			for i in range(len(reference_answer_labels)):
				rows.append([dataset.reference_answers[i].text, reference_answer_labels[i]])
			utils.write_csv_file(labels_path, 'reference_answer_labels.tsv', rows, delimiter='\t')

	end_time = datetime.datetime.now()
	logger.info('Encoding Finished, time used: {}'.format(end_time - start_time))
	return encoded_dataset if name is not None and question_id is None \
		else SubDataset(encoded_dataset=encoded_dataset, question=encoded_dataset.questions[0])

if __name__ == '__main__':
	parser = argparse.ArgumentParser()

	parser.add_argument('--name', help='dataset name, options={}'.format([key for key in constants.DATASETS.keys()]), required=True)
	parser.add_argument('--question_id', help='question_id', required=False)
	parser.add_argument('--encoder', help='encoder name, options={}'.format([key for key in constants.ENCODERS.keys()]), required=True)
	parser.add_argument('--model', help='model name', required=False)
	parser.add_argument('--checkpoint_name', help='checkpoint name (for skip_thoughts)', required=False)
	# parser.add_argument('--dataset_name', help='model dataset name (for BERT)', required=False)
	parser.add_argument('--dimension', help='encoded model dimension (for GloVE models)', required=False)
	parser.add_argument('--mapping', help='mapping to be applied to original labels', required=False)

	# for word embeddings
	parser.add_argument('--min_frequency', help='min_frequency for word embeddings', type=int, default=0, required=False)
	parser.add_argument('--not_lemmatize', help='not to lemmatize', action='store_true', default=False, required=False)
	parser.add_argument('--not_remove_stop_words', help='not to remove stop words', action='store_true', default=False, required=False)

	args = parser.parse_args()
	encoded_dataset = encode_dataset(**vars(args))

	# name = args.name
	# encoder = args.encoder
	# model = args.model
	# checkpoint_name = args.checkpoint_name
	# # dataset_name = args.dataset_name
	# dimension = args.dimension
	# mapping = args.mapping
	# scale = 0.7 if name == 'USCIS' or (name == 'SEB3' and mapping == '2way') else 0.5

	# min_frequency = args.min_frequency
	# lemmatize = not args.not_lemmatize
	# remove_stop_words = not args.not_remove_stop_words

	# utils.validate_option(constants.DATASETS.keys(), name, 'dataset')

	# if model is None:
	# 	model = constants.ENCODERS[encoder]['default_model']
			
	# if '/' in model:
	# 	parts = model.split('/')
	# 	source_model = parts[0]
	# 	model = parts[1]
	# else:
	# 	source_model = None
	
	# start_time = datetime.datetime.now()

	# # dataset = utils.load(Path(os.path.abspath(os.path.dirname(__file__))) / 'data/datasets/processed' / constants.DATASETS[name]['processed_folder'] / 'data.txt')
	# dataset = utils.load(Path(config.ROOT_PATH) / 'data/datasets/processed'
	# 	/ constants.DATASETS[name]['processed_folder'] / 'data.txt')
	# print(dataset)

	# # output_path = 'data/datasets/encoded/{}/{}'.format(encoder, dataset.name)
	# if encoder == 'skip_thoughts':
	# 	from datasets.encoders import SkipThoughts
	# 	checkpoint_name = args.checkpoint_name if args.checkpoint_name is not None else constants.ENCODERS[encoder]['default_checkpoint_name']
	# 	encoded_dataset = SkipThoughts(model=model, checkpoint_name=checkpoint_name).encode(dataset)
	# elif encoder == 'google_universal_sentence_encoder':
	# 	from datasets.encoders import GoogleUniversalSentenceEncoder
	# 	encoded_dataset = GoogleUniversalSentenceEncoder(model=model).encode(dataset)
	# elif encoder == 'glove':
	# 	from datasets.encoders import Glove
	# 	# encoded_dataset = Glove(model=model, dimension=dimension, remove_stop_words=remove_stop_words).encode(dataset)
	# 	# output_path = 'data/datasets/encoded/{}{}/{}/{}'.format(encoder, '_without_stop_words' if remove_stop_words else '', dataset.name, encoded_dataset.encoder.model)

	# 	# encoded_dataset = Glove(source_model=model, ngram_range=(1, 3), min_frequency=min_frequency,
	# 	# 	retrain=False).encode(dataset)
	# 	encoded_dataset = Glove(source_model=source_model, ngram_range=(1, 3), min_frequency=min_frequency,
	# 		lemmatize=lemmatize, remove_stop_words=remove_stop_words).encode(dataset)
	# elif encoder == 'bert':
	# 	from datasets.encoders import Bert
	# 	# model bert_12_768_12
	# 	# dataset_name choices: book_corpus_wiki_en_uncased, book_corpus_wiki_en_cased, wiki_multilingual. wiki_multilingual_cased. wiki_cn

	# 	# model: bert_24_1024_16
	# 	# dataset_name choices: book_corpus_wiki_en_cased

	# 	# dataset_name = args.dataset_name if args.dataset_name is not None else constants.ENCODERS[encoder]['default_dataset_name']

	# 	# oov_handler choices: sum, avg, last
	# 	# encoded_dataset = Bert(model=model, dataset_name=dataset_name, oov_handler='avg',
	# 	# 	remove_stop_words=remove_stop_words).encode(dataset)
	# 	# output_path = 'data/datasets/encoded/{}{}/{}/{}'.format(encoder, '_without_stop_words' if remove_stop_words else '', dataset.name, encoded_dataset.encoder.model)
		
	# 	encoded_dataset = Bert(source_model=source_model, dataset_name=model,
	# 		ngram_range=(1, 3), min_frequency=min_frequency, lemmatize=lemmatize,
	# 		remove_stop_words=remove_stop_words, oov_handler='avg').encode(dataset)
	# elif encoder == 'fasttext':
	# 	from datasets.encoders import FastText
	# 	encoded_dataset = FastText(remove_stop_words=remove_stop_words).encode(dataset)
	# elif encoder == 'tfidf':
	# 	from datasets.encoders import TFIDF
	# 	encoded_dataset = TFIDF(ngram_range=(1, 3), min_frequency=min_frequency, retrain=False).encode(dataset)
	# elif encoder == 'count':
	# 	from datasets.encoders import Count
	# 	encoded_dataset = Count(ngram_range=(1, 3), min_frequency=min_frequency, retrain=False).encode(dataset)
	# elif encoder == 'lsa':
	# 	from datasets.encoders import LSA
	# 	encoded_dataset = LSA(ngram_range=(1, 3), min_frequency=min_frequency, n_components=100, retrain=False).encode(dataset)
	# elif encoder == 'jaccard_similarity':
	# 	from datasets.encoders import JaccardSimilarity
	# 	encoded_dataset = JaccardSimilarity(lemmatize=lemmatize, remove_stop_words=remove_stop_words).encode(dataset)
	# else:
	# 	raise utils.InvalidNameError('encoder', encoder)

	# output_path = '{}/data/datasets/encoded/{}/{}/{}'.format(os.path.abspath(os.path.dirname(__file__)),
	# 	encoded_dataset.encoder.name, encoded_dataset.encoder.model,
	# 	constants.DATASETS[name]['processed_folder'])

	# utils.save(encoded_dataset, output_path, 'dataset.txt')
	# # utils.save_zip(encoded_dataset, output_path, 'dataset.txt')

	# for question in encoded_dataset.questions:
	# 	dataset = SubDataset(encoded_dataset=encoded_dataset, question=question)
	# 	# labels = np.array([a.get_answer_class('2way', 0.7 if name == 'USCIS' else 0.5, dataset=dataset, question=question) for a in dataset.answers])
	# 	if not name.startswith('SEB'):
	# 		mapping = '2way'
	# 	else:
	# 		if name == 'SEB2':
	# 			mapping = '2way'
	# 		elif name == 'SEB3' and (mapping is None or (mapping not in ['2way', '3way'])):
	# 			mapping = '3way'
	# 		elif name == 'SEB5' and (mapping is None or (mapping not in ['2way', '3way', '5way'])):
	# 			mapping = '5way'
		
	# 	# labels = np.array([a.get_answer_class(mapping, 0.7 if name == 'USCIS' else 0.5, dataset=dataset, question=question) for a in dataset.answers])
	# 	labels = np.array([a.get_answer_class(mapping, scale, dataset=dataset,
	# 		question=question) for a in dataset.answers])
		
	# 	# utils.save(dataset.data, '{}/{}'.format(output_path, question.id), 'data.dat')
	# 	# np.savetxt('{}/{}/labels.txt'.format(output_path, question.id), labels, fmt='%s', delimiter='\n', newline='\n')
	# 	# value = np.array([a.text for a in dataset.answers])
	# 	# np.savetxt('{}/{}/value.txt'.format(output_path, question.id), value, fmt='%s', delimiter='\n', newline='\n')

	# 	if (name == 'SEB3' and mapping != '3way') or (name == 'SEB5' and mapping != '5way'):
	# 		labels_path = '{}/{}/{}'.format(output_path, question.id, mapping)
	# 	else:
	# 		labels_path = '{}/{}'.format(output_path, question.id)

	# 	question_folder_path = '{}/{}'.format(output_path, question.id)
	# 	if not os.path.exists(question_folder_path):
	# 		utils.create_directories(question_folder_path)

	# 	np.save(Path(output_path) / question.id / 'data', dataset.data, allow_pickle=True)
	# 	rows = []
	# 	for i in range(dataset.num_data):
	# 		rows.append([dataset.answers[i].text, labels[i]])
	# 	# utils.write_csv_file('{}/{}'.format(output_path, question.id), 'labels.tsv', rows, delimiter='\t')
	# 	utils.write_csv_file(labels_path, 'labels.tsv', rows, delimiter='\t')

	# 	# save reference answers separately
	# 	np.save(Path(output_path) / question.id / 'reference_answer_data', dataset.reference_answer_data, allow_pickle=True)
	# 	# reference_answer_labels = np.array([a.get_answer_class('2way', 0.7 if name == 'USCIS' else 0.5, dataset=dataset, question=question) for a in dataset.reference_answers])
	# 	# reference_answer_labels = np.array([a.get_answer_class(mapping, 0.7 if name == 'USCIS' else 0.5, dataset=dataset, question=question) for a in dataset.reference_answers])
	# 	reference_answer_labels = np.array([a.get_answer_class(mapping, scale, dataset=dataset,
	# 		question=question) for a in dataset.reference_answers])
	# 	rows = []
	# 	for i in range(len(reference_answer_labels)):
	# 		rows.append([dataset.reference_answers[i].text, reference_answer_labels[i]])
	# 	# utils.write_csv_file('{}/{}'.format(output_path, question.id), 'reference_answer_labels.tsv', rows, delimiter='\t')
	# 	utils.write_csv_file(labels_path, 'reference_answer_labels.tsv', rows, delimiter='\t')

	# end_time = datetime.datetime.now()
	# print('Encoding Finished, time used: {}'.format(end_time - start_time))
