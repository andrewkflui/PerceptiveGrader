import os, shutil, orjson, time, datetime

from typing import Optional, Dict
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request, Depends
from fastapi.responses import ORJSONResponse, FileResponse
from fastapi_pagination import Page, add_pagination, paginate, Params
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
# from starlette.responses import StreamingResponse

from core import utils
from basis.config import ROOT_PATH
from basis.logger import logger

from web.api.project import POSSIBLE_GRADES_OPTIONS, SUBSPACE_OPTION_LIST, ProjectManager, \
	Serializer, ProjectSerializer, GALSerializer, GALSubspaceSerializer

TEMP_PATH = os.path.join(ROOT_PATH, 'web', 'api', 'temp')
PROJECT_DIRCTORY = os.path.join(ROOT_PATH, 'data', 'projects')
FILE_UPLOADS_LOCATION = os.path.join(TEMP_PATH)
if not os.path.exists(FILE_UPLOADS_LOCATION):
	utils.create_directories(str(FILE_UPLOADS_LOCATION))

global project_manager
project_manager = ProjectManager(temp_path=TEMP_PATH)
project_manager.load_saved_project_names(directory=PROJECT_DIRCTORY)

class PageSerializer(Serializer):
	pass

def upload_file(file):
	if file is None:
		return None
	# file_name = datetime.datetime.now().strftime('%Y%m%d%H%m%S')
	file_name = 'temp'
	extension = file.filename.split('.')[-1]
	logger.debug(f'api.upload_file, file_name: {file_name}, extension: {extension}')
	file_name = f'{file_name}.{extension}'
	file_path = os.path.join(FILE_UPLOADS_LOCATION, file_name)
	with open(file_path, 'wb+') as f:
		shutil.copyfileobj(file.file, f)
		logger.info(f'api.upf_file, file {file_name} saved to {file_path}')
	return file_path

def get_project(name):
	project = project_manager.get_project(name)
	if project is None:
		raise HTTPException(status_code=404, detail=f'No project named \'{name}\'')
	return project

# app = FastAPI()
app = FastAPI(default_response_class=ORJSONResponse)
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True,
	allow_headers=['*'], allow_methods=['*'])
app.add_middleware(GZipMiddleware, minimum_size=500)
add_pagination(app)

awaiting_events = []

def add_awaiting_event(event_name, data):
	logger.debug(f'api.add_awaiting_event, {event_name}')
	awaiting_events.append((event_name, data))

@app.get('/')
def root():
	return {'GAL': 'Grading System'}

# @app.get('/stream/')
# async def stream(request: Request):
# 	async def event_generator():
# 		while True:
# 			if len(awaiting_events) > 0:
# 				logger.debug(f'api.stream.event_generator, awaiting_events count: {len(awaiting_events)}')
# 				name, data = awaiting_events.pop(0)
# 				yield str({'event_name': name, 'data': data})
# 				logger.debug(f'api.stream.event_generator, yield: {name}, {data}')
# 			time.sleep(10)
# 	return StreamingResponse(event_generator())
@app.get('/project/options/')
async def get_project_options():
	return {
		'possible_grades_options': orjson.loads(orjson.dumps(POSSIBLE_GRADES_OPTIONS,
			option=orjson.OPT_NON_STR_KEYS)),
		'subspace_option_list': list(SUBSPACE_OPTION_LIST.keys())
	}

@app.post('/project/create/')
async def create_project(file: UploadFile = File(...), name: str = Form(...),
	possible_grades_option: int = Form(...), subspace_param_list_key: str = Form(...)):
	logger.debug(f'api.create_project, {name}, {possible_grades_option}, {subspace_param_list_key}')
	if name in project_manager.projects:
		raise HTTPException(status_code=409, detail='Duplicate project name')
	file_path = upload_file(file)
	data = ProjectSerializer.serialize(project_manager.create_project(name, file_path,
		possible_grades_option, subspace_param_list_key))
	project_manager.save_project(name, os.path.join(PROJECT_DIRCTORY, name))
	return FileResponse(utils.save_json(data, TEMP_PATH, f'{name}.json'))

