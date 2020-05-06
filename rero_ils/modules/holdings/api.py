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

from builtins import classmethod
from copy import deepcopy
from functools import partial

from flask import current_app
from flask_babelex import gettext as _
from invenio_search import current_search
from invenio_search.api import RecordsSearch
from jinja2 import Template

from .models import HoldingIdentifier
from ..api import IlsRecord, IlsRecordsIndexer
from ..documents.api import Document
from ..errors import MissingRequiredParameterError
from ..fetchers import id_fetcher
from ..items.api import Item, ItemsSearch
from ..locations.api import Location
from ..minters import id_minter
from ..organisations.api import Organisation
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
        doc_types = None

    @classmethod
    def flush(cls):
        """Flush indexes."""
        current_search.flush_and_refresh(cls.Meta.index)


class Holding(IlsRecord):
    """Holding class."""

    minter = holding_id_minter
    fetcher = holding_id_fetcher
    provider = HoldingProvider
    # model_cls = HoldingMetadata
    pids_exist_check = {
        'required': {
            'doc': 'document',
            'loc': 'location',
            'itty': 'circulation_category'
        }
    }

    def extended_validation(self, **kwargs):
        """Add additional record validation.

        Ensures that holdings of type serials are created only on
        journal documents i.e. serial mode_of_issuance documents.

        Ensures that holdings of type electronic are created only on
        ebooks documents i.e. harvested documents.

        Ensures that for the holdings of type serials, if it has a regular
        frequency the first_expected_date should be given.

        :returns: False if
            - document type is not journal and holding type is serial.
            - document type is journal and holding type is not serial.
            - document type is ebook and holding type is not electronic.
            - document type is not ebook and holding type is electronic.
            - holding type is serial and the first_expected_date
              is not given for a regular frequency.
        """
        document = Document.get_record_by_pid(self.document_pid)
        is_serial = self.holdings_type == 'serial'
        if is_serial:
            patterns = self.get('patterns', {})
            if patterns and \
                patterns.get('frequency') != 'rdafr:1016' \
                    and not patterns.get('first_expected_date'):
                return False
        is_electronic = self.holdings_type == 'electronic'
        is_issuance = document.dumps().get('issuance') == 'rdami:1003'
        return not(
            (is_issuance ^ is_serial) or (document.harvested ^ is_electronic)
            )

    @property
    def is_serial(self):
        """Shortcut to check if holding is a serial holding record."""
        document = Document.get_record_by_pid(self.document_pid).dumps()
        is_serial = self.holdings_type == 'serial'
        is_issuance = document.get('issuance') == 'rdami:1003'
        return is_serial and is_issuance

    @property
    def holdings_type(self):
        """Shortcut to return the type of the holding."""
        return self.get('holdings_type')

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
    def library_pid(self):
        """Shortcut for library of the holding location."""
        return Location.get_record_by_pid(self.location_pid).library_pid

    @property
    def organisation_pid(self):
        """Get organisation pid for holding."""
        return Location.get_record_by_pid(self.location_pid).organisation_pid

    @property
    def available(self):
        """Get availability for holding."""
        items = []
        for item_pid in Item.get_items_pid_by_holding_pid(self.pid):
            items.append(Item.get_record_by_pid(item_pid))
        return Holding.isAvailable(items)

    @classmethod
    def isAvailable(cls, items):
        """."""
        for item in items:
            if item.available:
                return True
        return False

    @property
    def get_items_count_by_holding_pid(self):
        """Returns items count from holding pid."""
        results = ItemsSearch()\
            .filter('term', holding__pid=self.pid)\
            .source(['pid']).count()
        return results

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

    @classmethod
    def get_holdings_pid_by_document_pid_by_org(cls, document_pid, org_pid):
        """Returns holding pids attached for a given document pid."""
        results = HoldingsSearch()\
            .filter('term', document__pid=document_pid)\
            .filter('term', organisation__pid=org_pid)\
            .source(['pid']).scan()
        for holding in results:
            yield holding.pid

    @classmethod
    def get_holdings_by_document_by_view_code(cls, document_pid, viewcode):
        """Returns holding pids by document and view code."""
        es_query = HoldingsSearch()\
            .filter('term', document__pid=document_pid)\
            .source(['pid'])
        if (viewcode != current_app.
                config.get('RERO_ILS_SEARCH_GLOBAL_VIEW_CODE')):
            org_pid = Organisation.get_record_by_viewcode(viewcode)['pid']
            es_query = es_query.filter('term', organisation__pid=org_pid)
        return [result.pid for result in es_query.scan()]

    def get_items_filter_by_viewcode(self, viewcode):
        """Return items filter by view code."""
        items = []
        holdings_items = [
            Item.get_record_by_pid(item_pid)
            for item_pid in Item.get_items_pid_by_holding_pid(self.get('pid'))
        ]
        if (viewcode != current_app.
                config.get('RERO_ILS_SEARCH_GLOBAL_VIEW_CODE')):
            org_pid = Organisation.get_record_by_viewcode(viewcode)['pid']
            for item in holdings_items:
                if item.organisation_pid == org_pid:
                    items.append(item)
            return items
        return holdings_items

    @property
    def get_items(self):
        """Return items of holding record."""
        for item_pid in Item.get_items_pid_by_holding_pid(self.pid):
            yield Item.get_record_by_pid(item_pid)
        # return [Item.get_record_by_pid(item_pid)
        #         for item_pid in Item.get_items_pid_by_holding_pid(self.pid)]

    def get_number_of_items(self):
        """Get holding number of items."""
        results = ItemsSearch().filter(
            'term', holding__pid=self.pid).source().count()
        return results

    def get_links_to_me(self):
        """Get links that can block the holding deletion.

        Attached items to a holding record blocks the deletion.

        :returns: a list of records links to the holding record.
        """
        links = {}
        # get number of attached items
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

    def get_holding_loan_conditions(self):
        """Returns loan conditions for a given holding."""
        from ..patrons.api import current_patron
        from ..item_types.api import ItemType
        from ..circ_policies.api import CircPolicy

        if current_patron and current_patron.is_patron:
            cipo = CircPolicy.provide_circ_policy(
                self.library_pid,
                current_patron.patron_type_pid,
                self.circulation_category_pid
            )
            text = '{0} {1} days'.format(
                _(cipo.get('name')), cipo.get('checkout_duration'))
            return text
        else:
            return ItemType.get_record_by_pid(
                self.circulation_category_pid).get('name')

    @property
    def patterns(self):
        """Shortcut for holdings patterns."""
        return self.get('patterns')

    @property
    def next_issue_display_text(self):
        """Display the text of the next predicted issue."""
        if self.patterns:
            return self._get_next_issue_display_text(self.patterns)

    @classmethod
    def _get_next_issue_display_text(cls, patterns):
        """Display the text for the next predicted issue.

        :param patterns: List of a valid holdings patterns.
        :returns: A display text of the next predicted issue.
        """
        issue_data = {}
        for pattern in patterns.get('values', []):
            pattern_name = pattern.get('name', '')
            level_data = {}
            for level in pattern.get('levels', []):
                text_value = level.get('next_value', level.get(
                    'starting_value', 1))
                mapping = level.get('mapping_values')
                if mapping:
                    text_value = mapping[text_value - 1]
                level_data.update({
                    level.get(
                        'number_name', level.get('list_name')
                    ): str(text_value)
                })
            issue_data[pattern_name] = level_data
        return Template(patterns.get('template')).render(**issue_data)

    def increment_next_prediction(self):
        """Increment next prediction."""
        if not self.patterns or not self.patterns.get('values'):
            return
        self['patterns'] = self._increment_next_prediction(self.patterns)

    @classmethod
    def _increment_next_prediction(cls, patterns):
        """Increment the next predicted issue.

        :param patterns: List of a valid holdings patterns.
        :returns: The updated patterns with the next issue.
        """
        for pattern in patterns.get('values', []):
            for level in reversed(pattern.get('levels', [])):
                max_value = level.get('completion_value')
                if level.get('mapping_values'):
                    max_value = len(level.get('mapping_values'))
                next_value = level.get('next_value', level.get(
                    'starting_value', 1))
                if max_value == next_value:
                    level['next_value'] = level.get(
                        'starting_value', 1)
                else:
                    level['next_value'] = next_value + 1
                    break
        return patterns

    def prediction_issues_preview(self, predictions=1):
        """Display preview of next predictions.

        :param predictions: Number of the next issues to predict.
        :returns: An array of issues display text.
        """
        text = []
        if self.patterns and self.patterns.get('values'):
            patterns = deepcopy(self.patterns)
            for r in range(predictions):
                text.append(self._get_next_issue_display_text(patterns))
                patterns = self._increment_next_prediction(patterns)
        return text

    @classmethod
    def prediction_issues_preview_for_pattern(
            cls, patterns, number_of_predictions=1, ):
        """Display preview of next predictions for a given pattern.

        :param predictions: Number of the next issues to predict.
        :param patterns: The patterns to predict.
        :returns: An array of issues display text.
        """
        text = []
        if patterns and patterns.get('values'):
            for r in range(number_of_predictions):
                text.append(Holding._get_next_issue_display_text(patterns))
                patterns = Holding._increment_next_prediction(patterns)
        return text


