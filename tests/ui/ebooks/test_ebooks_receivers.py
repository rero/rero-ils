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

"""Test ebooks receivers."""

from collections import namedtuple

from rero_ils.modules.documents.api import Document
from rero_ils.modules.ebooks.receivers import publish_harvested_records


def test_publish_harvested_records(app, ebooks_1_xml, ebooks_2_xml,
                                   org_martigny, org_sion):
    """Test publish harvested records."""
    Identifier = namedtuple('Identifier', 'identifier')
    Record = namedtuple('Record', 'xml deleted header')
    records = []
    records.append(Record(xml=ebooks_1_xml, deleted=False,
                          header=Identifier(identifier='record1')))
    records.append(Record(xml=ebooks_2_xml, deleted=False,
                          header=Identifier(identifier='record2')))
    publish_harvested_records(sender=None, records=records)

    assert len(Document.get_all_pids()) == 2
    doc1 = Document.get_record_by_pid('1')
    assert doc1.get('identifiedBy') == [
        {'type': 'bf:Isbn', 'value': '9782075118842'},
        {'type': 'bf:Local', 'value': 'cantook-EDEN502344'},
        {'type': 'bf:Local', 'source': 'cantook', 'value': 'record1'}
    ]
    doc2 = Document.get_record_by_pid('2')
    assert doc2.get('identifiedBy') == [
        {'type': 'bf:Isbn', 'value': '9782811234157'},
        {'type': 'bf:Local', 'value': 'cantook-immateriel.frO1006810'},
        {'type': 'bf:Local', 'source': 'cantook', 'value': 'record2'}
    ]
