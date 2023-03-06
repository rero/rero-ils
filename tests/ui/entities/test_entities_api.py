# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

"""Entities Record tests."""

from __future__ import absolute_import, print_function

import tempfile
from copy import deepcopy

import mock
from utils import flush_index, mock_response

from rero_ils.modules.documents.api import Document, DocumentsSearch
from rero_ils.modules.entities.api import EntitiesSearch, Entity, \
    entity_id_fetcher
from rero_ils.modules.entities.sync import SyncAgent


def test_entity_create(app, entity_person_data_tmp, caplog):
    """Test MEF entity creation."""
    pers = Entity.get_record_by_pid('1')
    assert not pers
    pers = Entity.create(
        entity_person_data_tmp,
        dbcommit=True,
        delete_pid=True
    )
    assert pers == entity_person_data_tmp
    assert pers.get('pid') == '1'

    pers = Entity.get_record_by_pid('1')
    assert pers == entity_person_data_tmp

    fetched_pid = entity_id_fetcher(pers.id, pers)
    assert fetched_pid.pid_value == '1'
    assert fetched_pid.pid_type == 'ent'
    entity_person_data_tmp['viaf_pid'] = '1234'
    Entity.create(entity_person_data_tmp, dbcommit=True, delete_pid=True)
    pers = Entity.get_record_by_pid('2')
    assert pers.get('viaf_pid') == '1234'

    assert pers.organisation_pids == []

    pers.delete_from_index()
    # test the messages from current_app.logger
    assert caplog.records[0].name == 'elasticsearch'
    assert caplog.record_tuples[1] == (
        'invenio', 30, 'Can not delete from index Entity: 2'
    )


@mock.patch('requests.get')
def test_entity_mef_create(
    mock_contributions_mef_get, app, mef_agents_url,
    entity_person_data_tmp, entity_person_response_data
):
    """Test MEF contribution creation."""
    count = Entity.count()
    mock_contributions_mef_get.return_value = mock_response(
        json_data=entity_person_response_data
    )
    pers_mef, online = Entity.get_record_by_ref(
        f'{mef_agents_url}/rero/A017671081')
    flush_index(EntitiesSearch.Meta.index)
    assert pers_mef == entity_person_data_tmp
    assert online
    assert Entity.count() == count + 1
    pers_mef.pop('idref')
    pers_mef['sources'] = ['gnd']
    pers_mef.replace(pers_mef, dbcommit=True)
    pers_db, online = Entity.get_record_by_ref(
        f'{mef_agents_url}/gnd/13343771X')
    assert pers_db['sources'] == ['gnd']
    assert not online
    # remove created contribution
    Entity.get_record_by_pid(entity_person_data_tmp['pid']).delete(
        True, True, True)


