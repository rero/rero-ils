# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 RERO.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Pytest configuration."""

from __future__ import absolute_import, print_function

import os
import shutil
import tempfile

import pytest
from flask import Flask
from flask_babelex import Babel
from flask_menu import Menu
from flask_security.utils import hash_password
from invenio_access import InvenioAccess
from invenio_accounts import InvenioAccounts
from invenio_db import InvenioDB
from invenio_jsonschemas import InvenioJSONSchemas
from invenio_pidstore import InvenioPIDStore
from invenio_records import InvenioRecords
from invenio_records_ui import InvenioRecordsUI
from sqlalchemy_utils.functions import create_database, database_exists
from werkzeug.local import LocalProxy

from reroils_app.modules.documents_items.api import DocumentsWithItems
from reroils_app.modules.ext import REROILSDATA
from reroils_app.modules.items.api import Item
from reroils_app.modules.items.views import blueprint as item_blueprint
from reroils_app.modules.locations.api import Location
from reroils_app.modules.members_locations.api import MemberWithLocations

# TODO: get url dynamiclly
url_schema = 'http://ils.test.rero.ch/schema'


@pytest.yield_fixture()
def minimal_patron_record():
    """Simple patron record."""
    yield {
        '$schema': url_schema + '/patrons/patron-v0.0.1.json',
        'pid': '1',
        'first_name': 'Simonetta',
        'last_name': 'Casalini',
        'street': 'Avenue Leopold-Robert, 132',
        'postal_code': '2300',
        'city': 'La Chaux-de-Fonds',
        'barcode': '2050124311',
        'birth_date': '1967-06-07',
        'member_pid': '1',
        'email': 'simolibri07@gmail.com',
        'phone': '+41324993585',
        'patron_type': 'standard_user'
    }


@pytest.yield_fixture()
def minimal_patron_only_record():
    """Simple patron record."""
    yield {
        '$schema': 'http://ils.test.rero.ch/schema/patrons/patron-v0.0.1.json',
        'pid': '2',
        'first_name': 'Simonetta',
        'last_name': 'Casalini',
        'street': 'Avenue Leopold-Robert, 132',
        'postal_code': '2300',
        'city': 'La Chaux-de-Fonds',
        'barcode': '2050124311',
        'birth_date': '1967-06-07',
        'email': 'simolibri07@gmail.com',
        'phone': '+41324993585',
        'patron_type': 'standard_user',
        'is_staff': False,
        'is_patron': True
    }


@pytest.yield_fixture()
def minimal_staff_only_record():
    """Simple patron record."""
    yield {
        '$schema': 'http://ils.test.rero.ch/schema/patrons/patron-v0.0.1.json',
        'pid': '3',
        'first_name': 'Simonetta',
        'last_name': 'Casalini',
        'street': 'Avenue Leopold-Robert, 132',
        'postal_code': '2300',
        'city': 'La Chaux-de-Fonds',
        'birth_date': '1967-06-07',
        'email': 'simolibri07@gmail.com',
        'phone': '+41324993585',
        'member_pid': '1',
        'is_staff': True,
        'is_patron': False
    }


@pytest.yield_fixture()
def minimal_staff_patron_record():
    """Simple patron record."""
    yield {
        '$schema': 'http://ils.test.rero.ch/schema/patrons/patron-v0.0.1.json',
        'pid': '3',
        'first_name': 'Simonetta',
        'last_name': 'Casalini',
        'street': 'Avenue Leopold-Robert, 132',
        'barcode': '2050124311',
        'postal_code': '2300',
        'city': 'La Chaux-de-Fonds',
        'birth_date': '1967-06-07',
        'birth_date': '1967-06-07',
        'email': 'simolibri07@gmail.com',
        'phone': '+41324993585',
        'patron_type': 'standard_user',
        'is_staff': True,
        'is_patron': True
    }


@pytest.yield_fixture()
def minimal_document_record():
    """Minimal document."""
    yield {
        '$schema': url_schema + '/documents/document-v0.0.1.json',
        'pid': '2',
        'title': 'RERO21 pour les nuls : les premiers pas',
        'type': 'book',
        'languages': [{'language': 'fre'}],
    }


