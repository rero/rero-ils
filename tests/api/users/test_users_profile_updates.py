# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022-2023 RERO
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

"""Users profile updates tests."""

from __future__ import absolute_import, print_function

import json

from flask import url_for
from invenio_accounts.testutils import login_user_via_session

from rero_ils.modules.patrons.api import Patron
from rero_ils.modules.patrons.models import CommunicationChannel
from rero_ils.modules.users.api import User


def test_user_profile_updates(
        client, patron_martigny, system_librarian_martigny, json_header,
        mailbox):
    """Test users profile updates."""
    # if none of email nor username is provided the request should failed
    login_user_via_session(client, patron_martigny.user)
    user_metadata = User.get_record(patron_martigny.user.id).dumps_metadata()
    user_metadata.pop('email', None)
    user_metadata.pop('username', None)
    res = client.put(
        url_for('api_users.users_item', id=patron_martigny.user.id),
        data=json.dumps(user_metadata),
        headers=json_header
    )
    assert res.status_code == 400
    assert not (len(mailbox))
    # login with a patron has only the patron role, this means we are logging
    # into the public interface
    assert patron_martigny.patron['communication_channel'] == \
        CommunicationChannel.MAIL
    login_user_via_session(client, patron_martigny.user)
    # mailbox is empty
    assert not (len(mailbox))
    user_metadata = User.get_record(patron_martigny.user.id).dumps_metadata()
    # changing the email by another does not send any reset_password
    # notification
    user_metadata['email'] = 'toto@toto.com'
    res = client.put(
        url_for('api_users.users_item', id=patron_martigny.user.id),
        data=json.dumps(user_metadata),
        headers=json_header
    )
    assert res.status_code == 200
    assert not (len(mailbox))
    patron_martigny = Patron.get_record_by_pid(patron_martigny.pid)
    # an email was added to patron, communication_channel will change
    # automatically to email
    assert patron_martigny.patron.get('communication_channel') == \
        CommunicationChannel.EMAIL

    # removing the email from profile does not send any reset_password
    # notification
    user_metadata.pop('email', None)
    res = client.put(
        url_for(
            'api_users.users_item',
            id=patron_martigny.user.id),
        data=json.dumps(user_metadata),
        headers=json_header
    )
    assert res.status_code == 200
    assert not (len(mailbox))
    # the corresponding patron changes its communication_channel to mail
    # autmoatically if user has no email configured and patron has no
    # additional_communication_email configured
    patron_martigny = Patron.get_record_by_pid(patron_martigny.pid)
    assert patron_martigny.patron.get('communication_channel') == \
        CommunicationChannel.MAIL

    # login as a system_librarian this means we are logging into the
    # professional interface
    login_user_via_session(client, system_librarian_martigny.user)
    # adding an email to a profile does not send any reset_password
    # notification
    user_metadata['email'] = 'toto@toto.com'
    res = client.put(
        url_for(
            'api_users.users_item',
            id=patron_martigny.user.id),
        data=json.dumps(user_metadata),
        headers=json_header
    )
    assert res.status_code == 200
    assert not (len(mailbox))
    # removing the email from profile does not send any reset_password
    # notification
    user_metadata.pop('email', None)
    res = client.put(
        url_for(
            'api_users.users_item',
            id=patron_martigny.user.id),
        data=json.dumps(user_metadata),
        headers=json_header
    )
    assert res.status_code == 200
    assert not (len(mailbox))
    patron_martigny = Patron.get_record_by_pid(patron_martigny.pid)
    assert patron_martigny.patron.get('communication_channel') == \
        CommunicationChannel.MAIL


def test_user_birthdate(
        client, patron_martigny, system_librarian_martigny, json_header):
    """Test user birth_date."""
    login_user_via_session(client, system_librarian_martigny.user)
    user_metadata = User.get_record(patron_martigny.user.id).dumps_metadata()

    # Invalid date of birth
    user_metadata['birth_date'] = '0070-01-01'
    res = client.put(
        url_for('api_users.users_item', id=patron_martigny.user.id),
        data=json.dumps(user_metadata),
        headers=json_header
    )
    assert res.status_code == 400

    # Valid date of birth
    user_metadata['birth_date'] = '1970-01-01'
    res = client.put(
        url_for('api_users.users_item', id=patron_martigny.user.id),
        data=json.dumps(user_metadata),
        headers=json_header
    )
    assert res.status_code == 200

    user_metadata['birth_date'] = '2001-01-01'
    res = client.put(
        url_for('api_users.users_item', id=patron_martigny.user.id),
        data=json.dumps(user_metadata),
        headers=json_header
    )
    assert res.status_code == 200
