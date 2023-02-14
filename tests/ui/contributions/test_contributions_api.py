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

"""CircPolicy Record tests."""

from __future__ import absolute_import, print_function

import tempfile
from copy import deepcopy

import mock
from utils import flush_index, mock_response

from rero_ils.modules.contributions.api import Contribution, \
    ContributionsSearch, contribution_id_fetcher
from rero_ils.modules.contributions.sync import SyncAgent
from rero_ils.modules.documents.api import Document, DocumentsSearch


def test_contribution_create(app, contribution_person_data_tmp, caplog):
    """Test MEF contribution creation."""
    pers = Contribution.get_record_by_pid('1')
    assert not pers
    pers = Contribution.create(
        contribution_person_data_tmp,
        dbcommit=True,
        delete_pid=True
    )
    assert pers == contribution_person_data_tmp
    assert pers.get('pid') == '1'

    pers = Contribution.get_record_by_pid('1')
    assert pers == contribution_person_data_tmp

    fetched_pid = contribution_id_fetcher(pers.id, pers)
    assert fetched_pid.pid_value == '1'
    assert fetched_pid.pid_type == 'cont'
    contribution_person_data_tmp['viaf_pid'] = '1234'
    pers = Contribution.create(
        contribution_person_data_tmp,
        dbcommit=True,
        delete_pid=True
    )
    pers = Contribution.get_record_by_pid('2')
    assert pers.get('viaf_pid') == '1234'

    assert pers.organisation_pids == []

    pers.delete_from_index()
    # test the messages from current_app.logger
    assert caplog.records[0].name == 'elasticsearch'
    assert caplog.record_tuples[1] == (
        'invenio', 30, 'Can not delete from index Contribution: 2'
    )


@mock.patch('requests.get')
def test_contribution_mef_create(mock_contributions_mef_get, app,
                                 contribution_person_data_tmp,
                                 contribution_person_response_data):
    """Test MEF contribution creation."""
    count = Contribution.count()
    mock_contributions_mef_get.return_value = mock_response(
        json_data=contribution_person_response_data
    )
    pers_mef, online = Contribution.get_record_by_ref(
        'https://mef.rero.ch/api/agents/rero/A017671081')
    flush_index(ContributionsSearch.Meta.index)
    assert pers_mef == contribution_person_data_tmp
    assert online
    assert Contribution.count() == count + 1
    pers_mef.pop('idref')
    pers_mef['sources'] = ['gnd']
    pers_mef.replace(pers_mef, dbcommit=True)
    pers_db, online = Contribution.get_record_by_ref(
        'https://mef.rero.ch/api/agents/gnd/13343771X')
    assert pers_db['sources'] == ['gnd']
    assert not online
    # remove created contribution
    Contribution.get_record_by_pid(contribution_person_data_tmp['pid']).delete(
        True, True, True)


@mock.patch('rero_ils.modules.contributions.api.requests.get')
def test_sync_contribution(mock_get, app, contribution_person_data_tmp,
                           document_data_ref):
    """Test MEF agent synchronization."""

    # === setup
    log_path = tempfile.mkdtemp()
    sync = SyncAgent(log_dir=log_path)
    assert sync

    pers = Contribution.create(
        contribution_person_data_tmp,
        dbcommit=True,
        reindex=True,
        delete_pid=True
    )
    flush_index(ContributionsSearch.Meta.index)

    idref_pid = pers['idref']['pid']
    document_data_ref['contribution'][0]['entity']['$ref'] = \
        f'https://mef.rero.ch/api/agents/idref/{idref_pid}'

    doc = Document.create(
        deepcopy(document_data_ref),
        dbcommit=True,
        reindex=True,
        delete_pid=True
    )
    flush_index(DocumentsSearch.Meta.index)

    # === nothing to update
    sync._get_latest = mock.MagicMock(
        return_value=contribution_person_data_tmp)
    # nothing touched as it is up to date
    assert (0, 0, set()) == sync.sync(f'{pers.pid}')
    # nothing removed
    assert (0, []) == sync.remove_unused(f'{pers.pid}')

    # === MEF metadata has been changed
    data = deepcopy(contribution_person_data_tmp)
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
    assert Contribution.get_record_by_pid(
        pers.pid)['idref']['authorized_access_point'] == 'foo'
    assert DocumentsSearch().query(
        'term', contribution__entity__authorized_access_point_fr='foo').count()
    # nothing has been removed as only metadata has been changed
    assert (0, []) == sync.remove_unused(f'{pers.pid}')

    # === a new MEF exists with the same content
    data = deepcopy(contribution_person_data_tmp)
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
    # record has been udpated, no errors
    assert (1, 1, set()) == sync.sync(f'{pers.pid}')
    flush_index(DocumentsSearch.Meta.index)
    # new contribution has been created
    assert Contribution.get_record_by_pid('foo_mef')
    assert Contribution.get_record_by_ref(
        f'https://mef.rero.ch/api/agents/idref/{idref_pid}')[0]
    db_agent = Document.get_record_by_pid(
        doc.pid).get('contribution')[0]['entity']
    assert db_agent['pid'] == 'foo_mef'
    # the old MEF has been removed
    assert (1, []) == sync.remove_unused(f'{pers.pid}')
    # should not exists anymore
    assert not Contribution.get_record_by_pid(pers.pid)

    # === Update the MEF links content
    data = deepcopy(contribution_person_data_tmp)
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
    assert Contribution.get_record_by_pid('foo_mef')
    # document has been updated with the new MEF and IDREF pid
    assert DocumentsSearch().query(
        'term', contribution__entity__pid='foo_mef').count()
    assert DocumentsSearch().query(
        'term', contribution__entity__id_idref='foo_idref').count()
    db_agent = Document.get_record_by_pid(
        doc.pid).get('contribution')[0]['entity']
    assert db_agent['$ref'] == 'https://mef.rero.ch/api/agents/idref/foo_idref'
    assert db_agent['pid'] == 'foo_mef'

    # remove the document
    doc.delete(True, True, True)
    flush_index(DocumentsSearch.Meta.index)

    # the MEF record can be removed
    assert (1, []) == sync.remove_unused()
    # should not exists anymore
    assert not Contribution.get_record_by_pid('foo_mef')
