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

"""Holdings records."""
from __future__ import absolute_import, print_function

from builtins import classmethod
from copy import deepcopy
from datetime import datetime, timezone
from functools import partial

from dateutil.relativedelta import relativedelta
from elasticsearch_dsl import Q
from flask import current_app
from flask_babelex import gettext as _
from invenio_records_rest.utils import obj_or_import_string
from jinja2 import Environment

from rero_ils.modules.items.models import ItemIssueStatus

from .models import HoldingIdentifier, HoldingMetadata, HoldingTypes
from ..api import IlsRecord, IlsRecordError, IlsRecordsIndexer, \
    IlsRecordsSearch
from ..documents.api import Document
from ..errors import MissingRequiredParameterError, RegularReceiveNotAllowed
from ..fetchers import id_fetcher
from ..items.api import Item, ItemsSearch
from ..locations.api import Location
from ..minters import id_minter
from ..operation_logs.extensions import OperationLogObserverExtension
from ..organisations.api import Organisation
from ..providers import Provider
from ..record_extensions import OrgLibRecordExtension
from ..utils import extracted_data_from_ref, get_ref_for_pid, \
    get_schema_for_resource, sorted_pids
from ..vendors.api import Vendor
from ...filter import format_date_filter

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

# load jinja Environment
JINJA_ENV = Environment()
JINJA_ENV.filters['format_date_filter'] = format_date_filter


