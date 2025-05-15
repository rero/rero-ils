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

import mock
import pytest

from rero_ils.modules.acquisition.acq_accounts.api import AcqAccount, AcqAccountsSearch
from rero_ils.modules.acquisition.acq_order_lines.api import (
    AcqOrderLine,
    AcqOrderLinesSearch,
)
from rero_ils.modules.acquisition.acq_orders.api import AcqOrder, AcqOrdersSearch
from rero_ils.modules.acquisition.acq_orders.models import AcqOrderStatus
from rero_ils.modules.acquisition.acq_receipt_lines.api import (
    AcqReceiptLine,
    AcqReceiptLinesSearch,
)
from rero_ils.modules.acquisition.acq_receipts.api import AcqReceipt, AcqReceiptsSearch
from rero_ils.modules.acquisition.budgets.api import Budget, BudgetsSearch
from rero_ils.modules.utils import get_ref_for_pid as get_ref
from rero_ils.modules.vendors.api import Vendor, VendorsSearch
from tests.api.acquisition.acq_utils import _make_resource


@pytest.fixture(scope="module")
def vendor_martigny_data(acquisition):
    """Load vendor data."""
    return deepcopy(acquisition.get("vndr1"))


@pytest.fixture(scope="module")
def vendor_martigny(app, org_martigny, vendor_martigny_data):
    """Load vendor record."""
    vendor = Vendor.create(
        data=vendor_martigny_data, delete_pid=False, dbcommit=True, reindex=True
    )
    VendorsSearch.flush_and_refresh()
    return vendor


@pytest.fixture(scope="module")
def vendor_martigny_tmp(app, org_martigny, vendor_martigny):
    """Load vendor record."""
    vendor = Vendor.create(
        data=vendor_martigny, delete_pid=True, dbcommit=True, reindex=True
    )
    VendorsSearch.flush_and_refresh()
    return vendor


@pytest.fixture(scope="module")
def vendor2_martigny_data(acquisition):
    """Load vendor data."""
    return deepcopy(acquisition.get("vndr2"))


@pytest.fixture(scope="module")
def vendor2_martigny(app, org_martigny, vendor2_martigny_data):
    """Load vendor record."""
    vendor = Vendor.create(
        data=vendor2_martigny_data, delete_pid=False, dbcommit=True, reindex=True
    )
    VendorsSearch.flush_and_refresh()
    return vendor


@pytest.fixture(scope="module")
def vendor3_martigny_data(acquisition):
    """Load vendor 3 data."""
    return deepcopy(acquisition.get("vndr3"))


@pytest.fixture(scope="module")
def vendor3_martigny(app, org_martigny, vendor3_martigny_data):
    """Load vendor record."""
    vendor = Vendor.create(
        data=vendor3_martigny_data, delete_pid=False, dbcommit=True, reindex=True
    )
    VendorsSearch.flush_and_refresh()
    return vendor


@pytest.fixture(scope="module")
def vendor_sion_data(acquisition):
    """Load vendor data."""
    return deepcopy(acquisition.get("vndr4"))


@pytest.fixture(scope="module")
def vendor_sion(app, org_sion, vendor_sion_data):
    """Load vendor record."""
    vendor = Vendor.create(
        data=vendor_sion_data, delete_pid=False, dbcommit=True, reindex=True
    )
    VendorsSearch.flush_and_refresh()
    return vendor


@pytest.fixture(scope="module")
def vendor2_sion_data(acquisition):
    """Load vendor data."""
    return deepcopy(acquisition.get("vndr5"))


@pytest.fixture(scope="module")
def vendor2_sion(app, org_sion, vendor2_sion_data):
    """Load vendor record."""
    vendor = Vendor.create(
        data=vendor2_sion_data, delete_pid=False, dbcommit=True, reindex=True
    )
    VendorsSearch.flush_and_refresh()
    return vendor


@pytest.fixture(scope="function")
def budget_2020_martigny_data_tmp(acquisition):
    """Load standard budget 2020 of martigny."""
    return deepcopy(acquisition.get("budg1"))


