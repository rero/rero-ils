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
invenio records create --pid-minter recid demo.json
invenio index reindex --yes-i-know --pid-type recid
invenio index run