def get_standard_holding_pid_by_doc_location_item_type(
        document_pid, location_pid, item_type_pid):
    """Returns standard holding pid for document/location/item type."""
    result = HoldingsSearch().filter(
        'term',
        document__pid=document_pid
    ).filter(
        'term',
        holdings_type='standard'
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


def get_holdings_by_document_item_type(
        document_pid, item_type_pid):
    """Returns holding locations for document/item type."""
    results = HoldingsSearch().filter(
        'term',
        document__pid=document_pid
    ).filter(
        'term',
        circulation_category__pid=item_type_pid
    ).source(['pid']).scan()
    return [Holding.get_record_by_pid(result.pid) for result in results]


def create_holding(
        document_pid=None, location_pid=None, item_type_pid=None,
        electronic_location=None, holdings_type=None, patterns=None):
    """Create a new holding."""
    if not (document_pid and location_pid and item_type_pid):
        raise MissingRequiredParameterError(
            "One of the parameters 'document_pid' "
            "or 'location_pid' or 'item_type_pid' is required."
        )
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
    if electronic_location:
        data['electronic_location'] = [electronic_location]
    if not holdings_type:
        holdings_type = 'standard'
    data['holdings_type'] = holdings_type
    if patterns and holdings_type == 'serial':
        data['patterns'] = patterns
    record = Holding.create(
        data, dbcommit=True, reindex=True, delete_pid=True)
    return record.get('pid')


class HoldingsIndexer(IlsRecordsIndexer):
    """Holdings indexing class."""

    record_cls = Holding

    def index(self, record):
        """Indexing a holding record."""
        return_value = super(HoldingsIndexer, self).index(record)
        # current_search.flush_and_refresh(HoldingsSearch.Meta.index)
        return return_value
