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

"""API for manipulating Acquisition Order Line."""

from copy import deepcopy
from functools import partial

from .models import AcqOrderLineIdentifier, AcqOrderLineMetadata
from ..api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..providers import Provider
from ..utils import get_ref_for_pid

# provider
AcqOrderLineProvider = type(
    'AcqOrderLineProvider',
    (Provider,),
    dict(identifier=AcqOrderLineIdentifier, pid_type='acol')
)
# minter
acq_order_line_id_minter = partial(id_minter, provider=AcqOrderLineProvider)
# fetcher
acq_order_line_id_fetcher = partial(id_fetcher, provider=AcqOrderLineProvider)


class AcqOrderLinesSearch(IlsRecordsSearch):
    """Acquisition Order Line Search."""

    class Meta:
        """Search only on Acquisition Order Line index."""

        index = 'acq_order_lines'
        doc_types = None


class AcqOrderLine(IlsRecord):
    """Acquisition Order Line class."""

    minter = acq_order_line_id_minter
    fetcher = acq_order_line_id_fetcher
    provider = AcqOrderLineProvider
    model_cls = AcqOrderLineMetadata
    pids_exist_check = {
        'required': {
            'doc': 'document',
            'acac': 'acq_account',
            'acor': 'acq_order'
        },
        'not_required': {
            'org': 'organisation'
        }
    }

    @classmethod
    def create(cls, data, id_=None, delete_pid=False,
               dbcommit=True, reindex=True, **kwargs):
        """Create Acquisition Order Line record."""
        cls._acq_order_line_build_org_ref(data)
        cls._build_total_amount_for_order_line(data)
        record = super(AcqOrderLine, cls).create(
            data, id_, delete_pid, dbcommit, reindex, **kwargs)
        return record

    def update(self, data, dbcommit=True, reindex=True):
        """Update Acquisition Order Line record."""
        new_data = deepcopy(dict(self))
        new_data.update(data)
        self._acq_order_line_build_org_ref(new_data)
        self._build_total_amount_for_order_line(new_data)
        super(AcqOrderLine, self).update(new_data, dbcommit, reindex)
        return self

    @classmethod
    def _acq_order_line_build_org_ref(cls, data):
        """Build $ref for the organisation of the acquisition order."""
        from ..acq_orders.api import AcqOrder
        order = data.get('acq_order', {})
        order_pid = order.get('pid') or \
            order.get('$ref').split('acq_orders/')[1]
        data['organisation'] = {'$ref': get_ref_for_pid(
            'org',
            AcqOrder.get_record_by_pid(order_pid).organisation_pid
        )}
        return data

    @classmethod
    def _build_total_amount_for_order_line(cls, data):
        """Build total amount for order line."""
        total_amount = data['amount'] * data['quantity']
        if data['discount_amount']:
            total_amount -= data['discount_amount']
        data['total_amount'] = total_amount

    @property
    def order_pid(self):
        """Shortcut for acquisition order pid."""
        return self.replace_refs().get('acq_order').get('pid')

    @property
    def organisation_pid(self):
        """Get organisation pid for acquisition order."""
        return self.get_order().organisation_pid

    @property
    def library_pid(self):
        """Shortcut for acquisition order library pid."""
        return self.get_order().library_pid

    def get_order(self):
        """Shortcut to the order of the order line."""
        from ..acq_orders.api import AcqOrder
        return AcqOrder.get_record_by_pid(self.order_pid)

    def get_number_of_acq_order_lines(self):
        """Get number of aquisition order lines."""
        results = AcqOrderLinesSearch().filter(
            'term', acq_order__pid=self.order_pid).source().count()
        return results


class AcqOrderLinesIndexer(IlsRecordsIndexer):
    """Indexing Acquisition Order Line in Elasticsearch."""

    record_cls = AcqOrderLine

    def index(self, record):
        """Index an Acquisition Order Line and update total amount of order."""
        return_value = super(AcqOrderLinesIndexer, self).index(record)
        self._update_order_total_amount(record)

        return return_value

    def delete(self, record):
        """Delete a Acquisition Order Line and update total amount of order."""
        return_value = super(AcqOrderLinesIndexer, self).delete(record)
        self._update_order_total_amount(record)

        return return_value

    def _update_order_total_amount(self, record):
        """Update total amount of the order."""
        from ..acq_orders.api import AcqOrder

        order_pid = record.replace_refs()['acq_order']['pid']
        order = AcqOrder.get_record_by_pid(order_pid)
        order['total_amount'] = order.get_order_total_amount()
        order.update(order, dbcommit=True, reindex=True)
