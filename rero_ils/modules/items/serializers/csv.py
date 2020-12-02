# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
# Copyright (C) 2020 UCLouvain
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

"""Item serializers."""

import csv

from flask import current_app, request
from invenio_i18n.ext import current_i18n
from invenio_records_rest.serializers.csv import CSVSerializer, Line

from rero_ils.filter import format_date_filter
from rero_ils.modules.documents.api import search_document_by_pid
from rero_ils.modules.documents.utils import title_format_text_head
from rero_ils.modules.items.api import Item, search_active_loans_for_item
from rero_ils.modules.locations.api import LocationsSearch
from rero_ils.utils import get_i18n_supported_languages

role_filter = [
    'rsp',
    'cre',
    'enj',
    'dgs',
    'prg',
    'dsr',
    'ctg',
    'cmp',
    'inv',
    'com',
    'pht',
    'ivr',
    'art',
    'ive',
    'chr',
    'aut',
    'arc',
    'fmk',
    'pra',
    'csl'
]


class ItemCSVSerializer(CSVSerializer):
    """Serialize and filter item circulation status."""

    def transform_search_hit(
        self, pid, record_hit, links_factory=None, **kwargs
    ):
        """Transform search result hit into an intermediate representation.

        :param pid: Persistent identifier instance.
        :param pid: Persistent identifier instance.
        :param record_hit: Record metadata retrieved via search.
        :param links_factory: Factory function for record links.
        """
        hit = self.preprocess_search_hit(
            pid, record_hit, links_factory=links_factory, **kwargs
        )
        return hit

    def preprocess_search_hit(self, pid, record_hit, links_factory=None,
                              **kwargs):
        """Prepare a record hit from Elasticsearch for serialization.

        :param pid: Persistent identifier instance.
        :param record_hit: Record metadata retrieved via search.
        :param links_factory: Factory function for record links.
        """
        language = kwargs.get('language')

        record = record_hit['_source']
        # inherit holdings call number when possible
        item = Item(record)
        issue_call_number = item.issue_inherited_first_call_number
        if issue_call_number:
            record['call_number'] = issue_call_number
        item_pid = pid.pid_value

        # process location
        locations_map = kwargs.get('locations_map')
        record['location_name'] = locations_map[
            record.get('location').get('pid')]

        # retrieve and process document
        document = search_document_by_pid(record['document']['pid'])
        record['document_title'] = title_format_text_head(document.title,
                                                          with_subtitle=True)

        # process contributions
        creator = []
        if 'contribution' in document:
            for contribution in document.contribution:
                if any(role in contribution.role for role in role_filter):
                    authorized_access_point = \
                        'authorized_access_point_{language}'.format(
                            language=language
                        )
                    if authorized_access_point in contribution['agent']:
                        creator.append(
                            contribution['agent'][authorized_access_point]
                        )
        if creator:
            record['document_creator'] = ' ; '.join(creator)
        record['document_type'] = document.type

        # get loans information
        loans_count, loans = search_active_loans_for_item(item_pid)
        record['loans_count'] = loans_count
        if loans_count:
            # get first loan
            loan = next(loans)
            record['last_transaction_date'] = format_date_filter(
                loan.transaction_date,
                date_format='short',
                locale=language,
            )

        record['created'] = format_date_filter(
            record['_created'],
            date_format='short',
            locale=language,
        )

        # prevent csv key error
        # TODO: find other way to prevent csv key error
        del(record['type'])

        return record

    def serialize_search(self, pid_fetcher, search_result, links=None,
                         item_links_factory=None):
        """Serialize a search result.

        :param pid_fetcher: Persistent identifier fetcher.
        :param search_result: Elasticsearch search result.
        :param links: Dictionary of links to add to response.
        :param item_links_factory: Factory function for record links.
        """
        # language
        language = request.args.get("lang", current_i18n.language)
        if not language or language not in get_i18n_supported_languages():
            language = current_app.config.get('BABEL_DEFAULT_LANGUAGE', 'en')

        records = []
        locations_map = {}
        for location in LocationsSearch().filter().scan():
            locations_map[location.pid] = location.name
        for hit in search_result['hits']['hits']:
            processed_hit = self.transform_search_hit(
                pid_fetcher(hit['_id'], hit['_source']),
                hit,
                links_factory=item_links_factory,
                locations_map=locations_map,
                language=language
            )
            records.append(self.process_dict(processed_hit))

        return self._format_csv(records)

    def _format_csv(self, records):
        """Return the list of records as a CSV string.

        :param records: Records metadata to format.
        """
        # build a unique list of all keys in included fields as CSV headers
        headers = dict.fromkeys(self.csv_included_fields)
        # write the CSV output in memory
        line = Line()
        writer = csv.DictWriter(line,
                                quoting=csv.QUOTE_ALL,
                                fieldnames=headers)
        writer.writeheader()
        yield line.read()

        for record in records:
            writer.writerow(record)
            yield line.read()
