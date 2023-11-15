# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

"""API for manipulating Acquisition Orders."""
from datetime import datetime, timezone
from functools import partial

from flask_babel import gettext as _
from invenio_records_rest.utils import obj_or_import_string

from rero_ils.modules.acquisition.acq_order_lines.api import AcqOrderLine, \
    AcqOrderLinesSearch
from rero_ils.modules.acquisition.acq_order_lines.models import \
    AcqOrderLineStatus
from rero_ils.modules.acquisition.acq_receipts.api import AcqReceipt, \
    AcqReceiptsSearch
from rero_ils.modules.acquisition.api import AcquisitionIlsRecord
from rero_ils.modules.acquisition.budgets.api import Budget
from rero_ils.modules.api import IlsRecordsIndexer, IlsRecordsSearch
from rero_ils.modules.fetchers import id_fetcher
from rero_ils.modules.minters import id_minter
from rero_ils.modules.notifications.api import Notification
from rero_ils.modules.notifications.dispatcher import Dispatcher
from rero_ils.modules.notifications.models import NotificationType
from rero_ils.modules.providers import Provider
from rero_ils.modules.utils import extracted_data_from_ref, \
    get_endpoint_configuration, get_objects, get_ref_for_pid, sorted_pids

from .extensions import AcquisitionOrderCompleteDataExtension, \
    AcquisitionOrderExtension
from .models import AcqOrderIdentifier, AcqOrderMetadata, AcqOrderStatus

# provider
AcqOrderProvider = type(
    'AcqOrderProvider',
    (Provider,),
    dict(identifier=AcqOrderIdentifier, pid_type='acor')
)
# minter
acq_order_id_minter = partial(id_minter, provider=AcqOrderProvider)
# fetcher
acq_order_id_fetcher = partial(id_fetcher, provider=AcqOrderProvider)


