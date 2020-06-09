# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2020 RERO
# Copyright (C) 2020 UCLouvain
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

from flask import current_app
from flask_security.utils import verify_password
from werkzeug.local import LocalProxy

datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


def check_sip2_module():
    """Check if invenio-sip2 module is installed.

    :return: ``True``` if module spec found for `ìnvenio-sip2`` or ``False``.
    """
    sip2_spec = importlib.util.find_spec("invenio_sip2")
    return sip2_spec is not None


def authorize_selfckeck_user(email, password, **kwargs):
    """Get user for sip2 client password.

    Grant 'password' for user.
    :param email: User email.
    :param password: Password.
    :return: The user instance or ``None``.
    """
    user = datastore.find_user(email=email)
    if user and verify_password(password, user.password):
        return user


def format_patron_address(patron):
    """Format the patron address for sip2.

    :param patron: patron instance.
    :return: Formated address like 'street postal code city' for patron.
    """
    return '{street}, {postal_code} {city}'.format(
        street=patron.get('street'),
        postal_code=patron.get('postal_code'),
        city=patron.get('city')
    )
