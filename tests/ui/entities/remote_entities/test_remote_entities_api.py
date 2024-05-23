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
from rero_ils.modules.entities.remote_entities.api import \
    RemoteEntitiesSearch, RemoteEntity, remote_entity_id_fetcher
from rero_ils.modules.entities.remote_entities.replace import \
    ReplaceIdentifiedBy
from rero_ils.modules.entities.remote_entities.sync import SyncEntity


def test_remote_entity_create(app, entity_person_data_tmp, caplog):
    """Test MEF entity creation."""
    pers = RemoteEntity.get_record_by_pid('1')
    assert not pers
    pers = RemoteEntity.create(
        entity_person_data_tmp,
        dbcommit=True,
        delete_pid=True
    )
    assert pers == entity_person_data_tmp
    assert pers.get('pid') == '1'

    pers = RemoteEntity.get_record_by_pid('1')
    assert pers == entity_person_data_tmp

    fetched_pid = remote_entity_id_fetcher(pers.id, pers)
    assert fetched_pid.pid_value == '1'
    assert fetched_pid.pid_type == 'rement'
    entity_person_data_tmp['viaf_pid'] = '1234'
    RemoteEntity.create(entity_person_data_tmp, dbcommit=True, delete_pid=True)
    pers = RemoteEntity.get_record_by_pid('2')
    assert pers.get('viaf_pid') == '1234'

    assert pers.organisation_pids == []

    pers.delete_from_index()
    # test the messages from current_app.logger
    assert caplog.records[0].name == 'elasticsearch'
    assert caplog.record_tuples[1] == (
        'invenio', 30, 'Can not delete from index RemoteEntity: 2'
    )


@mock.patch('requests.Session.get')
def test_remote_entity_mef_create(
    mock_contributions_mef_get, app, mef_agents_url,
    entity_person_data_tmp, entity_person_response_data
):
    """Test MEF contribution creation."""
    count = RemoteEntity.count()
    mock_contributions_mef_get.return_value = mock_response(
        json_data=entity_person_response_data
    )
    pers_mef, online = RemoteEntity.get_record_by_ref(
        f'{mef_agents_url}/rero/A017671081')
    flush_index(RemoteEntitiesSearch.Meta.index)
    assert pers_mef == entity_person_data_tmp
    assert online
    assert RemoteEntity.count() == count + 1
    pers_mef.pop('idref')
    pers_mef['sources'] = ['gnd']
    pers_mef.replace(pers_mef, dbcommit=True)
    pers_db, online = RemoteEntity.get_record_by_ref(
        f'{mef_agents_url}/gnd/13343771X')
    assert pers_db['sources'] == ['gnd']
    assert not online
    # remove created contribution
    RemoteEntity.get_record_by_pid(entity_person_data_tmp['pid']).delete(
        True, True, True)