@mock.patch('rero_ils.modules.entities.api.requests.get')
def test_sync_contribution(
    mock_get, app, mef_agents_url, entity_person_data_tmp, document_data_ref
):
    """Test MEF agent synchronization."""
    # === setup
    log_path = tempfile.mkdtemp()
    sync = SyncAgent(log_dir=log_path)
    assert sync

    pers = Entity.create(
        entity_person_data_tmp,
        dbcommit=True,
        reindex=True,
        delete_pid=True
    )
    flush_index(EntitiesSearch.Meta.index)

    idref_pid = pers['idref']['pid']
    document_data_ref['contribution'][0]['entity']['$ref'] = \
        f'{mef_agents_url}/idref/{idref_pid}'

    doc = Document.create(
        deepcopy(document_data_ref),
        dbcommit=True,
        reindex=True,
        delete_pid=True
    )
    flush_index(DocumentsSearch.Meta.index)

    # === nothing to update
    sync._get_latest = mock.MagicMock(return_value=entity_person_data_tmp)
    # nothing touched as it is up-to-date
    assert (0, 0, set()) == sync.sync(f'{pers.pid}')
    # nothing removed
    assert (0, []) == sync.remove_unused(f'{pers.pid}')

    # === MEF metadata has been changed
    data = deepcopy(entity_person_data_tmp)
    data['idref']['authorized_access_point'] = 'foo'
    sync._get_latest = mock.MagicMock(return_value=data)
    mock_resp = dict(hits=dict(hits=[dict(
        id=data['pid'],
        metadata=data
    )]))
    mock_get.return_value = mock_response(json_data=mock_resp)
    assert DocumentsSearch().query(
        'term',
        contribution__entity__authorized_access_point_fr='foo').count() == 0
    # synchronization the same document has been updated 3 times, one MEF
    # record has been updated, no errors
    assert (1, 1, set()) == sync.sync(f'{pers.pid}')
    flush_index(DocumentsSearch.Meta.index)

    # contribution and document should be changed
    assert Entity.get_record_by_pid(
        pers.pid)['idref']['authorized_access_point'] == 'foo'
    assert DocumentsSearch().query(
        'term', contribution__entity__authorized_access_point_fr='foo').count()
    # nothing has been removed as only metadata has been changed
    assert (0, []) == sync.remove_unused(f'{pers.pid}')

    # === a new MEF exists with the same content
    data = deepcopy(entity_person_data_tmp)
    # MEF pid has changed
    data['pid'] = 'foo_mef'
    # mock MEF services
    sync._get_latest = mock.MagicMock(return_value=data)
    mock_resp = dict(hits=dict(hits=[dict(
        id=data['pid'],
        metadata=data
    )]))
    mock_get.return_value = mock_response(json_data=mock_resp)

    # synchronization the same document has been updated 3 times, one MEF
    # record has been updated, no errors
    assert (1, 1, set()) == sync.sync(f'{pers.pid}')
    flush_index(DocumentsSearch.Meta.index)
    # new contribution has been created
    assert Entity.get_record_by_pid('foo_mef')
    assert Entity.get_record_by_ref(
        f'{mef_agents_url}/idref/{idref_pid}')[0]
    db_agent = Document.get_record_by_pid(
        doc.pid).get('contribution')[0]['entity']
    assert db_agent['pid'] == 'foo_mef'
    # the old MEF has been removed
    assert (1, []) == sync.remove_unused(f'{pers.pid}')
    # should not exists anymore
    assert not Entity.get_record_by_pid(pers.pid)

    # === Update the MEF links content
    data = deepcopy(entity_person_data_tmp)
    # MEF pid has changed
    data['pid'] = 'foo_mef'
    # IDREF pid has changed
    data['idref']['pid'] = 'foo_idref'
    # mock MEF services
    sync._get_latest = mock.MagicMock(return_value=data)
    mock_resp = dict(hits=dict(hits=[dict(
        id=data['pid'],
        metadata=data
    )]))
    mock_get.return_value = mock_response(json_data=mock_resp)

    # synchronization the same document has been updated 3 times, one MEF
    # record has been udpated, no errors
    assert (1, 1, set()) == sync.sync(f'{data["pid"]}')
    flush_index(DocumentsSearch.Meta.index)
    # new contribution has been created
    assert Entity.get_record_by_pid('foo_mef')
    # document has been updated with the new MEF and IDREF pid
    assert DocumentsSearch().query(
        'term', contribution__entity__pid='foo_mef').count()
    assert DocumentsSearch().query(
        'term', contribution__entity__id_idref='foo_idref').count()
    db_agent = Document.get_record_by_pid(
        doc.pid).get('contribution')[0]['entity']
    assert db_agent['$ref'] == f'{mef_agents_url}/idref/foo_idref'
    assert db_agent['pid'] == 'foo_mef'

    # remove the document
    doc = Document.get_record_by_pid(doc.pid)
    doc.delete(True, True, True)
    flush_index(DocumentsSearch.Meta.index)

    # the MEF record can be removed
    assert (1, []) == sync.remove_unused()
    # should not exists anymore
    assert not Entity.get_record_by_pid('foo_mef')


def test_entity_properties(
    entity_person, item_lib_martigny, document, document_data
):
    """Test entity properties."""
    item = item_lib_martigny

    assert document.pid not in entity_person.documents_pids()
    assert document.id not in entity_person.documents_ids()
    assert item.organisation_pid not in entity_person.organisation_pids
    document['contribution'] = [{
        'entity': {
            '$ref': 'https://mef.rero.ch/api/agents/idref/223977268'
        },
        'role': ['cre']
    }]
    document.update(document, dbcommit=True, reindex=True)
    assert document.pid in entity_person.documents_pids()
    assert str(document.id) in entity_person.documents_ids()
    assert item.organisation_pid in entity_person.organisation_pids

    assert entity_person == Entity.get_entity('mef', entity_person.pid)
    assert entity_person == Entity.get_entity('viaf', '70119347')

    sources_pids = entity_person.source_pids()
    assert sources_pids['idref'] == '223977268'
    assert sources_pids['gnd'] == '13343771X'
    assert sources_pids['rero'] == 'A017671081'

    document.index_contributions()
    document.index_contributions(True)

    # Reset fixture
    document.update(document_data, dbcommit=True, reindex=True)
