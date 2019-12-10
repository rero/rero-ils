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

"""API for manipulating vendors."""

from functools import partial

from .models import VendorIdentifier
from ..api import IlsRecord, IlsRecordsSearch
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..providers import Provider

# provider
VendorProvider = type(
    'VendorProvider',
    (Provider,),
    dict(identifier=VendorIdentifier, pid_type='vndr')
)
# minter
vendor_id_minter = partial(id_minter, provider=VendorProvider)
# fetcher
vendor_id_fetcher = partial(id_fetcher, provider=VendorProvider)


class VendorsSearch(IlsRecordsSearch):
    """VendorsSearch."""

    class Meta:
        """Search only on vendor index."""

        index = 'vendors'


class Vendor(IlsRecord):
    """Vendor class."""

    minter = vendor_id_minter
    fetcher = vendor_id_fetcher
    provider = VendorProvider
