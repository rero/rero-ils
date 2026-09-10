# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Views tests."""

from urllib.parse import urlsplit

import pytest
from bs4 import BeautifulSoup
from flask import render_template, session, url_for
from flask_login import login_user, logout_user
from flask_security import url_for_security
from invenio_accounts.testutils import login_user_via_session, login_user_via_view
from invenio_oauth2server.models import Client
from invenio_oauth2server.proxies import current_oauth2server

from rero_ils.modules.users.api import user_formatted_name
from rero_ils.theme.views import localized_label, nl2br
from tests.utils import postdata


def test_nl2br():
    """Test nl2br function view."""
    assert nl2br("foo\nBar") == "foo<br>Bar"


def test_localized_label():
    """Test localized label filter."""
    values = [
        {"language": "fr", "value": "Bonjour"},
        {"language": "en", "value": "Hello"},
    ]

    assert localized_label(values, "en") == "Hello"
    assert localized_label(values, "de") == "Bonjour"
    assert localized_label(values, "it", None) == " "
    assert localized_label([{"language": "en", "value": "Hello"}], "de") == "Hello"
    assert localized_label([], "fr") is None
    assert localized_label(None, "fr") is None


def test_error(client):
    """Test error entrypoint."""
    with pytest.raises(RuntimeError):
        client.get(url_for("rero_ils.error"))


def test_schemaform(client):
    """Test schema form."""
    result = client.get(url_for("rero_ils.schemaform", document_type="documents"))
    assert result.status_code == 200

    result = client.get(url_for("rero_ils.schemaform", document_type="not_exists"))
    assert result.status_code == 404


def test_homepage_global_view(client):
    """The global view falls back to the general (hardcoded) homepage."""
    result = client.get(url_for("rero_ils.index"))
    assert result.status_code == 200
    # general slogan and block are rendered from the config templates
    assert "Get into your library" in result.text
    assert "RERO+ catalogue" in result.text


def test_homepage_organisation_with_data(client, org_sion):
    """An organisation view renders its own homepage from the database."""
    result = client.get(url_for("rero_ils.index_with_view_code", viewcode="org2"))
    assert result.status_code == 200
    assert "Welcome to the Sion libraries" in result.text
    assert "Search the Sion libraries" in result.text
    assert "Global catalogue" in result.text
    # the general homepage must not leak into a personalized view
    assert "Get into your library" not in result.text
    assert "RERO+ catalogue" not in result.text


def test_homepage_organisation_without_data(client, org_martigny):
    """An organisation view without homepage data shows no fallback."""
    result = client.get(url_for("rero_ils.index_with_view_code", viewcode="org1"))
    assert result.status_code == 200
    # organisation views never fall back to the general homepage
    assert "Get into your library" not in result.text
    assert "RERO+ catalogue" not in result.text


def test_view_parameter_exists(client):
    """Test view parameter exception."""
    result = client.get(url_for("rero_ils.index_with_view_code", viewcode="global"))
    assert result.status_code == 302


def test_view_parameter_e2e(client):
    """Test view parameter with e2e viewcode."""
    result = client.get(url_for("rero_ils.index_with_view_code", viewcode="e2e"))
    assert result.status_code == 404


def test_view_parameter_notfound(client):
    """Test view parameter exception."""
    result = client.get(url_for("rero_ils.index_with_view_code", viewcode="foo"))
    assert result.status_code == 404


def test_external_endpoint_on_institution_homepage(client, org_martigny, app):
    """Test organisation CSS endpoint configuration.

    Verify that:
    - The CSS endpoint is configured to use local static files
    - The endpoint path appears in the rendered organisation homepage
    """
    result = client.get(url_for("rero_ils.index_with_view_code", viewcode="org1"))
    assert result.status_code == 200
    endpoint = app.config["RERO_ILS_THEME_ORGANISATION_CSS_ENDPOINT"]

    # Verify endpoint is configured for local static files
    assert endpoint == "/static/themes/css/", f"Expected local static CSS endpoint, got: {endpoint}"

    # Verify endpoint appears in the organisation homepage response
    assert endpoint in result.text, f"CSS endpoint '{endpoint}' not found in homepage response"


def test_help(client):
    """Test help entrypoint."""
    result = client.get(url_for("wiki.index"))
    assert result.status_code == 302


