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

"""Holdings records."""
from __future__ import absolute_import, print_function

from builtins import classmethod
from copy import deepcopy
from datetime import datetime
from functools import partial

from dateutil.relativedelta import relativedelta
from flask import current_app
from flask_babelex import gettext as _
from invenio_search import current_search
from invenio_search.api import RecordsSearch
from jinja2 import Template

from rero_ils.modules.items.models import ItemIssueStatus

from .models import HoldingIdentifier
from ..api import IlsRecord, IlsRecordsIndexer
from ..documents.api import Document
from ..errors import MissingRequiredParameterError, RegularReceiveNotAllowed
from ..fetchers import id_fetcher
from ..items.api import Item, ItemsSearch
from ..locations.api import Location
from ..minters import id_minter
from ..organisations.api import Organisation
from ..providers import Provider
from ..utils import extracted_data_from_ref, get_ref_for_pid, \
    get_schema_for_resource

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
        fields = ('*', )
        facets = {}

        default_filter = None

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
    # interval definitions for pattern frequencies
    # the RDA Frequencies are available here:
    # http://www.rdaregistry.info/termList/frequency/
    frequencies = {
        'rdafr:1001': relativedelta(days=1),  # Daily
        'rdafr:1002': relativedelta(days=2, hours=8),  # Three times a week
        'rdafr:1003': relativedelta(weeks=2),  # Biweekly
        'rdafr:1004': relativedelta(weeks=1),  # Weekly
        'rdafr:1005': relativedelta(days=3, hours=12),  # Semiweekly
        'rdafr:1006': relativedelta(days=10),  # Three times a month
        'rdafr:1007': relativedelta(months=2),  # Bimonthly
        'rdafr:1008': relativedelta(months=1),  # Monthly
        'rdafr:1009': relativedelta(days=15),  # Semimonthly
        'rdafr:1010': relativedelta(months=3),  # Quarterly
        'rdafr:1011': relativedelta(months=4),  # Three times a year
        'rdafr:1012': relativedelta(months=6),  # Semiannual
        'rdafr:1013': relativedelta(years=1),  # Annual
        'rdafr:1014': relativedelta(years=2),  # Biennial
        'rdafr:1015': relativedelta(years=3)  # Triennial
    }

    def extended_validation(self, **kwargs):
        """Add additional record validation.

        Ensures that holdings of type serials are created only on
        journal documents i.e. serial mode_of_issuance main_type of documents.

        Ensures that holdings of type electronic are created only on
        ebooks documents i.e. harvested documents.

        Ensures that for the holdings of type serials, if it has a regular
        frequency the next_expected_date should be given.

        :return: False if
            - document type is not journal and holding type is serial.
            - document type is journal and holding type is not serial.
            - document type is ebook and holding type is not electronic.
            - document type is not ebook and holding type is electronic.
            - holding type is serial and the next_expected_date
              is not given for a regular frequency.
            - if not a serial holdings contain one of optional serials fields.
            - if notes array has multiple notes with same type
        """
        document_pid = extracted_data_from_ref(
            self.get('document').get('$ref'))
        document = Document.get_record_by_pid(document_pid)
        if not document:
            return _('Document does not exist {pid}.'.format(pid=document_pid))
        is_serial = self.holdings_type == 'serial'
        if is_serial:
            patterns = self.get('patterns', {})
            if patterns and \
                patterns.get('frequency') != 'rdafr:1016' \
                    and not patterns.get('next_expected_date'):
                return _(
                    'Must have next expected date for regular frequencies.')
        is_electronic = self.holdings_type == 'electronic'
        is_issuance = \
            document.get('issuance', {}).get('main_type') == 'rdami:1003'
        if (is_serial and not is_issuance) \
                or (document.harvested ^ is_electronic):
            msg = _('Holding is not attached to the correct document type.'
                    ' document: {pid}')
            return _(msg.format(pid=document_pid))
        # the enumeration and chronology optional fields are only allowed for
        # serial holdings
        if not is_serial:
            fields = [
                'enumerationAndChronology', 'notes', 'index', 'missing_issues',
                'supplementaryContent'
            ]
            for field in fields:
                if self.get(field):
                    msg = _('{field} is allowed only for serial holdings')
                    return _(msg.format(field=field))
        # No multiple notes with same type
        note_types = [note.get('type') for note in self.get('notes', [])]
        if len(note_types) != len(set(note_types)):
            return _('Can not have multiple notes of same type.')

        return True

    @property
    def is_serial(self):
        """Shortcut to check if holding is a serial holding record."""
        document = Document.get_record_by_pid(self.document_pid).dumps()
        is_serial = self.holdings_type == 'serial'
        is_issuance = \
            document.get('issuance', {}).get('main_type') == 'rdami:1003'
        return is_serial and is_issuance

    @property
    def holding_is_serial(self):
        """Shortcut to check if holding is a serial holding record."""
        return self.holdings_type == 'serial'

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

    @property
    def notes(self):
        """Return notes related to this holding.

        :return an array of all notes related to the holding. Each note should
                have two keys : `type` and `content`.
        """
        return self.get('notes', [])

    def get_note(self, note_type):
        """Return an holdings note by its type.

        :param note_type: the type of note (see ``HoldingNoteTypes``)
        :return the content of the note, None if note type is not found
        """
        notes = [note.get('content') for note in self.notes
                 if note.get('type') == note_type]
        return next(iter(notes), None)

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
    def get_holdings_type_by_holding_pid(cls, holding_pid):
        """Returns holdings type for a holding pid."""
        holding = cls.get_record_by_pid(holding_pid)
        if holding:
            return holding.holdings_type
        return None

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
            item = Item.get_record_by_pid(item_pid)
            if item.issue_status != ItemIssueStatus.DELETED:
                yield item

    def get_number_of_items(self):
        """Get holding number of items."""
        results = ItemsSearch().filter(
            'term', holding__pid=self.pid).source().count()
        return results

    def get_links_to_me(self):
        """Get links that can block the holding deletion.

        Attached items to a holding record blocks the deletion.

        :return: a list of records links to the holding record.
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
        from ..circ_policies.api import CircPolicy
        from ..item_types.api import ItemType
        from ..patrons.api import current_patron

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
            return self._get_next_issue_display_text(self.patterns)[0]

    @classmethod
    def _get_next_issue_display_text(cls, patterns):
        """Display the text for the next predicted issue.

        :param patterns: List of a valid holdings patterns.
        :return: A display text of the next predicted issue.
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
        next_expected_date = patterns.get('next_expected_date')
        return Template(patterns.get('template')).render(
            **issue_data), next_expected_date

    def increment_next_prediction(self):
        """Increment next prediction."""
        if not self.patterns or not self.patterns.get('values'):
            return
        self['patterns'] = self._increment_next_prediction(self.patterns)
        return self

    @classmethod
    def _increment_next_prediction(cls, patterns):
        """Increment the next predicted issue.

        Predicts the next value and next_expected_date for the given patterns.

        :param patterns: List of a valid holdings patterns.
        :return: The updated patterns with the next issue.
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
        frequency = patterns.get('frequency')
        if frequency:
            next_expected_date = datetime.strptime(
                patterns.get('next_expected_date'), '%Y-%m-%d')
            interval = cls.frequencies[frequency]
            next_expected_date = next_expected_date + interval
            patterns['next_expected_date'] = \
                next_expected_date.strftime('%Y-%m-%d')
        return patterns

    def prediction_issues_preview(self, predictions=1):
        """Display preview of next predictions.

        :param predictions: Number of the next issues to predict.
        :return: An array of issues display text.
        """
        text = []
        if self.patterns and self.patterns.get('values'):
            patterns = deepcopy(self.patterns)
            for r in range(predictions):
                issue, expected_date = self._get_next_issue_display_text(
                    patterns)
                issue_data = self._prepare_issue_data(issue, expected_date)
                text.append(issue_data)
                patterns = self._increment_next_prediction(patterns)
        return text

    @classmethod
    def prediction_issues_preview_for_pattern(
            cls, patterns, number_of_predictions=1, ):
        """Display preview of next predictions for a given pattern.

        :param predictions: Number of the next issues to predict.
        :param patterns: The patterns to predict.
        :return: An array of issues display text.
        """
        text = []
        if patterns and patterns.get('values'):
            for r in range(number_of_predictions):
                issue, expected_date = cls._get_next_issue_display_text(
                    patterns)
                issue_data = cls._prepare_issue_data(issue, expected_date)
                text.append(issue_data)
                patterns = Holding._increment_next_prediction(patterns)
        return text

    @staticmethod
    def _prepare_issue_data(issue, expected_date):
        """Prepare issue record.

        :param issue: The issue display text to prepare.
        :param expected_date: The issue expected_date to prepare.
        :return: The prepared issue data.
        """
        issue_data = {
            'issue': issue,
            'expected_date':  expected_date
        }
        return issue_data

    def _prepare_issue_record(
            self, item=None, issue_display=None, expected_date=None):
        """Prepare the issue record before creating the item."""
        data = {
            'issue': {
                'status': 'received',
                'received_date': datetime.now().strftime('%Y-%m-%d'),
                'expected_date': expected_date,
                'regular': True
            },
            'enumerationAndChronology': issue_display,
            'status': 'on_shelf'
        }
        if item:
            issue = item.pop('issue', None)
            if issue:
                data['issue'].update(issue)
            data.update(item)
        # ensure that we have the right item fields such as location,
        # and item_type and document.
        forced_data = {
            '$schema': get_schema_for_resource(Item),
            'acquisition_date': datetime.now().strftime('%Y-%m-%d'),
            'location': self.get('location'),
            'document': self.get('document'),
            'item_type': self.get('circulation_category'),
            'type': 'issue',
            'holding': {'$ref': get_ref_for_pid('hold', self.pid)},
            'organisation':
                {'$ref': get_ref_for_pid('org', self.organisation_pid)}
        }
        data.update(forced_data)

        return data

    def receive_regular_issue(self, item=None, dbcommit=False, reindex=False):
        """Receive the next expected regular issue for the holdings record."""
        # receive is allowed only on holdings of type serials and regular
        # frequency
        if self.holdings_type != 'serial' or self.get(
                'patterns', {}).get('frequency') == 'rdafr:1016':
            raise RegularReceiveNotAllowed()

        issue_display, expected_date = self._get_next_issue_display_text(
                    self.get('patterns'))

        data = self._prepare_issue_record(
            item=item, issue_display=issue_display,
            expected_date=expected_date)

        issue = Item.create(data=data, dbcommit=dbcommit, reindex=reindex)

        return issue


def get_holding_pid_by_doc_location_item_type(
        document_pid, location_pid, item_type_pid, holdings_type='standard'):
    """Returns standard holding pid for document/location/item type."""
    result = HoldingsSearch().filter(
        'term',
        document__pid=document_pid
    ).filter(
        'term',
        holdings_type=holdings_type
    ).filter(
        'term',
        circulation_category__pid=item_type_pid
    ).filter(
        'term',
        location__pid=location_pid
    ).source('pid').scan()
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
        electronic_location=None, holdings_type=None, patterns=None,
        enumerationAndChronology=None, supplementaryContent=None, index=None,
        missing_issues=None, call_number=None, second_call_number=None,
        notes=[]):
    """Create a new holdings record from a given list of fields.

    :param document_pid: the document pid.
    :param location_pid: the location pid.
    :param item_type_pid: the item type pid.
    :param electronic_location: the location for online items.
    :param holdings_type: the type of holdings record.
    :param patterns: the patterns and chronology for the holdings.
    :param enumerationAndChronology: the Enumeration and Chronology.
    :param supplementaryContent: the Supplementary Content.
    :param index: the index of the holdings.
    :param missing_issues: the missing issues.
    :param notes: the notes of the holdings record.
    :param call_number: the call_number of the holdings record.
    :param second_call_number: the second_call_number of the holdings record.
    :return: the created holdings record.
    """
    if not (document_pid and location_pid and item_type_pid):
        raise MissingRequiredParameterError(
            "One of the parameters 'document_pid' "
            "or 'location_pid' or 'item_type_pid' is required."
        )
    data = {}
    # add mandatory holdings fields
    data['$schema'] = get_schema_for_resource('hold')
    data['location'] = {'$ref': get_ref_for_pid('loc', location_pid)}
    data['circulation_category'] = {
        '$ref': get_ref_for_pid('itty', item_type_pid)}
    data['document'] = {'$ref': get_ref_for_pid('doc', document_pid)}

    if not holdings_type:
        holdings_type = 'standard'
    data['holdings_type'] = holdings_type

    # add optional holdings fields if given
    holdings_fields = [
        {'key': 'enumerationAndChronology', 'value': enumerationAndChronology},
        {'key': 'supplementaryContent', 'value': supplementaryContent},
        {'key': 'index', 'value': index},
        {'key': 'missing_issues', 'value': missing_issues},
        {'key': 'notes', 'value': notes},
        {'key': 'call_number', 'value': call_number},
        {'key': 'second_call_number', 'value': second_call_number}
    ]
    for field in holdings_fields:
        value = field['value']
        if value:
            data[field['key']] = field['value']

    if electronic_location:
        data['electronic_location'] = [electronic_location]

    if patterns and holdings_type == 'serial':
        data['patterns'] = patterns
    holding = Holding.create(
        data, dbcommit=True, reindex=True, delete_pid=True)
    return holding


class HoldingsIndexer(IlsRecordsIndexer):
    """Holdings indexing class."""

    record_cls = Holding

    def index(self, record):
        """Indexing a holding record."""
        return_value = super(HoldingsIndexer, self).index(record)
        # current_search.flush_and_refresh(HoldingsSearch.Meta.index)
        return return_value

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super(HoldingsIndexer, self).bulk_index(record_id_iterator,
                                                doc_type='hold')
