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

"""Local entities record tests."""

from __future__ import absolute_import, print_function

import time
from datetime import timedelta

from utils import flush_index

from rero_ils.modules.documents.api import Document, DocumentsSearch
from rero_ils.modules.utils import get_ref_for_pid


def test_local_entity_properties(local_entity_person):
    """Test local entity property"""
    assert local_entity_person.get_authorized_access_point(None) == \
           local_entity_person['authorized_access_point']


def test_local_entity_indexing(app, local_entity_person, document_data_tmp):
    """Test local entity indexing."""
    entity = local_entity_person

    # Check relations between local entity and other resources.
    data = document_data_tmp
    data.setdefault('contribution', []).append({
        'entity': {'$ref': get_ref_for_pid('locent', entity.pid)},
        'role': ['aut']
    })
    doc = Document.create(data, delete_pid=True, reindex=True, dbcommit=True)
    reasons = entity.reasons_not_to_delete()
    assert reasons['links']['documents']

    # Update the local entity and check if related resources are updated
    original_access_point = entity['authorized_access_point']
    entity['name'] = 'my_local_access_point'
    entity = entity.update(entity, dbcommit=True, reindex=True, commit=True)
    # updating related resource is an asynchronous task (to not block app if
    # there are a lot of related resource). We need to wait to the end of the
    # task to check id related resources are up-to-date.
    delay = app.config.get('RERO_ILS_INDEXER_TASK_DELAY', 0) \
        + timedelta(seconds=2)
    time.sleep(delay.seconds)  # find a better way to detect task is finished.

    flush_index(DocumentsSearch.Meta.index)
    hit = DocumentsSearch().get_record_by_pid(doc.pid)
    assert any(
        contribution['entity']['authorized_access_point_fr'] ==
        entity.get_authorized_access_point(language='fr')
        for contribution in hit.contribution
    )

    # reset fixtures
    entity['authorized_access_point'] = original_access_point
    entity.update(entity, dbcommit=True, reindex=True)
    doc.delete()
