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

"""RERO ID OAuth2 configuration."""

from flask import redirect, url_for
from invenio_db import db
from invenio_oauthclient.handlers import \
    authorized_signup_handler as base_authorized_signup_handler
from invenio_oauthclient.handlers import oauth_error_handler
from invenio_oauthclient.utils import oauth_link_external_id, \
    oauth_unlink_external_id

OAUTH_URL = 'https://id.rero.ch'
REMOTE_APP = dict(
    title='RERO ID',
    description='RERO Identity server.',
    icon='fa fa-user',
    authorized_handler='rero_ils.modules.oauth.reroid'
                       ':authorized_signup_handler',
    disconnect_handler='invenio_oauthclient.handlers'
                       ':disconnect_handler',
    signup_handler=dict(
        info='rero_ils.modules.oauth.reroid:account_info',
        setup='rero_ils.modules.oauth.reroid:account_setup',
        view='invenio_oauthclient.handlers:signup_handler',
    ),
    params=dict(
        request_token_params={'scope': 'user:email'},
        base_url=OAUTH_URL,
        request_token_url=None,
        access_token_url='{server}/oauth/token'.format(server=OAUTH_URL),
        access_token_method='POST',
        authorize_url='{server}/oauth/authorize'.format(server=OAUTH_URL),
        app_key='REROID_APP_CREDENTIALS',
    )
)

OAUTH_TEST_URL = 'https://id.test.rero.ch'
TEST_REMOTE_APP = dict(REMOTE_APP)
TEST_REMOTE_APP['params'].update(dict(
    base_url=OAUTH_TEST_URL,
    access_token_url='{server}/oauth/token'.format(server=OAUTH_TEST_URL),
    authorize_url='{server}/oauth/authorize'.format(server=OAUTH_TEST_URL)
))

OAUTH_DEV_URL = 'https://iddev.test.rero.ch'
DEV_REMOTE_APP = dict(REMOTE_APP)
DEV_REMOTE_APP['params'].update(dict(
    base_url=OAUTH_DEV_URL,
    access_token_url='{server}/oauth/token'.format(server=OAUTH_DEV_URL),
    authorize_url='{server}/oauth/authorize'.format(server=OAUTH_DEV_URL)
))


@oauth_error_handler
def authorized_signup_handler(resp, remote, *args, **kwargs):
    """Store access token in session.

    Default authorized handler.
    :param remote: The remote application.
    :param resp: The response.
    :returns: Redirect response.
    """
    _redirect = base_authorized_signup_handler(resp, remote, *args, **kwargs)
    # do not redirect to the settings page until we have a clean settings page
    if _redirect.location == url_for('invenio_oauthclient_settings.index'):
        return redirect(url_for('rero_ils.index'))
    return _redirect


def account_info(remote, resp):
    """Retrieve remote account information used to find local user.

    It returns a dictionary with the following structure:
    .. code-block:: python
        {
            'user': {
                'email': '...',
                'profile': {
                    'username': '...',
                    'full_name': '...',
                }
            },
            'external_id': 'github-unique-identifier',
            'external_method': 'github',
        }
    Information inside the user dictionary are available for other modules.
    For example, they are used from the module invenio-userprofiles to fill
    the user profile.
    :param remote: The remote application.
    :param resp: The response.
    :returns: A dictionary with the user information.
    """
    user = resp.get('user')
    return dict(
        user=dict(
            email=user.get('email')
        ),
        external_id=str(user.get('id')),
        external_method='reroid'
    )


def account_setup(remote, token, resp):
    """Perform additional setup after user have been logged in.

    :param remote: The remote application.
    :param token: The token value.
    :param resp: The response.
    """
    with db.session.begin_nested():
        user = resp.get('user')

        token.remote_account.extra_data = {
            'email_verified': user.get('email_verified'),
            'id': user.get('id')
        }

        # Create user <-> external id link.
        oauth_link_external_id(
            token.remote_account.user, dict(
                id=str(user.get('id')),
                method='reroid')
        )
