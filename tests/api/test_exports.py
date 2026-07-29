# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests resource streamed exports."""

from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from invenio_db import db

from rero_ils.modules.utils import get_ref_for_pid
from tests.utils import get_csv, parse_csv, parse_xlsx


def test_items_exports(client, patron_martigny, librarian_martigny, item_lib_martigny):
    """Test inventory streamed export permissions and content."""
    url = url_for("api_exports.item_export", q=f"pid:{item_lib_martigny.pid}")

    res = client.get(url)
    assert res.status_code == 401

    login_user_via_session(client, patron_martigny.user)
    res = client.get(url)
    assert res.status_code == 403

    login_user_via_session(client, librarian_martigny.user)
    res = client.get(url)
    assert res.status_code == 200
    rows = list(parse_csv(get_csv(res)))
    assert "item_pid" in rows[0]
    assert len(rows) == 2


def test_loans_exports(app, client, librarian_martigny, loan_pending_martigny, loan2_validated_martigny):
    """Test loans streamed exportation."""
    # STEP#1 :: CHECK EXPORT PERMISSION
    #   Only authenticated user could export loans.
    url = url_for("api_exports.loan_export")
    res = client.get(url)
    assert res.status_code == 401

    # STEP#2 :: CHECK EXPORT RESOURCES
    #   Logged as librarian and test the export endpoint.
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(url)
    assert res.status_code == 200
    csv_rows = list(parse_csv(get_csv(res)))
    data = list(csv_rows)

    header = data.pop(0)
    header_columns = [
        "pid",
        "document_title",
        "item_barcode",
        "item_call_numbers",
        "patron_name",
        "patron_barcode",
        "patron_email",
        "patron_type",
        "owning_library",
        "transaction_library",
        "pickup_library",
        "state",
        "end_date",
        "request_expire_date",
    ]
    assert all(field in header for field in header_columns)
    assert len(data) == 2

    res = client.get(url_for("api_exports.loan_export", format="xlsx"))
    assert res.status_code == 200
    assert res.mimetype == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert res.headers["Content-Disposition"].endswith('.xlsx"')
    assert res.headers["X-Accel-Buffering"] == "no"
    assert parse_xlsx(res.get_data(), csv_compatible=True) == csv_rows


def test_patron_transaction_events_exports(
    app,
    client,
    librarian_martigny,
    patron_transaction_overdue_event_martigny,
    patron_martigny,
    item4_lib_martigny,
    patron_type_children_martigny,
    document,
):
    """Test patron transaction events expotation."""
    ptre = patron_transaction_overdue_event_martigny
    # STEP#1 :: CHECK EXPORT PERMISSION
    #   Only authenticated user could export loans.
    url = url_for("api_exports.patron_transaction_events_export")
    res = client.get(url)
    assert res.status_code == 401

    # STEP#2 :: CHECK EXPORT RESOURCES
    #   Logged as librarian and test the export endpoint.
    #   DEV NOTE :: update `operator` to max the code coverage
    login_user_via_session(client, librarian_martigny.user)
    ptre["operator"] = {"$ref": get_ref_for_pid("ptrn", librarian_martigny.pid)}
    ptre.update(ptre, dbcommit=False, reindex=True)

    # If some missing related resources are missing, this will not cause any
    # errors when consuming the stream : Ensure about that.
    for resource, delindex in [
        (patron_martigny, False),
        (item4_lib_martigny, False),
        (document, False),
        (patron_type_children_martigny, True),
    ]:
        resource.delete(force=True, dbcommit=False, delindex=delindex)
        res = client.get(url)
        assert res.status_code == 200
        # We need to consume the stream to produce a possible error.
        list(parse_csv(get_csv(res)))
        db.session.rollback()
        resource.reindex()

    res = client.get(url)
    assert res.status_code == 200
    csv_rows = list(parse_csv(get_csv(res)))
    data = list(csv_rows)

    header = data.pop(0)
    header_columns = [
        "category",
        "type",
        "subtype",
        "transaction_date",
        "amount",
        "patron_name",
        "patron_barcode",
        "patron_email",
        "patron_type",
        "document_pid",
        "document_title",
        "item_barcode",
        "item_owning_library",
        "transaction_library",
        "operator_name",
    ]
    assert all(field in header for field in header_columns)
    assert len(data) == 1

    res = client.get(url_for("api_exports.patron_transaction_events_export", format="xlsx"))
    assert res.status_code == 200
    assert res.mimetype == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert res.headers["Content-Disposition"].endswith('.xlsx"')
    xlsx_rows = parse_xlsx(res.get_data())
    assert xlsx_rows[0] == csv_rows[0]
    assert len(xlsx_rows) == len(csv_rows)
    transaction_date_index = header.index("transaction_date")
    assert [value for index, value in enumerate(xlsx_rows[1]) if index != transaction_date_index] == [
        value for index, value in enumerate(csv_rows[1]) if index != transaction_date_index
    ]