@app.get('/project/list/')
async def get_project_list():
	return {'project_list': list(project_manager.projects.keys())}

# TO-DO: accept file
@app.post('/project/load/')
async def load_project(name: str, file: Optional[UploadFile] = File(None)):
	data = ProjectSerializer.serialize(project_manager.load_project(os.path.join(PROJECT_DIRCTORY, name)))
	return FileResponse(utils.save_json(data, TEMP_PATH, f'{name}.json'))

@app.post('/project/{name}/save/')
async def save_project(name: str):
	project_manager.save_project(name, os.path.join(PROJECT_DIRCTORY, name))
	return {}

@app.post('/project/{name}/delete')
async def delete_project(name: str):
	project_manager.delete_project(name)
	return {}

# @app.post('/project/{name}/select_answer/')
# async def select_answer(name, index: int):
# 	project = get_project(name)
# 	project.select_answer(index)
# 	return {'selected_answer': project.selectd_answer_index, 'state': project.state, 'saved': project.saved}

@app.get('/project/{name}/algorithm/')
async def get_algorithm(name: str):
	project = get_project(name)
	data = GALSerializer.serialize(project.algorithm)
	return FileResponse(utils.save_json(data, TEMP_PATH, f'{name}_algorithm.json'))

@app.get('/project/{name}/algorithm/subspaces/')
async def get_algorithm_subspaces(name: str, params: Params = Depends()):
	params.size = 1
	project = get_project(name)
	data = [GALSubspaceSerializer.serialize(s) for s in project.algorithm.subspaces]
	# return FileResponse(utils.save_json(data, TEMP_PATH, f'{name}_algorithm_subspaces.json'))
	# data = PageSerializer.serialize(paginate(data, pagination_params))
	data = PageSerializer.serialize(paginate(data, params))
	return FileResponse(utils.save_json(data, TEMP_PATH, f'{name}_algorithm_subspaces_{params.page}.json'))

@app.post('/project/{name}/markup/')
async def answer_markup(name, original_index: int = Form(...), value: int = Form(...)):
	project = get_project(name)
	project.answer_markup(original_index, value)
	# return {'index': original_index, 'markup': project.dataset.answers[original_index].markup}
	return {'index': original_index, 'markup_class': project.dataset.answers[original_index].markup_class}

@app.post('/project/{name}/mark_answers/')
async def mark_answers(name, answer_label_dict: Dict[int, str]):
	# project = project_manager.get_project(name)
	project = get_project(name)
	ordered_answer_list, pgv_values, results = project.run(answer_label_dict)
	return {
		"algorithm": {
			"known_data_labels": orjson.loads(orjson.dumps(
				project.algorithm.known_data_labels, option=orjson.OPT_NON_STR_KEYS)),
			"reduced_known_data_labels": orjson.loads(orjson.dumps(
				project.algorithm.reduced_known_data_labels, option=orjson.OPT_NON_STR_KEYS))
		},
		"ordered_answer_list": ordered_answer_list, "pgv_values": pgv_values, "results": results
	}

@app.post('/project/{name}/algorithm/adjust/')
async def adjust(name, adjust_type: str = Form(...), value: float = Form(...)):
	# project = project_manager.get_project(name)
	project = get_project(name)
	project.adjust_cutoff(adjust_type, value)
	# return ProjectSerializer.serialize(project)
	data = ProjectSerializer.serialize(project)
	return FileResponse(utils.save_json(data, TEMP_PATH, f'{name}.json'))

@app.post('/project/{name}/adddata/')
async def add_data(name, file: UploadFile = File(...)):
	project = project_manager.get_project(name)
	file_path = upload_file(file)
	project.add_data(file_path)
	data = ProjectSerializer.serialize(project)
	return FileResponse(utils.save_json(data, TEMP_PATH, f'{name}.json'))
