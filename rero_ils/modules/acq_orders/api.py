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

"""API for manipulating Acquisition Orders."""
from datetime import datetime
from functools import partial

from flask_babelex import gettext as _

from .extensions import AcquisitionOrderCompleteDataExtension, \
    AcquisitionOrderExtension
from .models import AcqOrderIdentifier, AcqOrderMetadata, AcqOrderStatus
from ..acq_order_lines.api import AcqOrderLine, AcqOrderLinesSearch
from ..acq_order_lines.models import AcqOrderLineStatus
from ..api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..notifications.api import Notification
from ..notifications.dispatcher import Dispatcher
from ..notifications.models import NotificationType
from ..providers import Provider
from ..utils import extracted_data_from_ref, get_ref_for_pid, sorted_pids
from ..vendors.api import Vendor

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


class AcqOrder(IlsRecord):
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
            return _('Can not have multiple notes of same type.')

        return True

    @classmethod
    def create(cls, data, id_=None, delete_pid=False,
               dbcommit=False, reindex=False, **kwargs):
        """Create acquisition order record."""
        # TODO : should be used into `pre_create` hook extensions but seems not
        #   work as expected.
        AcquisitionOrderCompleteDataExtension.populate_currency(data)
        record = super().create(
            data, id_, delete_pid, dbcommit, reindex, **kwargs)
        return record

    @property
    def vendor(self):
        """Shortcut for vendor."""
        return Vendor.get_record_by_pid(self.vendor_pid)

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
    def vendor_pid(self):
        """Shortcut for acquisition order vendor pid."""
        return extracted_data_from_ref(self.get('vendor'))

    @property
    def status(self):
        """Get the order status based on related order lines statuses."""
        status = AcqOrderStatus.PENDING
        search = AcqOrderLinesSearch().filter('term', acq_order__pid=self.pid)
        search.aggs.bucket('status', 'terms', field='status')
        results = search.execute()
        statuses = [hit.key for hit in results.aggregations.status.buckets]

        if len(statuses) > 1:
            if AcqOrderLineStatus.RECEIVED in statuses:
                status = AcqOrderStatus.PARTIALLY_RECEIVED
            elif AcqOrderLineStatus.ORDERED in statuses:
                status = AcqOrderStatus.ORDERED
        elif len(statuses) == 1:
            map = {
                AcqOrderLineStatus.APPROVED: AcqOrderStatus.PENDING,
                AcqOrderLineStatus.ORDERED: AcqOrderStatus.ORDERED,
                AcqOrderLineStatus.RECEIVED: AcqOrderStatus.RECEIVED,
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
    def item_quantity_received(self):
        """Get the total of received item quantity for this order."""
        search = AcqOrderLinesSearch() \
            .filter('term', acq_order__pid=self.pid) \
            .exclude('term', status=AcqOrderLineStatus.CANCELLED)
        search.aggs.metric('total_quantity', 'sum', field='quantity_received')
        results = search.execute()
        return results.aggregations.total_quantity.value

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

    def get_order_lines(self, output=None, includes=None):
        """Get order lines related to this order.

        :param output: output method. 'count', 'pids' or None.
        :param includes: a list of statuses to include order lines.
        :return a generator of related order lines (or length).
        """
        def _list_object():
            for hit in query.source().scan():
                yield AcqOrderLine.get_record_by_id(hit.meta.id)

        query = AcqOrderLinesSearch()\
            .filter('term', acq_order__pid=self.pid)
        if includes:
            query = query.filter('terms', status=includes)

        if output == 'count':
            return query.count()
        elif output == 'pids':
            return sorted_pids(query)
        else:
            return _list_object()

    def get_order_total_amount(self):
        """Get total amount of order."""
        search = AcqOrderLinesSearch()\
            .filter('term', acq_order__pid=self.pid) \
            .exclude('term', status=AcqOrderLineStatus.CANCELLED)
        search.aggs.metric(
            'order_total_amount',
            'sum',
            field='total_amount',
            script={
                'source': 'Math.round(_value*100)/100.00'
            }
        )
        results = search.execute()
        return results.aggregations.order_total_amount.value

    def get_links_to_me(self, get_pids=False):
        """Record links.

        :param get_pids: if True list of linked pids
                         if False count of linked records
        """
        output = 'pids' if get_pids else 'count'
        links = {
            'acq_order_lines': self.get_order_lines(output=output)
        }
        return {k: v for k, v in links.items() if v}

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        cannot_delete = {}
        links = self.get_links_to_me()
        # The link with AcqOrderLine ressources isn't a reason to not delete
        # an AcqOrder. Indeed, when we delete an AcqOrder, we also delete all
        # related AcqOrderLines (cascade delete). Check the extension
        # ``pre_delete`` hook.
        links.pop('acq_order_lines', None)
        if self.status != AcqOrderStatus.PENDING:
            cannot_delete['others'] = {
                _(f'Order status is {self.status}'): True
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
            "notification_type": NotificationType.ACQUISITION_ORDER,
            "context": {
                "order": {'$ref': get_ref_for_pid('acor', self.pid)},
                "recipients": emails
            }
        }
        notif = Notification.create(data=record, dbcommit=True, reindex=True)
        dispatcher_result = Dispatcher.dispatch_notifications(
            notification_pids=[notif.get('pid')])

        # If the dispatcher result is good, update the order_lines status and
        # reindex myself. Reload the notification to obtain the right
        # notification metadata (status, process_date, ...)
        if dispatcher_result.get('sent', 0):
            order_date = datetime.now().strftime('%Y-%m-%d')
            order_lines = self.get_order_lines(
                includes=[AcqOrderLineStatus.APPROVED])
            for order_line in order_lines:
                order_line['order_date'] = order_date
                order_line.update(order_line, dbcommit=True, reindex=True)
            self.reindex()
            notif = Notification.get_record_by_id(notif.id)

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