@mock.patch('requests.Session.get')
def test_sync_contribution(
    mock_get, app, mef_agents_url, entity_person_data_tmp, document_data_ref
):
    """Test MEF agent synchronization."""
    # === setup
    log_path = tempfile.mkdtemp()
    sync_entity = SyncEntity(log_dir=log_path)
    assert sync_entity

    pers = RemoteEntity.create(
        entity_person_data_tmp,
        dbcommit=True,
        reindex=True,
        delete_pid=True
    )
    flush_index(RemoteEntitiesSearch.Meta.index)

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

    # Test that entity could not be deleted
    assert pers.get_links_to_me(True)['documents'] == [doc.pid]
    assert pers.reasons_not_to_delete()['links']['documents'] == 1

    # === nothing to update
    sync_entity._get_latest = mock.MagicMock(
        return_value=entity_person_data_tmp
    )
    # nothing touched as it is up-to-date
    assert (0, 0, set()) == sync_entity.sync(f'{pers.pid}')
    # nothing removed
    assert (0, []) == sync_entity.remove_unused(f'{pers.pid}')

    # === MEF metadata has been changed
    data = deepcopy(entity_person_data_tmp)
    data['idref']['authorized_access_point'] = 'foo'
    sync_entity._get_latest = mock.MagicMock(return_value=data)
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
    assert (1, 1, set()) == sync_entity.sync(f'{pers.pid}')
    flush_index(DocumentsSearch.Meta.index)

    # contribution and document should be changed
    assert RemoteEntity.get_record_by_pid(
        pers.pid)['idref']['authorized_access_point'] == 'foo'
    assert DocumentsSearch().query(
        'term', contribution__entity__authorized_access_point_fr='foo').count()
    # nothing has been removed as only metadata has been changed
    assert (0, []) == sync_entity.remove_unused(f'{pers.pid}')

    # === a new MEF exists with the same content
    data = deepcopy(entity_person_data_tmp)
    # MEF pid has changed
    data['pid'] = 'foo_mef'
    # mock MEF services
    sync_entity._get_latest = mock.MagicMock(return_value=data)
    mock_resp = dict(hits=dict(hits=[dict(
        id=data['pid'],
        metadata=data
    )]))
    mock_get.return_value = mock_response(json_data=mock_resp)

    # synchronization the same document has been updated 3 times, one MEF
    # record has been updated, no errors
    assert (1, 1, set()) == sync_entity.sync(f'{pers.pid}')
    flush_index(DocumentsSearch.Meta.index)
    # new contribution has been created
    assert RemoteEntity.get_record_by_pid('foo_mef')
    assert RemoteEntity.get_record_by_ref(
        f'{mef_agents_url}/idref/{idref_pid}')[0]
    db_agent = Document.get_record_by_pid(
        doc.pid).get('contribution')[0]['entity']
    assert db_agent['pid'] == 'foo_mef'
    # the old MEF has been removed
    assert (1, []) == sync_entity.remove_unused(f'{pers.pid}')
    # should not exists anymore
    assert not RemoteEntity.get_record_by_pid(pers.pid)

    # === Update the MEF links content
    data = deepcopy(entity_person_data_tmp)
    # MEF pid has changed
    data['pid'] = 'foo_mef'
    # IDREF pid has changed
    data['idref']['pid'] = 'foo_idref'
    # mock MEF services
    sync_entity._get_latest = mock.MagicMock(return_value=data)
    mock_resp = dict(hits=dict(hits=[dict(
        id=data['pid'],
        metadata=data
    )]))
    mock_get.return_value = mock_response(json_data=mock_resp)

    # synchronization the same document has been updated 3 times,
    # one MEF record has been updated, no errors
    assert (1, 1, set()) == sync_entity.sync(f'{data["pid"]}')
    flush_index(DocumentsSearch.Meta.index)
    # new contribution has been created
    assert RemoteEntity.get_record_by_pid('foo_mef')
    # document has been updated with the new MEF and IDREF pid
    assert DocumentsSearch().query(
        'term', contribution__entity__pids__remote='foo_mef').count()
    assert DocumentsSearch().query(
        'term', contribution__entity__pids__idref='foo_idref').count()
    db_agent = Document.get_record_by_pid(
        doc.pid).get('contribution')[0]['entity']
    assert db_agent['$ref'] == f'{mef_agents_url}/idref/foo_idref'
    assert db_agent['pid'] == 'foo_mef'

    # remove the document
    doc = Document.get_record_by_pid(doc.pid)
    doc.delete(True, True, True)
    flush_index(DocumentsSearch.Meta.index)

    # the MEF record can be removed
    assert (1, []) == sync_entity.remove_unused()
    # should not exists anymore
    assert not RemoteEntity.get_record_by_pid('foo_mef')