@pytest.yield_fixture()
def minimal_item_record():
    """Simple item record."""
    yield {
        '$schema': url_schema + '/items/item-v0.0.1.json',
        'pid': '1',
        'barcode': '10000000000',
        'call_number': 'PA-41234',
        'location_pid': '1',
        'item_type': 'standard_loan',
        '_circulation': {
            'holdings': [{
                'patron_barcode': '123456',
                'start_date': '2018-01-01',
                'end_date': '2018-02-01',
                'renewal_count': 0
            }, {
                'patron_barcode': '654321',
                'start_date': '2018-10-10',
                'end_date': '2018-11-10',
                'pickup_member_pid': '1'
            }],
            'status': 'on_loan'
        }
    }


@pytest.yield_fixture()
def item_record_on_shelf():
    """Simple item record with no transactions."""
    yield {
        '$schema': url_schema + '/items/item-v0.0.1.json',
        'pid': '1',
        'barcode': '10000000000',
        'call_number': 'PA-41234',
        'location_pid': '1',
        'item_type': 'standard_loan',
        '_circulation': {
            'holdings': [],
            'status': 'on_shelf'
        }
    }


@pytest.yield_fixture()
def item_record_in_transit():
    """Simple item record with no transactions."""
    yield {
        '$schema': url_schema + '/items/item-v0.0.1.json',
        'pid': '1',
        'barcode': '10000000000',
        'call_number': 'PA-41234',
        'location_pid': '1',
        'item_type': 'standard_loan',
        '_circulation': {
            'holdings': [],
            'status': 'in_transit'
        }
    }


@pytest.yield_fixture()
def item_record_on_shelf_requested():
    """Simple item record with no transactions."""
    yield {
        '$schema': url_schema + '/items/item-v0.0.1.json',
        'pid': '1',
        'barcode': '10000000000',
        'call_number': 'PA-41234',
        'location_pid': '1',
        'item_type': 'standard_loan',
        '_circulation': {
            'holdings': [{
                'patron_barcode': '654321',
                'start_date': '2018-10-10',
                'end_date': '2018-11-10',
                'pickup_member_pid': '1'
            }],
            'status': 'on_shelf'
        }
    }


@pytest.yield_fixture()
def item_record_on_loan():
    """Simple item record."""
    yield {
        '$schema': url_schema + '/items/item-v0.0.1.json',
        'pid': '1',
        'barcode': '10000000000',
        'call_number': 'PA-41234',
        'location_pid': '1',
        'item_type': 'standard_loan',
        '_circulation': {
            'holdings': [{
                'patron_barcode': '123456',
                'start_date': '2018-01-01',
                'end_date': '2018-02-01',
                'renewal_count': 0
            }],
            'status': 'on_loan'
        }
    }


@pytest.yield_fixture()
def minimal_organisation_record():
    """Simple organisation record."""
    yield {
        '$schema': url_schema + '/organisations/organisation-v0.0.1.json',
        'pid': '1',
        'name': 'MV Sion',
        'address': 'address'
    }


@pytest.yield_fixture()
def minimal_member_record():
    """Simple member record."""
    yield {
        '$schema': url_schema + '/members/member-v0.0.1.json',
        'pid': '1',
        'code': 'vsmvvs',
        'name': 'MV Sion',
        'address': 'Rue Pratifori',
        'email': 'info@mv.ch'
    }


@pytest.yield_fixture()
def minimal_location_record():
    """Simple location record."""
    yield {
        '$schema': url_schema + '/locations/location-v0.0.1.json',
        'pid': '1',
        'code': 'net-store-base',
        'name': 'Store Base',
    }


@pytest.yield_fixture()
def create_minimal_resources(db, minimal_member_record,
                             minimal_location_record, minimal_item_record,
                             minimal_document_record):
    """Simple patron record."""
    member = MemberWithLocations.create(minimal_member_record, dbcommit=True)
    location = Location.create(minimal_location_record, dbcommit=True)
    member.add_location(location)
    doc = DocumentsWithItems.create(minimal_document_record, dbcommit=True)
    item = Item.create({})
    item.update(minimal_item_record, dbcommit=True)
    doc.add_item(item, dbcommit=True)
    db.session.commit()
    yield doc, item, member, location


@pytest.yield_fixture()
def create_minimal_resources_on_shelf(db, minimal_member_record,
                                      minimal_location_record,
                                      item_record_on_shelf,
                                      minimal_document_record):
    """Simple patron record."""
    member = MemberWithLocations.create(minimal_member_record, dbcommit=True)
    location = Location.create(minimal_location_record, dbcommit=True)
    member.add_location(location)
    doc = DocumentsWithItems.create(minimal_document_record, dbcommit=True)
    item = Item.create({})
    item.update(item_record_on_shelf, dbcommit=True)
    doc.add_item(item, dbcommit=True)
    db.session.commit()
    yield doc, item, member, location


