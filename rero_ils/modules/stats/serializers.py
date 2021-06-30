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

"""Record serialization."""
import csv

from invenio_records_rest.serializers.csv import CSVSerializer, Line
from invenio_records_rest.serializers.response import record_responsify


class StatCSVSerializer(CSVSerializer):
    """Mixin serializing records as JSON."""

    def _format_csv(self, records):
        """Return the list of records as a CSV string."""
        # build a unique list of all records keys as CSV headers
        assert len(records) == 1
        record = records[0]
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
            writer.writerow(value)
            yield line.read()

    def process_dict(self, dictionary):
        """Transform record dict with nested keys to a flat dict.

        Needed to overide the parent method to do nothing.
        :param dictionary: dict - an input dictionary
        :returns: an untouched dictionary
        :rtype: dict
        """
        return dictionary


csv_v1 = StatCSVSerializer()
"""JSON v1 serializer."""

csv_v1_response = record_responsify(csv_v1, 'text/csv')
