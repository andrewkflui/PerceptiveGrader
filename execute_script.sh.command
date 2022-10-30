#!/bin/bash
echo_requirement_satisfied(){
	echo "$1 requirement satisfied"
}

get_platform_name(){
	if [[ "$OSTYPE" == "msys" ]]; then
		PLATFORM="windows"
	elif [[ "$OSTYPE" == "darwin"* ]]; then
		PLATFORM="mac"
	fi
}

get_processor_name(){
	PROCESSOR=$(command uname -p)
}

check_python_37(){
	PYPATH=$(command -v python)
	# PYVERSION=$(python --version)
	# if [[ ${PYPATH,,} == *"python37"* ]]; then
	# 	echo_requirement_satisfied "Python 3.7"
	# elif [[ $1 == "windows" ]]; then
	# 	echo "Please download and install Python 3.7.3 from the https://www.python.org/downloads/release/python-373/"
	# 	exit 1
	# else
	# 	echo "Mac, Install Python 3.7"
	# fi

	if [[ $1 == "windows" && ${PYPATH,,} != *"python37"* ]]; then
		echo "Please download and install Python 3.7.3 from the https://www.python.org/downloads/release/python-373/"
		exit 1
	elif [[ ! -f "/usr/local/bin/python3.7" ]]; then
		brew install python@3.7
	elif [[ $1 == "mac" ]]; then
		PYPATH="/usr/local/bin/python3.7"
	fi
}

install_virtualenv(){
	if [[ $1 != "arm" ]]; then
		if [[ ! $(command -v virtualenv) ]]; then
			echo "Install virtualenv..."
			command python -m pip install virtualenv
		else
			echo_requirement_satisfied "virtualenv"
		fi
	elif [[ ! $(command conda) ]]; then
		echo "[ERROR] Conda not found. Please download and install Conda first."
		exit 1
	else
		echo_requirement_satisfied "conda"
	fi
}

create_virtualenv(){
	if [ ! -d "VE" ]; then
		echo "Create VE..."
		if [[ $1 != "arm" ]]; then
			if [[ $PLATFORM == "windows" ]]; then
				virtualenv VE -p "$PYPATH.exe"
			else
				virtualenv VE -p $PYPATH
			fi
		else
			conda env create -p "./VE" -f "VE_M1.yml"
		fi
	else
		echo_requirement_satisfied "VE"
	fi
}

activate_virtualenv(){
	if [[ $1 != "arm" ]]; then
		if [[ $PLATFORM == "windows" ]]; then
			source VE/Scripts/activate
		else
			source VE/bin/activate
		fi

		if [[ "$(type -t deactivate)" != function ]]; then
			echo "Cannot activate virtualenv! Exit"
			exit 1
		elif [[ $PLATFORM == "windows" ]]; then
			pip install -r requirements_windows.txt --no-deps
		else
			echo "Install Packages"
			pip install -r requirements_tf2.txt
		fi
	else
		eval "$(conda shell.bash hook)"
		conda activate ./VE
	fi
}

run(){
	python web/executor.py
}

PLATFORM="Unknown"
get_platform_name
if [[ $PLATFORM == "mac" ]]; then
	cd "$(dirname "$BASH_SOURCE")"
fi
PROCESSOR="Unknown"
get_processor_name
if [[ $PROCESSOR != "arm" ]]; then
	check_python_37 $PLATFORM
fi
install_virtualenv $PROCESSOR
create_virtualenv $PROCESSOR
activate_virtualenv $PROCESSOR
run

# python -c "import sys; print('\n'.join(sys.path))"
# python -m pip install virtualenv
# if [[ "$OSTYPE" == "msys" ]]; then

# else if [[ "$OSTYPE" == "darwin"* ]]; then
# 	virtualenv VE -p /usr/local/bin/python3.7
# 	source VE/bin/activate
# 	pip install -r requirements_tf2.txt
# fi