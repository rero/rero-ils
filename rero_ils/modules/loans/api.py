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

"""API for manipulating Loans."""
import math
from bisect import bisect_right
from datetime import datetime, timedelta, timezone

import ciso8601
from dateutil.relativedelta import relativedelta
from elasticsearch_dsl import A, Q
from flask import current_app
from flask_babelex import gettext as _
from invenio_circulation.errors import MissingRequiredParameterError
from invenio_circulation.pidstore.fetchers import loan_pid_fetcher
from invenio_circulation.pidstore.minters import loan_pid_minter
from invenio_circulation.pidstore.providers import CirculationLoanIdProvider
from invenio_circulation.proxies import current_circulation
from invenio_circulation.search.api import search_by_patron_item_or_document
from invenio_circulation.utils import str2datetime
from invenio_jsonschemas import current_jsonschemas

from rero_ils.modules.circ_policies.api import DUE_SOON_REMINDER_TYPE, \
    OVERDUE_REMINDER_TYPE, CircPolicy

from .extensions import CirculationDatesExtension
from .models import LoanAction, LoanState
from ..api import IlsRecord, IlsRecordError, IlsRecordsIndexer, \
    IlsRecordsSearch
from ..errors import NoCirculationActionIsPermitted
from ..items.models import ItemStatus
from ..items.utils import item_pid_to_object
from ..libraries.api import LibrariesSearch, Library
from ..locations.api import Location, LocationsSearch
from ..notifications.api import Notification, NotificationsSearch
from ..notifications.dispatcher import Dispatcher as NotificationDispatcher
from ..notifications.models import NotificationType
from ..patron_transactions.api import PatronTransactionsSearch
from ..patrons.api import Patron, PatronsSearch
from ..utils import date_string_to_utc, get_ref_for_pid


