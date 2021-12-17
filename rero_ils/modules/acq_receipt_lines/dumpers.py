# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
# Copyright (C) 2021 UCLouvain
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

"""Acquisition receipt line dumpers."""

from invenio_records.dumpers import Dumper as InvenioRecordsDumper

from rero_ils.modules.documents.utils import title_format_text_head


class AcqReceiptLineESDumper(InvenioRecordsDumper):
    """ElasticSearch dumper class for an AcqReceiptLine."""

    def dump(self, record, data):
        """Dump an AcqReceiptLine instance for ElasticSearch.

        For ElasticSearch integration, we need to dump basic informations from
        a `AcqReceiptLine` object instance, and add some basic data about
        related.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        """
        # Keep only some attributes from AcqReceiptLine object initial dump.
        for attr in ['pid', 'receipt_date', 'amount', 'quantity', 'vat_rate']:
            value = record.get(attr)
            if value:
                data.update({attr: value})
        notes = record.get('notes', [])
        if notes:
            data['notes'] = [note['content'] for note in notes]

        # Add document informations: pid, formatted title and ISBN identifiers.
        # (remove None values from document metadata)
        document = record.order_line.document
        data['document'] = {
            'pid': document.pid,
            'title': title_format_text_head(document.get('title', [])),
            'identifiers': document.get_identifier_values(filters=['bf:Isbn'])
        }
        data['document'] = {k: v for k, v in data['document'].items() if v}
        return data