@mock.patch('requests.Session.get')
def test_sync_concept(
    mock_get, app, mef_concepts_url, entity_topic_data,
    document_data_subject_ref
):
    #
    """Test MEF agent synchronization."""
    # === setup
    log_path = tempfile.mkdtemp()
    sync_entity = SyncEntity(log_dir=log_path)
    assert sync_entity

    topic = RemoteEntity.create(
        entity_topic_data,
        dbcommit=True,
        reindex=True,
        delete_pid=True
    )
    flush_index(RemoteEntitiesSearch.Meta.index)

    entity_url = f'{mef_concepts_url}/idref/{topic["idref"]["pid"]}'
    document_data_subject_ref['subjects'][0]['entity']['$ref'] = entity_url

    doc = Document.create(
        deepcopy(document_data_subject_ref),
        dbcommit=True,
        reindex=True,
        delete_pid=True
    )
    flush_index(DocumentsSearch.Meta.index)

    # === nothing to update
    sync_entity._get_latest = mock.MagicMock(return_value=entity_topic_data)
    # nothing touched as it is up-to-date
    assert (0, 0, set()) == sync_entity.sync(f'pid:{topic.pid}')
    # nothing removed
    assert (0, []) == sync_entity.remove_unused(f'pid:{topic.pid}')

    # === MEF metadata has been changed
    data = deepcopy(entity_topic_data)
    data['idref']['authorized_access_point'] = 'foo'
    sync_entity._get_latest = mock.MagicMock(return_value=data)
    mock_resp = dict(hits=dict(hits=[dict(
        id=data['pid'],
        metadata=data
    )]))
    mock_get.return_value = mock_response(json_data=mock_resp)
    assert DocumentsSearch().query(
        'term',
        subjects__entity__authorized_access_point_fr='foo').count() == 0
    # synchronization the same document has been updated 3 times, one MEF
    # record has been updated, no errors
    assert (1, 1, set()) == sync_entity.sync(f'pid:{topic.pid}')
    flush_index(DocumentsSearch.Meta.index)

    # contribution and document should be changed
    entity = RemoteEntity.get_record_by_pid(topic.pid)
    assert entity['idref']['authorized_access_point'] == 'foo'
    assert DocumentsSearch()\
        .query('term', subjects__entity__authorized_access_point_fr='foo')\
        .count()
    # nothing has been removed as only metadata has been changed
    assert (0, []) == sync_entity.remove_unused(topic.pid)

    # RESET FIXTURES
    #  * Remove the document
    #  * Entity record can be removed ; and should not exist anymore
    doc = Document.get_record_by_pid(doc.pid)
    doc.delete(True, True, True)
    flush_index(DocumentsSearch.Meta.index)
    assert (1, []) == sync_entity.remove_unused()
    assert not RemoteEntity.get_record_by_pid('foo_mef')


def test_remote_entity_properties(
    entity_person, item_lib_martigny, document, document_data, mef_concept1
):
    """Test entity properties."""
    item = item_lib_martigny

    assert document.pid not in entity_person.documents_pids()
    assert str(document.id) not in entity_person.documents_ids()
    assert item.organisation_pid not in entity_person.organisation_pids
    document['contribution'] = [{
        'entity': {
            '$ref': 'https://mef.rero.ch/api/agents/idref/223977268',
        },
        'role': ['cre']
    }]
    document.update(document, dbcommit=True, reindex=True)
    assert document.pid in entity_person.documents_pids()
    assert str(document.id) in entity_person.documents_ids()
    assert item.organisation_pid in entity_person.organisation_pids

    assert entity_person == RemoteEntity.get_entity('mef', entity_person.pid)
    assert entity_person == RemoteEntity.get_entity('viaf', '70119347')

    sources_pids = entity_person.source_pids()
    assert sources_pids['idref'] == '223977268'
    assert sources_pids['gnd'] == '13343771X'
    assert sources_pids['rero'] == 'A017671081'

    # Test special behavior of `get_record_by_ref` ::
    #   Simulate an exception into the entity creation to test the exception
    #   catching block statement.
    with mock.patch(
        'rero_ils.modules.entities.remote_entities.api.RemoteEntity.create',
        side_effect=Exception()
    ):
        entity, _ = RemoteEntity.get_record_by_ref(
            'https://bib.rero.ch/api/documents/dummy_doc')
        assert entity is None

    # remove contribution
    document.pop('contribution')
    document.update(document, dbcommit=True, reindex=True)
    assert document.pid not in entity_person.documents_pids()
    assert str(document.id) not in entity_person.documents_ids()
    assert item.organisation_pid not in entity_person.organisation_pids

    # add subjects
    document['subjects'] = [{
        'entity': {
            '$ref': 'https://mef.rero.ch/api/concepts/idref/ent_concept_idref',
        }
    }]
    document.update(document, dbcommit=True, reindex=True)
    assert document.pid in mef_concept1.documents_pids()
    assert str(document.id) in mef_concept1.documents_ids()
    assert item.organisation_pid in mef_concept1.organisation_pids
    # remove subjects
    document.pop('subjects')
    document.update(document, dbcommit=True, reindex=True)
    assert document.pid not in mef_concept1.documents_pids()
    assert str(document.id) not in mef_concept1.documents_ids()
    assert item.organisation_pid not in mef_concept1.organisation_pids

    # add genreForm
    document['genreForm'] = [{
        'entity': {
            '$ref': 'https://mef.rero.ch/api/concepts/idref/ent_concept_idref',
        }
    }]
    document.update(document, dbcommit=True, reindex=True)
    assert document.pid in mef_concept1.documents_pids()
    assert str(document.id) in mef_concept1.documents_ids()
    assert item.organisation_pid in mef_concept1.organisation_pids

    # Reset fixture
    document.update(document_data, dbcommit=True, reindex=True)


