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

"""API for manipulating Loans."""

from datetime import datetime, timedelta, timezone

import ciso8601
from flask import current_app
from invenio_circulation.pidstore.fetchers import loan_pid_fetcher
from invenio_circulation.pidstore.minters import loan_pid_minter
from invenio_circulation.pidstore.providers import CirculationLoanIdProvider
from invenio_circulation.proxies import current_circulation
from invenio_circulation.search.api import search_by_patron_item_or_document
from invenio_circulation.utils import str2datetime
from invenio_jsonschemas import current_jsonschemas

from ..api import IlsRecord, IlsRecordError, IlsRecordsIndexer, \
    IlsRecordsSearch
from ..documents.api import Document
from ..items.models import ItemCirculationAction
from ..items.utils import item_pid_to_object
from ..libraries.api import Library
from ..locations.api import Location
from ..notifications.api import Notification, NotificationsSearch, \
    number_of_reminders_sent
from ..patrons.api import Patron
from ..utils import get_ref_for_pid


class LoanAction(object):
    """Class holding all availabe circulation loan actions."""

    REQUEST = 'request'
    CHECKOUT = 'checkout'
    CHECKIN = 'checkin'
    VALIDATE = 'validate'
    RECEIVE = 'receive'
    RETURN_MISSING = 'return_missing'
    EXTEND = 'extend'
    CANCEL = 'cancel'
    LOSE = 'lose'
    NO = 'no'


class LoansSearch(IlsRecordsSearch):
    """Libraries search."""

    class Meta():
        """Meta class."""

        index = 'loans'
        doc_types = None


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
    DATE_FIELDS = [
        "start_date",
        "end_date",
        "request_expire_date",
        "request_start_date",
    ]
    DATETIME_FIELDS = ["transaction_date"]

    def __init__(self, data, model=None):
        """Loan init."""
        self['state'] = current_app.config['CIRCULATION_LOAN_INITIAL_STATE']
        super(Loan, self).__init__(data, model)

    @classmethod
    def create(cls, data, id_=None, delete_pid=True,
               dbcommit=False, reindex=False, **kwargs):
        """Create a new ils record."""
        data['$schema'] = current_jsonschemas.path_to_url(cls._schema)
        if delete_pid and data.get(cls.pid_field):
            del(data[cls.pid_field])
        cls._loan_build_org_ref(data)
        record = super(Loan, cls).create(
            data=data, id_=id_, delete_pid=delete_pid, dbcommit=dbcommit,
            reindex=reindex, **kwargs)
        return record

    def update(self, data, dbcommit=False, reindex=False):
        """Update loan record."""
        self._loan_build_org_ref(data)
        super(Loan, self).update(data, dbcommit, reindex)
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
    def _loan_build_org_ref(cls, data):
        """Build $ref for the organisation of the Loan."""
        from ..items.api import Item
        item_pid = data.get('item_pid', {}).get('value')
        data['organisation'] = {'$ref': get_ref_for_pid(
            'org',
            Item.get_record_by_pid(item_pid).organisation_pid
        )}
        return data

    @property
    def pid(self):
        """Shortcut for pid."""
        return self.get('pid')

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

    def dumps_for_circulation(self):
        """Dumps for circulation."""
        loan = self.replace_refs()
        data = loan.dumps()
        patron = Patron.get_record_by_pid(loan['patron_pid'])
        ptrn_data = patron.dumps()
        data['patron'] = {}
        data['patron']['barcode'] = ptrn_data['barcode']
        data['patron']['name'] = ', '.join((
            ptrn_data['first_name'], ptrn_data['last_name']))
        if loan.get('pickup_location_pid'):
            location = Location.get_record_by_pid(loan['pickup_location_pid'])
            library = location.get_library()
            loc_data = location.dumps()
            data['pickup_location'] = {}
            data['pickup_location']['name'] = loc_data['name']
            data['pickup_location']['library_name'] = library.get('name')
        return data

    def is_notified(self, notification_type=None):
        """Check if a notification exist already for a loan by type."""
        results = NotificationsSearch().filter(
            'term', loan__pid=self.pid
        ).filter('term', notification_type=notification_type).source().count()
        return results > 0

    def create_notification(self, notification_type=None):
        """Creates a recall notification from a checked-out loan."""
        notification = {}
        record = {}
        creation_date = datetime.now(timezone.utc).isoformat()
        record['creation_date'] = creation_date
        record['notification_type'] = notification_type
        base_url = current_app.config.get('RERO_ILS_APP_BASE_URL')
        url_api = '{base_url}/api/{doc_type}/{pid}'
        record['loan'] = {
            '$ref': url_api.format(
                base_url=base_url,
                doc_type='loans',
                pid=self.pid)
        }
        notification_to_create = False
        if notification_type == 'recall':
            if self.get('state') == 'ITEM_ON_LOAN' and \
                    not self.is_notified(notification_type=notification_type):
                notification_to_create = True
        elif notification_type == 'availability' and \
                not self.is_notified(notification_type=notification_type):
            notification_to_create = True
        elif notification_type == 'due_soon':
            if self.get('state') == 'ITEM_ON_LOAN' and \
                    not self.is_notified(notification_type=notification_type):
                notification_to_create = True
        elif notification_type == 'overdue':
            if self.get('state') == 'ITEM_ON_LOAN' and \
                    not number_of_reminders_sent(self):
                record['reminder_counter'] = 1
                notification_to_create = True
        if notification_to_create:
            notification = Notification.create(
                data=record, dbcommit=True, reindex=True)
            notification = notification.dispatch()
        return notification


