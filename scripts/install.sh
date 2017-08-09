#!/bin/bash

if [ $# -ne 1 ];
    then echo "Usage: install.sh <virtualenv_name>"
    exit
fi

VIRTUALENV_NAME=$1

# Set the python environment
eval "$(pyenv init -)"
pyenv shell 3.5.2
pyenv virtualenvwrapper

# use the virtualenv
workon ${VIRTUALENV_NAME}

# upgrade python installer
pip install --upgrade pip

# go to the instance dir
cdvirtualenv src/reroils-app

# install instance
pip install -e .

# install nodejs dev tools
npm install -g --prefix ${VIRTUAL_ENV} npm
npm install -g --prefix ${VIRTUAL_ENV} node-sass clean-css clean-css-cli requirejs uglify-js

# collect and install nodejs packages
invenio npm
cdvirtualenv var/instance/static
npm install
cd -

# collect static files
invenio collect -v

# build assets to check that everything is ok
invenio assets build

echo "Now try: invenio run"
