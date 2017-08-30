#! /bin/bash

./install.sh

source reroils/bin/activate

invenio run -h 0.0.0.0