def test_replace_identified_by(
    app, entity_organisation, entity_person_rero, person2_data,
    entity_person_all, entity_topic_data_2, entity_topic_data_temporal,
    entity_place_data,
    document, document_sion_items, export_document
):
    """Test replace identified by with $ref."""
    # === setup
    log_path = tempfile.mkdtemp()
    replace_identified_by = ReplaceIdentifiedBy(
        field='contribution',
        verbose=True,
        dry_run=False,
        log_dir=log_path
    )
    assert replace_identified_by
    assert replace_identified_by.count() == 2

    # no MEF response for agents in contribution
    with mock.patch(
        'requests.Session.get',
        side_effect=[mock_response(status=404), mock_response(status=404)]
    ):
        changed, not_found, rero_only = replace_identified_by.run()
        assert changed == 0
        assert not_found == 2
        assert rero_only == 0
        assert replace_identified_by.not_found == {
            'bf:Organisation': {
                'gnd:1161956409': 'Convegno internazionale '
                                  'di italianistica Craiova'
            },
            'bf:Person': {
                    'rero:A003633163': 'Nebehay, Christian Michael'
            }
        }
        replace_identified_by.set_timestamp()
        data = replace_identified_by.get_timestamp()
        assert 'contribution' in data
        assert data['contribution']['changed'] == 0
        assert data['contribution']['not found'] == 2
        assert data['contribution']['rero only'] == 0

    # with MEF response for agents in contribution
    with mock.patch(
        'requests.Session.get',
        side_effect=[
            mock_response(json_data=entity_person_rero),
            mock_response(json_data=entity_organisation)
        ]
    ):
        changed, not_found, rero_only = replace_identified_by.run()
        assert changed == 1
        assert not_found == 0
        assert rero_only == 1
        assert replace_identified_by.rero_only == {
            'bf:Person': {
                'rero:A003633163': 'Nebehay, Christian Michael'
            }
        }
    # with MEF response for concepts in subjects
    replace_identified_by = ReplaceIdentifiedBy(
        field='subjects',
        verbose=True,
        dry_run=False,
        log_dir=log_path
    )
    assert replace_identified_by
    assert replace_identified_by.count() == 2
    with mock.patch(
        'requests.Session.get',
        side_effect=[
            mock_response(json_data=entity_person_all),
            mock_response(json_data=entity_topic_data_temporal),
            mock_response(json_data=entity_place_data),
            mock_response(json_data=person2_data),
            mock_response(json_data={'rero': {
                'authorized_access_point': 'Europe occidentale',
                'type': 'bf:Place'
            }}),
            mock_response(json_data=entity_topic_data_2)
        ]
    ):
        changed, not_found, rero_only = replace_identified_by.run()
        assert changed == 1
        assert not_found == 0
        assert rero_only == 3
        assert dict(sorted(replace_identified_by.rero_only.items())) == {
            'bf:Person': {
                'rero:A009963344': 'Athenagoras (patriarche oecuménique ; 1)'
            },
            'bf:Topic': {
                'rero:A021039750': 'Bases de données déductives'
            },
            'bf:Place': {
                'rero:A009975209': 'Europe occidentale'
            }
        }


def test_entity_get_record_by_ref(
    mef_agents_url, entity_person, entity_person_data_tmp
):
    """Test remote entity: get record by ref."""
    dummy_ref = f'{mef_agents_url}/idref/dummy_idref_pid'
    assert (None, False) == RemoteEntity.get_record_by_ref(dummy_ref)

    # Remote entity from ES index
    RemoteEntitiesSearch().filter('term', pid=entity_person.pid).delete()
    flush_index(RemoteEntitiesSearch.Meta.index)
    ent_ref = f'{mef_agents_url}/idref/{entity_person["idref"]["pid"]}'
    with mock.patch(
        'rero_ils.modules.entities.remote_entities.api.get_mef_data_by_type',
        return_value=entity_person_data_tmp
    ):
        entity, online = RemoteEntity.get_record_by_ref(ent_ref)
        assert entity and online
    flush_index(RemoteEntitiesSearch.Meta.index)
    assert RemoteEntitiesSearch().filter('term', pid=entity_person.pid).count()


def test_remote_entity_resolve(entity_person):
    """Test remote entity resolver."""
    # TODO :: Only for code coverage for now. When relations between entities
    #         will be implemented, this test should be corrected.
    assert entity_person.resolve()
