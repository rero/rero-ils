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

"""Record serialization."""
import csv

from flask import current_app
from invenio_records_rest.serializers.csv import CSVSerializer, Line
from invenio_records_rest.serializers.response import add_link_header

from rero_ils.modules.stats.models import StatDistributions, StatType
from rero_ils.modules.stats.utils import swap_distributions_required


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

    def _create_table(self, record):
        """Create table for reports with 2 distributions.

        :param record: statistics report record
        :returns: formatted data table
        """
        data = record['metadata']['values']
        org_pid = data[0].get('org_pid')
        config = record['metadata']['config']
        indicator = config['category']['indicator'].get('type')
        distributions = config['category']['indicator'] \
            .get('distributions', [])

        # swap distributions
        if swap_distributions_required(distributions):
            dist2, dist1 = distributions
        else:
            dist1, dist2 = distributions

        # Case dist1 is library
        if dist1 in [StatDistributions.LIBRARY,
                     StatDistributions.ITEM_OWNING_LIBRARY]:
            # columns of row header (first row) of csv file
            header = ['org_pid', 'library_pid', 'library_name']
            # unique values of dist1
            dist1_values = sorted(set([(d['library_pid'], d['library_name'])
                                  for d in data]))
        else:
            # Case neither dist1 or dist2 is library
            header = ['org_pid', dist1]
            # unique values of dist1
            dist1_values = sorted(set([d[dist1] for d in data]))

        len_header = len(header)

        # unique values of dist2
        dist2_values = sorted(set([d[dist2] for d in data]))

        # add to header unique values of dist2
        header.extend(dist2_values)

        processed_data = [tuple(header)]

        # add rows
        for d1 in dist1_values:
            # case dist1 is library
            if type(d1) is tuple:
                row = [org_pid]
                row.extend(d1)
            else:
                # case neither dist1 or dist2 is library
                row = [org_pid, d1]

            # for each pair dist1, dist2 fill in table
            # with the indicator value and put 0 in case of no value
            for i in range(len_header, len(header)):
                # Case dist1 is library
                if type(d1) is tuple:
                    value = [d for d in data if d['library_pid'] == d1[0]
                             and d[dist2] == header[i]]
                else:
                    # Case neither dist1 or dist2 is library
                    value = [d for d in data
                             if d[dist1] == d1 and d[dist2] == header[i]]
                if value:
                    row.insert(i, value[0][indicator])
                else:
                    row.insert(i, 0)

            processed_data.append(tuple(row))

        return processed_data

    def _format_csv(self, records):
        """Return the list of records as a CSV string."""
        # build a unique list of all records keys as CSV headers
        assert len(records) == 1
        record = records[0]

        if record['metadata'].get('type') == 'librarian':
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
        elif record['metadata'].get('type') == StatType.REPORT:
            # statistics of type report
            indicator = record['metadata']['config']['category']['indicator']
            distributions = indicator.get('distributions', [])
            results = True

            # case report with no query results
            if len(record['metadata']['values']) == 1\
               and record['metadata']['values'][0][indicator['type']] == 0:
                results = False

            # case report with 2 distributions
            if len(distributions) == 2 and results:
                # transform list into table
                line = Line()
                writer = csv.writer(line)
                for value in self._create_table(record):
                    writer.writerow(value)
                    yield line.read()
            # cases report with 1 or no distributions
            # and case report with no results
            else:
                fieldnames = list(record['metadata']['values'][0].keys())
                line = Line()
                writer = csv.DictWriter(line, fieldnames=fieldnames)
                writer.writeheader()
                yield line.read()

                for value in record['metadata']['values']:
                    writer.writerow(value)
                    yield line.read()
        else:
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
