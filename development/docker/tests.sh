#! /bin/bash

./install.sh

source reroils/bin/activate
cd /home/invenio/reroils/src/reroils-app
./run-tests.sh
