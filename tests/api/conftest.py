# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Pytest fixtures and plugins for the API application."""

from __future__ import absolute_import, print_function

from copy import deepcopy
from datetime import datetime

import pytest
from flask_security.utils import hash_password
from invenio_accounts.models import User
from utils import flush_index

from rero_ils.modules.documents.api import Document, DocumentsSearch
from rero_ils.modules.documents.models import DocumentFictionType
from rero_ils.modules.items.api import Item, ItemsSearch


@pytest.fixture(scope='function')
def user_without_profile(db, default_user_password):
    """Create a simple invenio user with a profile."""
    with db.session.begin_nested():
        user = User(
            email='user_without_profile@test.com',
            password=hash_password(default_user_password),
            user_profile=None,
            active=True,
        )
        db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture(scope='function')
def user_with_profile(db, default_user_password):
    """Create a simple invenio user with a profile."""
    with db.session.begin_nested():
        user = User(
            email='user_with_profile@test.com',
            password=hash_password(default_user_password),
            user_profile={},
            active=True,
        )
        db.session.add(user)
        profile = dict(
            birth_date=datetime(1990, 1, 1),
            first_name='User',
            last_name='With Profile',
            city='Nowhere'
        )
        profile.username = 'user_with_profile'
        user.user_profile = profile
        db.session.merge(user)
    db.session.commit()
    return user


@pytest.fixture(scope='module')
def create_app():
    """Create test app."""
    from invenio_app.factory import create_api

    return create_api


@pytest.fixture(scope='module')
def doc_title_travailleurs(app):
    """Document with title with travailleur."""
    data = {
        '$schema': 'https://bib.rero.ch/schemas/documents/'
                   'document-v0.0.1.json',
        'pid': 'doc_title_test1',
        'type': [{
            "main_type": "docmaintype_book",
            "subtype": "docsubtype_other_book"
        }],
        'fiction_statement': DocumentFictionType.Unspecified.value,
        'language': [{'type': 'bf:Language', 'value': 'fre'}],
        'title': [{
            'type': 'bf:Title',
            'mainTitle': [{
                'value': 'Les travailleurs assidus sont de retours'
            }],
            'subtitle': [
                {'value': 'les jeunes arrivent bientôt ? Quelle histoire!'}]
        }],
        "provisionActivity": [
          {
            "type": "bf:Publication",
            "startDate": 1818
          }
        ],
        'issuance': {
            'main_type': 'rdami:1001',
            'subtype': 'materialUnit'
        },
        'adminMetadata': {
            'encodingLevel': 'Minimal level'
        },
        "seriesStatement": [{
            "seriesTitle": [
                {
                    "value": "Boy & Girl"
                }
            ]
        }],
    }
    doc = Document.create(
        data=data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(DocumentsSearch.Meta.index)
    return doc


@pytest.fixture(scope='module')
def doc_title_travailleuses(app):
    """Document with title with travailleuses."""
    data = {
        '$schema': 'https://bib.rero.ch/schemas/documents/'
                   'document-v0.0.1.json',
        'pid': 'doc_title_test2',
        'type': [{
            "main_type": "docmaintype_book",
            "subtype": "docsubtype_other_book"
        }],
        'fiction_statement': DocumentFictionType.Unspecified.value,
        'language': [{'type': 'bf:Language', 'value': 'fre'}],
        'title': [{
            'type': 'bf:Title',
            'mainTitle': [{
                'value': "Les travailleuses partent à l'école 100"
            }],
            'subtitle': [{'value': "lorsqu'un est bœuf ex aequo"}]

        }],
        'contribution': [
            {
                'entity': {
                    'authorized_access_point': 'Müller, John',
                    'type': 'bf:Person'
                },
                'role': ['aut']
            },
            {
                'entity': {
                    'authorized_access_point': 'Corminbœuf, Gruß',
                    'type': 'bf:Person'
                },
                'role': ['aut']
            }
        ],
        "provisionActivity": [
            {
                "type": "bf:Publication",
                "startDate": 1818
            }
        ],
        'issuance': {
            'main_type': 'rdami:1001',
            'subtype': 'materialUnit'
        },
        'adminMetadata': {
            'encodingLevel': 'Minimal level'
        }
    }
    doc = Document.create(
        data=data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(DocumentsSearch.Meta.index)
    return doc


@pytest.fixture(scope="function")
def item_lib_martigny_masked(
        app,
        document,
        item_lib_martigny_data,
        loc_public_martigny,
        item_type_standard_martigny):
    """Create item of martigny library."""
    data = deepcopy(item_lib_martigny_data)
    data['barcode'] = 'masked'
    data['pid'] = f'maked-{data["pid"]}'
    data['_masked'] = True
    item = Item.create(
        data=data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(ItemsSearch.Meta.index)
    yield item
    item.delete(True, True, True)
