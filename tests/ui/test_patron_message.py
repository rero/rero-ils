# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests message UI view for patrons."""

from bs4 import BeautifulSoup
from flask import url_for
from invenio_accounts.testutils import login_user_via_view


def test_info_message(app, client, patron_martigny, patron_martigny_data, org_martigny_data):
    """Test info message."""
    patron_martigny["patron"]["blocked"] = True
    patron_martigny["patron"]["blocked_note"] = "This is a blocked message."
    patron_martigny["patron"]["expiration_date"] = "2022-12-31"
    patron_martigny.update(patron_martigny, dbcommit=True, reindex=True)

    blocked_message = patron_martigny["patron"]["blocked_note"]

    # If the user is not identified, there is no user information
    res = client.get("/")
    soup = BeautifulSoup(res.data, "html.parser")
    assert soup.find("div", {"class": "patron-info-message"}) is None

    login_user_via_view(
        client,
        email=patron_martigny_data["email"],
        password=patron_martigny_data["password"],
    )

    # If the user is identified, we see the name of the organization
    # and the message on the global view
    res = client.get(url_for("rero_ils.index"))
    soup = BeautifulSoup(res.data, "html.parser")
    li = soup.find("div", {"class": "patron-info-message"}).find("li")

    assert org_martigny_data["name"] == li.find("span").text
    assert (
        f"Your account is currently blocked. Reason: {blocked_message}"
        == li.find("div", {"class": "message-blocked"}).text
    )
    assert li.find("div", {"class": "message-expired"}).text == "Your account has expired. Please contact your library."

    # If the view of the organization, there is no name of it
    res = client.get(url_for("rero_ils.index_with_view_code", viewcode=org_martigny_data["code"]))
    soup = BeautifulSoup(res.data, "html.parser")
    div = soup.find("div", {"class": "patron-info-message"})

    assert div.find("span") is None
    assert (
        f"Your account is currently blocked. Reason: {blocked_message}"
        == div.find("div", {"class": "message-blocked"}).text
    )
    assert (
        div.find("div", {"class": "message-expired"}).text == "Your account has expired. Please contact your library."
    )
