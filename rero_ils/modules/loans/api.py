# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""API for manipulating Loans."""


from datetime import datetime, timedelta, timezone

from flask import current_app, url_for
from invenio_circulation.errors import CirculationException
from invenio_circulation.pidstore.fetchers import loan_pid_fetcher
from invenio_circulation.pidstore.minters import loan_pid_minter
from invenio_circulation.pidstore.providers import CirculationLoanIdProvider
from invenio_circulation.proxies import current_circulation
from invenio_circulation.search.api import search_by_patron_item
from invenio_jsonschemas import current_jsonschemas

from ..api import IlsRecord
from ..locations.api import Location
from ..notifications.api import Notification, is_availability_created, \
    is_recalled
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
    pid_field = "loan_pid"
    _schema = "loans/loan-ils-v0.0.1.json"

    def __init__(self, data, model=None):
        """Loan init."""
        self["state"] = current_app.config["CIRCULATION_LOAN_INITIAL_STATE"]
        super(Loan, self).__init__(data, model)

    @classmethod
    def create(cls, data, id_=None, delete_pid=True,
               dbcommit=False, reindex=False, **kwargs):
        """Create a new ils record."""
        data["$schema"] = current_jsonschemas.path_to_url(cls._schema)
        if delete_pid and data.get(cls.pid_field):
            del(data[cls.pid_field])
        record = super(Loan, cls).create(
            data=data, id_=id_, delete_pid=delete_pid, dbcommit=dbcommit,
            reindex=reindex, **kwargs)
        return record

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
        states = current_app.config["CIRCULATION_STATES_LOAN_ACTIVE"]
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

    def create_notification(self, notification_type=None):
        """Creates a recall notification from a checked-out loan."""
        data = {}
        record = {}
        base_url = current_app.config.get('RERO_ILS_APP_BASE_URL')
        url_api = '{base_url}/api/{doc_type}/{pid}'
        record['patron'] = {
            '$ref': url_api.format(
                base_url=base_url,
                doc_type='patrons',
                pid=self.get('patron_pid'))
        }
        record['item'] = {
            '$ref': url_api.format(
                base_url=base_url,
                doc_type='items',
                pid=self.get('item_pid'))
        }
        record['transaction_location'] = {
            '$ref': url_api.format(
                base_url=base_url,
                doc_type='locations',
                pid=self.get('transaction_location_pid'))
        }
        creation_date = datetime.now(timezone.utc).isoformat()
        record['creation_date'] = creation_date
        record['loan_pid'] = self.get('loan_pid')
        if notification_type == 'availability' and \
                not is_availability_created(self):
                library_pid = Location.get_record_by_pid(
                    self.get('pickup_location_pid')).library_pid
                record['pickup_library'] = {
                    '$ref': url_api.format(
                        base_url=base_url,
                        doc_type='libraries',
                        pid=library_pid)
                }
                record['notification_type'] = notification_type
        elif notification_type == 'recall':
            if self.get('state') == 'ITEM_ON_LOAN' and not is_recalled(self):
                record['due_date'] = self.get('end_date')
                record['notification_type'] = notification_type
        if record.get('notification_type'):
            data = Notification.create(
                data=record, dbcommit=True, reindex=True)
        return data


def get_request_by_item_pid_by_patron_pid(item_pid, patron_pid):
    """Get pending, item_on_transit, item_at_desk loans for item, patron."""
    search = search_by_patron_item(
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
        .source(['loan_pid'])\
        .params(preserve_order=True)\
        .filter('term', patron_pid=patron_pid)\
        .sort({'transaction_date': {'order': 'asc'}})\
        .scan()
    for loan in results:
        yield Loan.get_record_by_pid(loan.loan_pid)


def get_last_transaction_loc_for_item(item_pid):
    """Return last transaction location for an item."""
    results = current_circulation.loan_search\
        .source(['loan_pid'])\
        .params(preserve_order=True)\
        .filter('term', item_pid=item_pid)\
        .exclude('terms', state=['PENDING', 'CREATED'])\
        .sort({'transaction_date': {'order': 'desc'}})\
        .scan()
    try:
        loan_pid = next(results).loan_pid
        return Loan.get_record_by_pid(
            loan_pid).get('transaction_location_pid')
    except StopIteration:
        return None