class AcqOrdersSearch(IlsRecordsSearch):
    """Acquisition Orders Search."""

    class Meta:
        """Search only on acq_order index."""

        index = 'acq_orders'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class AcqOrder(AcquisitionIlsRecord):
    """AcqOrder class."""

    _extensions = [
        AcquisitionOrderExtension(),
        AcquisitionOrderCompleteDataExtension()
    ]

    minter = acq_order_id_minter
    fetcher = acq_order_id_fetcher
    provider = AcqOrderProvider
    model_cls = AcqOrderMetadata
    pids_exist_check = {
        'required': {
            'lib': 'library',
            'vndr': 'vendor'
        },
        'not_required': {
            'org': 'organisation'
        }
    }

    def extended_validation(self, **kwargs):
        """Add additional record validation.

        :return: False if
            - notes array has multiple notes with same type
        """
        # NOTES fields testing
        note_types = [note.get('type') for note in self.get('notes', [])]
        if len(note_types) != len(set(note_types)):
            return _('Can not have multiple notes of the same type.')

        return True

    @classmethod
    def create(cls, data, id_=None, delete_pid=False,
               dbcommit=False, reindex=False, **kwargs):
        """Create acquisition order record."""
        # TODO : should be used into `pre_create` hook extensions but seems not
        #   work as expected.
        AcquisitionOrderCompleteDataExtension.populate_currency(data)
        return super().create(data, id_, delete_pid, dbcommit, reindex,
                              **kwargs)

    @property
    def vendor(self):
        """Shortcut for vendor."""
        return extracted_data_from_ref(self.get('vendor'), data='record')

    @property
    def organisation_pid(self):
        """Shortcut for acquisition order organisation pid."""
        library = extracted_data_from_ref(self.get('library'), data='record')
        return library.organisation_pid

    @property
    def library_pid(self):
        """Shortcut for acquisition order library pid."""
        return extracted_data_from_ref(self.get('library'))

    @property
    def library(self):
        """Shortcut for acquisition order library."""
        return extracted_data_from_ref(self.get('library'), data='record')

    @property
    def vendor_pid(self):
        """Shortcut for acquisition order vendor pid."""
        return extracted_data_from_ref(self.get('vendor'))

    @property
    def status(self):
        """Get the order status based on related order lines statuses.

        The order received the order status:
        PENDING:    if all related order lines has PENDING status.
        ORDERED:
          * if all related order lines has ORDERED status.
          * if order lines statuses are multiple, and at least one order line
            is ORDERED but none are RECEIVED, PARTIALLY_RECEIVED.
        CANCELLED:  if all related order lines has CANCELLED status.
        PARTIALLY_RECEIVED:
          * if order contains only 1 order line and this order line status is
            PARTIALLY_RECEIVED
          * if order lines statuses are multiple, and at least one order line
            is PARTIALLY_RECEIVED or RECEIVED.
        RECEIVED:   if all related order lines has RECEIVED status.
        """
        status = AcqOrderStatus.PENDING
        search = AcqOrderLinesSearch().filter('term', acq_order__pid=self.pid)
        search.aggs.bucket('status', 'terms', field='status')
        results = search.execute()
        statuses = [hit.key for hit in results.aggregations.status.buckets]

        # If the ES query return multiple values, then we can remove
        # 'CANCELLED' status to compute the correct order status value.
        if len(statuses) > 1 and AcqOrderLineStatus.CANCELLED in statuses:
            statuses.remove(AcqOrderLineStatus.CANCELLED)

        if len(statuses) > 1:
            if any(s in AcqOrderLineStatus.RECEIVED_STATUSES
                   for s in statuses):
                status = AcqOrderStatus.PARTIALLY_RECEIVED
            elif AcqOrderLineStatus.ORDERED in statuses:
                status = AcqOrderStatus.ORDERED

        elif len(statuses) == 1:
            map = {
                AcqOrderLineStatus.APPROVED: AcqOrderStatus.PENDING,
                AcqOrderLineStatus.ORDERED: AcqOrderStatus.ORDERED,
                AcqOrderLineStatus.RECEIVED: AcqOrderStatus.RECEIVED,
                AcqOrderLineStatus.PARTIALLY_RECEIVED:
                    AcqOrderStatus.PARTIALLY_RECEIVED,
                AcqOrderLineStatus.CANCELLED: AcqOrderStatus.CANCELLED,
            }
            if statuses[0] in map:
                status = map[statuses[0]]

        return status

    @property
    def order_date(self):
        """Get the order date of this order."""
        result = AcqOrderLinesSearch()\
            .filter('term', acq_order__pid=self.pid)\
            .filter('exists', field='order_date')\
            .source(['order_date']).scan()
        dates = [hit.order_date for hit in result]
        return next(iter(dates or []), None)

    @property
    def item_quantity(self):
        """Get the total of item quantity for this order."""
        search = AcqOrderLinesSearch() \
            .filter('term', acq_order__pid=self.pid) \
            .exclude('term', status=AcqOrderLineStatus.CANCELLED)
        search.aggs.metric('total_quantity', 'sum', field='quantity')
        results = search.execute()
        return results.aggregations.total_quantity.value

    @property
    def item_received_quantity(self):
        """Get the total of received item quantity for this order."""
        search = AcqOrderLinesSearch() \
            .filter('term', acq_order__pid=self.pid) \
            .exclude('term', status=AcqOrderLineStatus.CANCELLED)
        search.aggs.metric('total_quantity', 'sum', field='received_quantity')
        results = search.execute()
        return results.aggregations.total_quantity.value

    @property
    def previous_order(self):
        """Try to find the previous order in the order history."""
        if prev_version := self.get('previousVersion'):
            prev_pid = extracted_data_from_ref(prev_version)
            return AcqOrder.get_record_by_pid(prev_pid)

    @property
    def next_order(self):
        """Try to find an acquisition order representing next order."""
        query = AcqOrdersSearch() \
            .filter('term', previousVersion__pid=self.pid)\
            .source('pid')
        if hit := next(query.scan(), None):
            return AcqOrder.get_record(hit.meta.id)

    @property
    def budget(self):
        """Get the budget related to this order.

        Acquisition order are not directly related to a budget. The relation
        can be found by related order lines (related to account, related to
        budget). But a newly created order doesn't have any order line. In this
        case, the current active budget of the organisation will be used.
        """
        if self.pid and (line := next(self.get_order_lines(), None)):
            return line.account.budget
        org = self.library.get_organisation()
        return Budget.get_record_by_pid(org.get('current_budget_pid'))

    @property
    def is_active(self):
        """Check if the order should be considered as active.

        To know if an order is active, we need to check the related
        budget of its lines. This budget has an 'is_active' field.
        """
        # When trying to create a record the pid field is empty, this is why
        # we check if self.pid is there or not. In this case and when no order
        # has no lines we return True.
        if self.pid:
            order_lines = self.get_order_lines()
            # There is no need to check all the lines, we will not mix lines
            # from different budgets in same order.
            if order_line := next(order_lines, None):
                return order_line.is_active
        return True

    def get_note(self, note_type):
        """Get a specific type of note.

        Only one note of each type could be created.
        :param note_type: the note type to filter as `OrderNoteType` value.
        :return the note content if exists, otherwise returns None.
        """
        note = [
            note.get('content') for note in self.get('notes', [])
            if note.get('type') == note_type
        ]
        return next(iter(note), None)

    def get_receipts(self, output=None):
        """Get AcqReceipts related to this AcqOrder.

        :param output: output method. 'count', 'query' or None.
        :return a generator of related AcqReceipts.
        """
        query = AcqReceiptsSearch().filter('term', acq_order__pid=self.pid)
        if output == 'count':
            return query.count()
        elif output == 'query':
            return query
        else:
            return get_objects(AcqReceipt, query)

    def get_related_notes(self, resource_filters=None):
        """Get all notes from resource relates to this `AcqOrder`.

        :param resource_filters: the list of resource acronym where to search
                                 related notes. If `None` all related resources
                                 will be fetched.
        :return a list of tuples. Each tuple was compose of three elements :
            * the note dict (type and content)
            * the source record class
            * the related resource pid
        """
        # Add here the SearchClass where to search about notes related to this
        # AcqOrder.
        related_resources = ['acol', 'acre', 'acrl']
        resource_filters = resource_filters or related_resources
        for resource_acronym in resource_filters:
            # search about config for this acronym. If not found : continue
            config = get_endpoint_configuration(resource_acronym)
            if not config:
                continue
            record_cls = obj_or_import_string(config['record_class'])
            source_search_class = obj_or_import_string(config['search_class'])
            search_class = source_search_class()

            query = search_class \
                .filter('term', acq_order__pid=self.pid) \
                .filter('exists', field='notes') \
                .source(['notes', 'pid'])
            for hit in query.scan():
                for note in hit.notes:
                    yield note, record_cls, hit.pid

    def get_related_orders(self, output=None):
        """Get orders related to this order.

        :param output: output method : 'count', 'query' or None.
        """
        query = AcqOrdersSearch()\
            .filter('term', previousVersion__pid=self.pid)
        if output == 'count':
            return query.count()
        elif output == 'query':
            return query
        else:
            return get_objects(AcqOrder, query)

    def get_order_lines(self, output=None, includes=None):
        """Get order lines related to this order.

        :param output: output method. 'count', 'query' or None.
        :param includes: a list of statuses to include order lines.
        :return a generator of related order lines (or length).
        """

        def preserve_order(query):
            """Keep results in order.

            :param: query: the es query.
            :return the es query.
            """
            return query.params(preserve_order=True) \
                .sort({'pid': {"order": "asc"}})

        query = AcqOrderLinesSearch().filter('term', acq_order__pid=self.pid)
        if includes:
            query = query.filter('terms', status=includes)

        if output == 'count':
            return query.count()
        elif output == 'query':
            return preserve_order(query)
        else:
            return get_objects(AcqOrderLine, preserve_order(query))

    def get_order_provisional_total_amount(self):
        """Get provisional total amount of this order."""
        search = AcqOrderLinesSearch()\
            .filter('term', acq_order__pid=self.pid) \
            .exclude('term', status=AcqOrderLineStatus.CANCELLED)
        search.aggs.metric(
            'order_total_amount',
            'sum',
            field='total_amount',
            script={'source': 'Math.round(_value*100)/100.00'}
        )
        results = search.execute()
        return round(results.aggregations.order_total_amount.value, 2)

    def get_order_expenditure_total_amount(self):
        """Get total amount of known expenditures of this order."""
        search = AcqReceiptsSearch().filter('term', acq_order__pid=self.pid)
        search.aggs.metric(
            'receipt_total_amount',
            'sum',
            field='total_amount',
            script={'source': 'Math.round(_value*100)/100.00'}
        )
        results = search.execute()
        return round(results.aggregations.receipt_total_amount.value, 2)

    def get_account_statement(self):
        """Get account statement for this order.

        Accounting informations contains data about encumbrance and
        expenditure. For each section, we can find the total amount and the
        related item quantity.
        """
        return {
            'provisional': {
                'total_amount': self.get_order_provisional_total_amount(),
                'quantity': self.item_quantity,
            },
            'expenditure': {
                'total_amount': self.get_order_expenditure_total_amount(),
                'quantity': self.item_received_quantity
            }
        }

    def get_links_to_me(self, get_pids=False):
        """Get related record links.

        :param get_pids: if True list of related record pids, if False count
                         of related records.
        """
        output = 'query' if get_pids else 'count'
        links = {
            'orders': self.get_related_orders(output=output),
            'order_lines': self.get_order_lines(output=output),
            'receipts': self.get_receipts(output=output),
        }
        links = {k: v for k, v in links.items() if v}
        if get_pids:
            links = {k: sorted_pids(v) for k, v in links.items()}
        return links

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        cannot_delete = {}
        # Note: not possible to delete records attached to rolled_over budget.
        if not self.is_active:
            cannot_delete['links'] = {'rolled_over': True}
            return cannot_delete
        links = self.get_links_to_me()
        # The link with AcqOrderLine resources isn't a reason to not delete
        # an AcqOrder. Indeed, when we delete an AcqOrder, we also delete all
        # related AcqOrderLines (cascade delete). Check the extension
        # ``pre_delete`` hook.
        links.pop('order_lines', None)
        if self.status != AcqOrderStatus.PENDING:
            cannot_delete['others'] = {
                _('Order status is %s') % _(self.status): True
            }
        if links:
            cannot_delete['links'] = links
        return cannot_delete

    def send_order(self, emails=None):
        """Send an acquisition order to list of recipients.

        Creates an acquisition_order notification from order and dispatch it.
        If the notification is well dispatched, then update the related
        order_lines to ORDERED status, then reindex the order to obtain the
        ORDERED status on it if necessary.

        :param emails: list of recipients emails.
        :return: the list of created notifications
        """
        # Create the notification and dispatch it synchronously.
        record = {
            'creation_date': datetime.now(timezone.utc).isoformat(),
            'notification_type': NotificationType.ACQUISITION_ORDER,
            'context': {
                'order': {'$ref': get_ref_for_pid('acor', self.pid)},
                'recipients': emails
            }
        }
        notif = Notification.create(data=record, dbcommit=True, reindex=True)
        dispatcher_result = Dispatcher.dispatch_notifications(
            notification_pids=[notif.get('pid')])

        # If the dispatcher result is correct, update the order_lines status
        # and reindex myself. Reload the notification to obtain the right
        # notification metadata (status, process_date, ...)
        if dispatcher_result.get('sent', 0):
            order_date = datetime.now().strftime('%Y-%m-%d')
            order_lines = self.get_order_lines(
                includes=[AcqOrderLineStatus.APPROVED])
            for order_line in order_lines:
                order_line['order_date'] = order_date
                order_line.update(order_line, dbcommit=True, reindex=True)
            self.reindex()
            notif = Notification.get_record(notif.id)

        return notif


class AcqOrdersIndexer(IlsRecordsIndexer):
    """Indexing documents in Elasticsearch."""

    record_cls = AcqOrder

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='acor')

    def delete(self, record):
        """Delete a record from indexer.

        First delete order lines from the ES index, then delete the order.
        """
        es_query = AcqOrderLinesSearch()\
            .filter('term', acq_order__pid=record.pid)
        if es_query.count():
            es_query.delete()
            AcqOrderLinesSearch.flush_and_refresh()
        super().delete(record)
