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

"""API for manipulating acq_accounts."""

from functools import partial

from flask import current_app

from .models import AcqAccountIdentifier
from ..acq_order_lines.api import AcqOrderLinesSearch
from ..api import IlsRecord, IlsRecordsSearch
from ..fetchers import id_fetcher
from ..libraries.api import Library
from ..minters import id_minter
from ..providers import Provider

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


class AcqAccount(IlsRecord):
    """AcqAccount class."""

    minter = acq_account_id_minter
    fetcher = acq_account_id_fetcher
    provider = AcqAccountProvider

    @classmethod
    def create(cls, data, id_=None, delete_pid=False,
               dbcommit=False, reindex=False, **kwargs):
        """Create acq account record."""
        cls._acq_account_build_org_ref(data)
        record = super(AcqAccount, cls).create(
            data, id_, delete_pid, dbcommit, reindex, **kwargs)
        return record

    @classmethod
    def _acq_account_build_org_ref(cls, data):
        """Build $ref for the organisation of the acq account."""
        library_pid = data.get('library', {}).get('pid')
        if not library_pid:
            library_pid = data.get('library').get(
                '$ref').split('libraries/')[1]
            org_pid = Library.get_record_by_pid(library_pid).organisation_pid
        base_url = current_app.config.get('RERO_ILS_APP_BASE_URL')
        url_api = '{base_url}/api/{doc_type}/{pid}'
        org_ref = {
            '$ref': url_api.format(
                base_url=base_url,
                doc_type='organisations',
                pid=org_pid or cls.organisation_pid)
        }
        data['organisation'] = org_ref

    @property
    def library_pid(self):
        """Shortcut for acq account library pid."""
        return self.replace_refs().get('library').get('pid')

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
