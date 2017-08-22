#! /bin/bash

./install.sh

invenio db init create
invenio index init
invenio index queue init
invenio records create --pid-minter recid  reroils/src/reroils-app/docker/devel/demo.json
invenio index reindex --yes-i-know --pid-type recid
invenio index run

invenio run -h 0.0.0.0