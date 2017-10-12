#! /bin/bash

invenio db destroy --yes-i-know || true
invenio index destroy --yes-i-know || true
invenio db init create
invenio index init
invenio index queue init
#invenio records create --pid-minter recid  reroils/src/reroils-app/development/docker/demo.json
dojson -i reroils/src/reroils-data/data/10k_2017_10_06_complete.json schema http://ils.test.rero.ch/schema/records/record-v0.0.1.json | invenio records create --pid-minter bibid
invenio index reindex --yes-i-know --pid-type recid
invenio index run