def test_help_front_end(client):
    """Test that the help pages provide what the wiki front-end needs."""
    result = client.get(url_for("wiki.page", url="home"))
    assert result.status_code == 200
    # the wiki icons are rendered with the Font Awesome of the theme bundle
    assert "fa-magnifying-glass" in result.text
    # no front-end library is loaded from a CDN
    assert "cdn.jsdelivr.net" not in result.text
    # the toasts wiki.js reveals by id, in the toast stack of the application
    assert 'class="toast-container"' in result.text
    assert 'id="copy-success"' in result.text
    assert 'id="copy-error"' in result.text


@pytest.mark.parametrize("role_name", ["editor", "admin"])
def test_help_edit_permission(client, app, db, user_with_profile, role_name):
    """Test the wiki edition permission."""
    url = url_for("wiki.edit", url="home")

    # an anonymous user is redirected to the login page
    result = client.get(url)
    assert result.status_code == 302
    assert url_for_security("login") in result.location

    # a logged user without any editor role is not allowed
    login_user_via_session(client, user_with_profile)
    assert client.get(url).status_code == 403

    # the editor and admin roles both grant the wiki edition
    datastore = app.extensions["invenio-accounts"].datastore
    role = datastore.find_or_create_role(name=role_name)
    datastore.add_role_to_user(user_with_profile, role)
    datastore.commit()
    db.session.commit()
    assert client.get(url).status_code == 200


# TODO: uncomment tests when rero-ils-ui is deployed on npm
# def test_search_no_parameter(client):
#     """Test search entrypoint."""
#     result = client.get(url_for(
#         'rero_ils.search', recordType='document', viewcode='global'))
#     assert result.status_code == 302


# def test_search_with_parameters(client):
#     """Test search entrypoint with parameters."""
#     result = client.get(url_for(
#         'rero_ils.search',
#         recordType='document',
#         viewcode='global',
#         q='',
#         size=20,
#         page=1
#         ))
#     assert result.status_code == 200


def test_language(client, app):
    """Test the language endpoint."""
    res, data = postdata(client, "rero_ils.set_language", {"lang": "fr"})
    assert session[app.config["I18N_SESSION_KEY"]] == "fr"
    assert data == {"lang": "fr"}
    assert res.status_code == 200

    res, data = postdata(client, "rero_ils.set_language", {"lang": "it"})
    assert session[app.config["I18N_SESSION_KEY"]] == "it"

    res, data = postdata(client, "rero_ils.set_language", {"language": "fr"})
    assert res.status_code == 400

    res, data = postdata(client, "rero_ils.set_language", {"lang": "foo"})
    assert res.status_code == 400

    # session is unchanged
    assert session[app.config["I18N_SESSION_KEY"]] == "it"


def test_set_user_name(
    app,
    librarian_martigny,
    patron_martigny,
    user_with_profile,
    user_without_name,
    user_without_name_email,
):
    """Test the user_name in the flask session."""
    # should be the formatted name
    login_user(user=user_with_profile)
    assert "user_name" in session
    assert session["user_name"] == user_formatted_name(user_with_profile)
    # should be removed
    logout_user()
    assert "user_name" not in session

    # should be the email
    login_user(user=user_without_name)
    assert session["user_name"] == user_without_name.email
    logout_user()

    # should be the user.username
    login_user(user=user_without_name_email)
    assert session["user_name"] == user_without_name_email.username
    logout_user()

    # should be the formatted name
    login_user(user=patron_martigny.user)
    assert session["user_name"] == patron_martigny.formatted_name
    logout_user()

    # should be the formatted name
    login_user(user=librarian_martigny.user)
    assert session["user_name"] == librarian_martigny.formatted_name
    logout_user()


def test_flashed_message_categories(client):
    """Test that a flashed message is rendered as a toast of a styled category."""
    # an error is displayed as a danger toast, the only red category styled
    with client.session_transaction() as session:
        session["_flashes"] = [("error", "an error")]
    result = client.get(url_for("rero_ils.index"))
    assert "toast-danger" in result.text
    assert "toast-error" not in result.text

    # a message flashed without any category falls back on the info toast
    with client.session_transaction() as session:
        session["_flashes"] = [("message", "a notice")]
    result = client.get(url_for("rero_ils.index"))
    assert "toast-info" in result.text


