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

"""Common pytest fixtures and plugins."""


from copy import deepcopy

import pytest
from utils import flush_index

from rero_ils.modules.vendors.api import Vendor, VendorsSearch


@pytest.fixture(scope="module")
def vendor_martigny_data(acquisition):
    """Load vendor data."""
    return deepcopy(acquisition.get('vndr1'))


@pytest.fixture(scope="module")
def vendor_martigny(app, org_martigny, vendor_martigny_data):
    """Load vendor record."""
    vendor = Vendor.create(
        data=vendor_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(VendorsSearch.Meta.index)
    return vendor


@pytest.fixture(scope="module")
def vendor_martigny_tmp(app, org_martigny, vendor_martigny):
    """Load vendor record."""
    vendor = Vendor.create(
        data=vendor_martigny,
        delete_pid=True,
        dbcommit=True,
        reindex=True)
    flush_index(VendorsSearch.Meta.index)
    return vendor


@pytest.fixture(scope="module")
def vendor2_martigny_data(acquisition):
    """Load vendor data."""
    return deepcopy(acquisition.get('vndr2'))


@pytest.fixture(scope="module")
def vendor2_martigny(app, vendor2_martigny_data):
    """Load vendor record."""
    vendor = Vendor.create(
        data=vendor2_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(VendorsSearch.Meta.index)
    return vendor


@pytest.fixture(scope="module")
def vendor3_martigny_data(acquisition):
    """Load vendor 3 data."""
    return deepcopy(acquisition.get('vndr3'))


@pytest.fixture(scope="module")
def vendor3_martigny(app, vendor3_martigny_data):
    """Load vendor record."""
    vendor = Vendor.create(
        data=vendor3_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(VendorsSearch.Meta.index)
    return vendor


@pytest.fixture(scope="module")
def vendor_sion_data(acquisition):
    """Load vendor data."""
    return deepcopy(acquisition.get('vndr4'))


@pytest.fixture(scope="module")
def vendor_sion(app, vendor_sion_data):
    """Load vendor record."""
    vendor = Vendor.create(
        data=vendor_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(VendorsSearch.Meta.index)
    return vendor


@pytest.fixture(scope="module")
def vendor2_sion_data(acquisition):
    """Load vendor data."""
    return deepcopy(acquisition.get('vndr5'))


@pytest.fixture(scope="module")
def vendor2_sion(app, vendor2_sion_data):
    """Load vendor record."""
    vendor = Vendor.create(
        data=vendor2_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(VendorsSearch.Meta.index)
    return vendor