@pytest.fixture(scope="module")
def budget_2020_sion_data(acquisition):
    """Load budget 2020 sion."""
    return deepcopy(acquisition.get("budg2"))


@pytest.fixture(scope="module")
def budget_2020_martigny_data(acquisition):
    """Load budget 2020 martigny."""
    return deepcopy(acquisition.get("budg1"))


@pytest.fixture(scope="module")
def budget_2019_martigny_data(acquisition):
    """Load budget 2019 martigny."""
    return deepcopy(acquisition.get("budg3"))


@pytest.fixture(scope="module")
def budget_2018_martigny_data(acquisition):
    """Load budget 2018 martigny."""
    return deepcopy(acquisition.get("budg4"))


@pytest.fixture(scope="module")
def budget_2017_martigny_data(acquisition):
    """Load budget 2017 martigny."""
    return deepcopy(acquisition.get("budg5"))


@pytest.fixture(scope="module")
def budget_2017_martigny(app, org_martigny, budget_2017_martigny_data):
    """Load budget 2017 martigny record."""
    budget = Budget.create(
        data=budget_2017_martigny_data, delete_pid=False, dbcommit=True, reindex=True
    )
    BudgetsSearch.flush_and_refresh()
    return budget


@pytest.fixture(scope="module")
def budget_2018_martigny(app, org_martigny, budget_2018_martigny_data):
    """Load budget 2018 martigny record."""
    budget = Budget.create(
        data=budget_2018_martigny_data, delete_pid=False, dbcommit=True, reindex=True
    )
    BudgetsSearch.flush_and_refresh()
    return budget


@pytest.fixture(scope="module")
def budget_2020_martigny(app, org_martigny, budget_2020_martigny_data):
    """Load budget 2020 martigny record."""
    budget = Budget.create(
        data=budget_2020_martigny_data, delete_pid=False, dbcommit=True, reindex=True
    )
    BudgetsSearch.flush_and_refresh()
    return budget


@pytest.fixture(scope="module")
def budget_2019_martigny(app, org_martigny, budget_2019_martigny_data):
    """Load budget 2019 martigny record."""
    budget = Budget.create(
        data=budget_2019_martigny_data, delete_pid=False, dbcommit=True, reindex=True
    )
    BudgetsSearch.flush_and_refresh()
    return budget


@pytest.fixture(scope="module")
def budget_2020_sion(app, org_sion, budget_2020_sion_data):
    """Load budget 2020 sion record."""
    budget = Budget.create(
        data=budget_2020_sion_data, delete_pid=False, dbcommit=True, reindex=True
    )
    BudgetsSearch.flush_and_refresh()
    return budget


@pytest.fixture(scope="function")
def acq_account_fiction_martigny_data_tmp(acquisition):
    """Load standard acq account of martigny."""
    return deepcopy(acquisition.get("acac1"))


@pytest.fixture(scope="module")
def acq_account_fiction_martigny_data(acquisition):
    """Load acq_account lib martigny fiction data."""
    return deepcopy(acquisition.get("acac1"))


