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

import pytest
from utils import flush_index

from rero_ils.modules.documents.api import Document, DocumentsSearch


@pytest.fixture(scope='module')
def create_app():
    """Create test app."""
    from invenio_app.factory import create_api

    return create_api


@pytest.fixture(scope='module')
def doc_title_travailleurs(app):
    """Document with title with travailleur."""
    data = {
        '$schema': 'https://ils.rero.ch/schemas/documents/'
                   'document-v0.0.1.json',
        'pid': 'doc_title_test1', 'type': 'book',
        'language': [{'type': 'bf:Language', 'value': 'fre'}],
        'title': [{
            'type': 'bf:Title',
            'mainTitle': [{
                'value': 'Les travailleurs assidus sont de retours'
            }],
            'subtitle': [{'value': 'les jeunes arrivent bientôt ?'}]
        }],
        'issuance': {
            'main_type': 'rdami:1001',
            'subtype': 'materialUnit'
        }
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
        '$schema': 'https://ils.rero.ch/schemas/documents/'
                   'document-v0.0.1.json',
        'pid': 'doc_title_test2', 'type': 'book',
        'language': [{'type': 'bf:Language', 'value': 'fre'}],
        'title': [{
            'type': 'bf:Title',
            'mainTitle': [{
                'value': "Les travailleuses partent à l'école"
            }],
            'subtitle': [{'value': "lorsqu'un est bœuf ex aequo"}]

        }],
        'authors': [{
            'name': 'Müller, John', 'type': 'person'
        }, {
            'name': 'Corminbœuf, Gruß', 'type': 'person'
        }],
        'issuance': {
            'main_type': 'rdami:1001',
            'subtype': 'materialUnit'
        }
    }
    doc = Document.create(
        data=data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(DocumentsSearch.Meta.index)
    return doc
