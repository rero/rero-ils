# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
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

"""DOJSON transformation for Dublin Core module tests."""

from __future__ import absolute_import, print_function

from copy import deepcopy

import mock
from utils import mock_response

from rero_ils.modules.documents.api import Document, DocumentsSearch
from rero_ils.modules.documents.tasks import replace_idby_contribution, \
    replace_idby_subjects
from rero_ils.modules.documents.utils_mef import \
    ReplaceMefIdentifiedByContribution, ReplaceMefIdentifiedBySubjects
from rero_ils.modules.entities.api import Entity


@mock.patch('requests.get')
def test_replace_idby_contribution(mock_contributions_mef_get, app,
                                   document_data,
                                   entity_person_response_data):
    """Test replace identifiedBy in contribution."""
    assert replace_idby_contribution() == (0, 0, 0, 0, 0)

    doc = Document.create(data=document_data, dbcommit=True, reindex=True)
    DocumentsSearch.flush_and_refresh()
    mock_contributions_mef_get.return_value = mock_response(
        status=500
    )
    replace = ReplaceMefIdentifiedByContribution()
    replace.process()
    assert replace.counts_len == (0, 0, 0, 0, 1)

    without_idref_gnd = deepcopy(entity_person_response_data)
    without_idref_gnd['hits']['hits'][0]['metadata'].pop('idref')
    without_idref_gnd['hits']['hits'][0]['metadata'].pop('gnd')
    mock_contributions_mef_get.return_value = mock_response(
        json_data=without_idref_gnd
    )
    assert replace_idby_contribution() == (0, 0, 0, 1, 0)

    without_idref_gnd = deepcopy(entity_person_response_data)
    without_idref_gnd['hits']['hits'][0]['metadata']['deleted'] = '2022'
    mock_contributions_mef_get.return_value = mock_response(
        json_data=without_idref_gnd
    )
    assert replace_idby_contribution() == (0, 0, 1, 0, 0)

    mock_contributions_mef_get.return_value = mock_response(
        json_data=entity_person_response_data
    )
    assert replace_idby_contribution() == (1, 0, 0, 0, 0)

    # clean up
    doc.delete(dbcommit=True, delindex=True, force=True)
    for id in Entity.get_all_ids():
        cont = Entity.get_record(id)
        cont.delete(dbcommit=True, delindex=True, force=True)


@mock.patch('requests.get')
def test_replace_idby_subjects(mock_contributions_mef_get, app,
                               document_data,
                               entity_person_response_data):
    """Test replace identifiedBy in subjects."""
    assert replace_idby_subjects() == (0, 0, 0, 0, 0)

    doc = Document.create(data=document_data, dbcommit=True, reindex=True)
    DocumentsSearch.flush_and_refresh()
    replace = ReplaceMefIdentifiedBySubjects()
    replace.process()
    assert replace.counts_len == (0, 0, 0, 0, 1)

    without_idref_gnd = deepcopy(entity_person_response_data)
    without_idref_gnd['hits']['hits'][0]['metadata'].pop('idref')
    without_idref_gnd['hits']['hits'][0]['metadata'].pop('gnd')
    mock_contributions_mef_get.return_value = mock_response(
        json_data=without_idref_gnd
    )
    assert replace_idby_subjects() == (0, 0, 0, 1, 0)

    without_idref_gnd = deepcopy(entity_person_response_data)
    without_idref_gnd['hits']['hits'][0]['metadata']['deleted'] = '2022'
    mock_contributions_mef_get.return_value = mock_response(
        json_data=without_idref_gnd
    )
    assert replace_idby_subjects() == (0, 0, 1, 0, 0)

    mock_contributions_mef_get.return_value = mock_response(
        json_data=entity_person_response_data
    )
    assert replace_idby_subjects() == (1, 0, 0, 0, 0)

    # clean up
    doc.delete(dbcommit=True, delindex=True, force=True)
    for id in Entity.get_all_ids():
        cont = Entity.get_record(id)
        cont.delete(dbcommit=True, delindex=True, force=True)
