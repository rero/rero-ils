# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
# Copyright (C) 2022 UCLouvain
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

"""Selfcheck Utilities."""

from __future__ import absolute_import, print_function

import importlib
from datetime import datetime

from flask import current_app
from flask_security.utils import verify_password
from invenio_db import db
from invenio_oauth2server.provider import get_token

from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.patron_types.api import PatronType
from rero_ils.modules.users.api import User


def check_sip2_module():
    """Check if invenio-sip2 module is installed.

    :return: ``True``` if module spec found for `ìnvenio-sip2`` or ``False``.
    """
    sip2_spec = importlib.util.find_spec("invenio_sip2")
    return sip2_spec is not None


def authorize_selfckeck_terminal(terminal, access_token, **kwargs):
    """Authorize selfcheck terminal for given creditential.

    Grant 'token' for terminal.
    :param terminal: terminal instance.
    :param access_token: access token.
    :return: The granted user instance or ``None``.
    """
    if terminal and terminal.access_token == access_token:
        token = get_token(access_token=access_token)
        if token:
            terminal.last_login_at = datetime.utcnow()
            terminal.last_login_ip = kwargs.get('terminal_ip', None)
            db.session.merge(terminal)
            return token.user


def authorize_selfckeck_user(login, password, **kwargs):
    """Get user for sip2 client password.

    Grant 'password' for user.
    :param login: User login such as username or email.
    :param password: Password.
    :return: The user instance or ``None``.
    """
    user = User.get_by_username_or_email(login)
    if user and verify_password(password, user.user.password):
        return user


def format_patron_address(patron):
    """Format the patron address for sip2.

    :param patron: patron instance.
    :return: Formated address like 'street postal code city' for patron.
    """
    address = patron.get('second_address')
    if address:
        formated_address = '{street}, {postal_code} {city}'.format(
            street=address.get('street'),
            postal_code=address.get('postal_code'),
            city=address.get('city')
        )
    else:
        profile = patron.user.profile
        formated_address = '{street}, {postal_code} {city}'.format(
            street=profile.street.strip(),
            postal_code=profile.postal_code.strip(),
            city=profile.city.strip()
        )
    # Should never append, but can be imported from an old system
    return formated_address.replace(r'\n', ' ').replace(r'\r', ' ')\
        .replace('\n', ' ').replace('\r', ' ')


def get_patron_status(patron):
    """Return patron status useful for sip2.

    * check if the user is blocked ?
    * check if the user reaches the maximum loans limit ?
    * check if the user reaches the maximum fee amount limit ?

    add PatronStatusType e.g.:
        patron_status.add_patron_status_type(
            SelfcheckPatronStatusTypes.CARD_REPORTED_LOST)

    :return SelfcheckPatronStatus object or None.
    """
    if check_sip2_module():
        from invenio_sip2.models import PatronStatus, PatronStatusTypes

        patron_status = PatronStatus()
        # check if patron is blocked
        if patron.is_blocked:
            patron_status.add_patron_status_type(
                PatronStatusTypes.CHARGE_PRIVILEGES_DENIED)
            patron_status.add_patron_status_type(
                PatronStatusTypes.RENEWAL_PRIVILEGES_DENIED)
            patron_status.add_patron_status_type(
                PatronStatusTypes.RECALL_PRIVILEGES_DENIED)
            patron_status.add_patron_status_type(
                PatronStatusTypes.HOLD_PRIVILEGES_DENIED)

        patron_type = PatronType.get_record_by_pid(patron.patron_type_pid)
        # check the patron type checkout limit
        if not patron_type.check_checkout_count_limit(patron):
            patron_status.add_patron_status_type(
                PatronStatusTypes.CHARGE_PRIVILEGES_DENIED)
            patron_status.add_patron_status_type(
                PatronStatusTypes.RENEWAL_PRIVILEGES_DENIED)
            patron_status.add_patron_status_type(
                PatronStatusTypes.HOLD_PRIVILEGES_DENIED)
            patron_status.add_patron_status_type(
                PatronStatusTypes.TOO_MANY_ITEMS_CHARGED)

        # check the patron type fee amount limit
        if not patron_type.check_fee_amount_limit(patron):
            patron_status.add_patron_status_type(
                PatronStatusTypes.CHARGE_PRIVILEGES_DENIED)
            patron_status.add_patron_status_type(
                PatronStatusTypes.RENEWAL_PRIVILEGES_DENIED)
            patron_status.add_patron_status_type(
                PatronStatusTypes.HOLD_PRIVILEGES_DENIED)
            patron_status.add_patron_status_type(
                PatronStatusTypes.EXCESSIVE_OUTSTANDING_FINES)
            patron_status.add_patron_status_type(
                PatronStatusTypes.EXCESSIVE_OUTSTANDING_FEES)

        # check the patron type overdue limit
        if not patron_type.check_overdue_items_limit(patron):
            patron_status.add_patron_status_type(
                PatronStatusTypes.CHARGE_PRIVILEGES_DENIED)
            patron_status.add_patron_status_type(
                PatronStatusTypes.RENEWAL_PRIVILEGES_DENIED)
            patron_status.add_patron_status_type(
                PatronStatusTypes.HOLD_PRIVILEGES_DENIED)
            patron_status.add_patron_status_type(
                PatronStatusTypes.TOO_MANY_ITEMS_OVERDUE)

        return patron_status


def map_media_type(media_type):
    """Get mapped media type.

    :param media_type: Document type
    :return: sip2 media type (see invenio_sip2.models.SelfcheckMediaType)
    """
    return current_app.config.get('SIP2_MEDIA_TYPES').get(
        media_type, 'docmaintype_other'
    )


def map_item_circulation_status(item_status):
    """Get mapped item status.

    :param item_status: Item circulation status
    :return: sip2 circulation status
             (see invenio_sip2.models.SelfcheckCirculationStatus)
    """
    circulation_status = {
        ItemStatus.ON_SHELF: 'AVAILABLE',
        ItemStatus.AT_DESK: 'WAITING_ON_HOLD_SHELF',
        ItemStatus.ON_LOAN: 'CHARGED',
        ItemStatus.IN_TRANSIT: 'IN_TRANSIT',
        ItemStatus.EXCLUDED: 'OTHER',
        ItemStatus.MISSING: 'MISSING',
    }

    return circulation_status.get(item_status, 'OTHER')
