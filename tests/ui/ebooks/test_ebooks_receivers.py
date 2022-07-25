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

from utils import flush_index

from rero_ils.modules.documents.api import Document, DocumentsSearch
from rero_ils.modules.ebooks.receivers import publish_harvested_records
from rero_ils.modules.ebooks.tasks import create_records, delete_records
from rero_ils.modules.holdings.api import Holding, HoldingsSearch


def test_publish_harvested_records(app, ebooks_1_xml, ebooks_2_xml,
                                   org_martigny, loc_online_martigny,
                                   item_type_online_martigny,
                                   org_sion, loc_online_sion,
                                   item_type_online_sion):
    """Test publish harvested records."""
    Identifier = namedtuple('Identifier', 'identifier')
    Record = namedtuple('Record', 'xml deleted header')
    records = [Record(xml=ebooks_1_xml, deleted=False,
                      header=Identifier(identifier='record1'))]
    records.append(Record(xml=ebooks_2_xml, deleted=False,
                          header=Identifier(identifier='record2')))
    records.append(Record(xml=ebooks_2_xml, deleted=True,
                          header=Identifier(identifier='record3')))

    kwargs = {'max': 100}
    publish_harvested_records(sender=None, records=records, kwargs=kwargs)
    flush_index(DocumentsSearch.Meta.index)
    flush_index(HoldingsSearch.Meta.index)

    assert Document.count() == 2
    doc1 = Document.get_record_by_pid('1')
    assert doc1.get('$schema') is not None
    assert doc1.get('identifiedBy') == [
        {'type': 'bf:Isbn', 'value': '9782075118842'},
        {'type': 'bf:Local', 'value': 'cantook-EDEN502344'},
        {'type': 'bf:Local', 'source': 'cantook', 'value': 'record1'}
    ]
    assert len(list(Holding.get_holdings_pid_by_document_pid(doc1.pid))) == 1
    doc2 = Document.get_record_by_pid('2')
    assert doc2.get('$schema') is not None
    assert doc2.get('identifiedBy') == [
        {'type': 'bf:Isbn', 'value': '9782811234157'},
        {'type': 'bf:Local', 'value': 'cantook-immateriel.frO1006810'},
        {'type': 'bf:Local', 'source': 'cantook', 'value': 'record2'}
    ]
    assert len(list(Holding.get_holdings_pid_by_document_pid(doc2.pid))) == 1

    # test update
    # cretae a double holding
    hold_pid = next(Holding.get_holdings_pid_by_document_pid(doc1.pid))
    hold = Holding.get_record_by_pid(hold_pid)
    Holding.create(data=hold, dbcommit=True, reindex=True, delete_pid=True)
    # create a holding without valid source uri
    hold['electronic_location'][0]['uri'] = 'https://invalid.uri/XXXXXX'
    Holding.create(data=hold, dbcommit=True, reindex=True, delete_pid=True)
    HoldingsSearch.flush_and_refresh()
    publish_harvested_records(sender=None, records=records)
    DocumentsSearch.flush_and_refresh()
    HoldingsSearch.flush_and_refresh()
    assert len(list(Holding.get_holdings_pid_by_document_pid(doc1.pid))) == 1
    assert len(list(Holding.get_holdings_pid_by_document_pid(doc2.pid))) == 1

    # test delete
    records = []
    del doc1['electronicLocator']
    records.append(doc1)
    doc2['electronicLocator'] = [{
        "content": "coverImage",
        "type": "relatedResource",
        "url": "http://images.immateriel.fr/covers/DEQ2C5A.png"
    }]
    records.append(doc2)

    create_records(records=records)
    DocumentsSearch.flush_and_refresh()
    HoldingsSearch.flush_and_refresh()
    assert not list(Holding.get_holdings_pid_by_document_pid(doc1.pid))
    assert not list(Holding.get_holdings_pid_by_document_pid(doc2.pid))

    assert 2 == delete_records(records=records)
