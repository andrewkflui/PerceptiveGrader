import os, sys, csv, pickle, argparse
from pathlib import Path
from enum import Enum

import xlrd, docx2txt
from xml.etree import ElementTree

from basis import config, constants
from basis.logger import logger
from core import utils
from datasets import datasets

def process_dataset(name=None, root=None, file_path=None, save=True):
	processed_folder = Path(config.ROOT_PATH) / 'data' / 'datasets' / 'processed'
	if name is not None:
		utils.validate_option(constants.DATASETS.keys(), name, 'dataset')
		root_path = root / constants.DATASETS[name]['source_folder']
		processed_folder /= constants.DATASETS[name]['processed_folder']
	else:
		root_path = file_path

	if name == 'SEB2':
		dataset = datasets.SciEntsBank2013Task7('2', '2way', score_classes=['incorrect', 'correct'], root_path=root_path)
	elif name == 'SEB3':
		dataset = datasets.SciEntsBank2013Task7('3', '3way', score_classes=['incorrect', 'contradictory', 'correct'], root_path=root_path)
	elif name == 'SEB5':
		dataset = datasets.SciEntsBank2013Task7('5', 'Core', score_classes=['non_domain', 'irrelevant', 'contradictory', 'partially_correct_incomplete', 'correct'], root_path=root_path)
	elif name == 'USCIS':
		dataset = datasets.USCIS(root_path=root_path)
	elif name == 'USCIS':
		dataset = datasets.USCIS(root_path=root_path, include_100=True)
	# elif name == 'Mobley':
	# 	dataset = datasets.Mobley(root_path=root_path)
	elif name == 'UNT':
		dataset = datasets.UNTComputerScienceShortAnswerDataset(root_path=root_path)
	elif name == 'CAK':
		dataset = datasets.ChakrabortyAndKonar(root_path=root_path)
	elif name == 'ASAPAES':
		dataset = datasets.ASAPAES(root_path=root_path)
	elif name == 'ASAPSAS':
		dataset = datasets.ASAPSAS(root_path=root_path)
	else:
		dataset = datasets.Dataset(path=root_path)
		name = dataset.name
		processed_folder /= name.lower()
	
	if save:
		utils.save(dataset, processed_folder, 'data.txt')
		logger.info('Dataset processed, saved to', str(processed_folder))
		
		for question in dataset.questions:
			path = processed_folder / question.id
			utils.save(dataset.create_question_dataset(question.id), path, 'data.txt')
			logger.info('Dataset processed, Question \'{}\' saved to {}'.format(question.id, str(path)))
	logger.info(dataset)
	return dataset

if __name__ == '__main__':
	parser = argparse.ArgumentParser()

	parser.add_argument('--root', help='datasets folder', default=str(Path(config.ROOT_PATH) \
		/ 'data' / 'datasets' / 'raw'))
	parser.add_argument('--name', help='dataset name, preset options={}'.format([key for key in constants.DATASETS.keys()]), required=False)
	parser.add_argument('--path', help='dataset file (excel) path, must be provided if not using presets', required=False)
	
	args = parser.parse_args()
	_ = process_dataset(args.name, Path(args.root), args.path, save=True)

	# root = Path(args.root)
	# name = args.name
	# path = args.path

	# processed_folder = Path(config.ROOT_PATH) / 'data/datasets/processed'
	# if args.path is None:
	# 	utils.validate_option(constants.DATASETS.keys(), name, 'dataset')
	# 	root_path = root / constants.DATASETS[name]['source_folder']
	# 	processed_folder /= constants.DATASETS[name]['processed_folder']
	# else:
	# 	root_path = path
	# 	processed_folder /= name.lower()

	# if name == 'SEB2':
	# 	dataset = datasets.SciEntsBank2013Task7('2', '2way', score_classes=['incorrect', 'correct'], root_path=root_path)
	# elif name == 'SEB3':
	# 	dataset = datasets.SciEntsBank2013Task7('3', '3way', score_classes=['incorrect', 'contradictory', 'correct'], root_path=root_path)
	# elif name == 'SEB5':
	# 	dataset = datasets.SciEntsBank2013Task7('5', 'Core', score_classes=['non_domain', 'irrelevant', 'contradictory', 'partially_correct_incomplete', 'correct'], root_path=root_path)
	# elif name == 'USCIS':
	# 	dataset = datasets.USCIS(root_path=root_path)
	# elif name == 'USCIS':
	# 	dataset = datasets.USCIS(root_path=root_path, include_100=True)
	# elif name == 'Mobley':
	# 	dataset = datasets.Mobley(root_path=root_path)
	# elif name == 'CAK':
	# 	dataset = datasets.ChakrabortyAndKonar(root_path=root_path)
	# elif name == 'ASAP':
	# 	dataset = datasets.ASAP(root_path=root_path)

	# utils.save(dataset, '{}/data/datasets/processed/{}'.format(config.ROOT_PATH,
	# 	constants.DATASETS[name]['processed_folder']), 'data.txt')
	# utils.save(dataset, processed_folder, 'data.txt')
	# print('Dataset processed, saved to', str(processed_folder))
	# print(dataset)
