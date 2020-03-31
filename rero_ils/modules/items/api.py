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

"""API for manipulating items."""

from datetime import datetime, timezone
from functools import partial, wraps

from elasticsearch.exceptions import NotFoundError
from flask import current_app
from invenio_circulation.api import get_loan_for_item, \
    patron_has_active_loan_on_item
from invenio_circulation.errors import MissingRequiredParameterError, \
    NoValidTransitionAvailableError
from invenio_circulation.proxies import current_circulation
from invenio_circulation.search.api import search_by_pid
from invenio_i18n.ext import current_i18n
from invenio_search import current_search

from .models import ItemIdentifier, ItemStatus
from ..api import IlsRecord, IlsRecordError, IlsRecordIndexer, IlsRecordsSearch
from ..circ_policies.api import CircPolicy
from ..documents.api import Document, DocumentsSearch
from ..errors import InvalidRecordID
from ..fetchers import id_fetcher
from ..libraries.api import Library
from ..loans.api import Loan, LoanAction, get_last_transaction_loc_for_item, \
    get_request_by_item_pid_by_patron_pid
from ..locations.api import Location
from ..minters import id_minter
from ..organisations.api import Organisation
from ..patrons.api import Patron, current_patron
from ..providers import Provider
from ..utils import trim_barcode_for_record
from ...filter import format_date_filter

# provider
ItemProvider = type(
    'ItemProvider',
    (Provider,),
    dict(identifier=ItemIdentifier, pid_type='item')
)
# minter
item_id_minter = partial(id_minter, provider=ItemProvider)
# fetcher
item_id_fetcher = partial(id_fetcher, provider=ItemProvider)


class ItemsIndexer(IlsRecordIndexer):
    """Indexing items in Elasticsearch."""

    def index(self, record):
        """Index an item."""
        from ..holdings.api import Holding
        # get the old holding record if exists
        items = ItemsSearch().filter(
            'term', pid=record.get('pid')
        ).source().execute().hits

        holding_pid = None
        if items.total:
            item = items.hits[0]['_source']
            holding_pid = item.get('holding', {}).get('pid')

        return_value = super(ItemsIndexer, self).index(record)
        document_pid = record.replace_refs()['document']['pid']
        document = Document.get_record_by_pid(document_pid)
        document.reindex()
        current_search.flush_and_refresh(DocumentsSearch.Meta.index)

        # check if old holding can be deleted
        if holding_pid:
            holding_rec = Holding.get_record_by_pid(holding_pid)
            try:
                # TODO: Need to split DB and elasticsearch deletion.
                holding_rec.delete(force=False, dbcommit=True, delindex=True)
            except IlsRecordError.NotDeleted:
                pass

        return return_value

    def delete(self, record):
        """Delete a record.

        :param record: Record instance.
        """
        from ..holdings.api import Holding

        return_value = super(ItemsIndexer, self).delete(record)
        rec_with_refs = record.replace_refs()
        document_pid = rec_with_refs['document']['pid']
        document = Document.get_record_by_pid(document_pid)
        document.reindex()
        current_search.flush_and_refresh(DocumentsSearch.Meta.index)

        holding = rec_with_refs.get('holding', '')
        if holding:
            holding_rec = Holding.get_record_by_pid(holding.get('pid'))
            try:
                # TODO: Need to split DB and elasticsearch deletion.
                holding_rec.delete(force=False, dbcommit=True, delindex=True)
            except IlsRecordError.NotDeleted:
                pass

        return return_value


class ItemsSearch(IlsRecordsSearch):
    """ItemsSearch."""

    class Meta:
        """Search only on item index."""

        index = 'items'

    @classmethod
    def flush(cls):
        """Flush indexes."""
        current_search.flush_and_refresh(DocumentsSearch.Meta.index)
        current_search.flush_and_refresh(cls.Meta.index)


