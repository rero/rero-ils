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

"""MEF persons Record tests."""

from __future__ import absolute_import, print_function

from rero_ils.modules.mef_persons.api import MefPerson, MefPersonsSearch, \
    mef_person_id_fetcher


def test_mef_person_create(es_clear, mef_person_data_tmp):
    """Test persanisation creation."""
    pers = MefPerson.get_record_by_pid('pers1')
    assert not pers
    pers = MefPerson.create(
        mef_person_data_tmp,
        reindex=True
    )
    assert pers == mef_person_data_tmp
    assert pers.get('pid') == 'pers1'

    pers = MefPerson.get_record_by_pid('pers1')
    # assert pers == mef_person_data_tmp

    mef_person_data_tmp['viaf_pid'] = '1234'
    pers = MefPerson.create(
        mef_person_data_tmp,
        reindex=True
    )
    pers = MefPerson.get_record_by_pid('pers1')
    assert pers.get('viaf_pid') == '1234'


def test_mef_persons_index(mef_person, mef_person_data_tmp):
    """Test record indexing."""

    # check if mef_person is indexed
    count = MefPersonsSearch().filter(
        'match',
        _id=mef_person.id
    ).execute().hits.total
    assert count == 1

    # delete mef_person from index
    mef_person.delete()

    # try to delete a record not indexed
    mef_person_data_tmp['pid'] = 'pers2'
    pers = MefPerson.create(
        mef_person_data_tmp,
        reindex=False
    )
    pers.delete()

    count = MefPersonsSearch().filter(
        'match',
        _id=mef_person.id
    ).execute().hits.total
    assert count == 0

    # reindex mef_person
    mef_person.reindex(
        forceindex=True
    )

    # check if record is indexed
    count = MefPersonsSearch().filter(
        'match',
        _id=mef_person.id
    ).execute().hits.total
    assert count == 1


def test_mef_person_linked_document(mef_person, document_ref):
    """Test mef person linked documents."""
    count = mef_person.get_number_of_linked_documents()

    assert count == 1

    documents = mef_person.get_linked_documents()
    assert document_ref.pid == next(documents).pid

    pids = mef_person.get_linked_documents_pid()
    assert len(pids) == 1


def test_mef_person_linked_document_filtered(document_ref,
                                             mef_person,
                                             org_martigny,
                                             item_lib_sion_mef,
                                             mef_person_response_data):
    """Test mef person linked documents filtered by organisation."""
    org_pid = org_martigny.pid
    count = mef_person.get_number_of_linked_documents(org_pid)
    assert count == 0

    pids = mef_person.get_linked_documents_pid(org_pid)
    assert len(pids) == 0

    organisation = item_lib_sion_mef.get_organisation()
    org_pid = organisation.pid
    count = mef_person.get_number_of_linked_documents(org_pid)
    assert count == 1

    documents = mef_person.get_linked_documents(org_pid)
    document = next(documents)
    assert document_ref.pid == document.pid