class HoldingsSearch(IlsRecordsSearch):
    """RecordsSearch for holdings."""

    class Meta:
        """Search only on holdings index."""

        index = 'holdings'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class Holding(IlsRecord):
    """Holding class."""

    _extensions = [
        OrgLibRecordExtension(),
        OperationLogObserverExtension()
    ]

    minter = holding_id_minter
    fetcher = holding_id_fetcher
    provider = HoldingProvider
    model_cls = HoldingMetadata
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

        Ensures that holdings of type standard are created only on
        non journal documents.

        Ensures that holdings of type electronic are created only on
        ebooks documents i.e. harvested documents.

        Ensures that for the holdings of type serials, if it has a regular
        frequency the next_expected_date should be given.

        :return: False if
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

        if self.is_serial:
            patterns = self.get('patterns', {})
            if patterns and \
                patterns.get('frequency') != 'rdafr:1016' \
                    and not patterns.get('next_expected_date'):
                return _(
                    'Must have next expected date for regular frequencies.')
        if document.harvested ^ self.is_electronic:
            msg = _('Electronic Holding is not attached to the correct \
                    document type. document: {pid}')
            return _(msg.format(pid=document_pid))
        # the enumeration and chronology optional fields are only allowed for
        # serial or electronic holdings
        if not self.is_serial ^ self.is_electronic:
            fields = [
                'enumerationAndChronology', 'notes', 'index', 'missing_issues',
                'supplementaryContent', 'acquisition_status',
                'acquisition_method', 'acquisition_expected_end_date',
                'general_retention_policy', 'completeness',
                'composite_copy_report', 'issue_binding'
            ]
            for field in fields:
                if self.get(field):
                    msg = _('{field} is allowed only for serial holdings')
                    return _(msg.format(field=field))
        # No multiple notes with same type
        note_types = [note.get('type') for note in self.get('notes', [])]
        if len(note_types) != len(set(note_types)):
            return _('Can not have multiple notes of the same type.')
        return True

    def delete(self, force=False, dbcommit=False, delindex=False):
        """Delete record and persistent identifier."""
        can, _ = self.can_delete
        if can:
            if self.is_serial:
                # Delete all attached items
                for item in self.get_all_items():
                    item.delete(
                        force=force, dbcommit=dbcommit, delindex=False)
            return super().delete(
                force=force, dbcommit=dbcommit, delindex=delindex)
        else:
            raise IlsRecordError.NotDeleted()

    @property
    def is_serial(self):
        """Shortcut to check if holding is a serial holding record."""
        return self.holdings_type == HoldingTypes.SERIAL

    @property
    def is_electronic(self):
        """Shortcut to check if holding is a electronic record."""
        return self.holdings_type == HoldingTypes.ELECTRONIC

    @property
    def holdings_type(self):
        """Shortcut to return the type of the holding."""
        return self.get('holdings_type')

    @property
    def document_pid(self):
        """Shortcut for document pid of the holding."""
        return extracted_data_from_ref(self.get('document'))

    @property
    def circulation_category_pid(self):
        """Shortcut for circulation_category pid of the holding."""
        return extracted_data_from_ref(self.get('circulation_category'))

    @property
    def location_pid(self):
        """Shortcut for location pid of the holding."""
        return extracted_data_from_ref(self.get('location'))

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
        if self.is_electronic:
            return True
        if self.get('_masked', False):
            return False
        return self._exists_available_child()

    @property
    def max_number_of_claims(self):
        """Shortcut to return the max_number_of_claims."""
        return self.get('patterns', {}).get('max_number_of_claims', 0)

    @property
    def days_before_first_claim(self):
        """Shortcut to return the days_before_first_claim."""
        return self.get('patterns', {}).get('days_before_first_claim', 0)

    @property
    def days_before_next_claim(self):
        """Shortcut to return the days_before_next_claim."""
        return self.get('patterns', {}).get('days_before_next_claim', 0)

    @property
    def vendor_pid(self):
        """Shortcut for vendor pid of the holding."""
        if self.get('vendor'):
            return extracted_data_from_ref(self.get('vendor'))

    @property
    def vendor(self):
        """Shortcut to return the vendor record."""
        if self.vendor_pid:
            return Vendor.get_record_by_pid(self.vendor_pid)

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

    def _exists_available_child(self):
        """Check if at least one child of this holding is available."""
        for pid in Item.get_items_pid_by_holding_pid(self.pid):
            item = Item.get_record_by_pid(pid)
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
        holding = cls.get_record_by_pid(holding_pid)
        return extracted_data_from_ref(holding.get('document'))

    @classmethod
    def get_holdings_type_by_holding_pid(cls, holding_pid):
        """Returns holdings type for a holding pid."""
        holding = cls.get_record_by_pid(holding_pid)
        if holding:
            return holding.holdings_type

    @classmethod
    def get_holdings_pid_by_document_pid(cls, document_pid, with_masked=True):
        """Returns holding pids attached for a given document pid."""
        es_query = HoldingsSearch()\
            .filter('term', document__pid=document_pid)\
            .source(['pid'])
        if not with_masked:
            es_query = es_query.filter(
                'bool', must_not=[Q('term', _masked=True)])
        for holding in es_query.scan():
            yield holding.pid

    @classmethod
    def get_holdings_pid_by_document_pid_by_org(cls, document_pid, org_pid,
                                                with_masked=True):
        """Returns holding pids attached for a given document pid."""
        es_query = HoldingsSearch()\
            .filter('term', document__pid=document_pid)\
            .filter('term', organisation__pid=org_pid)\
            .source(['pid'])
        if not with_masked:
            es_query = es_query.filter(
                'bool', must_not=[Q('term', _masked=True)])
        for holding in es_query.scan():
            yield holding.pid

    def get_items_filter_by_viewcode(self, viewcode):
        """Return items filter by view code."""
        items = [
            Item.get_record_by_pid(item_pid)
            for item_pid in Item.get_items_pid_by_holding_pid(self.get('pid'))
        ]
        if (viewcode != current_app.
                config.get('RERO_ILS_SEARCH_GLOBAL_VIEW_CODE')):
            org_pid = Organisation.get_record_by_viewcode(viewcode)['pid']
            return [item for item in items if item.organisation_pid == org_pid]
        return items

    @property
    def get_items(self):
        """Return standard items and received issues for a holding record."""
        for item_pid in Item.get_items_pid_by_holding_pid(self.pid):
            if item := Item.get_record_by_pid(item_pid):
                if not item.issue_status or \
                        item.issue_status == ItemIssueStatus.RECEIVED:
                    # inherit holdings first call#
                    # for issues with no 1st call#.
                    if call_number := item.issue_inherited_first_call_number:
                        item['call_number'] = call_number
                    yield item

    def get_all_items(self):
        """Return all items a holding record."""
        for item_pid in Item.get_items_pid_by_holding_pid(self.pid):
            yield Item.get_record_by_pid(item_pid)

    def get_links_to_me(self, get_pids=False):
        """Record links.

        :param get_pids: if True list of linked pids
                         if False count of linked records
        """
        links = {}
        query = ItemsSearch().filter('term', holding__pid=self.pid)
        if get_pids:
            items = sorted_pids(query)
        else:
            items = query.count()
        # get number of attached items
        if items:
            links['items'] = items
        return links

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        cannot_delete = {}
        if self.is_serial:
            # Find out if we can delete all items
            not_deleteable_items = [
                item for item in self.get_items if item.reasons_not_to_delete()
            ]
            if not_deleteable_items:
                count = len(not_deleteable_items)
                cannot_delete['others'] = {
                    _('has {count} items with loan attached'.format(
                        count=count)): count}
        else:
            links = self.get_links_to_me()
            if links:
                cannot_delete['links'] = links
        return cannot_delete

    def get_holding_loan_conditions(self):
        """Returns loan conditions for a given holding."""
        from ..circ_policies.api import CircPolicy
        from ..item_types.api import ItemType
        from ..patrons.api import current_patrons

        def find_patron(organisation_pid):
            for ptrn in current_patrons:
                if ptrn.organisation_pid == organisation_pid:
                    return ptrn

        patron = find_patron(self.organisation_pid)
        if patron:
            cipo = CircPolicy.provide_circ_policy(
                self.organisation_pid,
                self.library_pid,
                patron.patron_type_pid,
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

    def get_location(self):
        """Shortcut to the location of holding."""
        return Location.get_record_by_pid(self.location_pid)

    def can(self, action, **kwargs):
        """Check if a specific action is allowed on this holding.

        :param action : the action to check as HoldingCirculationAction part
        :param kwargs : all others named arguments useful to check
        :return a tuple with True|False to know if the action is possible and
                a list of reasons to disallow if False.
        """
        can, reasons = True, []
        actions = current_app.config\
            .get('HOLDING_CIRCULATION_ACTIONS_VALIDATION', {})
        for func_name in actions['request']:
            class_name = func_name.__self__.__name__
            func_callback = obj_or_import_string(func_name)
            func_can, func_reasons = func_callback(self, **kwargs)
            reasons += func_reasons
            can = can and func_can
        return can, reasons

    @classmethod
    def can_request(cls, holding, **kwargs):
        """Check if holding can be requested depending on type.

        :param holding : the holding to check
        :param kwargs : addition arguments
        :return a tuple with True|False and reasons to disallow if False.
        """
        if holding and not holding.is_serial:
            return False, [_('Only serial holdings can be requested.')]
        return True, []

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

        # TODO: inform the PO about the use of filter format_date_filter
        # for additional manipulation of the expected date
        tmpl = JINJA_ENV.from_string(patterns.get('template'))

        next_expected_date = patterns.get('next_expected_date')
        # send the expected date info with the issue data
        expected_date = datetime.strptime(next_expected_date, '%Y-%m-%d')
        issue_data['next_expected_date'] = next_expected_date
        issue_data['expected_date'] = {
                    'day': expected_date.day,
                    'month': expected_date.month,
                    'year': expected_date.year
                }
        return tmpl.render(**issue_data), next_expected_date

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
        return {'issue': issue, 'expected_date': expected_date}

    def _prepare_issue_record(
            self, item=None, issue_display=None, expected_date=None):
        """Prepare the issue record before creating the item."""
        data = {
            'issue': {
                'status': ItemIssueStatus.RECEIVED,
                'status_date': datetime.now(timezone.utc).isoformat(),
                'received_date': datetime.now().strftime('%Y-%m-%d'),
                'expected_date': expected_date,
                'regular': True
            },
            'enumerationAndChronology': issue_display,
            'status': 'on_shelf'
        }
        if item:
            if issue := item.pop('issue', None):
                data['issue'].update(issue)
            data.update(item)
        # ensure that we have the right item fields such as location,
        # and item_type and document.
        forced_data = {
            '$schema': get_schema_for_resource(Item),
            'organisation': self.get('organisation'),
            'library': self.get('library'),
            'location': self.get('location'),
            'document': self.get('document'),
            'item_type': self.get('circulation_category'),
            'type': 'issue',
            'holding': {'$ref': get_ref_for_pid('hold', self.pid)}
        }
        data.update(forced_data)
        return data

    def receive_regular_issue(self, item=None, dbcommit=False, reindex=False):
        """Receive the next expected regular issue for the holdings record."""
        # receive is allowed only on holdings of type serials with a regular
        # frequency
        if self.holdings_type != HoldingTypes.SERIAL \
           or self.get('patterns', {}).get('frequency') == 'rdafr:1016':
            raise RegularReceiveNotAllowed()

        issue_display, expected_date = self._get_next_issue_display_text(
                    self.get('patterns'))
        data = self._prepare_issue_record(
            item=item,
            issue_display=issue_display,
            expected_date=expected_date
        )
        return Item.create(data=data, dbcommit=dbcommit, reindex=reindex)


def get_holding_pid_by_doc_location_item_type(
        document_pid, location_pid, item_type_pid, holdings_type='standard'):
    """Returns standard holding pid for document/location/item type."""
    result = HoldingsSearch() \
        .filter('term', document__pid=document_pid) \
        .filter('term', holdings_type=holdings_type) \
        .filter('term', circulation_category__pid=item_type_pid) \
        .filter('term', location__pid=location_pid) \
        .source('pid') \
        .scan()
    try:
        return next(result).pid
    except StopIteration:
        return None


def get_holdings_by_document_item_type(
        document_pid, item_type_pid):
    """Returns holding locations for document/item type."""
    results = HoldingsSearch() \
        .params(preserve_order=True)\
        .filter('term', document__pid=document_pid) \
        .filter('term', circulation_category__pid=item_type_pid) \
        .sort({'pid': {"order": "asc"}}) \
        .source(['pid']) \
        .scan()
    return [Holding.get_record_by_pid(result.pid) for result in results]


def create_holding(
        document_pid=None, location_pid=None, item_type_pid=None,
        electronic_location=None, holdings_type=HoldingTypes.STANDARD,
        patterns=None, enumerationAndChronology=None,
        supplementaryContent=None, index=None, missing_issues=None,
        call_number=None, second_call_number=None, notes=None, vendor_pid=None,
        acquisition_status=None, acquisition_expected_end_date=None,
        acquisition_method=None, general_retention_policy=None,
        completeness=None, composite_copy_report=None, issue_binding=None,
        masked=False):
    """Create a new holdings record from a given list of fields.

    :param document_pid: the document pid.
    :param location_pid: the location pid.
    :param item_type_pid: the item type pid.
    :param electronic_location: the location for online items.
    :param holdings_type: the type of holdings record (default is 'standard')
    :param patterns: the patterns and chronology for the holdings.
    :param enumerationAndChronology: the Enumeration and Chronology.
    :param supplementaryContent: the Supplementary Content.
    :param index: the index of the holdings.
    :param missing_issues: the missing issues.
    :param notes: the notes of the holdings record.
    :param call_number: the call_number of the holdings record.
    :param second_call_number: the second_call_number of the holdings record.
    :param vendor_pid: the vendor of the holdings record.
    :param acquisition_status: the holdings acquisition_status.
    :param acquisition_expected_end_date: the acquisition_expected_end_date.
    :param acquisition_method: the acquisition_method.
    :param general_retention_policy: general_retention_policy.
    :param completeness: completeness.
    :param composite_copy_report: composite_copy_report.
    :param issue_binding: issue_binding.
    :param masked: holdings masking.
    :return: the created holdings record.
    """
    if not (document_pid and location_pid and item_type_pid):
        raise MissingRequiredParameterError(
            "One of the parameters 'document_pid' "
            "or 'location_pid' or 'item_type_pid' is required."
        )
    data = {
        '$schema': get_schema_for_resource('hold'),
        '_masked': masked,
        'holdings_type': holdings_type,
        'location': {
            '$ref': get_ref_for_pid('loc', location_pid)
        },
        'circulation_category': {
            '$ref': get_ref_for_pid('itty', item_type_pid)
        },
        'document': {
            '$ref': get_ref_for_pid('doc', document_pid)
        },
        'enumerationAndChronology': enumerationAndChronology,
        'supplementaryContent': supplementaryContent,
        'index': index,
        'missing_issues': missing_issues,
        'notes': notes,
        'call_number': call_number,
        'second_call_number': second_call_number,
        'acquisition_status': acquisition_status,
        'acquisition_method': acquisition_method,
        'completeness': completeness,
        'issue_binding': issue_binding,
        'composite_copy_report': composite_copy_report,
        'general_retention_policy': general_retention_policy,
        'acquisition_expected_end_date': acquisition_expected_end_date,
    }
    data = {k: v for k, v in data.items() if v}  # clean data from None/empty
    if electronic_location:
        data['electronic_location'] = [electronic_location]
    if vendor_pid:
        data['vendor'] = {'$ref': get_ref_for_pid('vndr', vendor_pid)}
    if patterns and holdings_type == HoldingTypes.SERIAL:
        data['patterns'] = patterns
    return Holding.create(
        data,
        dbcommit=True,
        reindex=True,
        delete_pid=True
    )


class HoldingsIndexer(IlsRecordsIndexer):
    """Holdings indexing class."""

    record_cls = Holding

    def index(self, record):
        """Indexing a holding record.

        Parent document is indexed as well.
        """
        return_value = super().index(record)
        document = Document.get_record_by_pid(record.document_pid)
        document.reindex()
        return return_value

    def delete(self, record):
        """Delete a record.

        :param record: Record instance.
        """
        # Delete all attached items
        if record.is_serial:
            query = ItemsSearch().filter('term', holding__pid=record.pid)
            query.delete()
            ItemsSearch.flush_and_refresh()
        document = Document.get_record_by_pid(record.document_pid)
        return_value = super().delete(record)
        document.reindex()
        return return_value

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='hold')
