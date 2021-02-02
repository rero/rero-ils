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

"""Utilities functions for rero-ils."""


from flask import current_app
from flask_security.confirmable import confirm_user
from invenio_i18n.ext import current_i18n


def unique_list(data):
    """Unicity of list."""
    return list(dict.fromkeys(data))


def get_current_language():
    """Return the current selected locale."""
    loc = current_i18n.locale
    return loc.language


def get_i18n_supported_languages():
    """Get defined languages from config.

    :returns: defined languages from config.
    """
    languages = [current_app.config.get('BABEL_DEFAULT_LANGUAGE')]
    i18n_languages = current_app.config.get('I18N_LANGUAGES')
    return languages + [ln[0] for ln in i18n_languages]


def remove_empties_from_dict(a_dict):
    """Remove empty values from a multi level dictionary.

    :return a cleaned dictionary.
    """
    new_dict = {}
    for k, v in a_dict.items():
        if isinstance(v, dict):
            v = remove_empties_from_dict(v)
        elif isinstance(v, list):
            v = [el for el in v if el]
        if v:
            new_dict[k] = v
    return new_dict or None

def create_user_from_data(data):
    """Create a user and set the profile fields from a data.

    :param data: A dict containing a mix of patron and user data.
    :returns: The modified dict.
    """
    from datetime import datetime

    from invenio_accounts.ext import hash_password
    from invenio_accounts.models import User
    from invenio_db import db

    profile_fields = [
        'first_name', 'last_name', 'street', 'postal_code',
        'city', 'birth_date', 'username', 'phone', 'keep_history'
    ]
    with db.session.begin_nested():
        # create the user
        user = User(
            password=hash_password(data.get('birth_date', '123456')),
            profile=dict(), active=True)
        db.session.add(user)
        # set the user fields
        if data.get('email') is not None:
            user.email = data.get('email')
        profile = user.profile
        # set the profile
        for field in profile_fields:
            value = data.get(field)
            if field == 'keep_history':
                value = data.get('patron', {}).get(field)
            if value is not None:
                if field == 'birth_date':
                    value = datetime.strptime(value, '%Y-%m-%d')
                setattr(profile, field, value)
        db.session.merge(user)
    db.session.commit()
    confirm_user(user)
    # remove the user fields from the data
    for field in profile_fields:
        try:
            if field == 'keep_history':
                del data['patron'][field]
            else:
                del data[field]
        except KeyError:
            pass
    data['user_id'] = user.id
    return data
