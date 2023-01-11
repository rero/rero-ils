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

"""Patron transaction event CSV serializer."""
import csv
from functools import wraps

from babel.numbers import format_decimal
from ciso8601 import parse_datetime
from flask import stream_with_context
from invenio_i18n.ext import current_i18n
from invenio_records_rest.serializers.csv import CSVSerializer, Line

from rero_ils.modules.documents.api import Document
from rero_ils.modules.documents.utils import title_format_text_head
from rero_ils.modules.items.api import Item
from rero_ils.modules.libraries.api import Library
from rero_ils.modules.loans.api import Loan
from rero_ils.modules.patron_transactions.api import PatronTransaction
from rero_ils.modules.patron_types.api import PatronTypesSearch
from rero_ils.modules.patrons.api import Patron
from rero_ils.modules.serializers import CachedDataSerializerMixin


class PatronTransactionEventCSVSerializer(CSVSerializer,
                                          CachedDataSerializerMixin):
    """Serialize patron transaction event search for csv."""

    def serialize_search(self, pid_fetcher, search_result, links=None,
                         item_links_factory=None):
        """Serialize a search result.

        :param pid_fetcher: Persistent identifier fetcher.
        :param search_result: Elasticsearch search result.
        :param links: Dictionary of links to add to response.
        :param item_links_factory: Factory function for record links.
        """

        def generate_csv():
            headers = dict.fromkeys(self.csv_included_fields)

            # write the CSV output in memory
            line = Line()
            writer = csv.DictWriter(
                line, quoting=csv.QUOTE_ALL, fieldnames=headers)
            writer.writeheader()
            yield line.read()

            for hit in search_result:
                event = hit.to_dict()
                parent = self.get_resource(
                    PatronTransaction,
                    event.get('parent', {}).get('pid')
                )
                transaction_date = parse_datetime(event.get('creation_date'))

                # Load related resources used to fill the file.
                #   !! 'dispute' doesn't have any amount --> can't be rounded
                if amount := event.get('amount'):
                    amount = format_decimal(amount, locale=current_i18n.locale)

                csv_data = {
                    'category': event.get('category'),
                    'type': event.get('type'),
                    'subtype': event.get('subtype'),
                    'amount': amount,
                    'transaction_date': transaction_date.isoformat()
                }

                if pid := event.get('patron', {}).get('pid'):
                    record = self.get_resource(Patron, pid)
                    csv_data |= _extract_patron_data(record)
                if pid := event.get('patron_type', {}).get('pid'):
                    record = self.get_resource(PatronTypesSearch(), pid)
                    csv_data |= _extract_patron_type_data(record)
                if pid := event.get('operator', {}).get('pid'):
                    record = self.get_resource(Patron, pid)
                    csv_data |= _extract_operator_data(record)
                if pid := event.get('library', {}).get('pid'):
                    record = self.get_resource(Library, pid)
                    csv_data |= _extract_transaction_library_data(record)
                    csv_data['transaction_date'] = transaction_date\
                        .astimezone(tz=record.get_timezone())\
                        .isoformat()
                if pid := parent.loan_pid:
                    loan = self.get_resource(Loan, pid)
                    document = self.get_resource(Document, loan.document_pid)
                    item = self.get_resource(Item, loan.item_pid)
                    csv_data |= _extract_document_data(document)
                    csv_data |= _extract_item_data(item, self)
                # removed empty entries.
                csv_data = {k: v for k, v in csv_data.items() if v}

                # write csv data
                data = self.process_dict(csv_data)
                writer.writerow(data)
                yield line.read()

        # return streamed content
        return stream_with_context(generate_csv())


def _skip_if_no_record(func):
    """Decorator used to skip extract function if record doesn't exist."""
    @wraps(func)
    def decorated_view(record, *args, **kwargs):
        return func(record, *args, **kwargs) if record else {}
    return decorated_view


@_skip_if_no_record
def _extract_patron_data(record):
    """Extract data from patron to include into the csv export file.

    :param record: the `Patron` to analyze.
    :returns a dictionary containing desired patron data.
    """
    return {
        'patron_name':
            record.formatted_name,
        'patron_barcode':
            ', '.join(record.get('patron', {}).get('barcode', [])),
        'patron_email':
            record.user.email or
            record.get('patron', {}).get('additional_communication_email')
    }


@_skip_if_no_record
def _extract_document_data(record):
    """Extract document from loan to include into the csv export file.

    :param record: the `Document` representing the document to analyze.
    :returns a dictionary containing desired document data.
    """
    return {
        'document_pid': record.pid,
        'document_title':
            title_format_text_head(record.get('title', []))
    }


@_skip_if_no_record
def _extract_item_data(record, collector):
    """Extract item from loan to include into the csv export file.

    :param record: the `Item` representing the item to analyze.
    :param collector: the class that call this method.
    :returns a dictionary containing desired item data.
    """
    library = collector.get_resource(Library, record.library_pid)
    return {
        'item_pid': record.pid,
        'item_barcode': record.get('barcode'),
        'item_owning_library': library.get('name')
    }


@_skip_if_no_record
def _extract_operator_data(record):
    """Extract data from operator to include into the csv export file.

    :param record: the `Patron` representing the operator to analyze.
    :returns a dictionary containing desired operator data.
    """
    return {
        'operator_name': record.formatted_name
    }


@_skip_if_no_record
def _extract_patron_type_data(record):
    """Extract data from patron type to include into the csv export file.

    :param record: a dictionary with indexed ES data about the patron type.
    :returns a dictionary containing desired patron type data.
    """
    return {
        'patron_type': record.get('name')
    }


@_skip_if_no_record
def _extract_transaction_library_data(record):
    """Extract data from library to include into the csv export file.

    :param record: the `Library` representing the transaction lib to analyze.
    :returns a dictionary containing desired library data.
    """
    return {
        'transaction_library': record.get('name')
    }
