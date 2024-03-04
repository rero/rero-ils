# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

"""API for manipulating users."""


from flask import current_app, url_for
from flask_babel import lazy_gettext as _
from flask_login import current_user
from flask_security.confirmable import confirm_user
from flask_security.recoverable import send_reset_password_instructions
from flask_security.utils import hash_password
from invenio_accounts.models import User as BaseUser
from invenio_db import db
from invenio_jsonschemas import current_jsonschemas
from invenio_records_rest.utils import obj_or_import_string
from jsonschema import Draft4Validator
from jsonschema.exceptions import ValidationError
from sqlalchemy import func
from werkzeug.local import LocalProxy

from ..api import ils_record_format_checker
from ..utils import PasswordValidatorException, get_schema_for_resource
from ...utils import remove_empties_from_dict

_records_state = LocalProxy(lambda: current_app.extensions['invenio-records'])


def get_profile_countries():
    """Get country list from the jsonschema."""
    schema = current_jsonschemas.get_schema('common/countries-v0.0.1.json')
    options = schema['country']['form']['options']
    return [
        (option.get('value'), _((option.get('label')))) for option in options
    ]


def get_readonly_profile_fields() -> list[str]:
    """Disallow to edit some fields for patrons."""
    if current_user.has_role('patron'):
        return ['first_name', 'last_name', 'birth_date']
    return ['keep_history']


def password_generator():
    """Password generator."""
    generator = obj_or_import_string(
        current_app.config['RERO_ILS_PASSWORD_GENERATOR'])
    return generator(
        current_app.config['RERO_ILS_PASSWORD_MIN_LENGTH'],
        current_app.config['RERO_ILS_PASSWORD_SPECIAL_CHAR']
    )


def password_validator(password):
    """Password validator."""
    validator = obj_or_import_string(
        current_app.config['RERO_ILS_PASSWORD_VALIDATOR'])
    return validator(
        password,
        current_app.config['RERO_ILS_PASSWORD_MIN_LENGTH'],
        current_app.config['RERO_ILS_PASSWORD_SPECIAL_CHAR']
    )


class User(object):
    """User API."""

    profile_fields = [
        'first_name', 'last_name', 'street', 'postal_code', 'gender',
        'city', 'birth_date', 'home_phone', 'business_phone',
        'mobile_phone', 'other_phone', 'keep_history', 'country'
    ]
    user_fields = [
        'email', 'username', 'password'
    ]

    def __init__(self, user):
        """User class initializer."""
        self.user = user

    @property
    def id(self):
        """Get user id."""
        return self.user.id

    @classmethod
    def create(cls, data, send_email=True, **kwargs):
        """User record creation.

        :param cls - class object
        :param data - dictionary representing a user record
        :param send_email - send the reset password email to the user
        """
        with db.session.begin_nested():
            # Generate password if not present
            profile = {
                k: v for k, v in data.items()
                if k in cls.profile_fields
            }
            if profile:
                cls._validate_profile(profile)
            cls._validate_data(data=data)
            password = data.get('password', password_generator())
            cls._validate_password(password=password)
            user = BaseUser(
                username=data.get('username'),
                password=hash_password(password),
                user_profile=profile, active=True)
            db.session.add(user)
            # send the reset password notification for new users
            if email := data.get('email'):
                user.email = email
            db.session.merge(user)
        db.session.commit()
        if data.get('email') and send_email:
            send_reset_password_instructions(user)
        confirm_user(user)
        return cls(user)

    def update(self, data):
        """User record update.

        :param data - dictionary representing a user record to update
        """
        from ..patrons.listener import update_from_profile
        profile = {k: v for k, v in data.items() if k in self.profile_fields}
        if profile:
            self._validate_profile(profile)
        if password := data.get('password'):
            self._validate_password(password=password)
        self._validate_data(data)

        user = self.user
        with db.session.begin_nested():
            if password:
                user.password = hash_password(password)
            user.username = data.get('username')
            if email := data.get('email'):
                user.email = email
            else:
                user._email = None
            user.user_profile = profile
            db.session.merge(user)
        db.session.commit()
        confirm_user(user)
        update_from_profile('user', self.user)
        return self

    @classmethod
    def _validate_data(cls, data):
        """Additional user record validations."""
        if not data.get('email') and not data.get('username'):
            raise ValidationError(
                _('A username or email is required.')
            )

    @classmethod
    def _validate_profile(cls, profile, **kwargs):
        """Validate user record against schema."""
        schema = get_schema_for_resource('user')
        profile['$schema'] = schema
        _records_state.validate(
            profile,
            schema,
            format_checker=ils_record_format_checker,
            cls=Draft4Validator
        )
        profile.pop('$schema')

    @classmethod
    def _validate_password(cls, password):
        """Validate password."""
        try:
            password_validator(password)
        except PasswordValidatorException as e:
            raise ValidationError(str(e)) from e

    @classmethod
    @property
    def fields(cls):
        """Validate password."""
        return cls.profile_fields + cls.user_fields

    @classmethod
    def remove_fields(cls, data):
        """."""
        return {k: v for k, v in data.items() if k not in cls.fields}

    @classmethod
    def get_record(cls, user_id):
        """Get a user by a user_id.

        :param user_id - the user_id
        :return: the user record
        """
        user = BaseUser.query.filter_by(id=user_id).first()
        if not user:
            return None
        return cls(user)

    def dumps(self):
        """Return pure Python dictionary with record metadata."""
        url = url_for('api_users.users_item', _external=True, id=self.user.id)
        return {
            'id': self.user.id,
            'links': {'self': url},
            'metadata': self.dumps_metadata(True)
        }

    def dumps_metadata(self, dump_patron: bool = False) -> dict:
        """Dumps the profile, email, roles metadata.

        :param dump_patron: is the patron metadata should be dumped.
        :return a dictionary with all dump user metadata.
        """
        from ..patrons.api import Patron
        metadata = {
            'roles': [r.name for r in self.user.roles]
        }
        if user_profile := self.user.user_profile:
            metadata.update(user_profile)
        if self.user.email:
            metadata['email'] = self.user.email
        if self.user.username:
            metadata['username'] = self.user.username
        if dump_patron:
            for patron in Patron.get_patrons_by_user(self.user):
                metadata.setdefault('patrons', []).append({
                    'pid': patron.pid,
                    'roles': patron.get('roles'),
                    'organisation': {
                        'pid': patron.organisation_pid
                    }
                })
        return remove_empties_from_dict(metadata)

    @classmethod
    def get_by_username(cls, username):
        """Get a user by a username.

        :param username - the user name
        :return: the user record
        """
        if base_user := BaseUser.query.filter_by(username=username).first():
            return cls(base_user)

    @classmethod
    def get_by_email(cls, email):
        """Get a user by email.

        :param email - the email of the user
        :return: the user record
        """
        user = BaseUser.query.filter(
            func.lower(BaseUser.email) == func.lower(email)).first()
        if not user:
            return None
        return cls(user)

    @classmethod
    def get_by_username_or_email(cls, username_or_email):
        """Get a user by email or username.

        :param username_or_email - the username or the email of a user
        :return: the user record
        """
        user = cls.get_by_email(username_or_email)
        return user or cls.get_by_username(username_or_email)
