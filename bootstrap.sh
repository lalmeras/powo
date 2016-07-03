#! /bin/bash

this_script=$( realpath "$0" )
this_path=$( dirname "$this_script" )
this_project=$( basename "$this_path" )
VIRTUALENVWRAPPER_PYTHON="/usr/bin/python"
VIRTUALENVWRAPPER_VIRTUALENV="/usr/bin/virtualenv"
VIRTUALENVWRAPPER_VIRTUALENV_CLONE="/usr/bin/virtualenv-clone"


if [ -n "$VIRTUALENVWRAPPER_SCRIPT" ]; then
	. $VIRTUALENVWRAPPER_SCRIPT
	if ! workon "$this_project" &> /dev/null; then
		mkvirtualenv "$python" -a "$this_path" "$this_project"
	fi
	workon "$this_project"
	cdvirtualenv
elif [ ! -d "$this_path/venv" ]; then
	virtualenv "$python" "$this_path/venv"
	cd "$this_project"
fi

pip="./bin/pip"
"$pip" install --upgrade pip
"$pip" install -r "$this_path/requirements_dev.txt"
if [ -f "$this_path/setup.py" ]; then
	"$pip" install -e "$this_path"
fi
