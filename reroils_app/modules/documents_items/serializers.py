# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 RERO.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Export formats."""

from invenio_records_rest.serializers.response import record_responsify, \
    search_responsify


class TextSerializer(object):
    """BibTeX serializer for records."""

    # pylint: disable=W0613
    def format_record(self, record):
        """Convert a record in a CSV string."""
        bib_fields = []

        bib_fields.append(record.get('title'))

        bib_fields.append(
            ';'.join([v.get('name') for v in record.get('authors', [])])
        )

        bib_fields.append(str(record.get('publicationYear', '')))
        bib_str = ','.join(['"%s"' % v for v in bib_fields])
        items = []
        for citem in record.get('citems', []):
            item_fields = []
            item_fields.append(str(citem.get('barcode')))
            item_fields.append(str(citem.get('call_number')))
            item_fields.append(str(citem.get('location')))
            item_fields.append(
                str(citem.get('_circulation', {}).get('status'))
            )
            item_str = ','.join(['"%s"' % v for v in item_fields])
            items.append(','.join((bib_str, item_str)))

        return '\n'.join(items)

    def serialize(self, pid, record, links_factory=None):
        """Serialize a single record and persistent identifier.

        :param pid: Persistent identifier instance.
        :param record: Record instance.
        :param links_factory: Factory function for record links.
        """
        return self.format_record(record)

    def serialize_search(self, pid_fetcher, search_result, links=None,
                         item_links_factory=None):
        """Serialize a search result.

        :param pid_fetcher: Persistent identifier fetcher.
        :param search_result: Elasticsearch search result.
        :param links: Dictionary of links to add to response.
        """
        records = []
        for hit in search_result['hits']['hits']:
            records.append(self.format_record(record=hit['_source']))

        return "\n".join(records)

documents_items_csv_v1 = TextSerializer()
documents_items_csv_v1_response = record_responsify(
    documents_items_csv_v1, 'text/csv'
)
documents_items_csv_v1_search = search_responsify(
    documents_items_csv_v1, 'text/csv'
)
