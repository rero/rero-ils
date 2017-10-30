#! /bin/bash

invenio db destroy --yes-i-know || true
invenio index destroy --force --yes-i-know || true

invenio db init create
invenio index init

# remove useless indexes
invenio index delete --force --yes-i-know marc21-bibliographic-bd-v1.0.0 || true
invenio index delete --force --yes-i-know circulation-item-default-v1.0.0 || true
invenio index delete --force --yes-i-know marc21-authority-ad-v1.0.0 || true
invenio index delete --force --yes-i-know marc21-holdings-hd-v1.0.0 || true

invenio index queue init
#invenio records create --pid-minter recid  reroils/src/reroils-app/development/docker/demo.json
dojson -i reroils/src/reroils-data/data/10k_2017_10_06_complete.json schema http://ils.test.rero.ch/schema/records/record-v0.0.1.json | invenio records create --pid-minter bibid
invenio index reindex --yes-i-know --pid-type recid
invenio index run

# circulation
invenio fixtures createitems
