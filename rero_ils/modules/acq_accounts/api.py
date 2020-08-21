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

"""API for manipulating acq_accounts."""

from functools import partial

from .models import AcqAccountIdentifier, AcqAccountMetadata
from ..acq_order_lines.api import AcqOrderLinesSearch
from ..api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from ..fetchers import id_fetcher
from ..libraries.api import Library
from ..minters import id_minter
from ..providers import Provider
from ..utils import get_ref_for_pid

# provider
AcqAccountProvider = type(
    'AcqAccountProvider',
    (Provider,),
    dict(identifier=AcqAccountIdentifier, pid_type='acac')
)
# minter
acq_account_id_minter = partial(id_minter, provider=AcqAccountProvider)
# fetcher
acq_account_id_fetcher = partial(id_fetcher, provider=AcqAccountProvider)


class AcqAccountsSearch(IlsRecordsSearch):
    """AcqAccountsSearch."""

    class Meta:
        """Search only on acq_account index."""

        index = 'acq_accounts'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class AcqAccount(IlsRecord):
    """AcqAccount class."""

    minter = acq_account_id_minter
    fetcher = acq_account_id_fetcher
    provider = AcqAccountProvider
    model_cls = AcqAccountMetadata
    pids_exist_check = {
        'required': {
            'lib': 'library',
            'budg': 'budget'
        },
        'not_required': {
            'org': 'organisation'
        }
    }

    @classmethod
    def create(cls, data, id_=None, delete_pid=False,
               dbcommit=False, reindex=False, **kwargs):
        """Create acq account record."""
        cls._acq_account_build_org_ref(data)
        record = super(AcqAccount, cls).create(
            data, id_, delete_pid, dbcommit, reindex, **kwargs)
        return record

    def update(self, data, dbcommit=False, reindex=False):
        """Update acq account record."""
        self._acq_account_build_org_ref(data)
        super(AcqAccount, self).update(data, dbcommit, reindex)
        return self

    @classmethod
    def _acq_account_build_org_ref(cls, data):
        """Build $ref for the organisation of the acq account."""
        library = data.get('library', {})
        library_pid = library.get('pid') or \
            library.get('$ref').split('libraries/')[1]
        data['organisation'] = {'$ref': get_ref_for_pid(
            'org',
            Library.get_record_by_pid(library_pid).organisation_pid
        )}
        return data

    @property
    def library_pid(self):
        """Shortcut for acq account library pid."""
        return self.replace_refs()['library']['pid']

    def get_number_of_acq_order_lines(self):
        """Get number of acquisition order lines linked to this account."""
        results = AcqOrderLinesSearch().filter(
            'term', acq_account__pid=self.pid).source().count()
        return results

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


class AcqAccountsIndexer(IlsRecordsIndexer):
    """Indexing documents in Elasticsearch."""

    record_cls = AcqAccount

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super(AcqAccountsIndexer, self).bulk_index(record_id_iterator,
                                                   doc_type='acac')