def get_request_by_item_pid_by_patron_pid(item_pid, patron_pid):
    """Get pending, item_on_transit, item_at_desk loans for item, patron."""
    search = search_by_patron_item_or_document(
        item_pid=item_pid_to_object(item_pid),
        patron_pid=patron_pid,
        filter_states=[
            'PENDING',
            'ITEM_AT_DESK',
            'ITEM_IN_TRANSIT_FOR_PICKUP',
            'ITEM_IN_TRANSIT_TO_HOUSE',
        ],
    )
    search_result = search.execute()
    if search_result.hits:
        return search_result.hits.hits[0]['_source']
    return {}


def get_loans_by_patron_pid(patron_pid):
    """Return all loans for patron."""
    results = current_circulation.loan_search_cls()\
        .filter('term', patron_pid=patron_pid)\
        .params(preserve_order=True).\
        sort({'transaction_date': {'order': 'asc'}})\
        .source(['pid']).scan()
    for loan in results:
        yield Loan.get_record_by_pid(loan.pid)


def patron_profile_loans(patron_pid):
    """Return formatted loans for patron profile display."""
    from ..items.api import Item

    checkouts = []
    requests = []
    history = []
    for loan in get_loans_by_patron_pid(patron_pid):
        item = Item.get_record_by_pid(loan.item_pid)
        document = Document.get_record_by_pid(
            item.replace_refs()['document']['pid'])
        loan['document_title'] = document.dumps()['title'][0].get('_text', '')
        loan['item_call_number'] = item['call_number']
        loan['library_name'] = Library.get_record_by_pid(
            item.holding_library_pid).get('name')
        if loan['state'] == 'ITEM_ON_LOAN':
            can, reasons = item.can(
                ItemCirculationAction.EXTEND,
                loan=loan
            )
            loan['can_renew'] = can
            checkouts.append(loan)
        elif loan['state'] in [
                'PENDING',
                'ITEM_AT_DESK',
                'ITEM_IN_TRANSIT_FOR_PICKUP'
        ]:
            pickup_loc = Location.get_record_by_pid(
                loan['pickup_location_pid'])
            loan['pickup_library_name'] = \
                pickup_loc.get_library().get('name')
            requests.append(loan)
        elif loan['state'] in ['ITEM_RETURNED', 'CANCELLED']:
            end_date = loan.get('end_date')
            if end_date:
                end_date = ciso8601.parse_datetime(end_date)
                loan_age = (datetime.utcnow() - end_date.replace(tzinfo=None))
                # Only history of last six months is displayed
                if loan_age <= timedelta(6*365/12):
                    history.append(loan)
    return checkouts, requests, history


def get_last_transaction_loc_for_item(item_pid):
    """Return last transaction location for an item."""
    results = current_circulation.loan_search_cls()\
        .filter('term', item_pid=item_pid)\
        .params(preserve_order=True)\
        .exclude('terms', state=['PENDING', 'CREATED'])\
        .sort({'transaction_date': {'order': 'desc'}})\
        .source(['pid']).scan()
    try:
        loan_pid = next(results).pid
        return Loan.get_record_by_pid(
            loan_pid).get('transaction_location_pid')
    except StopIteration:
        return None


def get_due_soon_loans():
    """Return all due_soon loans."""
    from .utils import get_circ_policy
    due_soon_loans = []
    results = current_circulation.loan_search_cls()\
        .filter('term', state='ITEM_ON_LOAN')\
        .params(preserve_order=True)\
        .sort({'transaction_date': {'order': 'asc'}})\
        .source(['pid']).scan()
    for record in results:
        loan = Loan.get_record_by_pid(record.pid)
        circ_policy = get_circ_policy(loan)
        now = datetime.now(timezone.utc)
        end_date = loan.get('end_date')
        due_date = ciso8601.parse_datetime(end_date).replace(
            tzinfo=timezone.utc)
        days_before = circ_policy.get('number_of_days_before_due_date')
        if due_date > now > due_date - timedelta(days=days_before):
            due_soon_loans.append(loan)
    return due_soon_loans


def get_overdue_loans():
    """Return all overdue loans."""
    from .utils import get_circ_policy
    overdue_loans = []
    results = current_circulation.loan_search_cls()\
        .filter('term', state='ITEM_ON_LOAN')\
        .params(preserve_order=True)\
        .sort({'transaction_date': {'order': 'asc'}})\
        .source(['pid']).scan()
    for record in results:
        loan = Loan.get_record_by_pid(record.pid)
        circ_policy = get_circ_policy(loan)
        now = datetime.now(timezone.utc)
        end_date = loan.get('end_date')
        due_date = ciso8601.parse_datetime(end_date)

        days_after = circ_policy.get('number_of_days_after_due_date')
        if now > due_date + timedelta(days=days_after):
            overdue_loans.append(loan)
    return overdue_loans


class LoansIndexer(IlsRecordsIndexer):
    """Holdings indexing class."""

    record_cls = Loan