@pytest.yield_fixture()
def create_minimal_resources_on_shelf_req(db, minimal_member_record,
                                          minimal_location_record,
                                          item_record_on_shelf_requested,
                                          minimal_document_record):
    """Simple patron record."""
    member = MemberWithLocations.create(minimal_member_record, dbcommit=True)
    location = Location.create(minimal_location_record, dbcommit=True)
    member.add_location(location)
    doc = DocumentsWithItems.create(minimal_document_record, dbcommit=True)
    item = Item.create({})
    item.update(item_record_on_shelf_requested, dbcommit=True)
    doc.add_item(item, dbcommit=True)
    db.session.commit()
    yield doc, item, member, location


@pytest.yield_fixture()
def create_minimal_resources_in_transit(db, minimal_member_record,
                                        minimal_location_record,
                                        item_record_in_transit,
                                        minimal_document_record):
    """Simple patron record."""
    member = MemberWithLocations.create(minimal_member_record, dbcommit=True)
    location = Location.create(minimal_location_record, dbcommit=True)
    member.add_location(location)
    doc = DocumentsWithItems.create(minimal_document_record, dbcommit=True)
    item = Item.create({})
    item.update(item_record_in_transit, dbcommit=True)
    doc.add_item(item, dbcommit=True)
    db.session.commit()
    yield doc, item, member, location


@pytest.yield_fixture()
def create_minimal_resources_on_loan(db, minimal_member_record,
                                     minimal_location_record,
                                     item_record_on_loan,
                                     minimal_document_record):
    """Simple patron record."""
    member = MemberWithLocations.create(minimal_member_record, dbcommit=True)
    location = Location.create(minimal_location_record, dbcommit=True)
    member.add_location(location)
    doc = DocumentsWithItems.create(minimal_document_record, dbcommit=True)
    item = Item.create({})
    item.update(item_record_on_loan, dbcommit=True)
    doc.add_item(item, dbcommit=True)
    db.session.commit()
    yield doc, item, member, location


@pytest.yield_fixture()
def instance_path():
    """Temporary instance path."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


@pytest.yield_fixture()
def http_client(app):
    """Client to perform GET, POST, etc. in the current app."""
    with app.test_client() as client:
        yield client


@pytest.yield_fixture()
def app(request):
    """Flask application fixture."""
    # Set temporary instance path for sqlite
    instance_path = tempfile.mkdtemp()
    app = Flask('testapp', instance_path=instance_path)

    app.config.update(
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'
        ),
        TESTING=True,
        SECRET_KEY='SECRET_KEY',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JSONSCHEMAS_ENDPOINT='/schema',
        JSONSCHEMAS_HOST='ils.test.rero.ch',
        RECORDS_UI_ENDPOINTS={
            "doc": {
                "pid_type": "doc",
                "route": "/documents/<pid_value>",
                "template": "reroils_app/detailed_view_documents_items.html"
            }
        }
    )

    InvenioDB(app)
    InvenioPIDStore(app)
    InvenioRecords(app)
    InvenioAccounts(app)
    REROILSDATA(app)
    InvenioAccess(app)
    InvenioJSONSchemas(app)
    InvenioRecordsUI(app)
    Menu(app)
    Babel(app)
    app.register_blueprint(item_blueprint)

    @app.route('/test/login')
    def login():
        from flask_security import login_user
        from flask import request as flask_request

        role = flask_request.args.get('role')
        if role:
            datastore.create_role(name=role)
            datastore.add_role_to_user(user, role)
        datastore.commit()
        login_user(user)
        return "Logged In"

    @app.route('/test/login')
    def logout():
        from flask_security import logout_user
        logout_user()
        return "Logged Out"

    from invenio_db import db as db_
    with app.app_context():
        if not database_exists(str(db_.engine.url)):
            create_database(str(db_.engine.url))
        db_.create_all()
        security = LocalProxy(lambda: app.extensions['security'])
        datastore = LocalProxy(lambda: security.datastore)
        user = datastore.create_user(
            email='test@rero.ch',
            active=True,
            password=hash_password('aafaf4as5fa')
        )
        yield app

        # Teardown instance path.
        db_.session.remove()
        db_.drop_all()
        shutil.rmtree(instance_path)


@pytest.yield_fixture()
def db(app):
    """Database fixture."""
    from invenio_db import db as db_
    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()

    yield db_

    db_.session.remove()
    db_.drop_all()
