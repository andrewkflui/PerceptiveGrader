import os, sys
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..{}'.format(os.sep)))

import socket, webbrowser, threading, subprocess, uvicorn, multiprocessing
from http.server import HTTPServer, SimpleHTTPRequestHandler, test

from basis.config import ROOT_PATH
from basis.logger import logger
from web.api.api import app

# CLIENT_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'client')
# CLIENT_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'web', 'client')
CLIENT_PATH = os.path.join(ROOT_PATH, 'web', 'client')

class ProjectHTTPRequestHandler(SimpleHTTPRequestHandler):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, directory=CLIENT_PATH, **kwargs)

	# def send_response(self, *args, **kwargs):
	# 	SimpleHTTPRequestHandler.send_response(self, *args, **kwargs)
	# 	self.send_header('Access-Control-Allow-Origin', '*')

	# def end_headers(self):
	# 	self.send_header('Access-Control-Allow-Origin', '*')
	# 	SimpleHTTPRequestHandler.end_headers(self)

def run_npm(command):
	cmd = f'npm {command}'
	subprocess.check_call(cmd, shell=True)

def get_local_ip_address():
	# ip_address - socket.gethostbyname(socket.gethostname())
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(('8.8.8.8', 1))
	ip_address, _ = s.getsockname()
	s.close()
	return ip_address

def start_api_servere(ip_address, port):
	command = f'uvicorn web.api.api:app --host {ip_address} --port {server_port} --timeout-keep-alive=600'
	if os.name != 'nt':
		command += ' --reload'
	subprocess.Popen(command, shell=True)
	multiprocessing.freeze_support()
	# uvicorn.run('web.api.api:app', host=ip_address, port=server_port, reload=os.name != 'nt')
	# uvicorn.run(app, host=ip_address, port=server_port, reload=os.name != 'nt')

	# try:
	# 	uvicorn.run(app, host=ip_address, port=server_port, reload=False)
	# except Exception as e:
	# 	logger.error(f'Start server Error, {e}')

def start_client_server(ip_address, port):
	logger.info(f'CURRENT_PATH: {os.path.dirname(__file__)}')
	logger.info(f'ROOT_PATH: {ROOT_PATH}')
	logger.info(f'CLIENT_PATH: {CLIENT_PATH}')
	# server = HTTPServer((ip_address, port), SimpleHTTPRequestHandler)
	server = HTTPServer((ip_address, port), ProjectHTTPRequestHandler)
	server.serve_forever()

if __name__ == '__main__':
	# run_npm('--help')
	# subprocess.Popen(["npm.cmd", "install", "open"], shell=True)

	ip_address = get_local_ip_address()
	server_port = 8000
	server_url = f'http://{ip_address}:{server_port}/'

	client_port = 8001
	client_url = f'http://{ip_address}:{client_port}/'

	threading.Thread(target=lambda: start_api_servere(ip_address, server_port), name='api_server_daemon',
		daemon=os.name != 'nt').start()

	if os.name == 'nt':
		chrome_path = 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s'
	else:
		chrome_path = 'open -a /Applications/Google\ Chrome.app %s'
	# if os.name != 'nt':
	# 	threading.Thread(target=lambda: start_client_server(ip_address, client_port), name='client_server',
	# 		daemon=True).start()
	# else:
	# 	start_client_server(ip_address, client_port)
	# start_client_server(ip_address, client_port)
	threading.Thread(target=lambda: start_client_server(ip_address, client_port), name='client_server',
		daemon=os.name == 'nt').start()
	webbrowser.get(chrome_path).open(client_url)
