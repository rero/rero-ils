# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

from rero_ils.modules.commons.identifiers import IdentifierType
from rero_ils.modules.documents.extensions import TitleExtension


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
            if value := record.get(attr):
                data.update({attr: value})
        if notes := record.get('notes', []):
            data['notes'] = [note['content'] for note in notes]

        order_line = record.order_line
        # Add acq_account information's: pid
        data['acq_account'] = {'pid': order_line.account_pid}
        # Add document information's: pid, formatted title and ISBN identifiers
        # (remove None values from document metadata)
        document = order_line.document
        identifiers = document.get_identifiers(
            filters=[IdentifierType.ISBN],
            with_alternatives=True
        )
        identifiers = [identifier.normalize() for identifier in identifiers]
        data['document'] = {
            'pid': document.pid,
            'title': TitleExtension.format_text(document.get('title', [])),
            'identifiers': identifiers
        }
        data['document'] = {k: v for k, v in data['document'].items() if v}
        return data
