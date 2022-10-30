import os, sys
# sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '../../../'))
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..{}..{}..{}'.format(os.sep, os.sep, os.sep)))

import random

from basis import config
from experiments.density_peak.gal.initialization import *

def save_subspaces_batch(name, question_id, subspace_param_list, grading_actions, iterations, class_count,
	args, random_seeds):
	for random_seed in random_seeds:
		iterations = int(grading_actions / batch_size) if batch_size is not None else iterations
		algorithm = save_subspaces(name, question_id, subspace_param_list, grading_actions, iterations,
			class_count, random_seed, args)
		if algorithm is not None:
			print('saved, question_id: {}, version: {}, {}, reduced_num_data: {}, random_seed: {}'.format(
				question_id, algorithm.version, get_subspace_dimension_string(subspace_param_list),
				algorithm.reduced_num_data, random_seed))
		else:
			raise Exception('Subspaces Not Saved!', name, quesiton_id, subspace_param_list, random_seed, args)

if __name__ == '__main__':
	name = 'USCIS'
	question_id = '3'
	encoder = 'google_universal_sentence_encoder'
	mapping = None
	subspace_param_list = [
		{'encoder': 'google_universal_sentence_encoder', 'weight': 0}
	]
	for i in range(16):
		subspace_param_list.append({'encoder': 'google_universal_sentence_encoder',
			'random_dimension': 64, 'random_reference_position': 0, 'id': i+1})
	
	grading_actions = 150
	iterations = None
	batch_size = 10
	class_count = 2

	random_seeds = [0, 49, 97, 53, 5, 33, 65, 62, 51, 100]
	args = {'batch_size': batch_size, 'version': 5, 'distance_function': 'angular',
		'relevant_subspace_number': 0, 'exclusion_rd_deduction_factor': 0.25,
		'grade_assignment_method': 'moc', 'label_search_boundary_factor': 2,
		'voting_version': 'weighted_average'}
	
	# run and evaluate
	algorithm, labels, text_list, reduced_labels, reduced_text_list, result, gp_dict, time_used \
		= evaluate(name, question_id, mapping, subspace_param_list, grading_actions, iterations, class_count,
		random_seed=config.RANDOM_SEED, load_subspaces=True, **args)
	folder_name, _, _ = print_selection_values(name, question_id, algorithm, gp_dict, labels, text_list,
		explicit_list=None, save_mode=2, folder_name=None)
	_, _ = print_wrongly_graded_answers(name, question_id, [algorithm], labels, text_list, [gp_dict], save_mode=1,
		folder_name=folder_name)
	
	# save subspaces  for speeding up
	# save_subspaces_batch(name, question_id, subspace_param_list, grading_actions, iterations, class_count,
	# 	args, random_seeds)
