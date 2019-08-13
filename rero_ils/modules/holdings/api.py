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

"""Holdings records."""

from __future__ import absolute_import, print_function

from functools import partial

from elasticsearch.exceptions import NotFoundError
from flask import current_app
from invenio_search import current_search
from invenio_search.api import RecordsSearch

from .models import HoldingIdentifier, HoldingMetadata
from ..api import IlsRecord, IlsRecordError, IlsRecordIndexer
from ..documents.api import Document, DocumentsSearch
from ..fetchers import id_fetcher
from ..items.api import ItemsSearch
from ..locations.api import Location
from ..minters import id_minter
from ..providers import Provider

# holing provider
HoldingProvider = type(
    'HoldingProvider',
    (Provider,),
    dict(identifier=HoldingIdentifier, pid_type='hold')
)
# holing minter
holding_id_minter = partial(id_minter, provider=HoldingProvider)
# holing fetcher
holding_id_fetcher = partial(id_fetcher, provider=HoldingProvider)


class HoldingsSearch(RecordsSearch):
    """RecordsSearch for holdings."""

    class Meta:
        """Search only on holdings index."""

        index = 'holdings'

    @classmethod
    def flush(cls):
        """Flush indexes."""
        current_search.flush_and_refresh(DocumentsSearch.Meta.index)
        current_search.flush_and_refresh(cls.Meta.index)


class HoldingsIndexer(IlsRecordIndexer):
    """Holdings indexing class."""

    def index(self, record):
        """Indexing a holding record."""
        return_value = super(HoldingsIndexer, self).index(record)
        document_pid = record.replace_refs()['document']['pid']
        document = Document.get_record_by_pid(document_pid)
        document.reindex()
        current_search.flush_and_refresh(DocumentsSearch.Meta.index)
        return return_value


class Holding(IlsRecord):
    """Holding class."""

    minter = holding_id_minter
    fetcher = holding_id_fetcher
    provider = HoldingProvider
    model_cls = HoldingMetadata
    indexer = HoldingsIndexer

    def delete_from_index(self):
        """Delete record from index."""
        try:
            HoldingsIndexer().delete(self)
        except NotFoundError:
            pass

    @property
    def document_pid(self):
        """Shortcut for document pid of the holding."""
        return self.replace_refs()['document']['pid']

    @property
    def circulation_category_pid(self):
        """Shortcut for circulation_category pid of the holding."""
        return self.replace_refs()['circulation_category']['pid']

    @property
    def location_pid(self):
        """Shortcut for location pid of the holding."""
        return self.replace_refs()['location']['pid']

    @property
    def organisation_pid(self):
        """Get organisation pid for holding."""
        location = Location.get_record_by_pid(self.location_pid)
        return location.organisation_pid

    @classmethod
    def get_document_pid_by_holding_pid(cls, holding_pid):
        """Returns document pid for a holding pid."""
        holding = cls.get_record_by_pid(holding_pid).replace_refs()
        return holding.get('document', {}).get('pid')

    @classmethod
    def get_holdings_pid_by_document_pid(cls, document_pid):
        """Returns holding pids attached for a given document pid."""
        results = HoldingsSearch()\
            .filter('term', document__pid=document_pid)\
            .source(['pid']).scan()
        for holding in results:
            yield holding.pid

    def get_number_of_items(self):
        """Get holding number of items."""
        results = ItemsSearch().filter(
            'term', holding__pid=self.pid).source().count()
        return results

    def get_links_to_me(self):
        """Get number of links."""
        links = {}
        items = self.get_number_of_items()
        if items:
            links['items'] = items
        return links

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        cannot_delete = {}
        links = self.get_links_to_me()
        if links:
            cannot_delete['links'] = links
        return cannot_delete


def get_holding_pid_for_item(document_pid, location_pid, item_type_pid):
    """Returns holding pid for document/location/item type."""
    result = HoldingsSearch().filter(
        'term',
        document__pid=document_pid
    ).filter(
        'term',
        circulation_category__pid=item_type_pid
    ).filter(
        'term',
        location__pid=location_pid
    ).source().scan()
    try:
        return next(result).pid
    except StopIteration:
        return None


def create_holding_for_item(document_pid, location_pid, item_type_pid):
    """Create a new holding to link an item."""
    data = {}
    schemas = current_app.config.get('RECORDS_JSON_SCHEMA')
    data_schema = {
        'base_url': current_app.config.get(
            'RERO_ILS_APP_BASE_URL'
        ),
        'schema_endpoint': current_app.config.get(
            'JSONSCHEMAS_ENDPOINT'
        ),
        'schema': schemas['hold']
    }
    data['$schema'] = '{base_url}{schema_endpoint}{schema}'\
        .format(**data_schema)
    base_url = current_app.config.get('RERO_ILS_APP_BASE_URL')
    url_api = '{base_url}/api/{doc_type}/{pid}'
    data['location'] = {
        '$ref': url_api.format(
            base_url=base_url,
            doc_type='locations',
            pid=location_pid)
    }
    data['circulation_category'] = {
        '$ref': url_api.format(
            base_url=base_url,
            doc_type='item_types',
            pid=item_type_pid)
    }
    data['document'] = {
        '$ref': url_api.format(
            base_url=base_url,
            doc_type='documents',
            pid=document_pid)
    }
    record = Holding.create(
        data, dbcommit=True, reindex=True, delete_pid=True)
    return record.get('pid')
