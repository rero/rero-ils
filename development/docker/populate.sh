#! /bin/bash

invenio db init create
invenio index init
invenio index queue init
invenio records create --pid-minter recid  reroils/src/reroils-app/development/docker/demo.json
invenio index reindex --yes-i-know --pid-type recid
invenio index run