class LoansSearch(IlsRecordsSearch):
    """Libraries search."""

    class Meta:
        """Meta class."""

        index = 'loans'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class Loan(IlsRecord):
    """Loan class."""

    minter = loan_pid_minter
    fetcher = loan_pid_fetcher
    provider = CirculationLoanIdProvider
    pid_field = 'pid'
    _schema = 'loans/loan-ils-v0.0.1.json'
    pids_exist_check = {
        'not_required': {
            'org': 'organisation',
            'item': 'item'
        }
    }
    DATE_FIELDS = []

    DATETIME_FIELDS = [
        "end_date",
        "request_expire_date",
        "request_start_date",
        "start_date",
        "transaction_date"
    ]
    # Invenio Records extensions
    _extensions = [
        CirculationDatesExtension()
    ]

    def __init__(self, data, model=None):
        """Loan init."""
        super().__init__(data, model)

    @classmethod
    def can_extend(cls, item, **kwargs):
        """Loan can extend."""
        from rero_ils.modules.loans.utils import extend_loan_data_is_valid
        loan = kwargs.get('loan')
        if loan is None:  # try to load the loan from kwargs
            loan, _unused_data = item.prior_extend_loan_actions(**kwargs)
            if loan is None:  # not relevant method :: return True
                return True, []
        if loan.get('state') != LoanState.ITEM_ON_LOAN:
            return False, [_('The loan cannot be extended')]
        # The parameters for the renewal is calculated based on the transaction
        # library and not the owning library.
        transaction_library_pid = Location\
            .get_record_by_pid(loan['transaction_location_pid'])\
            .get_library().get('pid')

        patron = Patron.get_record_by_pid(loan.get('patron_pid'))
        cipo = CircPolicy.provide_circ_policy(
            item.organisation_pid,
            transaction_library_pid,
            patron.patron_type_pid,
            item.item_type_circulation_category_pid
        )
        extension_count = loan.get('extension_count', 0)
        if not (cipo.get('number_renewals', 0) > 0 and
                extension_count < cipo.get('number_renewals', 0) and
                extend_loan_data_is_valid(
                    loan.get('end_date'),
                    cipo.get('renewal_duration'),
                    transaction_library_pid
               )):
            return False, [_('Circulation policies disallows the operation.')]
        if item.number_of_requests():
            return False, [_('A pending request exists on this item.')]
        return True, []

    def action_required_params(self, action=None):
        """List of required parameters for circulation actions."""
        shared_params = [
            'transaction_location_pid',
            'transaction_user_pid',
        ]
        params = {
            'request': [
                'item_pid',
                'pickup_location_pid',
                'patron_pid',
            ],
            'cancel_loan': [
                'pid'
            ],
            'checkin': [
                'pid'
            ],
            'validate_request': [
                'pid'
            ],
            'checkout': [
                'item_pid',
                'patron_pid',
                'transaction_location_pid',
                'transaction_user_pid',
            ],
            'extend_loan': [
                'item_pid'
            ],
            'receive': []
        }

        return params.get(action) + shared_params

    def check_required_params(self, action, **kwargs):
        """Validate that all required parameters are given for an action."""
        # TODO: do we need to check also the parameter exist and its value?
        required_params = self.action_required_params(action=action)
        missing_params = set(required_params) - set(kwargs)
        if missing_params:
            message = f'Parameters {missing_params} are required'
            raise MissingRequiredParameterError(description=message)

    def update_pickup_location(self, pickup_location_pid):
        """Update the pickup location for a loan.

        Pickup location update is only possible for pending and in_transit
        to house loans.

        :param pickup_location_pid: The new pickup_location_pid.
        :return: the new updated loan.
        """
        if self['state'] not in [
                LoanState.PENDING, LoanState.ITEM_IN_TRANSIT_FOR_PICKUP]:
            raise NoCirculationActionIsPermitted(
                'No circulation action is permitted')

        self['pickup_location_pid'] = pickup_location_pid
        return self.update(self, dbcommit=True, reindex=True)

    @classmethod
    def create(cls, data, id_=None, delete_pid=True,
               dbcommit=False, reindex=False, **kwargs):
        """Create the loan record.

        :param cls - class object
        :param data - dictionary representing a loan record.
        :param id_ - UUID, it would be generated if it is not given.
        :param delete_pid - remove the pid present in the data if True,
        :param dbcommit - commit the changes in the db after the creation.
        :param reindex - index the record after the creation.
        """
        data['$schema'] = current_jsonschemas.path_to_url(cls._schema)
        # default state assignment
        data.setdefault(
            'state',
            current_app.config['CIRCULATION_LOAN_INITIAL_STATE']
        )
        if delete_pid and data.get(cls.pid_field):
            del(data[cls.pid_field])
        cls._loan_build_org_ref(data)
        # set the field to_anonymize
        data['to_anonymize'] = \
            cls.can_anonymize(loan_data=data) and not data.get('to_anonymize')

        if not data.get('state'):
            data['state'] = LoanState.CREATED
        record = super(Loan, cls).create(
            data=data, id_=id_, delete_pid=delete_pid, dbcommit=dbcommit,
            reindex=reindex, **kwargs)
        return record

    def update(self, data, commit=False, dbcommit=False, reindex=False):
        """Update loan record."""
        self._loan_build_org_ref(data)
        # set the field to_anonymize
        if not self.get('to_anonymize') and Loan.can_anonymize(loan_data=data):
            data['to_anonymize'] = True
        super().update(
            data=data, commit=commit, dbcommit=dbcommit, reindex=reindex)
        return self

    def anonymize(self, loan, commit=True, dbcommit=False, reindex=False):
        """Anonymize a loan.

        :param loan: the loan to update.
        :param dbcommit - commit the changes in the db after the creation.
        :param reindex - index the record after the creation.
        """
        from rero_ils.modules.loans.logs.api import LoanOperationLog
        loan['to_anonymize'] = True
        try:
            super().update(loan, commit, dbcommit, reindex)
            # Anonymize loan operation logs
            LoanOperationLog.anonymize_logs(loan['pid'])
        except Exception as err:
            current_app.logger.error(
                f'Can not anonymize loan: {loan.get("pid")} {err}')
        return self

    def date_fields2datetime(self):
        """Convert string datetime fields to Python datetime."""
        for field in self.DATE_FIELDS + self.DATETIME_FIELDS:
            if field in self:
                self[field] = str2datetime(self[field])

    def date_fields2str(self):
        """Convert Python datetime fields to string."""
        for field in self.DATE_FIELDS:
            if field in self:
                self[field] = self[field].date().isoformat()
        for field in self.DATETIME_FIELDS:
            if field in self:
                self[field] = self[field].isoformat()

    @classmethod
    def requested_loans_to_validate(cls, library_pid):
        """Get Requests to be validated.

        :param library_pid: the library pid.
        """
        from ..item_types.api import ItemTypesSearch
        from ..items.api import ItemsSearch

        # Proxy record
        patrons = {}
        locations = {}
        libraries = {}
        holdings = {}
        items = {}
        item_types = {}

        def loans_pending():
            """Get pending loans."""
            return LoansSearch()\
                .params(preserve_order=True)\
                .filter('term', state=LoanState.PENDING)\
                .filter('term', library_pid=library_pid)\
                .sort({'_created': {"order": 'asc'}})\
                .source(includes=[
                    'pid', 'transaction_date', 'item_pid', 'patron_pid',
                    'document_pid', 'library_pid', 'state',
                    'transaction_location_pid', 'pickup_location_pid'
                ])\
                .scan()

        def patron_by_pid(pid, known_patrons):
            """Get patron by pid.

            :param pid: the patron pid.
            :param known_patrons: already known patrons.
            :return the corresponding patron.
            """
            fields = ['pid', 'first_name', 'last_name', 'patron.barcode']
            if pid not in known_patrons:
                results = PatronsSearch()\
                    .filter('term', pid=pid)\
                    .source(includes=fields)\
                    .execute()
                hit = next(iter(results or []), None)
                if hit:
                    known_patrons[pid] = hit.to_dict()
            return known_patrons.get(pid, {})

        def location_by_pid(pid, known_locations):
            """Get location by pid.

            :param pid: the location pid.
            :param known_locations: already known locations.
            :return the corresponding location.
            """
            fields = ['pid', 'name', 'library', 'pickup_name']
            if pid not in known_locations:
                results = LocationsSearch()\
                    .filter('term', pid=pid)\
                    .source(includes=fields)\
                    .execute()
                hit = next(iter(results or []), None)
                if hit:
                    data = hit.to_dict()
                    known_locations[pid] = {k: v for k, v in data.items() if v}
            return known_locations.get(pid, {})

        def library_name_by_pid(pid, known_libraries):
            """Get library name by pid.

            :param pid: the library pid.
            :param known_libraries: already known libraries.
            :return the corresponding library.
            """
            if pid not in known_libraries:
                results = LibrariesSearch()\
                    .filter('term', pid=pid)\
                    .source(includes='name')\
                    .execute()
                hit = next(iter(results or []), None)
                if hit:
                    known_libraries[pid] = hit.name
            return known_libraries.get(pid, {})

        def holding_by_pid(pid, known_holdings):
            """Get holdings by pid.

            :param pid: the holdings pid.
            :param known_holdings: already known holdings.
            :return the corresponding holdings.
            """
            from ..holdings.api import HoldingsSearch
            if pid not in known_holdings:
                results = HoldingsSearch()\
                    .filter('term', pid=pid)\
                    .source(includes='call_number')\
                    .execute()
                hit = next(iter(results or []), None)
                if hit:
                    known_holdings[pid] = hit.to_dict()
            return known_holdings.get(pid, {})

        def item_by_pid(pid, known_items):
            """Get item by pid.

            :param pid: the item pid.
            :param known_items: already known items.
            :return the corresponding item.
            """
            fields = ['pid', 'barcode', 'call_number',
                      'second_call_number', 'library', 'location',
                      'temporary_item_type', 'holding']
            if pid not in known_items:
                results = ItemsSearch()\
                    .filter('term', pid=pid)\
                    .filter('term', status=ItemStatus.ON_SHELF)\
                    .source(includes=fields)\
                    .execute()
                known_items[pid] = next(iter(results or []), None)
            return known_items.get(pid, {})

        def item_type_by_pid(pid, known_ittys):
            """Get item type by pid.

            :param pid: the item_type pid.
            :param known_ittys: already known item types
            :return the corresponding item type
            """
            if pid not in known_ittys:
                results = ItemTypesSearch()\
                    .filter('term', pid=pid)\
                    .filter('term', negative_availability=False)\
                    .execute()
                known_ittys[pid] = next(iter(results or []), None)
            return known_ittys.get(pid, {})

        metadata = []
        item_pids = []

        loans = loans_pending()
        for loan in loans:
            item_pid = loan['item_pid']['value']
            item = item_by_pid(item_pid, items)
            if item:
                add = True
                if 'temporary_item_type' in item:
                    itty_pid = item['temporary_item_type']['pid']
                    add = item_type_by_pid(itty_pid, item_types) is not None
                if add and item_pid not in item_pids:
                    item_pids.append(item_pid)
                    item_data = item.to_dict()
                    loan_data = loan.to_dict()
                    if 'call_number' not in item_data:
                        holding = holding_by_pid(
                            item['holding']['pid'],
                            holdings
                        )
                        if 'call_number' in holding:
                            item_data['call_number'] = holding['call_number']
                    item_data['library']['name'] = library_name_by_pid(
                        item_data['library']['pid'],
                        libraries
                    )
                    item_data['location']['name'] = location_by_pid(
                        item_data['location']['pid'],
                        locations
                    )['name']
                    patron_data = patron_by_pid(loan_data['patron_pid'],
                                                patrons)
                    loan_data['patron'] = {
                        'barcode': patron_data['patron']['barcode'],
                        'name': f'{patron_data["last_name"]}, '
                                f'{patron_data["first_name"]}'
                    }
                    loan_data['pickup_location'] = location_by_pid(
                        loan_data['pickup_location_pid'], locations)
                    loan_data['pickup_location']['library_name'] = \
                        library_name_by_pid(
                            loan_data['pickup_location']['library']['pid'],
                            libraries
                        )
                    metadata.append({
                        'item': item_data,
                        'loan': loan_data
                    })
        return metadata

    @classmethod
    def _loan_build_org_ref(cls, data):
        """Build $ref for the organisation of the Loan.

        :param data: data to add the organisation info.
        :returns: data with organisations informations.
        """
        from ..items.api import Item
        if not data.get('organisation'):
            item_pid = data.get('item_pid', {}).get('value')
            data['organisation'] = {'$ref': get_ref_for_pid(
                'org',
                Item.get_record_by_pid(item_pid).organisation_pid
            )}
        return data

    def is_loan_late(self):
        """Check if the loan due_date is over."""
        due_date = ciso8601.parse_datetime(self.end_date)
        return datetime.now(timezone.utc) > due_date

    def is_loan_overdue(self):
        """Check if the loan is overdue."""
        from .utils import get_circ_policy
        if self.state != LoanState.ITEM_ON_LOAN:
            return False

        circ_policy = get_circ_policy(self)
        now = datetime.now(timezone.utc)
        due_date = ciso8601.parse_datetime(self.end_date)
        days_after = circ_policy.initial_overdue_days
        if days_after and now > due_date + timedelta(days=days_after-1):
            return True
        return False

    def is_loan_due_soon(self, tstamp=None):
        """Check if the loan is due soon.

        :param tstamp: a timestamp to define the execution time of the function
                       Default to `datetime.now()`
        :returns: True if is due soon
        """
        date = tstamp or datetime.now(timezone.utc)
        due_soon_date = self.get('due_soon_date')
        """Check if a loan is due soon."""
        if due_soon_date:
            return ciso8601.parse_datetime(due_soon_date) <= date
        return False

    @property
    def request_creation_date(self):
        """Shortcut for request create date."""
        # TODO: remove this when the field request_creation_date is added.
        return self.created

    @property
    def pid(self):
        """Shortcut for pid."""
        return self.get('pid')

    @property
    def state(self):
        """Shortcut for state."""
        return self.get('state')

    @property
    def rank(self):
        """Shortcut for rank.

        Used by the sorted function
        """
        return self.get('rank')

    @property
    def transaction_date(self):
        """Shortcut for transaction date.

        Used by the sorted function
        """
        return self.get('transaction_date')

    @property
    def end_date(self):
        """Shortcut for end date.

        Used by the sorted function
        """
        return self.get('end_date')

    @property
    def overdue_date(self):
        """Get the date when the loan should be considerate as 'overdue'."""
        if self.end_date:
            d_after = date_string_to_utc(self.end_date) + timedelta(days=1)
            return datetime(
                year=d_after.year, month=d_after.month, day=d_after.day,
                tzinfo=timezone.utc
            )

    @property
    def item_pid(self):
        """Returns the item pid value."""
        return self.get('item_pid', {}).get('value', None)

    @property
    def item_pid_object(self):
        """Returns the loan item_pid object."""
        return self.get('item_pid', {})

    @property
    def patron_pid(self):
        """Shortcut for patron pid."""
        return self.get('patron_pid')

    @property
    def document_pid(self):
        """Shortcut for document pid."""
        return self.get('document_pid')

    @property
    def is_active(self):
        """Shortcut to check of loan is active."""
        states = current_app.config['CIRCULATION_STATES_LOAN_ACTIVE']
        if self.get('state') in states:
            return True
        return False

    @property
    def organisation_pid(self):
        """Get organisation pid for loan."""
        from ..items.api import Item
        item_pid = self.item_pid
        if item_pid:
            item = Item.get_record_by_pid(item_pid)
            return item.organisation_pid
        # return None
        raise IlsRecordError.PidDoesNotExist(
            self.provider.pid_type,
            'organisation_pid:item_pid'
        )

    @property
    def library_pid(self):
        """Get library PID regarding loan location."""
        return Location.get_record_by_pid(self.location_pid).library_pid

    @property
    def location_pid(self):
        """Get loan transaction_location PID or item owning location."""
        from ..items.api import Item
        location_pid = self.get('transaction_location_pid')
        item_pid = self.item_pid

        if not location_pid and item_pid:
            return Item.get_record_by_pid(item_pid).holding_location_pid
        elif location_pid:
            return location_pid
        return IlsRecordError.PidDoesNotExist(
            self.provider.pid_type,
            'library_pid'
        )

    @property
    def pickup_library(self):
        """Get the library pid related to the pickup location."""
        location_pid = self.pickup_location_pid
        if location_pid:
            return Location.get_record_by_pid(location_pid).get_library()

    @property
    def pickup_location_pid(self):
        """Get loan pickup_location PID."""
        return self.get('pickup_location_pid')

    @property
    def transaction_location_pid(self):
        """Get loan transaction_location PID."""
        return self.get('transaction_location_pid')

    @property
    def get_overdue_fees(self):
        """Get all overdue fees based based on incremental fees setting.

        :return An array of tuple. Each tuple are composed with two values :
                the fee amount and a related timestamp.
                Ex: [
                  (0.1, datetime.date('2021-01-28')),
                  (0.1, datetime.date('2021-01-29')),
                  (0.5, datetime.date('2021-01-30')),
                  ...
                ]
        """
        from .utils import get_circ_policy
        fees = []
        # if the loan isn't overdue, no need to continue.
        if not self.is_loan_overdue():
            return fees

        # find the circulation policy corresponding to the loan and check if
        # some 'overdue_fees' settings exists. If not, no need to continue.
        cipo = get_circ_policy(self)
        overdue_settings = cipo.get('overdue_fees')
        if overdue_settings is None:
            return fees

        # At this point, we know that we need to compute an overdue amount.
        # Initialize some useful variables to perform the job.
        loan_lib = Library.get_record_by_pid(self.library_pid)
        # add 1 day to end_date because the first overdue_date is next day
        # after the due date
        end_date = date_string_to_utc(self.end_date) + timedelta(days=1)
        total = 0
        max_overdue = overdue_settings.get('maximum_total_amount', math.inf)
        intervals = cipo.get_overdue_intervals()
        interval_lower_bounds = [inter['from'] for inter in intervals]

        # For each overdue day, we need to find the correct fee_amount to
        # charge. In the bellowed loop, `day_idx' is the day number from the
        # due date ; `day` is the datetime of this day

        for day_idx, day in enumerate(loan_lib.get_open_days(end_date), 1):
            # replace the hour to start of the day :: an overdue start at
            # at the beginning of the day
            day = day.replace(
                hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
            day = loan_lib.get_timezone().localize(day)
            # a) find the correct interval.
            # b) check the index found exist into intervals
            # c) check the upper limit of this interval is grower or equal
            #    to day index
            interval_idx = bisect_right(interval_lower_bounds, day_idx)-1
            if interval_idx == -1:
                continue
            if day_idx > intervals[interval_idx]['to']:
                continue
            # d) add the corresponding fee_amount to the fees array.
            # e) if maximum_overdue is reached, exit the loop
            fee_amount = intervals[interval_idx]['fee_amount']
            gap = round(max_overdue - total, 2)
            fee_amount = min(fee_amount, gap)
            total = round(math.fsum([total, fee_amount]), 2)
            fees.append((fee_amount, day))
            if max_overdue <= total:
                break
        return fees

    def dumps_for_circulation(self):
        """Dumps for circulation."""
        from ..items.api import Item
        loan = self.replace_refs()
        data = loan.dumps()
        patron = Patron.get_record_by_pid(loan['patron_pid'])

        # Add patron informations
        ptrn_data = patron.dumps()
        data['patron'] = {}
        data['patron']['barcode'] = ptrn_data['patron']['barcode']
        data['patron']['name'] = ', '.join((
            ptrn_data['last_name'], ptrn_data['first_name']))
        if loan.get('pickup_location_pid'):
            location = Location.get_record_by_pid(loan['pickup_location_pid'])
            data['pickup_location'] = {
                'name': location.get('name'),
                'library_name': location.get_library().get('name')
            }

        # Always add item destination readable informations if item state is
        # 'in transit' ; much more easier to know these informations for UI !
        item = Item.get_record_by_pid(self.item_pid)
        data['rank'] = item.patron_request_rank(patron)
        if item.status == ItemStatus.IN_TRANSIT:
            destination_loc_pid = item.location_pid
            if loan.get('state') == LoanState.ITEM_IN_TRANSIT_FOR_PICKUP:
                destination_loc_pid = self.get('pickup_location_pid')
            destination_loc = Location.get_record_by_pid(destination_loc_pid)
            destination_lib = destination_loc.get_library()
            data['item_destination'] = {
                'location_name': destination_loc.get('name'),
                'location_code': destination_loc.get('code'),
                'library_name': destination_lib.get('name'),
                'library_code': destination_lib.get('code')
            }
        return data

    def is_notified(self, notification_type=None, counter=0):
        """Check if a notification already exists for a loan by type."""
        trans_date = ciso8601.parse_datetime(self.get('transaction_date'))
        query_count = NotificationsSearch() \
            .filter('term', context__loan__pid=self.pid) \
            .filter('term', notification_type=notification_type) \
            .filter('range', creation_date={'gt': trans_date}) \
            .source().count()
        return query_count > counter

    def get_notification_candidates(self, trigger):
        """Get notification candidates to be created.

        This function will check the loan and return all possible notifications
        to be created related to it. In some case, a notification must be
        generated on an the basis of another loan than itself (in case of
        request).

        :param trigger: the fired action trigger (optional)
        :return a list of tuple. Each tuple represent a notification candidate.
                Each tuple is composed by 2 elements : the loan object, and the
                related notification type.
        """
        from ..items.api import Item
        candidates = []
        item = Item.get_record_by_pid(self.item_pid)
        # Get the list of requests pids for the related item and exclude myself
        # from the result list.
        requests = item.get_requests(output='pids')
        requests = [loan_pid for loan_pid in requests if loan_pid != self.pid]
        has_request = len(requests) > 0

        # AVAILABILITY NOTIFICATION
        #   If loan (items) just arrived at the library desk we can create
        #   an AVAILABILITY notification
        if self.state == LoanState.ITEM_AT_DESK:
            candidates.append((self, NotificationType.AVAILABILITY))

        # REQUEST & RECALL NOTIFICATION
        #   When a request is created on a item, the system create a 'pending'
        #   loan. If the corresponding item is checked-out, we can create a
        #   RECALL notification on it (ask the user to return the item because
        #   someone else requested it)
        if self.state == LoanState.PENDING and not has_request:
            # get the checked-out loan
            co_loan_pid = Item.get_loan_pid_with_item_on_loan(self.item_pid)
            # is the item on loan
            if co_loan_pid:
                co_loan = Loan.get_record_by_pid(co_loan_pid)
                if not co_loan.is_notified(NotificationType.RECALL):
                    candidates.append((co_loan, NotificationType.RECALL))
            elif not item.temp_item_type_negative_availability:
                # We could create a REQUEST notification to notify librarian
                # to prepare the item for a loan.
                candidates.append((self, NotificationType.REQUEST))

        # TRANSIT
        #   When the current loan (item) goes to transit and doesn't have any
        #   related request, we could create a TRANSIT_NOTICE notification to
        #   notify the transaction library to return the item to the owning
        #   library.
        if self.state == LoanState.ITEM_IN_TRANSIT_TO_HOUSE \
                and not has_request:
            candidates.append((self, NotificationType.TRANSIT_NOTICE))

        # BOOKING
        #   When the current loan (item) is checked-in and at least one request
        #   has been placed on the related item, we can create a BOOKING
        #   notification to notify the library to hold the item (at desk).
        if trigger == LoanAction.CHECKIN and has_request:
            candidates.append((self, NotificationType.BOOKING))
        return candidates

    def create_notification(self, trigger=None, _type=None, counter=0):
        """Creates a notification from base on a loan.

        :param trigger: circulation action trigger.
        :param _type: the notification type to create.
        :param counter: the reminder counter to use (for OVERDUE or DUE_SOON
                        notification)
        :return: the list of created notifications
        """
        from .utils import get_circ_policy
        types = [(self, t) for t in [_type] if t]
        notifications = []
        for loan, n_type in types or self.get_notification_candidates(trigger):
            create = True  # Should the notification actually be created.
            # Internal notification (library destination) should be directly
            # dispatched. Other notifications types could be asynchronously
            # processed (to save server response time).
            dispatch = n_type in NotificationType.INTERNAL_NOTIFICATIONS

            record = {
                'creation_date': datetime.now(timezone.utc).isoformat(),
                'notification_type': n_type,
                'context': {
                  'loan': {'$ref': get_ref_for_pid('loans', loan.pid)}
                }
            }
            # overdue + due_soon
            if n_type in NotificationType.REMINDERS_NOTIFICATIONS:
                # Do not recreate if an existing notification already exists.
                if loan.is_notified(n_type, counter):
                    create = False
                else:
                    # We only need to create a notification if a corresponding
                    # reminder exists into the linked cipo (we can't create a
                    # OVERDUE_NOTIFICATION#4 if the related cipo only define
                    # two overdue reminders.
                    cipo = get_circ_policy(loan)
                    reminder_type = DUE_SOON_REMINDER_TYPE
                    if n_type != NotificationType.DUE_SOON:
                        reminder_type = OVERDUE_REMINDER_TYPE
                    reminder = cipo.get_reminder(reminder_type, counter)
                    # Reminder does not exists on the circulation policy.
                    if not reminder:
                        create = False
                    else:
                        record['context']['reminder_counter'] = counter

            # create the notification and enqueue it.
            if create:
                notifications.append(self._create_notification_resource(
                    record,
                    dispatch=dispatch
                ))
        return notifications

    @classmethod
    def _create_notification_resource(cls, record, dispatch=False):
        """Create and dispatch notification if necessary.

        :param record: (dict) the notification data.
        :param dispatch: if True send the notification to the dispatcher.
        :return: the created `Notification` resource.
        """
        notification = Notification.create(
            data=record, dbcommit=True, reindex=True)
        if dispatch:
            NotificationDispatcher.dispatch_notifications(
                notification_pids=[notification.get('pid')]
            )
        return notification

    @classmethod
    def get_anonymized_candidates(cls):
        """Search for loans to anonymize.

        Depending of the related patron `keep_history` setting, there is two
        ways for searching loan candidates to:
        1) If the patron specifies to keep transaction history : we keep
           history for the 6 last months. After this delay, all loans will be
           anonymized anyway.
        2) If the patron doesn't specify to keep history : we can anonymize
           related loans except if they are not concluded than 3 months ago
           (we need to keep transactions for the last 3 months for circulation
           management).

        :return a generator of `Loan` candidate to anonymize.
        """
        three_month_ago = datetime.now() - relativedelta(months=3)
        six_month_ago = datetime.now() - relativedelta(months=6)

        patron_query = PatronsSearch().filter('bool', must_not=[
            Q('exists', field='keep_history'),
            Q('term', keep_history=True)
        ])
        anonym_patron_pids = [h.pid for h in patron_query.source('pid').scan()]

        query = LoansSearch() \
            .filter('terms', state=LoanState.CONCLUDED) \
            .filter('term', to_anonymize=False) \
            .filter('bool', should=[
                Q('range', transaction_date={'lt': six_month_ago}),
                (Q('terms', patron_pid=anonym_patron_pids) &
                 Q('range', transaction_date={'lt': three_month_ago}))
            ]) \
            .source(['pid'])
        for hit in query.scan():
            yield Loan.get_record_by_pid(hit.pid)

    @classmethod
    def concluded(cls, loan):
        """Check if loan is concluded.

        Loan is considered concluded if it has either ITEM_RETURNED or
        CANCELLED states and has no open patron_transactions.

        :param loan: the loan to check.
        :return True|False
        """
        return loan.get('state') in LoanState.CONCLUDED and\
            not loan_has_open_events(loan_pid=loan.get('pid'))

    @classmethod
    def age(cls, loan):
        """Return the age of a loan in days.

        The age of a loan is calculated based on the loan transaction date.

        :param loan: the loan to check.
        :return loan_age in number of days
        """
        transaction_date = ciso8601.parse_datetime(
            loan.get('transaction_date'))
        loan_age = datetime.utcnow() - transaction_date.replace(tzinfo=None)
        return loan_age.days

    @classmethod
    def can_anonymize(cls, loan_data=None, patron=None):
        """Check if a loan can be anonymized and excluded from loan searches.

        Loan can be anonymized if:
        1. it is concluded and 6 months old
        2. patron has the keep_history set to False and the loan is concluded.

        This method is class method because it needs to check the loan record
        during the loan.update process. this way, you can have access to the
        old and new version of the loan.

        :param loan_data: the loan data to check (could be a `Loan` or a dict).
        :param patron: the patron to check.
        :return True if the loan can be anonymized, False otherwise.
        """
        # CHECK #1 : Is the loan is concluded ?
        #   If the loan is still alive (item in loan, item requested), we can't
        #   anonymize it
        if not cls.concluded(loan_data):
            return False

        # CHECK #2 : is the loan is a old loan ?
        #   A concluded loan, older than a limit, could always be anonymized.
        #   The limit could be configure by 'RERO_ILS_ANONYMISATION_TIME_LIMIT'
        #   key into `config.py`.
        max_limit = current_app.config.get(
            'RERO_ILS_ANONYMISATION_MAX_TIME_LIMIT',
            math.inf
        )
        loan_age = cls.age(loan_data)
        if loan_age > max_limit:
            return True

        # CHECK #3 : is the loan is just concluded ?
        #   Circulation management and/or library manager needs to keep loan
        #   information for a delay (in days) after the concluded date anyway.
        min_limit = current_app.config.get(
            'RERO_ILS_ANONYMISATION_MIN_TIME_LIMIT',
            -math.inf
        )
        if loan_age < (min_limit + 1):
            return False

        # CHECK #4 : Check about patron preferences
        #   Patron could specify if it want keep transaction history or not
        patron_pid = loan_data.get('patron_pid')
        patron = patron or Patron.get_record_by_pid(patron_pid)
        keep_history = True
        if patron:
            keep_history = patron.user.profile.keep_history
        else:
            msg = f'Can not anonymize loan: {loan_data.get("pid")} ' \
                  f'no patron: {loan_data.get("patron_pid")}'
            current_app.logger.warning(msg)
        return not keep_history


def get_request_by_item_pid_by_patron_pid(item_pid, patron_pid):
    """Get pending, item_in_transit, item_at_desk loans for item, patron.

    :param item_pid: The item pid.
    :param patron_pid: The patron pid.
    :return: loans for given item and patron.
    """
    filter_states = [
        LoanState.PENDING,
        LoanState.ITEM_AT_DESK,
        LoanState.ITEM_IN_TRANSIT_FOR_PICKUP,
        LoanState.ITEM_IN_TRANSIT_TO_HOUSE
    ]
    return get_loans_by_item_pid_by_patron_pid(
        item_pid, patron_pid, filter_states)


def get_any_loans_by_item_pid_by_patron_pid(item_pid, patron_pid):
    """Get loans not ITEM_IN_TRANSIT_TO_HOUSE, CREATED for item, patron.

    :param item_pid: The item pid.
    :param patron_pid: The patron pid.
    :return: loans for given item and patron.
    """
    filter_states = [
        LoanState.PENDING,
        LoanState.ITEM_AT_DESK,
        LoanState.ITEM_IN_TRANSIT_FOR_PICKUP,
        LoanState.ITEM_ON_LOAN
    ]
    return get_loans_by_item_pid_by_patron_pid(
        item_pid, patron_pid, filter_states)


def get_loans_by_item_pid_by_patron_pid(item_pid, patron_pid,
                                        filter_states=None):
    """Get loans for item, patron according to the given filter_states.

    :param item_pid: The item pid.
    :param patron_pid: The patron pid.
    :param filter_states: states to use as a filter.
    :return: loans for given item and patron.
    """
    search = search_by_patron_item_or_document(
        item_pid=item_pid_to_object(item_pid),
        patron_pid=patron_pid,
        filter_states=filter_states,
    )
    search_result = search.execute()
    if search_result.hits:
        return search_result.hits.hits[0]['_source']
    return {}


def get_loans_stats_by_patron_pid(patron_pid):
    """Search loans for patron and aggregate result on loan state.

    :param patron_pid: The patron pid
    :return: a dict with loans state as key, number of loans as value
    """
    agg = A('terms', field='state')
    search = search_by_patron_item_or_document(patron_pid=patron_pid)
    search.aggs.bucket('state', agg)
    search = search[0:0]
    results = search.execute()
    stats = {}
    for result in results.aggregations.state.buckets:
        stats[result.key] = result.doc_count
    return stats


def get_loans_by_patron_pid(patron_pid, filter_states=None,
                            to_anonymize=False):
    """Search all loans for patron to the given filter_states.

    :param to_anonymize: filter by field to_anonymize.
    :param patron_pid: The patron pid.
    :param filter_states: loan states to use as a filter.
    :return: loans for given patron.
    """
    search = search_by_patron_item_or_document(
        patron_pid=patron_pid,
        filter_states=filter_states) \
        .params(preserve_order=True) \
        .sort({'_created': {'order': 'asc'}}) \
        .source(['pid'])
    search = search.filter('term', to_anonymize=to_anonymize)
    for loan in search.scan():
        yield Loan.get_record_by_pid(loan.pid)


def get_last_transaction_loc_for_item(item_pid):
    """Return last transaction location for an item."""
    results = current_circulation.loan_search_cls() \
        .filter('term', item_pid=item_pid) \
        .params(preserve_order=True) \
        .exclude('terms', state=[
            LoanState.PENDING, LoanState.CREATED]) \
        .sort({'_created': {'order': 'desc'}}) \
        .source(['pid']).scan()
    try:
        loan_pid = next(results).pid
        return Loan.get_record_by_pid(
            loan_pid).get('transaction_location_pid')
    except StopIteration:
        return None


def get_loans_count_by_library_for_patron_pid(patron_pid, filter_states=None):
    """Get loans count for patron and aggregate result on library_pid.

    :param patron_pid: The patron pid
    :param filter_states: loans type to filters
    :return: a dict with library_pid as key, number of loans as value
    """
    filter_states = filter_states or []  # prevent mutable argument warning
    agg = A('terms', field='library_pid')
    search = search_by_patron_item_or_document(
        patron_pid=patron_pid,
        filter_states=filter_states
    )
    search.aggs.bucket('library', agg)
    search = search[0:0]
    results = search.execute()
    stats = {}
    for result in results.aggregations.library.buckets:
        stats[result.key] = result.doc_count
    return stats


def get_due_soon_loans(tstamp=None):
    """Return all due_soon loans.

    :param tstamp: a limit timestamp. Default is `datetime.now()`.
    """
    end_date = tstamp or datetime.now()
    end_date = end_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    query = current_circulation.loan_search_cls() \
        .filter('term', state=LoanState.ITEM_ON_LOAN) \
        .filter('range', due_soon_date={'lte': end_date}) \
        .params(preserve_order=True) \
        .sort({'_created': {'order': 'asc'}}) \
        .source(['pid']).scan()
    for hit in query:
        yield Loan.get_record_by_pid(hit.pid)


def get_expired_request(tstamp=None):
    """Return all expired request.

    :param tstamp: a limit timestamp. Default is `datetime.now()`.
    """
    end_date = tstamp or datetime.now()
    end_date = end_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    query = current_circulation.loan_search_cls() \
        .filter('term', state=LoanState.ITEM_AT_DESK) \
        .filter('range', request_expire_date={'lte': end_date}) \
        .source(['pid']).scan()
    for hit in query:
        yield Loan.get_record_by_pid(hit.pid)


def get_overdue_loan_pids(patron_pid=None, tstamp=None):
    """Return all overdue loan pids optionally filtered for a patron pid.

    :param patron_pid: the patron pid. If none, return all overdue loans.
    :param tstamp: a timestamp to define the execution time of the function.
                   Default to `datetime.now()`.
    :return a generator of loan pid
    """
    end_date = tstamp or datetime.now()
    end_date = end_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    query = current_circulation.loan_search_cls() \
        .filter('term', state=LoanState.ITEM_ON_LOAN) \
        .filter('range', end_date={'lte': end_date})
    if patron_pid:
        query = query.filter('term', patron_pid=patron_pid)
    results = query\
        .params(preserve_order=True) \
        .sort({'_created': {'order': 'asc'}}) \
        .source(['pid']).scan()
    for hit in results:
        yield hit.pid


def get_overdue_loans(patron_pid=None, tstamp=None):
    """Return all overdue loans optionally filtered for a patron pid.

    :param patron_pid: the patron pid. If none, return all overdue loans.
    :param tstamp: a timestamp to define the execution time of the function
    :return a generator of Loan
    """
    for pid in get_overdue_loan_pids(patron_pid, tstamp):
        yield Loan.get_record_by_pid(pid)


def loan_has_open_events(loan_pid=None):
    """Check if a loan has open patron transactions.

    Loan has no open_events if the he has no related patron transaction with
    the status open.

    :return True|False.
    """
    if loan_pid:
        search = NotificationsSearch()\
            .filter('term', context__loan__pid=loan_pid)\
            .source(['pid']).scan()
        for record in search:
            transactions_count = PatronTransactionsSearch()\
                .filter('term', notification__pid=record.pid)\
                .filter('term', status='open')\
                .source().count()
            if transactions_count > 0:
                return True
    return False


def get_non_anonymized_loans(patron=None, org_pid=None):
    """Search all loans for non anonymized loans.

    :param patron: optional parameter to filter by patron_pid.
    :param org_pid: optional parameter to filter by organisation.
    :return: loans.
    """
    search = current_circulation.loan_search_cls() \
        .filter('term', to_anonymize=False) \
        .filter('terms', state=[LoanState.CANCELLED, LoanState.ITEM_RETURNED])\
        .source(['pid'])
    if patron:
        search = search.filter('term', patron_pid=patron.pid)
    if org_pid:
        search = search.filter('term', organisation__pid=org_pid)
    for record in search.scan():
        yield Loan.get_record_by_pid(record.pid)


def anonymize_loans(patron=None, org_pid=None, dbcommit=False, reindex=False):
    """Anonymize loans.

    :param dbcommit - commit the changes in the db after the creation.
    :param reindex - index the record after the creation.
    :param patron: optional parameter to filter by patron.
    :param org_pid: optional parameter to filter by organisation.
    :return: loans.
    """
    counter = 0
    for loan in get_non_anonymized_loans(patron=patron, org_pid=org_pid):
        if Loan.can_anonymize(loan_data=loan, patron=patron):
            loan.anonymize(loan, dbcommit=dbcommit, reindex=reindex)
            counter += 1
    return counter


class LoansIndexer(IlsRecordsIndexer):
    """Holdings indexing class."""

    record_cls = Loan

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='loan')

    def _get_record_class(self, payload):
        """Get the record class from payload."""
        return self.record_cls