def add_loans_parameters_and_flush_indexes(function):
    """Add missing action parameters."""
    @wraps(function)
    def wrapper(item, *args, **kwargs):
        """Executed before loan action."""
        loan = None
        web_request = False
        patron_pid = kwargs.get('patron_pid')
        loan_pid = kwargs.get('pid')
        # TODO: include in invenio-circulation
        if function.__name__ == 'request' and \
                not kwargs.get('pickup_location_pid'):
            raise MissingRequiredParameterError(
                description="Parameter 'pickup_location_pid' is required")

        if loan_pid:
            loan = Loan.get_record_by_pid(loan_pid)
        elif function.__name__ in ('checkout', 'request'):
            if function.__name__ == 'request' and not patron_pid:
                patron_pid = current_patron.pid
                web_request = True
            # create or get a loan
            if not patron_pid:
                raise MissingRequiredParameterError(
                    description="Parameter 'patron_pid' is required")
            if function.__name__ == 'checkout':
                request = get_request_by_item_pid_by_patron_pid(
                    item_pid=item.pid, patron_pid=patron_pid)
                if request:
                    loan = Loan.get_record_by_pid(request.get('pid'))

            if not loan:
                data = {
                    'item_pid': item.pid,
                    'patron_pid': patron_pid
                }
                loan = Loan.create(data, dbcommit=True, reindex=True)
        else:
            raise MissingRequiredParameterError(
                description="Parameter 'pid' is required")

        # set missing parameters
        kwargs['item_pid'] = item.pid
        kwargs['patron_pid'] = loan.get('patron_pid')
        kwargs['pid'] = loan.pid
        # TODO: case when user want to have his own transaction date
        kwargs['transaction_date'] = datetime.now(timezone.utc).isoformat()
        if not kwargs.get('transaction_user_pid'):
            kwargs.setdefault(
                'transaction_user_pid', current_patron.pid)
        kwargs.setdefault(
            'document_pid', item.replace_refs().get('document', {}).get('pid'))
        # TODO: change when it will be fixed in circulation
        if web_request:
            kwargs.setdefault(
                'transaction_location_pid', kwargs.get('pickup_location_pid'))
        elif not kwargs.get('transaction_location_pid'):
            kwargs.setdefault(
                'transaction_location_pid',
                Patron.get_librarian_pickup_location_pid()
            )

        item, action_applied = function(item, loan, *args, **kwargs)

        # commit and reindex item and loans
        current_search.flush_and_refresh(
            current_circulation.loan_search.Meta.index)
        item.status_update(dbcommit=True, reindex=True, forceindex=True)
        ItemsSearch.flush()
        return item, action_applied
    return wrapper


