# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests Serializers."""

import re
from copy import deepcopy

from flask import url_for
from invenio_accounts.testutils import login_user_via_session

from rero_ils.modules.holdings.api import Holding
from tests.utils import get_csv, get_json, parse_csv, parse_xlsx


def test_requests_export(
    client,
    csv_header,
    patron_martigny,
    librarian_martigny,
    librarian_sion,
    lib_martigny,
    loc_public_martigny,
    item_on_shelf_martigny_patron_and_loan_pending,
):
    """Test requests to validate exportation."""
    item, patron, _ = item_on_shelf_martigny_patron_and_loan_pending
    url = url_for("api_loan.requests_export", library_pid=lib_martigny.pid)

    # STEP#1 :: CHECK EXPORT PERMISSION
    #   Only librarians of the library organisation can export the requests.
    res = client.get(url)
    assert res.status_code == 401

    login_user_via_session(client, patron_martigny.user)
    res = client.get(url)
    assert res.status_code == 403

    login_user_via_session(client, librarian_sion.user)
    res = client.get(url)
    assert res.status_code == 403

    login_user_via_session(client, librarian_martigny.user)
    res = client.get(url_for("api_loan.requests_export", library_pid=lib_martigny.pid, format="pdf"))
    assert res.status_code == 400

    # an unknown library exports an empty file
    res = client.get(url_for("api_loan.requests_export", library_pid="dummy_pid"), headers=csv_header)
    assert res.status_code == 200
    assert len(list(parse_csv(get_csv(res)))) == 1

    # STEP#2 :: CHECK CSV CONTENT
    res = client.get(url, headers=csv_header)
    assert res.status_code == 200
    assert res.headers["Content-Disposition"].startswith('attachment; filename="export-requests-')
    assert res.headers["Content-Disposition"].endswith('.csv"')

    csv_rows = list(parse_csv(get_csv(res)))
    data = list(csv_rows)

    header = data.pop(0)
    assert header == [
        "item_barcode",
        "document_title",
        "document_contributions",
        "item_first_call_number",
        "item_second_call_number",
        "item_enumerationAndChronology",
        "requested_by",
        "item_location",
        "pickup_location",
        "request_date",
    ]
    assert len(data) == 1

    row = dict(zip(header, data[0], strict=True))
    assert row["item_barcode"] == item["barcode"]
    # the document has an alternate graphic title, displayed first as in the interface
    assert row["document_title"] == "titre en chinois. Part Number, Part Number = Titolo cinese : sottotitolo in cinese"
    assert row["document_contributions"] == "Nebehay, Christian Michael"
    assert row["item_first_call_number"] == item["call_number"]
    assert row["requested_by"] == f"{patron.formatted_name} ({patron['patron']['barcode'][0]})"
    assert row["item_location"] == f"{lib_martigny['name']} - {loc_public_martigny['name']}"
    # the pickup location defines a `pickup_name`, it takes precedence
    assert row["pickup_location"] == loc_public_martigny["pickup_name"]
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", row["request_date"])

    # STEP#3 :: CHECK JSON CONTENT
    #   The JSON export is a simple array of objects.
    res = client.get(url_for("api_loan.requests_export", library_pid=lib_martigny.pid, format="json"))
    assert res.status_code == 200
    assert res.headers["Content-Disposition"].endswith('.json"')
    assert get_json(res) == [row]

    # STEP#4 :: CHECK XLSX CONTENT
    res = client.get(url_for("api_loan.requests_export", library_pid=lib_martigny.pid, format="xlsx"))
    assert res.status_code == 200
    assert res.mimetype == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert res.headers["Content-Disposition"].endswith('.xlsx"')
    assert res.headers["X-Accel-Buffering"] == "no"
    assert parse_xlsx(res.get_data()) == csv_rows


def test_requests_export_inherited_call_numbers(
    client,
    csv_header,
    librarian_martigny,
    lib_martigny,
    item_on_shelf_martigny_patron_and_loan_pending,
):
    """Test the exported call numbers are inherited from the holdings."""
    item, _, _ = item_on_shelf_martigny_patron_and_loan_pending
    holding = Holding.get_record_by_pid(item.holding_pid)
    original_item, original_holding = deepcopy(item), deepcopy(holding)

    # move the call number to the holdings and add a second one
    holding["call_number"] = item.pop("call_number")
    holding["second_call_number"] = "second call number"
    holding.update(holding, dbcommit=True, reindex=True)
    item.update(item, dbcommit=True, reindex=True)

    login_user_via_session(client, librarian_martigny.user)
    url = url_for("api_loan.requests_export", library_pid=lib_martigny.pid)
    res = client.get(url, headers=csv_header)
    assert res.status_code == 200

    data = list(parse_csv(get_csv(res)))
    row = dict(zip(data[0], data[1], strict=True))
    assert row["item_first_call_number"] == holding["call_number"]
    assert row["item_second_call_number"] == holding["second_call_number"]

    holding.update(original_holding, dbcommit=True, reindex=True)
    item.update(original_item, dbcommit=True, reindex=True)


def test_requests_export_contributions(
    client,
    csv_header,
    librarian_martigny,
    lib_martigny,
    document,
    item_on_shelf_martigny_patron_and_loan_pending,
):
    """Test only the first three contributions of a document are exported."""
    original_document = deepcopy(document)
    document["contribution"] = [
        {
            "entity": {"type": "bf:Person", "authorized_access_point": f"Author {index}"},
            "role": ["aut"],
        }
        for index in range(1, 5)
    ]
    document.update(document, dbcommit=True, reindex=True)

    login_user_via_session(client, librarian_martigny.user)
    url = url_for("api_loan.requests_export", library_pid=lib_martigny.pid)
    res = client.get(url, headers=csv_header)
    assert res.status_code == 200

    data = list(parse_csv(get_csv(res)))
    row = dict(zip(data[0], data[1], strict=True))
    assert row["document_contributions"] == "Author 1 ; Author 2 ; Author 3"

    document.update(original_document, dbcommit=True, reindex=True)
