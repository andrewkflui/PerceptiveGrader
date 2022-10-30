import os, sys
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..{}'.format(os.sep)))

from pathlib import Path
from basis import config
from core import utils

def load_processed_dataset(name, question_ids, output_name):
	headers = 'Question ID,Question Text,Answer ID,Answer Text,Is Reference'.split(',')
	dataset_path = Path(config.ROOT_PATH) / 'data' / 'datasets' / 'processed' / name
	output_path = Path(config.ROOT_PATH) / 'data' / 'datasets' / 'raw' / output_name

	for question_id in question_ids:
		dataset = utils.load(dataset_path / question_id / 'data.txt')
		filename = f'{output_name}_{question_id}.csv'

		rows = [headers]
		for answer in dataset.questions[0].answers:
			rows += [[f'{output_name}:{question_id}', dataset.questions[0].text.strip(), answer.id,
				answer.text.strip(), answer.is_reference]]
		utils.write_csv_file(output_path, filename, rows, delimiter=',')

if __name__ == '__main__':
	# question_ids = ['DAMAGED_BULB_SWITCH_Q', 'DESCRIBE_GAP_LOCATE_PROCEDURE_Q', 'EV_12b', 'EV_25',
	# 	'HB_24b1', 'HB_35', 'HYBRID_BURNED_OUT_EXPLAIN_Q2', 'WA_52b']
	# load_processed_dataset('SEB2', question_ids, 'seb2custom')

	# load_processed_dataset('USCIS', [str(i) for i in range(1, 9)], 'usciscustom')
	load_processed_dataset('ASAPSAS', [str(i) for i in range(1, 11)], 'asapsascustom')