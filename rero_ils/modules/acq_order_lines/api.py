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

"""API for manipulating Acquisition Order Line."""

from copy import deepcopy
from functools import partial

from .extensions import AcqOrderLineCheckAccountBalance
from .models import AcqOrderLineIdentifier, AcqOrderLineMetadata
from ..api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..providers import Provider
from ..utils import extracted_data_from_ref

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
        fields = ('*', )
        facets = {}

        default_filter = None


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

    _extensions = [AcqOrderLineCheckAccountBalance()]

    @classmethod
    def create(cls, data, id_=None, delete_pid=False,
               dbcommit=True, reindex=True, **kwargs):
        """Create Acquisition Order Line record."""
        record = super().create(
            data, id_, delete_pid, dbcommit, reindex, **kwargs)
        return record

    def update(self, data, dbcommit=True, reindex=True):
        """Update Acquisition Order Line record."""
        new_data = deepcopy(dict(self))
        new_data.update(data)
        super().update(new_data, dbcommit, reindex)
        return self

    @property
    def order_pid(self):
        """Shortcut for acquisition order pid."""
        return extracted_data_from_ref(self.get('acq_order'))

    @property
    def order(self):
        """Shortcut to the order of the order line."""
        return extracted_data_from_ref(self.get('acq_order'), data='record')

    @property
    def account(self):
        """Shortcut to the account object related to this order line."""
        return extracted_data_from_ref(self.get('acq_account'), data='record')

    @property
    def organisation_pid(self):
        """Get organisation pid for acquisition order."""
        return self.order.organisation_pid

    @property
    def library_pid(self):
        """Shortcut for acquisition order library pid."""
        return self.order.library_pid


class AcqOrderLinesIndexer(IlsRecordsIndexer):
    """Indexing Acquisition Order Line in Elasticsearch."""

    record_cls = AcqOrderLine

    def index(self, record):
        """Index an Acquisition Order Line and update total amount of order."""
        from ..acq_orders.api import AcqOrder
        return_value = super().index(record)
        order = AcqOrder.get_record_by_pid(record.order_pid)
        order.reindex()
        record.account.reindex()
        return return_value

    def delete(self, record):
        """Delete a Acquisition Order Line and update total amount of order."""
        from ..acq_orders.api import AcqOrder
        return_value = super().delete(record)
        order = AcqOrder.get_record_by_pid(record.order_pid)
        order.reindex()
        record.account.reindex()
        return return_value

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='acol')
