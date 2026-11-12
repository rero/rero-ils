# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests patron transaction events facets."""

from copy import deepcopy

from flask import url_for
from invenio_accounts.testutils import login_user_via_session

from rero_ils.modules.patron_transaction_events.api import (
    PatronTransactionEvent,
    PatronTransactionEventsSearch,
)
from rero_ils.modules.patron_transaction_events.models import PatronTransactionEventType
from rero_ils.modules.patron_transactions.models import PatronTransactionType
from rero_ils.modules.utils import get_ref_for_pid
from tests.utils import get_json


def _create_payment(transaction, amount, subtype, operator):
    """Create a payment event for the given patron transaction."""
    data = deepcopy(dict(next(transaction.events)))
    data.pop("creation_date", None)
    data.update(
        {
            "type": PatronTransactionEventType.PAYMENT,
            "subtype": subtype,
            "amount": amount,
            "operator": {"$ref": get_ref_for_pid("patrons", operator.pid)},
        }
    )
    return PatronTransactionEvent.create(data, dbcommit=True, reindex=True, delete_pid=True)


def test_patron_transaction_events_total_facet(
    client,
    system_librarian_martigny,
    lib_martigny,
    lib_saxon,
    patron_transaction_overdue_martigny,
    patron_transaction_overdue_saxon,
):
    """Test the `total` facet follows the active post filters."""
    _create_payment(patron_transaction_overdue_martigny, 1, "cash", system_librarian_martigny)
    _create_payment(patron_transaction_overdue_saxon, 0.5, "debit_card", system_librarian_martigny)
    PatronTransactionEventsSearch.flush_and_refresh()

    login_user_via_session(client, system_librarian_martigny.user)

    def get_total(**kwargs):
        res = client.get(url_for("invenio_records_rest.ptre_list", **kwargs))
        assert res.status_code == 200
        total = get_json(res)["aggregations"]["total"]
        subtotals = {bucket["key"]: bucket["subtotal"]["value"] for bucket in total["subtype"]["buckets"]}
        return total["payment"]["value"], subtotals

    assert get_total() == (1.5, {"cash": 1, "debit_card": 0.5})
    # owning library and location are post filters: the total must follow them
    assert get_total(owning_library=lib_martigny.pid) == (1, {"cash": 1})
    assert get_total(owning_library=lib_saxon.pid) == (0.5, {"debit_card": 0.5})
    saxon_location_pid = patron_transaction_overdue_saxon.loan.item.location_pid
    assert get_total(owning_location=saxon_location_pid) == (0.5, {"debit_card": 0.5})
    # category is a post filter too
    assert get_total(category=PatronTransactionType.OVERDUE) == (1.5, {"cash": 1, "debit_card": 0.5})
    assert get_total(category=PatronTransactionType.PHOTOCOPY) == (0, {})
    # event types and subtypes are combined with OR, as for the hits
    assert get_total(subtype="cash") == (1, {"cash": 1})
    assert get_total(owning_library=lib_saxon.pid, subtype="cash") == (0, {})
    assert get_total(type=PatronTransactionEventType.FEE) == (0, {})
    assert get_total(type=PatronTransactionEventType.FEE, subtype="cash") == (1, {"cash": 1})
    all_payments = (1.5, {"cash": 1, "debit_card": 0.5})
    assert get_total(type=PatronTransactionEventType.PAYMENT, subtype="overdue") == all_payments
