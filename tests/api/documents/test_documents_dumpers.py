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

"""Test document dumpers."""
import pytest

from rero_ils.modules.acquisition.dumpers import document_acquisition_dumper
from rero_ils.modules.commons.exceptions import RecordNotFound
from rero_ils.modules.documents.api import Document
from rero_ils.modules.documents.dumpers import document_replace_refs_dumper, \
    document_title_dumper
from rero_ils.modules.entities.models import EntityType


def test_document_dumpers(document, document_data):
    """Test document dumpers."""
    dump_data = document.dumps(dumper=document_title_dumper)
    assert dump_data['pid']
    assert dump_data['title_text']

    dump_data = document.dumps(dumper=document_acquisition_dumper)
    assert dump_data['pid']
    assert dump_data['title_text']
    assert dump_data['identifiers']

    entity_data = {
        'entity': {
            '$ref': 'https://mef.rero.ch/api/agents/idref/dummy_idref',
            'pid': 'dummy_pid',
            'type': EntityType.PERSON
        }
    }
    document['contribution'] = [entity_data]
    with pytest.raises(RecordNotFound):
        document.dumps(dumper=document_replace_refs_dumper)
    document['contribution'] = document_data['contribution']
    document['subjects'] = [entity_data]
    with pytest.raises(RecordNotFound):
        document.dumps(dumper=document_replace_refs_dumper)


@pytest.mark.skip(reason="Dumper() not implement 'load()' method")
def test_multi_dumpers(document_data):
    """Test MultiDumper."""
    # TODO :: Try to fix this test.
    document_title_dumper.load(document_data, Document)
