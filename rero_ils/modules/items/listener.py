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

"""Signals connector for Item."""

from rero_ils.modules.documents.api import Document
from rero_ils.modules.local_fields.api import LocalField
from rero_ils.modules.local_fields.dumpers import \
    ElasticSearchDumper as LocalFieldESDumper

from .api import Item, ItemsSearch


def enrich_item_data(sender, json=None, record=None, index=None,
                     doc_type=None, arguments=None, **dummy_kwargs):
    """Signal sent before a record is indexed.

    :param json: The dumped record dictionary which can be modified.
    :param record: The record being indexed.
    :param index: The index in which the record will be indexed.
    :param doc_type: The doc_type for the record.
    """
    if index.split('-')[0] != ItemsSearch.Meta.index:
        return
    if not isinstance(record, Item):
        record = Item.get_record_by_pid(record.get('pid'))

    # Document type
    document = Document.get_record_by_pid(json['document']['pid'])
    json['document']['document_type'] = document['type']

    # Current pending requests
    json['current_pending_requests'] = record.get_requests(output='count')

    # add related local fields
    local_fields = [
        field.dumps(dumper=LocalFieldESDumper())
        for field in LocalField.get_local_fields(record)
    ]
    if local_fields:
        json['local_fields'] = local_fields

    if record.is_issue:
        # Issue `sort_date` is an optional field but value is used to sort
        # issues from one another ; if this field is empty, use the issue
        # `expected_date` as value
        json['issue']['sort_date'] = record.sort_date or record.expected_date
        # inherited_first_call_number to issue
        if call_number := record.issue_inherited_first_call_number:
            json['issue']['inherited_first_call_number'] = call_number
        # inherited_second_call_number to issue
        if call_number := record.issue_inherited_second_call_number:
            json['issue']['inherited_second_call_number'] = call_number
        # inject vendor pid
        if vendor_pid := record.vendor_pid:
            json['vendor'] = {'pid': vendor_pid, 'type': 'vndr'}
        # inject claims information: counter and dates
        if notifications := record.claim_notifications:
            dates = [
                notification['creation_date']
                for notification in notifications
                if 'creation_date' in notification
            ]
            json['issue']['claims'] = {
                'counter': len(notifications),
                'dates': dates
            }