@pytest.fixture(scope="module")
def acq_account_fiction_martigny(
    app, lib_martigny, acq_account_fiction_martigny_data, budget_2020_martigny
):
    """Load acq_account lib martigny fiction record."""
    acac = AcqAccount.create(
        data=acq_account_fiction_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    AcqAccountsSearch.flush_and_refresh()
    return acac


@pytest.fixture(scope="module")
def acq_account_books_martigny_data(acquisition):
    """Load acq_account lib martigny books data."""
    return deepcopy(acquisition.get("acac6"))


@pytest.fixture(scope="module")
def acq_account_books_martigny(
    app, lib_martigny, acq_account_books_martigny_data, budget_2020_martigny
):
    """Load acq_account lib martigny books record."""
    acac = AcqAccount.create(
        data=acq_account_books_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    AcqAccountsSearch.flush_and_refresh()
    return acac


@pytest.fixture(scope="module")
def acq_account_books_saxon_data(acquisition):
    """Load acq_account lib saxon books data."""
    return deepcopy(acquisition.get("acac2"))


@pytest.fixture(scope="module")
def acq_account_books_saxon(
    app, lib_saxon, acq_account_books_saxon_data, budget_2020_martigny
):
    """Load acq_account lib saxon books record."""
    acac = AcqAccount.create(
        data=acq_account_books_saxon_data, delete_pid=False, dbcommit=True, reindex=True
    )
    AcqAccountsSearch.flush_and_refresh()
    return acac


@pytest.fixture(scope="module")
def acq_account_general_fully_data(acquisition):
    """Load acq_account lib fully general data."""
    return deepcopy(acquisition.get("acac3"))


@pytest.fixture(scope="module")
def acq_account_general_fully(
    app, lib_fully, acq_account_general_fully_data, budget_2020_martigny
):
    """Load acq_account lib fully general record."""
    acac = AcqAccount.create(
        data=acq_account_general_fully_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    AcqAccountsSearch.flush_and_refresh()
    return acac


@pytest.fixture(scope="module")
def acq_account_fiction_sion_data(acquisition):
    """Load acq_account lib sion fiction data."""
    return deepcopy(acquisition.get("acac4"))


@pytest.fixture(scope="module")
def acq_account_fiction_sion(
    app, lib_sion, acq_account_fiction_sion_data, budget_2020_sion
):
    """Load acq_account lib sion fiction record."""
    acac = AcqAccount.create(
        data=acq_account_fiction_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    AcqAccountsSearch.flush_and_refresh()
    return acac


@pytest.fixture(scope="module")
def acq_account_general_aproz_data(acquisition):
    """Load acq_account lib aproz general data."""
    return deepcopy(acquisition.get("acac5"))


@pytest.fixture(scope="module")
def acq_account_general_aproz(
    app, lib_saxon, acq_account_general_aproz_data, budget_2020_sion
):
    """Load acq_account lib aproz general record."""
    acac = AcqAccount.create(
        data=acq_account_general_aproz_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    AcqAccountsSearch.flush_and_refresh()
    return acac


@pytest.fixture(scope="module")
def acq_order_fiction_martigny_data(acquisition):
    """Load acq_order lib martigny fiction data."""
    return deepcopy(acquisition.get("acor1"))


@pytest.fixture(scope="function")
def acq_order_fiction_martigny_data_tmp(acquisition):
    """Load acq_order lib martigny fiction data."""
    return deepcopy(acquisition.get("acor1"))


@pytest.fixture(scope="module")
def acq_order_fiction_martigny(
    app, lib_martigny, vendor_martigny, acq_order_fiction_martigny_data
):
    """Load acq_order lib martigny fiction record."""
    acor = AcqOrder.create(
        data=acq_order_fiction_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    AcqOrdersSearch.flush_and_refresh()
    return acor


@pytest.fixture(scope="module")
def acq_receipt_fiction_martigny_data(acquisition):
    """Load acq_receipt lib martigny fiction data."""
    return deepcopy(acquisition.get("acre1"))


@pytest.fixture(scope="module")
def acq_receipt_line_1_fiction_martigny_data(acquisition):
    """Load acq_receipt_line_1 lib martigny fiction data."""
    return deepcopy(acquisition.get("acrl1"))


@pytest.fixture(scope="module")
def acq_receipt_line_2_fiction_martigny_data(acquisition):
    """Load acq_receipt_line_2 lib martigny fiction data."""
    return deepcopy(acquisition.get("acrl2"))


@pytest.fixture(scope="function")
def acq_receipt_fiction_martigny_data_tmp(acquisition):
    """Load acq_receipt lib martigny fiction data."""
    return deepcopy(acquisition.get("acre1"))


@pytest.fixture(scope="function")
def acq_receipt_line_1_fiction_martigny_data_tmp(acquisition):
    """Load acq_receipt_line_1 lib martigny fiction data."""
    return deepcopy(acquisition.get("acrl1"))


@pytest.fixture(scope="module")
def acq_receipt_fiction_martigny(
    app,
    lib_martigny,
    acq_order_fiction_martigny,
    acq_order_line_fiction_martigny,
    acq_receipt_fiction_martigny_data,
    acq_account_fiction_martigny,
):
    """Load acq_receipt lib martigny fiction record."""
    if acq_order_fiction_martigny.status == AcqOrderStatus.PENDING:
        with mock.patch(
            "rero_ils.modules.notifications.dispatcher.Dispatcher.dispatch_notifications",
            mock.MagicMock(return_value={"sent": 1}),
        ):
            acq_order_fiction_martigny.send_order(
                [
                    {"type": "to", "address": "ils@foo.com"},
                    {"type": "reply_to", "address": "admin@foo.com"},
                ]
            )
    acor = AcqReceipt.create(
        data=acq_receipt_fiction_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    AcqReceiptsSearch.flush_and_refresh()
    return acor


@pytest.fixture(scope="module")
def acq_receipt_line_1_fiction_martigny(
    app,
    acq_order_fiction_martigny,
    acq_order_line_fiction_martigny,
    acq_receipt_fiction_martigny,
    acq_receipt_line_1_fiction_martigny_data,
):
    """Load acq_receipt_line_1 lib martigny fiction record."""
    acrl = AcqReceiptLine.create(
        data=acq_receipt_line_1_fiction_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    AcqReceiptLinesSearch.flush_and_refresh()
    return acrl


@pytest.fixture(scope="module")
def acq_receipt_line_2_fiction_martigny(
    app,
    acq_order_fiction_martigny,
    acq_order_line2_fiction_martigny,
    acq_receipt_fiction_martigny,
    acq_receipt_line_2_fiction_martigny_data,
):
    """Load acq_receipt_line_2 lib martigny fiction record."""
    acrl = AcqReceiptLine.create(
        data=acq_receipt_line_2_fiction_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    AcqReceiptLinesSearch.flush_and_refresh()
    return acrl


@pytest.fixture(scope="module")
def acq_order_fiction_saxon_data(acquisition):
    """Load acq_order lib saxon fiction data."""
    return deepcopy(acquisition.get("acor2"))


@pytest.fixture(scope="module")
def acq_order_fiction_saxon(
    app, lib_saxon, vendor2_martigny, acq_order_fiction_saxon_data
):
    """Load acq_order lib saxon fiction record."""
    acor = AcqOrder.create(
        data=acq_order_fiction_saxon_data, delete_pid=False, dbcommit=True, reindex=True
    )
    AcqOrdersSearch.flush_and_refresh()
    return acor


@pytest.fixture(scope="module")
def acq_receipt_fiction_saxon_data(acquisition):
    """Load acq_receipt lib saxon fiction data."""
    return deepcopy(acquisition.get("acre2"))


@pytest.fixture(scope="module")
def acq_receipt_line_fiction_saxon_data(acquisition):
    """Load acq_receipt_line lib saxon fiction data."""
    return deepcopy(acquisition.get("acrl3"))


@pytest.fixture(scope="module")
def acq_receipt_fiction_saxon(
    app,
    lib_saxon,
    vendor_martigny,
    acq_order_fiction_saxon,
    acq_order_line_fiction_saxon,
    acq_receipt_fiction_saxon_data,
    acq_account_books_saxon,
):
    """Load acq_receipt lib saxon fiction record."""
    if acq_order_fiction_saxon.status == AcqOrderStatus.PENDING:
        with mock.patch(
            "rero_ils.modules.notifications.dispatcher.Dispatcher.dispatch_notifications",
            mock.MagicMock(return_value={"sent": 1}),
        ):
            acq_order_fiction_saxon.send_order(
                [
                    {"type": "to", "address": "ils@foo.com"},
                    {"type": "reply_to", "address": "admin@foo.com"},
                ]
            )
    acre = AcqReceipt.create(
        data=acq_receipt_fiction_saxon_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    AcqReceiptsSearch.flush_and_refresh()
    return acre


@pytest.fixture(scope="module")
def acq_receipt_line_fiction_saxon(
    app,
    acq_order_fiction_saxon,
    acq_order_line_fiction_saxon,
    acq_receipt_fiction_saxon,
    acq_receipt_line_fiction_saxon_data,
):
    """Load acq_receipt_line lib saxon fiction record."""
    acrl = AcqReceiptLine.create(
        data=acq_receipt_line_fiction_saxon_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    AcqReceiptLinesSearch.flush_and_refresh()
    return acrl


@pytest.fixture(scope="module")
def acq_order_fiction_sion_data(acquisition):
    """Load acq_order lib sion fiction data."""
    return deepcopy(acquisition.get("acor3"))


@pytest.fixture(scope="module")
def acq_order_fiction_sion(app, lib_sion, vendor_sion, acq_order_fiction_sion_data):
    """Load acq_order lib sion fiction record."""
    acor = AcqOrder.create(
        data=acq_order_fiction_sion_data, delete_pid=False, dbcommit=True, reindex=True
    )
    AcqOrdersSearch.flush_and_refresh()
    return acor


@pytest.fixture(scope="module")
def acq_receipt_fiction_sion_data(acquisition):
    """Load acq_receipt lib sion fiction data."""
    return deepcopy(acquisition.get("acre3"))


@pytest.fixture(scope="module")
def acq_receipt_line_fiction_sion_data(acquisition):
    """Load acq_receipt_line lib sion fiction data."""
    return deepcopy(acquisition.get("acrl4"))


@pytest.fixture(scope="module")
def acq_receipt_fiction_sion(
    app,
    lib_sion,
    vendor_sion,
    acq_account_fiction_sion,
    acq_order_fiction_sion,
    acq_order_line_fiction_sion,
    acq_receipt_fiction_sion_data,
):
    """Load acq_receipt lib sion fiction record."""
    if acq_order_fiction_sion.status == AcqOrderStatus.PENDING:
        with mock.patch(
            "rero_ils.modules.notifications.dispatcher.Dispatcher.dispatch_notifications",
            mock.MagicMock(return_value={"sent": 1}),
        ):
            acq_order_fiction_sion.send_order(
                [
                    {"type": "to", "address": "ils@foo.com"},
                    {"type": "reply_to", "address": "admin@foo.com"},
                ]
            )
    acor = AcqReceipt.create(
        data=acq_receipt_fiction_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    AcqReceiptsSearch.flush_and_refresh()
    return acor


@pytest.fixture(scope="module")
def acq_receipt_line_fiction_sion(
    app,
    acq_order_fiction_sion,
    acq_order_line_fiction_sion,
    acq_receipt_fiction_sion,
    acq_receipt_line_fiction_sion_data,
):
    """Load acq_receipt_line lib sion fiction record."""
    acrl = AcqReceiptLine.create(
        data=acq_receipt_line_fiction_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    AcqReceiptLinesSearch.flush_and_refresh()
    return acrl


@pytest.fixture(scope="module")
def acq_order_line_fiction_martigny_data(acquisition):
    """Load acq_order_line lib martigny fiction data."""
    return deepcopy(acquisition.get("acol1"))


@pytest.fixture(scope="function")
def acq_order_line_fiction_martigny_data_tmp(acquisition):
    """Load acq_order_line lib martigny fiction data."""
    return deepcopy(acquisition.get("acol1"))


@pytest.fixture(scope="module")
def acq_order_line_fiction_martigny(
    app,
    acq_order_fiction_martigny,
    acq_account_fiction_martigny,
    document,
    acq_order_line_fiction_martigny_data,
):
    """Load acq_order_line lib martigny fiction record."""
    acol = AcqOrderLine.create(
        data=acq_order_line_fiction_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    AcqOrderLinesSearch.flush_and_refresh()
    return acol


@pytest.fixture(scope="module")
def acq_order_line2_fiction_martigny_data(acquisition):
    """Load acq_order_line lib martigny fiction data."""
    return deepcopy(acquisition.get("acol2"))


@pytest.fixture(scope="module")
def acq_order_line2_fiction_martigny(
    app,
    acq_account_fiction_martigny,
    document,
    acq_order_fiction_martigny,
    acq_order_line2_fiction_martigny_data,
):
    """Load acq_order_line lib martigny fiction record."""
    acol = AcqOrderLine.create(
        data=acq_order_line2_fiction_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    AcqOrderLinesSearch.flush_and_refresh()
    return acol


@pytest.fixture(scope="module")
def acq_order_line3_fiction_martigny_data(acquisition):
    """Load acq_order_line lib martigny fiction data."""
    return deepcopy(acquisition.get("acol5"))


@pytest.fixture(scope="module")
def acq_order_line3_fiction_martigny(
    app,
    acq_account_fiction_martigny,
    document,
    acq_order_fiction_martigny,
    acq_order_line3_fiction_martigny_data,
):
    """Load acq_order_line lib martigny fiction record."""
    acol = AcqOrderLine.create(
        data=acq_order_line3_fiction_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    AcqOrderLinesSearch.flush_and_refresh()
    return acol


@pytest.fixture(scope="module")
def acq_order_line_fiction_saxon_data(acquisition):
    """Load acq_order_line lib saxon fiction data."""
    return deepcopy(acquisition.get("acol3"))


@pytest.fixture(scope="module")
def acq_order_line_fiction_saxon(
    app,
    document,
    acq_account_books_saxon,
    acq_order_fiction_saxon,
    acq_order_line_fiction_saxon_data,
):
    """Load acq_order_line lib saxon fiction record."""
    acol = AcqOrderLine.create(
        data=acq_order_line_fiction_saxon_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    AcqOrderLinesSearch.flush_and_refresh()
    return acol


@pytest.fixture(scope="module")
def acq_order_line_fiction_sion_data(acquisition):
    """Load acq_order_line lib sion fiction data."""
    return deepcopy(acquisition.get("acol4"))


@pytest.fixture(scope="module")
def acq_order_line_fiction_sion(
    app,
    document,
    acq_account_fiction_sion,
    acq_order_fiction_sion,
    acq_order_line_fiction_sion_data,
):
    """Load acq_order_line lib sion fiction record."""
    acol = AcqOrderLine.create(
        data=acq_order_line_fiction_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    AcqOrderLinesSearch.flush_and_refresh()
    return acol


@pytest.fixture(scope="function")
def acq_full_structure_a(client, lib_martigny, vendor_martigny, document, org_martigny):
    """Create a full acquisition structure.

    Budget_A
      +--> Account_1
      |    +--> Order_10
      |         +--> OrderLine_10_1
      |         +--> OrderLine_10_2
      |         +--> Reception_10_1
      |              +--> ReceptionLine_10_1_1 (ref to OrderLine_10_1)
      +--> Account_2
      |    +--> Order_20
      +--> Account_3
           +--> Account_3.1
                +--> Order_30
                     +--> OrderLine_30_1
                     +--> Reception_30_1
                          + ReceptionLine_30_1_1 (ref to OrderLine_30_1)
    """
    org_ref = get_ref("org", org_martigny.pid)
    lib_ref = get_ref("lib", lib_martigny.pid)
    vendor_ref = get_ref("vndr", vendor_martigny.pid)
    # Budget ==============================================
    budget = _make_resource(
        client,
        "budg",
        {
            "name": "Budget A",
            "start_date": "2022-01-01",
            "end_date": "2022-12-31",
            "is_active": True,
            "organisation": {"$ref": org_ref},
        },
    )
    budget_ref = get_ref("budg", budget.pid)
    # Accounts ============================================
    acac1 = _make_resource(
        client,
        "acac",
        {
            "name": "account_1",
            "number": "000.0000.01",
            "allocated_amount": 1000,
            "budget": {"$ref": budget_ref},
            "library": {"$ref": lib_ref},
        },
    )
    acac2 = _make_resource(
        client,
        "acac",
        {
            "name": "account_2",
            "number": "000.0000.02",
            "allocated_amount": 2000,
            "budget": {"$ref": budget_ref},
            "library": {"$ref": lib_ref},
        },
    )
    acac3 = _make_resource(
        client,
        "acac",
        {
            "name": "account_3",
            "number": "000.0000.03",
            "allocated_amount": 3000,
            "budget": {"$ref": budget_ref},
            "library": {"$ref": lib_ref},
        },
    )
    acac31 = _make_resource(
        client,
        "acac",
        {
            "name": "account_3.1",
            "number": "000.0000.03",
            "allocated_amount": 300,
            "budget": {"$ref": budget_ref},
            "library": {"$ref": lib_ref},
            "parent": {"$ref": get_ref("acac", acac3.pid)},
        },
    )
    # Orders ==============================================
    order_10 = _make_resource(
        client,
        "acor",
        {"vendor": {"$ref": vendor_ref}, "library": {"$ref": lib_ref}},
    )
    order_20 = _make_resource(
        client,
        "acor",
        {"vendor": {"$ref": vendor_ref}, "library": {"$ref": lib_ref}},
    )
    order_30 = _make_resource(
        client,
        "acor",
        {"vendor": {"$ref": vendor_ref}, "library": {"$ref": lib_ref}},
    )
    # OrderLines ==========================================
    orderline_10_1 = _make_resource(
        client,
        "acol",
        {
            "acq_account": {"$ref": get_ref("acac", acac1.pid)},
            "acq_order": {"$ref": get_ref("acor", order_10.pid)},
            "document": {"$ref": get_ref("doc", document.pid)},
            "quantity": 4,
            "amount": 25,
        },
    )
    orderline_10_2 = _make_resource(
        client,
        "acol",
        {
            "acq_account": {"$ref": get_ref("acac", acac1.pid)},
            "acq_order": {"$ref": get_ref("acor", order_10.pid)},
            "document": {"$ref": get_ref("doc", document.pid)},
            "quantity": 2,
            "amount": 15,
        },
    )
    orderline_30_1 = _make_resource(
        client,
        "acol",
        {
            "acq_account": {"$ref": get_ref("acac", acac31.pid)},
            "acq_order": {"$ref": get_ref("acor", order_30.pid)},
            "document": {"$ref": get_ref("doc", document.pid)},
            "quantity": 3,
            "amount": 33,
        },
    )
    for order in [order_10, order_20, order_30]:
        with mock.patch(
            "rero_ils.modules.notifications.dispatcher.Dispatcher.dispatch_notifications",
            mock.MagicMock(return_value={"sent": 1}),
        ):
            order.send_order(
                [
                    {"type": "to", "address": "ils@foo.com"},
                    {"type": "reply_to", "address": "admin@foo.com"},
                ]
            )

    # Reception ===========================================
    reception_10_1 = _make_resource(
        client,
        "acre",
        {
            "acq_order": {"$ref": get_ref("acor", order_10.pid)},
            "amount_adjustments": [
                {
                    "label": "handling fees",
                    "amount": 2.0,
                    "acq_account": {"$ref": get_ref("acac", acac1.pid)},
                }
            ],
            "library": {"$ref": lib_ref},
        },
    )
    reception_30_1 = _make_resource(
        client,
        "acre",
        {
            "acq_order": {"$ref": get_ref("acor", order_30.pid)},
            "library": {"$ref": lib_ref},
        },
    )
    # ReceptionLine =======================================
    receptionLine_10_1_1 = _make_resource(
        client,
        "acrl",
        {
            "acq_receipt": {"$ref": get_ref("acre", reception_10_1.pid)},
            "acq_order_line": {"$ref": get_ref("acol", orderline_10_1.pid)},
            "quantity": 2,
            "amount": 25,
            "receipt_date": "2022-06-01",
            "library": {"$ref": lib_ref},
        },
    )
    receptionLine_30_1_1 = _make_resource(
        client,
        "acrl",
        {
            "acq_receipt": {"$ref": get_ref("acre", reception_30_1.pid)},
            "acq_order_line": {"$ref": get_ref("acol", orderline_30_1.pid)},
            "quantity": 1,
            "amount": 30,
            "receipt_date": "2022-07-01",
            "library": {"$ref": lib_ref},
        },
    )

    return budget
