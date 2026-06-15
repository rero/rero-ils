# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Ill request record tests."""

from flask import url_for

from tests.utils import login_user_for_view


def test_ill_request_create_request_form(
    client,
    app,
    ill_request_martigny_data_tmp,
    loc_public_martigny,
    patron_martigny,
    default_user_password,
):
    """Test ill request create form."""
    request_form_url = url_for("ill_requests.ill_request_form", viewcode="global")

    # Not logged user don't have access to request_form. It is redirected to
    # login form
    res = client.get(request_form_url)
    assert res.status_code == 302

    # logged as user
    login_user_for_view(client, patron_martigny, default_user_password)
    res = client.get(request_form_url)
    assert res.status_code == 200

    # try to create an ill_request with incorrect data
    #   as user request a copy of document part, they need to specify pages.
    #   the form submission, will return a response status == 200 (display the
    #   form with error message)
    form_data = {
        "document-title": "test title",
        "copy": "1",
        "document-year": "2020",
        "pickup_location": loc_public_martigny.pid,
    }
    res = client.post(request_form_url, data=form_data)
    assert res.status_code == 200

    # try to create an ill_request with correct data
    #   as user request a copy of document part, they need to specify pages.
    #   the form submission, will return a response status == 201 (user should
    #   be redirected to patron profile page)
    form_data["pages"] = "12-13"
    res = client.post(request_form_url, data=form_data)
    assert res.status_code == 302


def test_ill_request_with_document(client, app, document, patron_martigny, default_user_password):
    """Test ills request form with document data."""
    app.config["RERO_ILS_ILL_REQUEST_ON_GLOBAL_VIEW"] = True
    app.config["RERO_ILS_ILL_DEFAULT_SOURCE"] = "RERO +"

    request_form_url = url_for("ill_requests.ill_request_form", viewcode="global", record_pid=document.pid)

    # logged as user
    login_user_for_view(client, patron_martigny, default_user_password)
    res = client.get(request_form_url)
    assert res.status_code == 200

    # Check title
    assert b"titre en chinois" in res.data
    # Check author
    assert b"Zeng Lingliang zhu bian" in res.data
    # Check publisher
    assert b"H. Mignot" in res.data
    # Check year
    assert b"1971" in res.data
    # Check identifier
    assert b"9782844267788 (ISBN)" in res.data
    # Check source
    assert b"RERO +" in res.data
    # Check url
    assert b"http://localhost/global/documents/doc1" in res.data

    # Check if the request with document is disabled
    app.config["RERO_ILS_ILL_REQUEST_ON_GLOBAL_VIEW"] = False

    res = client.get(request_form_url)

    assert b"H. Mignot" not in res.data
