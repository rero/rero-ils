# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
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

"""Record serialization."""
import csv

from flask import current_app
from invenio_records_rest.serializers.csv import CSVSerializer, Line
from invenio_records_rest.serializers.response import add_link_header

from .models import StatType


class StatCSVSerializer(CSVSerializer):
    """Process data to write in csv file."""

    ordered_keys = [
        'library id',
        'library name',
        'checkouts_for_transaction_library',
        'checkouts_for_owning_library',
        'renewals',
        'validated_requests',
        'active_patrons_by_postal_code',
        'new_active_patrons_by_postal_code',
        'items_by_document_type_and_subtype',
        'new_items',
        'new_items_by_location',
        'new_documents',
        'loans_of_transaction_library_by_item_location'
    ]

    def _format_csv(self, records):
        """Return the list of records as a CSV string."""
        # build a unique list of all records keys as CSV headers
        assert len(records) == 1
        record = records[0]

        if record['metadata'].get('type') == StatType.LIBRARIAN:
            # statistics of type librarian
            headers = [key.capitalize().replace('_', ' ')
                       for key in self.ordered_keys]
            line = Line()
            writer = csv.writer(line)
            writer.writerow(headers)
            yield line.read()
            values = sorted(
                record['metadata']['values'],
                key=lambda v: v['library']['name']
            )

            for value in values:
                library = value['library']
                value['library name'] = library['name']
                value['library id'] = library['pid']
                del value['library']
                for v in value:
                    if isinstance(value[v], dict):
                        dict_to_text = ''
                        for k, m in value[v].items():
                            dict_to_text += f'{k} :{m}\r\n'
                        value[v] = dict_to_text
                value = StatCSVSerializer.sort_dict_by_key(value)[1]
                writer.writerow(value)
                yield line.read()
        elif record['metadata'].get('type') == StatType.BILLING:
            # statistics of type billing
            headers = set(('library name', 'library id'))
            for value in record['metadata']['values']:
                headers.update([v for v in value.keys() if v != 'library'])

            # write the CSV output in memory
            line = Line()
            writer = csv.DictWriter(line, fieldnames=sorted(headers))
            writer.writeheader()
            yield line.read()
            # sort by library name
            values = sorted(
                record['metadata']['values'],
                key=lambda v: v['library']['name']
            )

            for value in values:
                library = value['library']
                value['library name'] = library['name']
                value['library id'] = library['pid']
                del value['library']
                for v in value:
                    if isinstance(value[v], dict):
                        dict_to_text = ''
                        for k, m in value[v].items():
                            dict_to_text += f'{k} :{m}\r\n'
                        value[v] = dict_to_text
                writer.writerow(value)
                yield line.read()
        elif record['metadata'].get('type') == StatType.REPORT:
            values = record['metadata']['values'][0]['results']
            for value in values:
                line = Line()
                writer = csv.writer(line)
                writer.writerow(value)
                yield line.read()

    @classmethod
    def sort_dict_by_key(cls, dictionary):
        """Sort dict by dict of keys.

        :param dictionary: dict - an input dictionary
        :param ordered_keys: list - the ordered list keys
        :returns: a list of tuples
        :rtype: list
        """
        tuple_list = sorted(dictionary.items(),
                            key=lambda x: cls.ordered_keys.index(x[0]))
        return list(zip(*tuple_list))

    def process_dict(self, dictionary):
        """Transform record dict with nested keys to a flat dict.

        Needed to overide the parent method to do nothing.
        :param dictionary: dict - an input dictionary
        :returns: an untouched dictionary
        :rtype: dict
        """
        return dictionary


csv_v1 = StatCSVSerializer()
"""CSV serializer."""


def record_responsify(serializer, mimetype):
    """Create a Records-REST response serializer.

    This function is the same as the `invenio-records-rest`, but it adds an
    header to change the download file name.
    :param serializer: Serializer instance.
    :param mimetype: MIME type of response.
    :returns: Function that generates a record HTTP response.
    """
    def view(pid, record, code=200, headers=None, links_factory=None):
        response = current_app.response_class(
            serializer.serialize(pid, record, links_factory=links_factory),
            mimetype=mimetype)
        response.status_code = code
        response.cache_control.no_cache = True
        response.set_etag(str(record.revision_id))
        response.last_modified = record.updated
        if headers is not None:
            response.headers.extend(headers)

        # set the output filename
        date = record.created.isoformat()
        filename = f'stats-{date}.csv'
        if not response.headers.get('Content-Disposition'):
            response.headers['Content-Disposition'] = \
                f'attachment; filename="{filename}"'

        if links_factory is not None:
            add_link_header(response, links_factory(pid))

        return response

    return view


csv_v1_response = record_responsify(csv_v1, 'text/csv')
