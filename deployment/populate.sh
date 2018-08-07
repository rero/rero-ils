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

# confirm users
invenio users confirm admin@rero.ch

# create roles
invenio roles create -d "Admins Group" admins
invenio roles create -d "Super Users Group" superusers
invenio roles create -d "Cataloguer" cataloguer

# create a role for users qualified as a patron
invenio roles create -d "Patron" patrons

# create a role for users qualified as a staff member
invenio roles create -d "Staff" staff

# grant accesses to action roles
invenio access allow admin-access role admins
invenio access allow superuser-access role superusers

# grant roles to users
invenio roles add admin@rero.ch admins
invenio roles add admin@rero.ch superusers

# create the patron records
invenio fixtures importusers users.json -v

# create the organisations with members and locations
invenio fixtures importorganisations organisations-members-locations.json

# create the bib records
dojson -i documents.json reverse schema http://ils.test.rero.ch/schema/documents/document-v0.0.1.json | invenio records create --pid-minter document_id
invenio index reindex --yes-i-know --pid-type doc
invenio index run -c 4

# create items
invenio fixtures createitems -R

# create circulation transactions
invenio fixtures createcirctransactions circulation_transactions.json 
