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
from ..providers import Provider
from ..utils import extracted_data_from_ref

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
        """Get the order status based on related order lines status."""
        status = AcqOrderStatus.PENDING
        search = AcqOrderLinesSearch().filter('term', acq_order__pid=self.pid)
        search.aggs.bucket('status', 'terms', field='status')
        results = search.execute()
        statues = [hit.key for hit in results.aggregations.status.buckets]

        if len(statues) > 1:
            if AcqOrderLineStatus.RECEIVED in statues:
                status = AcqOrderStatus.PARTIALLY_RECEIVED
        elif len(statues) == 1:
            map = {
                AcqOrderLineStatus.APPROVED: AcqOrderStatus.PENDING,
                AcqOrderLineStatus.ORDERED: AcqOrderStatus.ORDERED,
                AcqOrderLineStatus.RECEIVED: AcqOrderStatus.RECEIVED,
                AcqOrderLineStatus.CANCELED: AcqOrderStatus.CANCELED,
            }
            if statues[0] in map:
                status = map[statues[0]]

        return status

    def get_order_lines(self, count=False):
        """Get order lines related to this order.

        :param count: if true, return the number of related order lines.
        :return a generator of related order lines (or length).
        """
        def _list_object():
            for hit in eq_query.source().scan():
                yield AcqOrderLine.get_record_by_id(hit.meta.id)

        eq_query = AcqOrderLinesSearch()\
            .filter('term', acq_order__pid=self.pid)
        return eq_query.count() if count else _list_object()

    def get_order_total_amount(self):
        """Get total amount of order."""
        search = AcqOrderLinesSearch().filter('term', acq_order__pid=self.pid)
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

    def get_links_to_me(self):
        """Get related resources."""
        links = {
            'acq_order_lines': self.get_order_lines(count=True)
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
