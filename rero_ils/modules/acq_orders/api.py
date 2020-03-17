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

"""API for manipulating Acquisition Orders."""

from functools import partial

from .models import AcqOrderIdentifier, AcqOrderMetadata
from ..acq_order_lines.api import AcqOrderLinesSearch
from ..api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from ..fetchers import id_fetcher
from ..libraries.api import Library
from ..minters import id_minter
from ..providers import Provider
from ..utils import get_ref_for_pid

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


class AcqOrder(IlsRecord):
    """AcqOrder class."""

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

    @classmethod
    def create(cls, data, id_=None, delete_pid=False,
               dbcommit=False, reindex=False, **kwargs):
        """Create acquisition order record."""
        cls._acq_order_build_org_ref(data)
        record = super(AcqOrder, cls).create(
            data, id_, delete_pid, dbcommit, reindex, **kwargs)
        return record

    def update(self, data, dbcommit=False, reindex=False):
        """Update acq order record."""
        self._acq_order_build_org_ref(data)
        super(AcqOrder, self).update(data, dbcommit, reindex)
        return self

    @classmethod
    def _acq_order_build_org_ref(cls, data):
        """Build $ref for the organisation of the acquisition order."""
        library = data.get('library', {})
        library_pid = library.get('pid') or \
            library.get('$ref').split('libraries/')[1]
        data['organisation'] = {'$ref': get_ref_for_pid(
            'org',
            Library.get_record_by_pid(library_pid).organisation_pid
        )}
        return data

    @property
    def organisation_pid(self):
        """Shortcut for acquisition order pid."""
        return self.replace_refs().get('organisation').get('pid')

    @property
    def library_pid(self):
        """Shortcut for acquisition order library pid."""
        return self.replace_refs()['library']['pid']

    def get_number_of_acq_order_lines(self):
        """Get number of acquisition order lines."""
        results = AcqOrderLinesSearch().filter(
            'term', acq_order__pid=self.pid).source().count()
        return results

    def get_order_total_amount(self):
        """Get total amount of order."""
        search = AcqOrderLinesSearch().filter(
            'term', acq_order__pid=self.pid)
        search.aggs.metric('order_total_amount', 'sum', field='total_amount')
        results = search.execute()
        return results.aggregations.order_total_amount.value

    def get_links_to_me(self):
        """Get number of links."""
        links = {}
        acq_orders = self.get_number_of_acq_order_lines()
        if acq_orders:
            links['acq_order_lines'] = acq_orders
        return links

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        cannot_delete = {}
        links = self.get_links_to_me()
        if links:
            cannot_delete['links'] = links
        return cannot_delete


class AcqOrdersIndexer(IlsRecordsIndexer):
    """Indexing documents in Elasticsearch."""

    record_cls = AcqOrder
