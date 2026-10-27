# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests Form for users."""

from datetime import UTC, datetime, timedelta
from unittest import mock

from bs4 import BeautifulSoup
from flask import url_for
from flask_security.recoverable import generate_reset_password_token
from freezegun import freeze_time


def test_register_form(client, app):
    """Test register form."""
    form_data = {"email": "foo@bar.com", "password": "123", "password_confirm": "123"}
    res = client.post(url_for("security.register"), data=form_data)
    soup = BeautifulSoup(res.data, "html.parser")
    el = soup.find("div", {"class": "alert-danger"}).find("p")
    assert el.text == "Field must be at least 8 characters long."

    app.config["RERO_ILS_PASSWORD_MIN_LENGTH"] = 10
    form_data = {"email": "foo@bar.com", "password": "123", "password_confirm": "123"}
    res = client.post(url_for("security.register"), data=form_data)
    soup = BeautifulSoup(res.data, "html.parser")
    el = soup.find("div", {"class": "alert-danger"}).find("p")
    assert el.text == "Field must be at least 10 characters long."

    app.config["RERO_ILS_PASSWORD_MIN_LENGTH"] = 8
    form_data = {
        "email": "foo@bar.com",
        "password": "12345678",
        "password_confirm": "12345678",
    }
    res = client.post(url_for("security.register"), data=form_data)
    soup = BeautifulSoup(res.data, "html.parser")
    el = soup.find("div", {"class": "alert-danger"}).find("p")
    assert el.text == "The password must contain a lower case character."

    form_data = {
        "email": "foo@bar.com",
        "password": "a12345678",
        "password_confirm": "a12345678",
    }
    res = client.post(url_for("security.register"), data=form_data)
    soup = BeautifulSoup(res.data, "html.parser")
    el = soup.find("div", {"class": "alert-danger"}).find("p")
    assert el.text == "The password must contain a upper case character."

    form_data = {
        "email": "foo@bar.com",
        "password": "NewHouse",
        "password_confirm": "NewHouse",
    }
    res = client.post(url_for("security.register"), data=form_data)
    soup = BeautifulSoup(res.data, "html.parser")
    el = soup.find("div", {"class": "alert-danger"}).find("p")
    assert el.text == "The password must contain a number."

    # Check special char
    app.config["RERO_ILS_PASSWORD_SPECIAL_CHAR"] = True
    form_data = {
        "email": "foo@bar.com",
        "password": "House1234",
        "password_confirm": "House1234",
    }
    res = client.post(url_for("security.register"), data=form_data)
    soup = BeautifulSoup(res.data, "html.parser")
    el = soup.find("div", {"class": "alert-danger"}).find("p")
    assert el.text == "The password must contain a special character."

    # Valid password
    app.config["RERO_ILS_PASSWORD_SPECIAL_CHAR"] = False
    form_data = {
        "email": "foo@bar.com",
        "password": "Pw123456",
        "password_confirm": "Pw123456",
    }
    res = client.post(url_for("security.register"), data=form_data)
    assert res.status_code == 302
    assert res.location == "/"

    form_data = {
        "email": "foo@bar.com",
        "password": "Eléphant$07_",
        "password_confirm": "Eléphant$07_",
    }
    res = client.post(url_for("security.register"), data=form_data)
    assert res.status_code == 302
    assert res.location == "/"


@mock.patch(
    "flask_security.views.reset_password_token_status",
    mock.MagicMock(return_value=[False, False, {"email": "foo@foo.com"}]),
)
@mock.patch("flask_security.views.update_password", mock.MagicMock())
def test_reset_password_form(client, app):
    """Test reset password form.

    All validator tests are performed by the test_register_form (above).
    Here we only test that the validator is active on the field.
    """
    form_data = {"email": "foo@bar.com", "password": "123", "password_confirm": "123"}
    res = client.post(url_for("security.reset_password", token="123ab"), data=form_data)
    soup = BeautifulSoup(res.data, "html.parser")
    el = soup.find("div", {"class": "text-danger"}).find("p")
    assert el.text == "Field must be at least 8 characters long."

    form_data = {
        "email": "foo@bar.com",
        "password": "12345678",
        "password_confirm": "12345678",
    }
    res = client.post(url_for("security.reset_password", token="123ab"), data=form_data)
    soup = BeautifulSoup(res.data, "html.parser")
    el = soup.find("div", {"class": "text-danger"}).find("p")
    assert el.text == "The password must contain a lower case character."


def test_reset_password_without_email(client, app, user_without_name_email, mailbox):
    """A reset link of a user without email sends no email and points to the library."""
    user = user_without_name_email
    forgot_url = url_for("security.forgot_password")
    message = "Your account has no email address. Please contact your library to reset your password."

    # An expired token would send new reset instructions.
    with freeze_time(datetime.now(UTC) - timedelta(days=1)):
        expired_token = generate_reset_password_token(user)
    res = client.get(url_for("security.reset_password", token=expired_token), follow_redirects=True)
    assert res.request.path == forgot_url
    assert message in res.get_data(as_text=True)

    # A valid token would send a reset notice.
    password = user.password
    form_data = {"password": "Pw123456", "password_confirm": "Pw123456"}
    res = client.post(url_for("security.reset_password", token=generate_reset_password_token(user)), data=form_data)
    assert res.location == forgot_url
    assert user.password == password

    assert not mailbox
