#! /bin/bash
#
# populate.sh
# Copyright (C) 2017 maj <maj@meleze>
#
# Distributed under terms of the MIT license.
#
invenio db destroy --yes-i-know || true
invenio index destroy --yes-i-know || true
invenio index delete records-record-v1.0.0 --yes-i-know || true
invenio db init create
invenio index init
invenio index queue init
dojson -i demo.json schema http://ils.test.rero.ch/schema/records/record-v0.0.1.json | invenio records create --pid-minter bibid
invenio index reindex --yes-i-know --pid-type recid
invenio index run
