#! /bin/bash
#
# populate.sh
# Copyright (C) 2017 maj <maj@meleze>
#
# Distributed under terms of the MIT license.
#
invenio db destroy --yes-i-know || true
invenio index destroy --force --yes-i-know || true
invenio index delete records-record-v1.0.0 --yes-i-know || true

invenio db init create
invenio index init

# remove useless indexes
invenio index delete --force --yes-i-know marc21-bibliographic-bd-v1.0.0 || true
invenio index delete --force --yes-i-know circulation-item-default-v1.0.0 || true
invenio index delete --force --yes-i-know marc21-authority-ad-v1.0.0 || true
invenio index delete --force --yes-i-know marc21-holdings-hd-v1.0.0 || true

invenio index queue init
dojson -i demo.json schema http://ils.test.rero.ch/schema/records/record-v0.0.1.json | invenio records create --pid-minter bibid
# invenio index reindex --yes-i-know --pid-type recid
# invenio index run

# create items and index bibitems
invenio fixtures createitems -v
