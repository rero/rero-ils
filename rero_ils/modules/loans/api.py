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
from flask import current_app, url_for
from invenio_circulation.errors import CirculationException, \
    MissingRequiredParameterError
from invenio_circulation.pidstore.fetchers import loan_pid_fetcher
from invenio_circulation.pidstore.minters import loan_pid_minter
from invenio_circulation.pidstore.providers import CirculationLoanIdProvider
from invenio_circulation.proxies import current_circulation
from invenio_circulation.search.api import search_by_patron_item_or_document
from invenio_jsonschemas import current_jsonschemas

from ..api import IlsRecord
from ..locations.api import Location
from ..notifications.api import Notification, NotificationsSearch, \
    number_of_reminders_sent
from ..patrons.api import Patron


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


class Loan(IlsRecord):
    """Loan class."""

    minter = loan_pid_minter
    fetcher = loan_pid_fetcher
    provider = CirculationLoanIdProvider
    pid_field = 'pid'
    _schema = 'loans/loan-ils-v0.0.1.json'

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
        record = super(Loan, cls).create(
            data=data, id_=id_, delete_pid=delete_pid, dbcommit=dbcommit,
            reindex=reindex, **kwargs)
        return record

    def attach_item_ref(self):
        """Attach item reference."""
        item_pid = self.get('item_pid')
        if not item_pid:
            raise MissingRequiredParameterError(
                description='item_pid missing from loan {0}'.format(
                    self.pid))
        if self.loan_build_item_ref:
            self['item'] = self.loan_build_item_ref(item_pid)

    def loan_build_item_ref(self, item_pid):
        """Build $ref for the Item attached to the Loan."""
        base_url = current_app.config.get('RERO_ILS_APP_BASE_URL')
        url_api = '{base_url}/api/{doc_type}/{pid}'
        return {
            '$ref': url_api.format(
                base_url=base_url,
                doc_type='items',
                pid=item_pid)
        }

    @property
    def pid(self):
        """Shortcut for pid."""
        return self.get('pid')

    @property
    def item_pid(self):
        """Shortcut for item pid."""
        return self.get('item_pid')

    @property
    def patron_pid(self):
        """Shortcut for patron pid."""
        return self.get('patron_pid')

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

        if self.get('item_pid'):
            item = Item.get_record_by_pid(self.get('item_pid'))
            return item.organisation_pid
        return None

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
        item_pid=item_pid,
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
    results = current_circulation.loan_search\
        .source(['pid'])\
        .params(preserve_order=True)\
        .filter('term', patron_pid=patron_pid)\
        .sort({'transaction_date': {'order': 'asc'}})\
        .scan()
    for loan in results:
        yield Loan.get_record_by_pid(loan.pid)


def get_last_transaction_loc_for_item(item_pid):
    """Return last transaction location for an item."""
    results = current_circulation.loan_search\
        .source(['pid'])\
        .params(preserve_order=True)\
        .filter('term', item_pid=item_pid)\
        .exclude('terms', state=['PENDING', 'CREATED'])\
        .sort({'transaction_date': {'order': 'desc'}})\
        .scan()
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
    results = current_circulation.loan_search\
        .source(['pid'])\
        .params(preserve_order=True)\
        .filter('term', state='ITEM_ON_LOAN')\
        .sort({'transaction_date': {'order': 'asc'}})\
        .scan()
    for record in results:
        loan = Loan.get_record_by_pid(record.pid)
        circ_policy = get_circ_policy(loan)
        now = datetime.now()
        end_date = loan.get('end_date')
        due_date = ciso8601.parse_datetime_as_naive(end_date)

        days_before = circ_policy.get('number_of_days_before_due_date')
        if due_date > now > due_date - timedelta(days=days_before):
            due_soon_loans.append(loan)
    return due_soon_loans


def get_overdue_loans():
    """Return all overdue loans."""
    from .utils import get_circ_policy
    overdue_loans = []
    results = current_circulation.loan_search\
        .source(['pid'])\
        .params(preserve_order=True)\
        .filter('term', state='ITEM_ON_LOAN')\
        .sort({'transaction_date': {'order': 'asc'}})\
        .scan()
    for record in results:
        loan = Loan.get_record_by_pid(record.pid)
        circ_policy = get_circ_policy(loan)
        now = datetime.now()
        end_date = loan.get('end_date')
        due_date = ciso8601.parse_datetime_as_naive(end_date)

        days_after = circ_policy.get('number_of_days_after_due_date')
        if now > due_date + timedelta(days=days_after):
            overdue_loans.append(loan)
    return overdue_loans
