#! /bin/bash

FLASK_DEBUG=0

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

# create new user
invenio users create -a admin@rero.ch --password administrator
invenio users create -a librarian@rero.ch --password librarian

# confirm users
invenio users confirm admin@rero.ch
invenio users confirm librarian@rero.ch

# create roles
invenio roles create -d "Admins Group" admins
invenio roles create -d "Super Users Group" superusers
invenio roles create -d "Cataloguer" cataloguer

# grant accesses to action roles
invenio access allow admin-access role admins
invenio access allow superuser-access role superusers

# grant roles to users
invenio roles add admin@rero.ch admins
invenio roles add admin@rero.ch superusers
invenio roles add librarian@rero.ch cataloguer


# create the patron records
dojson -i patrons.json schema http://ils.test.rero.ch/schema/patrons/patron-v0.0.1.json | invenio records create --pid-minter patron_id

invenio index reindex --yes-i-know --pid-type ptrn
invenio index run
#

# create the organisation records
dojson -i organisations.json schema http://ils.test.rero.ch/schema/organisations/organisation-v0.0.1.json | invenio records create --pid-minter organisation_id

invenio index reindex --yes-i-know --pid-type org
invenio index run

# create the bib records
dojson -i documents.json reverse schema http://ils.test.rero.ch/schema/documents/book-v0.0.1.json | invenio records create --pid-minter document_id

invenio index reindex --yes-i-know --pid-type doc
invenio index run

# create items and index bibitems
invenio fixtures createitems -c 10000