def test_google_analytics(client, app):
    """Testing the insertion of the google analytics code in the html page."""
    # The Google Analytics code must not be present on the page.
    result = client.get(url_for("rero_ils.index"))
    assert "gtag" not in result.text

    # The Google Analytics code must be present on the page.
    app.config["RERO_ILS_GOOGLE_ANALYTICS_TAG_ID"] = "GA-Foo"
    result = client.get(url_for("rero_ils.index"))
    assert "gtag" in result.text


def test_login(client, app, user_with_profile):
    """Testing the frontend login view."""
    ## bad password
    # be sure that no one is logged
    client.get(url_for_security("logout"))
    res = login_user_via_view(client=client, email=user_with_profile.username, password="bad password")
    assert "Invalid user or password" in res.text
    assert res.status_code == 200

    ## bad email
    client.get(url_for_security("logout"))
    res = login_user_via_view(
        client=client,
        email="bad@email.com",
        password=user_with_profile.password_plaintext,
    )
    assert "Invalid user or password" in res.text
    assert res.status_code == 200

    ## login with email
    client.get(url_for_security("logout"))
    res = login_user_via_view(
        client=client,
        email=user_with_profile.email,
        password=user_with_profile.password_plaintext,
    )
    assert res.status_code == 302

    ## login with username
    client.get(url_for_security("logout"))
    res = login_user_via_view(
        client=client,
        email=user_with_profile.username,
        password=user_with_profile.password_plaintext,
    )
    assert res.status_code == 302


def _asset_hosts(html):
    """Return where the third-party hosts the scripts and stylesheets of a page come from.

    The analytics tag is the one third-party script the application loads on
    purpose, from the host the CSP allows in `script-src`.
    """
    soup = BeautifulSoup(html, "html.parser")
    assets = [tag["src"] for tag in soup.select("script[src]")]
    assets += [tag["href"] for tag in soup.select('link[rel="stylesheet"][href]')]
    assert assets
    # An asset served by the application has no netloc.
    return {urlsplit(asset).netloc for asset in assets} - {"", "www.googletagmanager.com"}


def test_assets_are_served_by_the_application(client, app):
    """Test that the pages load their front-end libraries from no third-party host."""
    for url in [
        url_for("rero_ils.index"),
        url_for("wiki.page", url="home"),
        url_for_security("login"),
    ]:
        res = client.get(url)
        assert res.status_code == 200
        assert not _asset_hosts(res.text), url

    # The OAuth cover page has no route of its own without a registered client.
    with app.test_request_context():
        assert not _asset_hosts(render_template(app.config["OAUTH2SERVER_COVER_TEMPLATE"]))


def test_oauth_authorize_page(app, db, user_with_profile, user_without_name):
    """Test that the OAuth consent page tells the patron what is at stake."""
    oauth_client = Client(
        name="Test application",
        description="A test application",
        website="https://example.org",
        user=user_without_name,
        is_confidential=False,
        _redirect_uris="https://example.org/callback",
    )
    oauth_client.gen_salt()
    db.session.add(oauth_client)
    db.session.commit()

    scopes = list(current_oauth2server.scopes.values())
    with app.test_request_context():
        login_user(user_with_profile)
        html = render_template(app.config["OAUTH2SERVER_AUTHORIZE_TEMPLATE"], client=oauth_client, scopes=scopes)

    # the application asking for the access, and the data it would receive
    assert "Test application" in html
    assert "A test application" in html
    assert "Full name" in html
    # the account about to be shared, and the reassurance about the password
    assert user_with_profile.email in html
    assert "Your password is never shared with this application." in html
    # the owner of the OAuth client is no business of the patron
    assert user_without_name.email not in html
    # the page is styled by the theme bundle, not by a third-party stylesheet
    assert not _asset_hosts(html)


def test_oauth_authorize_page_website_scheme(app, user_with_profile):
    """Test that only a web address of the application becomes a link."""
    oauth_client = Client(name="Test application")

    def render(website):
        oauth_client.website = website
        with app.test_request_context():
            login_user(user_with_profile)
            return render_template(app.config["OAUTH2SERVER_AUTHORIZE_TEMPLATE"], client=oauth_client, scopes=[])

    assert 'href="https://example.org"' in render("https://example.org")
    assert 'href="HTTP://example.org"' in render("HTTP://example.org")
    # anything that is not a web address is not worth a link
    for website in ["javascript:alert(1)", "javascript://example.org/%0aalert(1)", "data:text/html,x", ""]:
        assert "Visit application website" not in render(website)
