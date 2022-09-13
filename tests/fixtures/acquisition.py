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

from rero_ils.modules.acquisition.acq_accounts.api import AcqAccount, \
    AcqAccountsSearch
from rero_ils.modules.acquisition.acq_invoices.api import AcquisitionInvoice, \
    AcquisitionInvoicesSearch
from rero_ils.modules.acquisition.acq_order_lines.api import AcqOrderLine, \
    AcqOrderLinesSearch
from rero_ils.modules.acquisition.acq_orders.api import AcqOrder, \
    AcqOrdersSearch
from rero_ils.modules.acquisition.acq_receipt_lines.api import \
    AcqReceiptLine, AcqReceiptLinesSearch
from rero_ils.modules.acquisition.acq_receipts.api import AcqReceipt, \
    AcqReceiptsSearch
from rero_ils.modules.acquisition.budgets.api import Budget, BudgetsSearch
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
def vendor2_martigny(app, org_martigny, vendor2_martigny_data):
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
def vendor3_martigny(app, org_martigny, vendor3_martigny_data):
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
def vendor_sion(app, org_sion, vendor_sion_data):
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
def vendor2_sion(app, org_sion, vendor2_sion_data):
    """Load vendor record."""
    vendor = Vendor.create(
        data=vendor2_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(VendorsSearch.Meta.index)
    return vendor


@pytest.fixture(scope="function")
def budget_2020_martigny_data_tmp(acquisition):
    """Load standard budget 2020 of martigny."""
    return deepcopy(acquisition.get('budg1'))


@pytest.fixture(scope="module")
def budget_2020_sion_data(acquisition):
    """Load budget 2020 sion."""
    return deepcopy(acquisition.get('budg2'))


@pytest.fixture(scope="module")
def budget_2020_martigny_data(acquisition):
    """Load budget 2020 martigny."""
    return deepcopy(acquisition.get('budg1'))


@pytest.fixture(scope="module")
def budget_2019_martigny_data(acquisition):
    """Load budget 2019 martigny."""
    return deepcopy(acquisition.get('budg3'))


@pytest.fixture(scope="module")
def budget_2018_martigny_data(acquisition):
    """Load budget 2018 martigny."""
    return deepcopy(acquisition.get('budg4'))


@pytest.fixture(scope="module")
def budget_2017_martigny_data(acquisition):
    """Load budget 2017 martigny."""
    return deepcopy(acquisition.get('budg5'))


@pytest.fixture(scope="module")
def budget_2017_martigny(
        app, org_martigny, budget_2017_martigny_data):
    """Load budget 2017 martigny record."""
    budget = Budget.create(
        data=budget_2017_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(BudgetsSearch.Meta.index)
    return budget


@pytest.fixture(scope="module")
def budget_2018_martigny(
        app, org_martigny, budget_2018_martigny_data):
    """Load budget 2018 martigny record."""
    budget = Budget.create(
        data=budget_2018_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(BudgetsSearch.Meta.index)
    return budget


@pytest.fixture(scope="module")
def budget_2020_martigny(
        app, org_martigny, budget_2020_martigny_data):
    """Load budget 2020 martigny record."""
    budget = Budget.create(
        data=budget_2020_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(BudgetsSearch.Meta.index)
    return budget


@pytest.fixture(scope="module")
def budget_2019_martigny(
        app, org_martigny, budget_2019_martigny_data):
    """Load budget 2019 martigny record."""
    budget = Budget.create(
        data=budget_2019_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(BudgetsSearch.Meta.index)
    return budget


@pytest.fixture(scope="module")
def budget_2020_sion(
        app, org_sion, budget_2020_sion_data):
    """Load budget 2020 sion record."""
    budget = Budget.create(
        data=budget_2020_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(BudgetsSearch.Meta.index)
    return budget


@pytest.fixture(scope="function")
def acq_account_fiction_martigny_data_tmp(acquisition):
    """Load standard acq account of martigny."""
    return deepcopy(acquisition.get('acac1'))


@pytest.fixture(scope="module")
def acq_account_fiction_martigny_data(acquisition):
    """Load acq_account lib martigny fiction data."""
    return deepcopy(acquisition.get('acac1'))


@pytest.fixture(scope="module")
def acq_account_fiction_martigny(
        app, lib_martigny, acq_account_fiction_martigny_data,
        budget_2020_martigny):
    """Load acq_account lib martigny fiction record."""
    acac = AcqAccount.create(
        data=acq_account_fiction_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(AcqAccountsSearch.Meta.index)
    return acac


@pytest.fixture(scope="module")
def acq_account_books_martigny_data(acquisition):
    """Load acq_account lib martigny books data."""
    return deepcopy(acquisition.get('acac6'))


@pytest.fixture(scope="module")
def acq_account_books_martigny(
        app, lib_martigny, acq_account_books_martigny_data,
        budget_2020_martigny):
    """Load acq_account lib martigny books record."""
    acac = AcqAccount.create(
        data=acq_account_books_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(AcqAccountsSearch.Meta.index)
    return acac


@pytest.fixture(scope="module")
def acq_account_books_saxon_data(acquisition):
    """Load acq_account lib saxon books data."""
    return deepcopy(acquisition.get('acac2'))


@pytest.fixture(scope="module")
def acq_account_books_saxon(
        app, lib_saxon, acq_account_books_saxon_data, budget_2020_martigny):
    """Load acq_account lib saxon books record."""
    acac = AcqAccount.create(
        data=acq_account_books_saxon_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(AcqAccountsSearch.Meta.index)
    return acac


@pytest.fixture(scope="module")
def acq_account_general_fully_data(acquisition):
    """Load acq_account lib fully general data."""
    return deepcopy(acquisition.get('acac3'))


@pytest.fixture(scope="module")
def acq_account_general_fully(
        app, lib_fully, acq_account_general_fully_data, budget_2020_martigny):
    """Load acq_account lib fully general record."""
    acac = AcqAccount.create(
        data=acq_account_general_fully_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(AcqAccountsSearch.Meta.index)
    return acac


@pytest.fixture(scope="module")
def acq_account_fiction_sion_data(acquisition):
    """Load acq_account lib sion fiction data."""
    return deepcopy(acquisition.get('acac4'))


@pytest.fixture(scope="module")
def acq_account_fiction_sion(
        app, lib_saxon, acq_account_fiction_sion_data, budget_2020_sion):
    """Load acq_account lib sion fiction record."""
    acac = AcqAccount.create(
        data=acq_account_fiction_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(AcqAccountsSearch.Meta.index)
    return acac


@pytest.fixture(scope="module")
def acq_account_general_aproz_data(acquisition):
    """Load acq_account lib aproz general data."""
    return deepcopy(acquisition.get('acac5'))


@pytest.fixture(scope="module")
def acq_account_general_aproz(
        app, lib_saxon, acq_account_general_aproz_data, budget_2020_sion):
    """Load acq_account lib aproz general record."""
    acac = AcqAccount.create(
        data=acq_account_general_aproz_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(AcqAccountsSearch.Meta.index)
    return acac


@pytest.fixture(scope="module")
def acq_order_fiction_martigny_data(acquisition):
    """Load acq_order lib martigny fiction data."""
    return deepcopy(acquisition.get('acor1'))


@pytest.fixture(scope="function")
def acq_order_fiction_martigny_data_tmp(acquisition):
    """Load acq_order lib martigny fiction data."""
    return deepcopy(acquisition.get('acor1'))


@pytest.fixture(scope="module")
def acq_order_fiction_martigny(
        app, lib_martigny, vendor_martigny, acq_order_fiction_martigny_data):
    """Load acq_order lib martigny fiction record."""
    acor = AcqOrder.create(
        data=acq_order_fiction_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(AcqOrdersSearch.Meta.index)
    return acor


@pytest.fixture(scope="module")
def acq_receipt_fiction_martigny_data(acquisition):
    """Load acq_receipt lib martigny fiction data."""
    return deepcopy(acquisition.get('acre1'))


@pytest.fixture(scope="module")
def acq_receipt_line_1_fiction_martigny_data(acquisition):
    """Load acq_receipt_line_1 lib martigny fiction data."""
    return deepcopy(acquisition.get('acrl1'))


@pytest.fixture(scope="module")
def acq_receipt_line_2_fiction_martigny_data(acquisition):
    """Load acq_receipt_line_2 lib martigny fiction data."""
    return deepcopy(acquisition.get('acrl2'))


@pytest.fixture(scope="function")
def acq_receipt_fiction_martigny_data_tmp(acquisition):
    """Load acq_receipt lib martigny fiction data."""
    return deepcopy(acquisition.get('acre1'))


@pytest.fixture(scope="function")
def acq_receipt_line_1_fiction_martigny_data_tmp(acquisition):
    """Load acq_receipt_line_1 lib martigny fiction data."""
    return deepcopy(acquisition.get('acrl1'))


@pytest.fixture(scope="module")
def acq_receipt_fiction_martigny(
        app, lib_martigny, acq_order_fiction_martigny,
        acq_receipt_fiction_martigny_data, acq_account_fiction_martigny):
    """Load acq_receipt lib martigny fiction record."""
    acor = AcqReceipt.create(
        data=acq_receipt_fiction_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(AcqReceiptsSearch.Meta.index)
    return acor


@pytest.fixture(scope="module")
def acq_receipt_line_1_fiction_martigny(
        app, acq_receipt_fiction_martigny, acq_order_line_fiction_martigny,
        acq_receipt_line_1_fiction_martigny_data):
    """Load acq_receipt_line_1 lib martigny fiction record."""
    acrl = AcqReceiptLine.create(
        data=acq_receipt_line_1_fiction_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(AcqReceiptLinesSearch.Meta.index)
    return acrl


@pytest.fixture(scope="module")
def acq_receipt_line_2_fiction_martigny(
        app, acq_receipt_fiction_martigny, acq_order_line2_fiction_martigny,
        acq_receipt_line_2_fiction_martigny_data):
    """Load acq_receipt_line_2 lib martigny fiction record."""
    acrl = AcqReceiptLine.create(
        data=acq_receipt_line_2_fiction_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(AcqReceiptLinesSearch.Meta.index)
    return acrl


@pytest.fixture(scope="module")
def acq_order_fiction_saxon_data(acquisition):
    """Load acq_order lib saxon fiction data."""
    return deepcopy(acquisition.get('acor2'))


@pytest.fixture(scope="module")
def acq_order_fiction_saxon(
        app, lib_saxon, vendor_martigny, acq_order_fiction_saxon_data):
    """Load acq_order lib saxon fiction record."""
    acor = AcqOrder.create(
        data=acq_order_fiction_saxon_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(AcqOrdersSearch.Meta.index)
    return acor


@pytest.fixture(scope="module")
def acq_receipt_fiction_saxon_data(acquisition):
    """Load acq_receipt lib saxon fiction data."""
    return deepcopy(acquisition.get('acre2'))


@pytest.fixture(scope="module")
def acq_receipt_line_fiction_saxon_data(acquisition):
    """Load acq_receipt_line lib saxon fiction data."""
    return deepcopy(acquisition.get('acrl3'))


@pytest.fixture(scope="module")
def acq_receipt_fiction_saxon(
        app, lib_saxon, vendor_martigny, acq_order_fiction_saxon,
        acq_receipt_fiction_saxon_data, acq_account_books_saxon):
    """Load acq_receipt lib saxon fiction record."""
    acre = AcqReceipt.create(
        data=acq_receipt_fiction_saxon_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(AcqReceiptsSearch.Meta.index)
    return acre


@pytest.fixture(scope="module")
def acq_receipt_line_fiction_saxon(
        app, acq_receipt_fiction_saxon, acq_order_line_fiction_saxon,
        acq_receipt_line_fiction_saxon_data):
    """Load acq_receipt_line lib saxon fiction record."""
    acrl = AcqReceiptLine.create(
        data=acq_receipt_line_fiction_saxon_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(AcqReceiptLinesSearch.Meta.index)
    return acrl


@pytest.fixture(scope="module")
def acq_order_fiction_sion_data(acquisition):
    """Load acq_order lib sion fiction data."""
    return deepcopy(acquisition.get('acor3'))


@pytest.fixture(scope="module")
def acq_order_fiction_sion(
        app, lib_sion, vendor_sion, acq_order_fiction_sion_data):
    """Load acq_order lib sion fiction record."""
    acor = AcqOrder.create(
        data=acq_order_fiction_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(AcqOrdersSearch.Meta.index)
    return acor


@pytest.fixture(scope="module")
def acq_receipt_fiction_sion_data(acquisition):
    """Load acq_receipt lib sion fiction data."""
    return deepcopy(acquisition.get('acre3'))


@pytest.fixture(scope="module")
def acq_receipt_line_fiction_sion_data(acquisition):
    """Load acq_receipt_line lib sion fiction data."""
    return deepcopy(acquisition.get('acrl4'))


@pytest.fixture(scope="module")
def acq_receipt_fiction_sion(
        app, lib_sion, vendor_sion, acq_order_fiction_sion,
        acq_receipt_fiction_sion_data, acq_account_fiction_sion):
    """Load acq_receipt lib sion fiction record."""
    acor = AcqReceipt.create(
        data=acq_receipt_fiction_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(AcqReceiptsSearch.Meta.index)
    return acor


@pytest.fixture(scope="module")
def acq_receipt_line_fiction_sion(
        app, acq_receipt_fiction_sion, acq_order_line_fiction_sion,
        acq_receipt_line_fiction_sion_data):
    """Load acq_receipt_line lib sion fiction record."""
    acrl = AcqReceiptLine.create(
        data=acq_receipt_line_fiction_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(AcqReceiptLinesSearch.Meta.index)
    return acrl


@pytest.fixture(scope="module")
def acq_order_line_fiction_martigny_data(acquisition):
    """Load acq_order_line lib martigny fiction data."""
    return deepcopy(acquisition.get('acol1'))


@pytest.fixture(scope="function")
def acq_order_line_fiction_martigny_data_tmp(acquisition):
    """Load acq_order_line lib martigny fiction data."""
    return deepcopy(acquisition.get('acol1'))


@pytest.fixture(scope="module")
def acq_order_line_fiction_martigny(
        app, acq_account_fiction_martigny, document,
        acq_order_fiction_martigny, acq_order_line_fiction_martigny_data):
    """Load acq_order_line lib martigny fiction record."""
    acol = AcqOrderLine.create(
        data=acq_order_line_fiction_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(AcqOrderLinesSearch.Meta.index)
    return acol


@pytest.fixture(scope="module")
def acq_order_line2_fiction_martigny_data(acquisition):
    """Load acq_order_line lib martigny fiction data."""
    return deepcopy(acquisition.get('acol2'))


@pytest.fixture(scope="module")
def acq_order_line2_fiction_martigny(
        app, acq_account_fiction_martigny, document,
        acq_order_fiction_martigny, acq_order_line2_fiction_martigny_data):
    """Load acq_order_line lib martigny fiction record."""
    acol = AcqOrderLine.create(
        data=acq_order_line2_fiction_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(AcqOrderLinesSearch.Meta.index)
    return acol


@pytest.fixture(scope="module")
def acq_order_line3_fiction_martigny_data(acquisition):
    """Load acq_order_line lib martigny fiction data."""
    return deepcopy(acquisition.get('acol5'))


@pytest.fixture(scope="module")
def acq_order_line3_fiction_martigny(
        app, acq_account_fiction_martigny, document,
        acq_order_fiction_martigny, acq_order_line3_fiction_martigny_data):
    """Load acq_order_line lib martigny fiction record."""
    acol = AcqOrderLine.create(
        data=acq_order_line3_fiction_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(AcqOrderLinesSearch.Meta.index)
    return acol


@pytest.fixture(scope="module")
def acq_order_line_fiction_saxon_data(acquisition):
    """Load acq_order_line lib saxon fiction data."""
    return deepcopy(acquisition.get('acol3'))


@pytest.fixture(scope="module")
def acq_order_line_fiction_saxon(
        app, acq_account_books_saxon,
        acq_order_fiction_saxon, acq_order_line_fiction_saxon_data):
    """Load acq_order_line lib saxon fiction record."""
    acol = AcqOrderLine.create(
        data=acq_order_line_fiction_saxon_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(AcqOrderLinesSearch.Meta.index)
    return acol


@pytest.fixture(scope="module")
def acq_order_line_fiction_sion_data(acquisition):
    """Load acq_order_line lib sion fiction data."""
    return deepcopy(acquisition.get('acol4'))


@pytest.fixture(scope="module")
def acq_order_line_fiction_sion(
        app, acq_account_fiction_sion,
        acq_order_fiction_sion, acq_order_line_fiction_sion_data):
    """Load acq_order_line lib sion fiction record."""
    acol = AcqOrderLine.create(
        data=acq_order_line_fiction_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(AcqOrderLinesSearch.Meta.index)
    return acol


@pytest.fixture(scope="module")
def acq_invoice_fiction_martigny_data(acquisition):
    """Load acq_invoice lib martigny fiction data."""
    return deepcopy(acquisition.get('acin1'))


@pytest.fixture(scope="module")
def acq_invoice_fiction_martigny(
        app, lib_martigny, vendor_martigny, acq_invoice_fiction_martigny_data,
        document, document_ref, acq_order_fiction_martigny,
        acq_order_line_fiction_martigny, acq_order_line2_fiction_martigny):
    """Load acq_invoice lib martigny fiction record."""
    acin = AcquisitionInvoice.create(
        data=acq_invoice_fiction_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(AcquisitionInvoicesSearch.Meta.index)
    return acin


@pytest.fixture(scope="module")
def acq_invoice_fiction_saxon_data(acquisition):
    """Load acq_invoice lib martigny fiction data."""
    return deepcopy(acquisition.get('acin2'))


@pytest.fixture(scope="module")
def acq_invoice_fiction_saxon(
        app, lib_saxon, vendor2_martigny, acq_invoice_fiction_saxon_data,
        acq_order_fiction_saxon, acq_order_line_fiction_saxon):
    """Load acq_invoice lib saxon fiction record."""
    acin = AcquisitionInvoice.create(
        data=acq_invoice_fiction_saxon_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(AcquisitionInvoicesSearch.Meta.index)
    return acin


@pytest.fixture(scope="module")
def acq_invoice_fiction_sion_data(acquisition):
    """Load acq_invoice lib sion fiction data."""
    return deepcopy(acquisition.get('acin3'))


@pytest.fixture(scope="module")
def acq_invoice_fiction_sion(
        app, lib_sion, vendor_sion, acq_invoice_fiction_sion_data,
        acq_order_fiction_sion, acq_order_line_fiction_sion):
    """Load acq_invoice lib sion fiction record."""
    acin = AcquisitionInvoice.create(
        data=acq_invoice_fiction_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(AcquisitionInvoicesSearch.Meta.index)
    return acin