class Item(IlsRecord):
    """Item class."""

    minter = item_id_minter
    fetcher = item_id_fetcher
    provider = ItemProvider
    indexer = ItemsIndexer

    statuses = {
        'ITEM_ON_LOAN': 'on_loan',
        'ITEM_AT_DESK': 'at_desk',
        'ITEM_IN_TRANSIT_FOR_PICKUP': 'in_transit',
        'ITEM_IN_TRANSIT_TO_HOUSE': 'in_transit',
    }

    def delete_from_index(self):
        """Delete record from index."""
        try:
            ItemsIndexer().delete(self)
        except NotFoundError:
            pass

    @classmethod
    def create(cls, data, id_=None, delete_pid=False,
               dbcommit=False, reindex=False, **kwargs):
        """Create item record."""
        cls._item_build_org_ref(data)
        data = trim_barcode_for_record(data=data)
        record = super(Item, cls).create(
            data, id_, delete_pid, dbcommit, reindex, **kwargs)
        if not data.get('holding'):
            record.link_item_to_holding()
        return record

    def update(self, data, dbcommit=False, reindex=False):
        """Update an item record.

        :param data: The record to update.
        :param dbcommit: boolean to commit the record to the database or not.
        :param reindex: boolean to reindex the record or not.
        :returns: The updated item record.
        """
        data = trim_barcode_for_record(data=data)
        super(Item, self).update(data, dbcommit, reindex)
        # TODO: some item updates do not require holding re-linking
        self.link_item_to_holding()

        return self

    @classmethod
    def _item_build_org_ref(cls, data):
        """Build $ref for the organisation of the item."""
        loc_pid = data.get('location', {}).get('pid')
        if not loc_pid:
            loc_pid = data.get('location').get('$ref').split('locations/')[1]
            org_pid = Location.get_record_by_pid(loc_pid).organisation_pid
        base_url = current_app.config.get('RERO_ILS_APP_BASE_URL')
        url_api = '{base_url}/api/{doc_type}/{pid}'
        org_ref = {
            '$ref': url_api.format(
                base_url=base_url,
                doc_type='organisations',
                pid=org_pid or cls.organisation_pid)
        }
        data['organisation'] = org_ref

    def link_item_to_holding(self):
        """Link an item to a standard holding record."""
        from ..holdings.api import \
            get_standard_holding_pid_by_doc_location_item_type, \
            create_holding

        item = self.replace_refs()
        document_pid = item.get('document').get('pid')

        holding_pid = get_standard_holding_pid_by_doc_location_item_type(
            document_pid, self.location_pid, self.item_type_pid)

        if not holding_pid:
            holding_pid = create_holding(
                document_pid=document_pid,
                location_pid=self.location_pid,
                item_type_pid=self.item_type_pid)

        base_url = current_app.config.get('RERO_ILS_APP_BASE_URL')
        url_api = '{base_url}/api/{doc_type}/{pid}'
        self['holding'] = {
            '$ref': url_api.format(
                base_url=base_url,
                doc_type='holdings',
                pid=holding_pid)
        }
        self.commit()
        self.dbcommit(reindex=True, forceindex=True)

    def dumps_for_circulation(self, sort_by=None):
        """Enhance item information for api_views."""
        item = self.replace_refs()
        data = item.dumps()

        document = Document.get_record_by_pid(item['document']['pid'])
        doc_data = document.dumps()
        data['document']['title'] = doc_data['title']

        location = Location.get_record_by_pid(item['location']['pid'])
        loc_data = location.dumps()
        data['location']['name'] = loc_data['name']
        organisation = self.get_organisation()
        data['location']['organisation'] = {
            'pid': organisation.get('pid'),
            'name': organisation.get('name')
        }
        data['actions'] = list(self.actions)
        data['available'] = self.available
        # data['number_of_requests'] = self.number_of_requests()
        for loan in self.get_requests(sort_by=sort_by):
            data.setdefault('pending_loans',
                            []).append(loan.dumps_for_circulation())
        return data

    @classmethod
    def get_items_pid_by_holding_pid(cls, holding_pid):
        """Returns item pids from holding pid."""
        results = ItemsSearch()\
            .filter('term', holding__pid=holding_pid)\
            .source(['pid']).scan()
        for item in results:
            yield item.pid

    @property
    def holding_pid(self):
        """Shortcut for item holding pid."""
        if self.replace_refs().get('holding'):
            return self.replace_refs()['holding']['pid']
        return None

    @classmethod
    def get_document_pid_by_item_pid(cls, item_pid):
        """Returns document pid from item pid."""
        item = cls.get_record_by_pid(item_pid).replace_refs()
        return item.get('document', {}).get('pid')

    @classmethod
    def get_items_pid_by_document_pid(cls, document_pid):
        """Returns item pisd from document pid."""
        results = ItemsSearch()\
            .filter('term', document__pid=document_pid)\
            .source(['pid']).scan()
        for item in results:
            yield item.pid

    @classmethod
    def get_loans_by_item_pid(cls, item_pid):
        """Return any loan loans for item."""
        results = current_circulation.loan_search.filter(
            'term', item_pid=item_pid).source(includes='pid').scan()
        for loan in results:
            yield Loan.get_record_by_pid(loan.pid)

    @classmethod
    def get_loan_pid_with_item_on_loan(cls, item_pid):
        """Returns loan pid for checked out item."""
        search = search_by_pid(
            item_pid=item_pid, filter_states=['ITEM_ON_LOAN'])
        results = search.source(['pid']).scan()
        try:
            return next(results).pid
        except StopIteration:
            return None

    @classmethod
    def get_loan_pid_with_item_in_transit(cls, item_pid):
        """Returns loan pi for in_transit item."""
        search = search_by_pid(
            item_pid=item_pid, filter_states=[
                "ITEM_IN_TRANSIT_FOR_PICKUP",
                "ITEM_IN_TRANSIT_TO_HOUSE"])
        results = search.source(['pid']).scan()
        try:
            return next(results).pid
        except StopIteration:
            return None

    @classmethod
    def get_item_by_barcode(cls, barcode=None):
        """Get item by barcode."""
        results = ItemsSearch().filter(
            'term', barcode=barcode).source(includes='pid').scan()
        try:
            return cls.get_record_by_pid(next(results).pid)
        except StopIteration:
            return None

    @classmethod
    def get_pendings_loans(cls, library_pid=None, sort_by='transaction_date'):
        """Return list of sorted pending loans for a given library.

        default sort is set to transaction_date
        """
        # check if library exists
        lib = Library.get_record_by_pid(library_pid)
        if not lib:
            raise Exception('Invalid Library PID')
        # the '-' prefix means a desc order.
        sort_by = sort_by or 'transaction_date'
        order_by = 'asc'
        if sort_by.startswith('-'):
            sort_by = sort_by[1:]
            order_by = 'desc'
        search = current_circulation.loan_search\
            .source(['pid'])\
            .params(preserve_order=True)\
            .filter('term', state='PENDING')\
            .filter('term', library_pid=library_pid)\
            .sort({sort_by: {"order": order_by}})
        results = search.scan()
        for loan in results:
            yield Loan.get_record_by_pid(loan.pid)

    @classmethod
    def get_checked_out_loans(
            cls, patron_pid=None, sort_by='transaction_date'):
        """Returns sorted checked out loans for a given patron."""
        # check library exists
        patron = Patron.get_record_by_pid(patron_pid)
        if not patron:
            raise InvalidRecordID('Invalid Patron PID')
        # the '-' prefix means a desc order.
        sort_by = sort_by or 'transaction_date'
        order_by = 'asc'
        if sort_by.startswith('-'):
            sort_by = sort_by[1:]
            order_by = 'desc'

        results = current_circulation.loan_search.source(['pid'])\
            .params(preserve_order=True)\
            .filter('term', state='ITEM_ON_LOAN')\
            .filter('term', patron_pid=patron_pid)\
            .sort({sort_by: {"order": order_by}}).scan()
        for loan in results:
            yield Loan.get_record_by_pid(loan.pid)

    @classmethod
    def get_checked_out_items(cls, patron_pid=None, sort_by=None):
        """Return sorted checked out items for a given patron."""
        loans = cls.get_checked_out_loans(
            patron_pid=patron_pid, sort_by=sort_by)
        returned_item_pids = []
        for loan in loans:
            item_pid = loan.get('item_pid')
            item = Item.get_record_by_pid(item_pid)
            if item.status == ItemStatus.ON_LOAN and \
                    item_pid not in returned_item_pids:
                returned_item_pids.append(item_pid)
                yield item, loan

    def get_requests(self, sort_by=None):
        """Return sorted pending, item_on_transit, item_at_desk loans.

        default sort is transaction_date.
        """
        search = search_by_pid(
            item_pid=self.pid, filter_states=[
                'PENDING',
                'ITEM_AT_DESK',
                'ITEM_IN_TRANSIT_FOR_PICKUP'
            ]).params(preserve_order=True).source(['pid'])
        order_by = 'asc'
        sort_by = sort_by or 'transaction_date'
        if sort_by.startswith('-'):
            sort_by = sort_by[1:]
            order_by = 'desc'
        search = search.sort({sort_by: {'order': order_by}})
        for result in search.scan():
            yield Loan.get_record_by_pid(result.pid)

    @classmethod
    def get_requests_to_validate(
            cls, library_pid=None, sort_by=None):
        """Returns list of requests to validate for a given library."""
        loans = cls.get_pendings_loans(
            library_pid=library_pid, sort_by=sort_by)
        returned_item_pids = []
        for loan in loans:
            item_pid = loan.get('item_pid')
            item = Item.get_record_by_pid(item_pid)
            if item.status == ItemStatus.ON_SHELF and \
                    item_pid not in returned_item_pids:
                returned_item_pids.append(item_pid)
                yield item, loan

    def get_organisation(self):
        """Shortcut to the organisation of the item location."""
        return self.get_library().get_organisation()

    def get_library(self):
        """Shortcut to the library of the item location."""
        return self.get_location().get_library()

    def get_location(self):
        """Shortcut to the location of the item."""
        location_pid = self.replace_refs()['location']['pid']
        return Location.get_record_by_pid(location_pid)

    def get_library_of_last_location(self):
        """Returns the library record of the circulation transaction location.

        of the last loan.
        """
        return self.get_last_location().get_library()

    def get_last_location(self):
        """Returns the location record of the transaction location.

        of the last loan.
        """
        location_pid = self.last_location_pid
        return Location.get_record_by_pid(location_pid)

    @property
    def status(self):
        """Shortcut for item status."""
        return self.get('status', '')

    @property
    def item_type_pid(self):
        """Shortcut for item type pid."""
        item_type_pid = None
        item_type = self.replace_refs().get('item_type')
        if item_type:
            item_type_pid = item_type.get('pid')
        return item_type_pid

    @property
    def holding_circulation_category_pid(self):
        """Shortcut for holding circulation category pid of an item."""
        from ..holdings.api import Holding
        circulation_category_pid = None
        if self.holding_pid:
            circulation_category_pid = \
                Holding.get_record_by_pid(
                    self.holding_pid).circulation_category_pid
        return circulation_category_pid

    @property
    def location_pid(self):
        """Shortcut for item location pid."""
        location_pid = None
        location = self.replace_refs().get('location')
        if location:
            location_pid = location.get('pid')
        return location_pid

    @property
    def holding_location_pid(self):
        """Shortcut for holding location pid of an item."""
        from ..holdings.api import Holding
        location_pid = None
        if self.holding_pid:
            location_pid = Holding.get_record_by_pid(
                self.holding_pid).location_pid
        return location_pid

    @property
    def library_pid(self):
        """Shortcut for item library pid."""
        location = Location.get_record_by_pid(self.location_pid).replace_refs()
        return location.get('library').get('pid')

    @property
    def holding_library_pid(self):
        """Shortcut for holding library pid of an item."""
        library_pid = None
        if self.holding_location_pid:
            location = Location.get_record_by_pid(
                self.holding_location_pid).replace_refs()
            library_pid = location.get('library').get('pid')
        return library_pid

    @property
    def last_location_pid(self):
        """Returns the location pid of the circulation transaction location.

        of the last loan.
        """
        loan_location_pid = get_last_transaction_loc_for_item(self.pid)
        if loan_location_pid and Location.get_record_by_pid(loan_location_pid):
            return loan_location_pid
        return self.location_pid

    def can_extend(self, loan):
        """Checks if the patron has the rights to renew this item."""
        from ..loans.utils import extend_loan_data_is_valid
        can_extend = True
        patron_pid = loan.get('patron_pid')
        patron_type_pid = Patron.get_record_by_pid(
            patron_pid).patron_type_pid
        circ_policy = CircPolicy.provide_circ_policy(
            self.library_pid,
            patron_type_pid,
            self.item_type_pid
        )
        extension_count = loan.get('extension_count', 0)
        if not (
                circ_policy.get('number_renewals') > 0 and
                extension_count < circ_policy.get('number_renewals') and
                extend_loan_data_is_valid(
                    loan.get('end_date'),
                    circ_policy.get('renewal_duration'),
                    self.library_pid
                )
        ) or self.number_of_requests():
            can_extend = False
        return can_extend

    def action_filter(self, action, loan):
        """Filter actions."""
        patron_pid = loan.get('patron_pid')
        patron_type_pid = Patron.get_record_by_pid(
            patron_pid).patron_type_pid
        circ_policy = CircPolicy.provide_circ_policy(
            self.library_pid,
            patron_type_pid,
            self.item_type_pid
        )
        data = {
            'action_validated': True,
            'new_action': None
        }
        if action == 'extend':
            if not self.can_extend(loan):
                data['action_validated'] = False
        if action == 'checkout':
            if not circ_policy.get('allow_checkout'):
                data['action_validated'] = False

        if action == 'receive':
            if (
                    circ_policy.get('allow_checkout') and
                    loan.get('state') == 'ITEM_IN_TRANSIT_FOR_PICKUP' and
                    loan.get('patron_pid') == patron_pid
            ):
                data['action_validated'] = False
                data['new_action'] = 'checkout'
        return data

    @property
    def actions(self):
        """Get all available actions."""
        transitions = current_app.config.get('CIRCULATION_LOAN_TRANSITIONS')
        loan = get_loan_for_item(self.pid)
        actions = set()
        if loan:
            for transition in transitions.get(loan.get('state')):
                action = transition.get('trigger')
                data = self.action_filter(action, loan)
                if data.get('action_validated'):
                    actions.add(action)
                if data.get('new_action'):
                    actions.add(data.get('new_action'))
        # default actions
        if not loan:
            for transition in transitions.get('CREATED'):
                action = transition.get('trigger')
                actions.add(action)
        # remove unsupported action
        for action in ['cancel', 'request']:
            try:
                actions.remove(action)
                # not yet supported
                # actions.add('cancel_loan')
            except KeyError:
                pass
        # rename
        try:
            actions.remove('extend')
            actions.add('extend_loan')
        except KeyError:
            pass
        # if self['status'] == ItemStatus.MISSING:
        #     actions.add('return_missing')
        # else:
        #     actions.add('lose')
        return actions

    def status_update(self, dbcommit=False, reindex=False, forceindex=False):
        """Update item status."""
        loan = get_loan_for_item(self.pid)
        if loan:
            self['status'] = self.statuses[loan.get('state')]
        else:
            if self['status'] != ItemStatus.MISSING:
                self['status'] = ItemStatus.ON_SHELF
        if dbcommit:
            self.commit()
            self.dbcommit(reindex=True, forceindex=True)

    @property
    def available(self):
        """Get availability for item."""
        return self.item_has_active_loan_or_request() == 0

    def get_item_end_date(self, format='short_date'):
        """Get item due date for a given item."""
        loan = get_loan_for_item(self.pid)
        if loan:
            end_date = loan['end_date']
            due_date = format_date_filter(
                end_date,
                format=format,
                locale=current_i18n.locale.language,
            )
            return due_date
        return None

    def get_extension_count(self):
        """Get item renewal count."""
        loan = get_loan_for_item(self.pid)
        if loan:
            return loan.get('extension_count', 0)
        return 0

    def number_of_requests(self):
        """Get number of requests for a given item."""
        return len(list(self.get_requests()))

    def patron_request_rank(self, patron_barcode):
        """Get the rank of patron in list of requests on this item."""
        patron = Patron.get_patron_by_barcode(patron_barcode)
        if patron:
            rank = 0
            requests = self.get_requests()
            for request in requests:
                rank += 1
                if request['patron_pid'] == patron.pid:
                    return rank
        return False

    def is_requested_by_patron(self, patron_barcode):
        """Check if the item is requested by a given patron."""
        patron = Patron.get_patron_by_barcode(patron_barcode)
        if patron:
            request = get_request_by_item_pid_by_patron_pid(
                item_pid=self.pid, patron_pid=patron.pid
            )
            if request:
                return True
        return False

    def is_loaned_to_patron(self, patron_barcode):
        """Check if the item is loaned by a given patron."""
        patron = Patron.get_patron_by_barcode(patron_barcode)
        if patron:
            patron_pid = patron.pid
            checkout = patron_has_active_loan_on_item(patron_pid, self.pid)
            if checkout:
                return True
        return False

    @classmethod
    def item_location_retriever(cls, item_pid, **kwargs):
        """Get item selflocation or the transaction location of the.

        last loan.
        """
        # TODO: for requests we probably need the transation_location_pid
        #       to deal with multiple pickup locations for a library
        item = cls.get_record_by_pid(item_pid)
        if item:
            # TODO: this will be useful for the very specific rero use cases

            # last_location = item.get_last_location()
            # if last_location:
            #     return last_location.pid
            return item.get_owning_pickup_location_pid()

    @add_loans_parameters_and_flush_indexes
    def validate_request(self, current_loan, **kwargs):
        """Validate item request."""
        loan = current_circulation.circulation.trigger(
            current_loan, **dict(kwargs, trigger='validate_request')
        )
        return self, {
            LoanAction.VALIDATE: loan
        }

    @add_loans_parameters_and_flush_indexes
    def extend_loan(self, current_loan, **kwargs):
        """Extend checkout duration for this item."""
        loan = current_circulation.circulation.trigger(
            current_loan, **dict(kwargs, trigger='extend')
        )
        return self, {
            LoanAction.EXTEND: loan
        }

    @add_loans_parameters_and_flush_indexes
    def request(self, current_loan, **kwargs):
        """Request item for the user and create notifications."""
        loan = current_circulation.circulation.trigger(
            current_loan, **dict(kwargs, trigger='request')
        )
        return self, {
            LoanAction.REQUEST: loan
        }

    @add_loans_parameters_and_flush_indexes
    def receive(self, current_loan, **kwargs):
        """Receive an item."""
        loan = current_circulation.circulation.trigger(
            current_loan, **dict(kwargs, trigger='receive')
        )
        return self, {
            LoanAction.RECEIVE: loan
        }

    @add_loans_parameters_and_flush_indexes
    def checkin(self, current_loan, **kwargs):
        """Checkin a given item."""
        checkin_loan = current_circulation.circulation.trigger(
            current_loan, **dict(kwargs, trigger='checkin')
        )
        # to return the list of all applied actions
        actions = {LoanAction.CHECKIN: checkin_loan}
        # if item is requested we will automatically:
        # - cancel the checked-in loan if still active
        # - validate the next request
        requests = self.number_of_requests()
        if requests:
            request = next(self.get_requests())
            if checkin_loan.is_active:
                item, cancel_actions = self.cancel_loan(pid=checkin_loan.pid)
                actions.update(cancel_actions)
            # pass the correct transaction location
            transaction_loc_pid = checkin_loan.get('transaction_location_pid')
            request['transaction_location_pid'] = transaction_loc_pid
            # validate the request
            item, validate_actions = self.validate_request(**request)
            actions.update(validate_actions)
            validate_loan = validate_actions[LoanAction.VALIDATE]
            # receive the request if it is requested at transaction library
            if validate_loan.get('state') == 'ITEM_IN_TRANSIT_FOR_PICKUP':
                trans_loc = Location.get_record_by_pid(transaction_loc_pid)
                req_loc = Location.get_record_by_pid(
                    request.get('pickup_location_pid'))
                if req_loc.library_pid == trans_loc.library_pid:
                    item, receive_action = self.receive(**request)
                    actions.update(receive_action)
        return self, actions

    def prior_checkout_actions(self, action_params):
        """Actions executed prior to a checkout."""
        actions = {}
        if action_params.get('pid'):
            loan = Loan.get_record_by_pid(action_params.get('pid'))
            if (
                loan.get('state') == 'ITEM_IN_TRANSIT_FOR_PICKUP' and
                loan.get('patron_pid') == action_params.get('patron_pid')
            ):
                item, receive_actions = self.receive(**action_params)
                actions.update(receive_actions)
            if loan.get('state') == 'ITEM_IN_TRANSIT_TO_HOUSE':
                item, cancel_actions = self.cancel_loan(pid=loan.get('pid'))
                actions.update(cancel_actions)
                del action_params['pid']
        else:
            loan = get_loan_for_item(self.pid)
            if (loan and loan.get('state') != 'ITEM_AT_DESK'):
                item, cancel_actions = self.cancel_loan(pid=loan.get('pid'))
                actions.update(cancel_actions)
        return action_params, actions

    @add_loans_parameters_and_flush_indexes
    def checkout(self, current_loan, **kwargs):
        """Checkout item to the user."""
        action_params, actions = self.prior_checkout_actions(kwargs)
        loan = Loan.get_record_by_pid(action_params.get('pid'))
        current_loan = loan or Loan.create(action_params,
                                           dbcommit=True,
                                           reindex=True)

        loan = current_circulation.circulation.trigger(
            current_loan, **dict(action_params, trigger='checkout')
        )
        actions.update({LoanAction.CHECKOUT: loan})
        return self, actions

    @add_loans_parameters_and_flush_indexes
    def cancel_loan(self, current_loan, **kwargs):
        """Cancel a given item loan for a patron."""
        loan = current_circulation.circulation.trigger(
            current_loan, **dict(kwargs, trigger='cancel')
        )
        return self, {
            LoanAction.CANCEL: loan
        }

    def get_owning_pickup_location_pid(self):
        """Returns the pickup location for the item owning location."""
        library = self.get_library()
        return library.get_pickup_location_pid()

    def automatic_checkin(self, trans_loc_pid=None):
        """Apply circ transactions for item."""
        data = {}
        if trans_loc_pid is not None:
            data['transaction_location_pid'] = trans_loc_pid
        if self.status == ItemStatus.ON_LOAN:
            loan_pid = self.get_loan_pid_with_item_on_loan(self.pid)
            return self.checkin(pid=loan_pid, **data)

        elif self.status == ItemStatus.IN_TRANSIT:
            do_receive = False
            loan_pid = self.get_loan_pid_with_item_in_transit(self.pid)
            loan = Loan.get_record_by_pid(loan_pid)

            transaction_location_pid = trans_loc_pid
            if trans_loc_pid is None:
                transaction_location_pid = \
                    Patron.get_librarian_pickup_location_pid()
            if loan['state'] == 'ITEM_IN_TRANSIT_FOR_PICKUP' and \
                    loan['pickup_location_pid'] == transaction_location_pid:
                do_receive = True
            if loan['state'] == 'ITEM_IN_TRANSIT_TO_HOUSE':
                trans_loc = Location.get_record_by_pid(trans_loc_pid)
                if self.library_pid == trans_loc.library_pid:
                    do_receive = True
            if do_receive:
                return self.receive(pid=loan_pid, **data)
            return self, {
                # None action are available. Send anyway last known loan
                # informations.
                LoanAction.NO: loan
            }

        if self.status == ItemStatus.MISSING:
            return self.return_missing()
        return self, {
            LoanAction.NO: None
        }

    def lose(self):
        """Lose the given item.

        This sets the status to ItemStatus.MISSING.
        All existing holdings will be canceled.
        """
        # cancel all actions if it is possible
        for loan in self.get_loans_by_item_pid(self.pid):
            loan_pid = loan['pid']
            try:
                self.cancel_loan(pid=loan_pid)
            except NoValidTransitionAvailableError:
                pass
        self['status'] = ItemStatus.MISSING
        self.status_update(dbcommit=True, reindex=True, forceindex=True)
        return self, {
            LoanAction.LOSE: None
        }

    def return_missing(self):
        """Return the missing item.

        The item's status will be set to ItemStatus.ON_SHELF.
        """
        # TODO: check transaction location
        self['status'] = ItemStatus.ON_SHELF
        self.status_update(dbcommit=True, reindex=True, forceindex=True)
        return self, {
            LoanAction.RETURN_MISSING: None
        }

    def get_number_of_loans(self):
        """Get number of loans."""
        search = search_by_pid(
            item_pid=self.pid,
            exclude_states=[
                'CANCELLED',
                'ITEM_RETURNED',
            ]
        )
        results = search.source().count()
        return results

    def get_links_to_me(self):
        """Get number of links."""
        links = {}
        loans = self.get_number_of_loans()
        if loans:
            links['loans'] = loans
        return links

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        cannot_delete = {}
        links = self.get_links_to_me()
        if links:
            cannot_delete['links'] = links
        return cannot_delete

    @property
    def organisation_pid(self):
        """Get organisation pid for item."""
        library = Library.get_record_by_pid(self.library_pid)
        return library.organisation_pid

    @property
    def organisation_view(self):
        """Get Organisation view for item."""
        organisation = Organisation.get_record_by_pid(self.organisation_pid)
        return organisation['view_code']

    def item_has_active_loan_or_request(self):
        """Return True if active loan or a request found for item."""
        states = ['PENDING'] + \
            current_app.config['CIRCULATION_STATES_LOAN_ACTIVE']
        search = search_by_pid(
            item_pid=self.pid,
            filter_states=states,
        )
        search_result = search.execute()
        return search_result.hits.total

    def dumps(self, **kwargs):
        """Return pure Python dictionary with record metadata."""
        dump = super(Item, self).dumps(**kwargs)
        dump['available'] = self.available
        return dump
