# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021-2023 RERO
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

from datetime import datetime

from flask import current_app, url_for
from flask_babelex import lazy_gettext as _
from flask_login import current_user
from flask_security.confirmable import confirm_user
from flask_security.recoverable import send_reset_password_instructions
from invenio_accounts.ext import hash_password
from invenio_accounts.models import User as BaseUser
from invenio_db import db
from invenio_jsonschemas import current_jsonschemas
from invenio_records.validators import PartialDraft4Validator
from invenio_records_rest.utils import obj_or_import_string
from invenio_userprofiles.models import UserProfile
from jsonschema.exceptions import ValidationError
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound
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
        'city', 'birth_date', 'username', 'home_phone', 'business_phone',
        'mobile_phone', 'other_phone', 'keep_history', 'country'
    ]

    def __init__(self, user):
        """User class initializer."""
        self.user = user

    @property
    def id(self):
        """Get user id."""
        return self.user.id

    @classmethod
    def create(cls, data, **kwargs):
        """User record creation.

        :param cls - class object
        :param data - dictionary representing a user record
        """
        with db.session.begin_nested():
            email = data.pop('email', None)
            data.pop('roles', None)
            # Generate password if not present
            password = data.pop('password', None)
            if not password:
                password = password_generator()
            cls._validate(data=data)
            user = BaseUser(
                password=hash_password(password),
                profile=data, active=True)
            db.session.add(user)
            profile = user.profile
            for field in cls.profile_fields:
                value = data.get(field)
                if value is not None:
                    if field == 'birth_date':
                        value = datetime.strptime(value, '%Y-%m-%d')
                    setattr(profile, field, value)
            # send the reset password notification for new users
            if email:
                user.email = email
            db.session.merge(user)
        db.session.commit()
        if user.email:
            send_reset_password_instructions(user)
        confirm_user(user)
        return cls(user)

    def update(self, data):
        """User record update.

        :param data - dictionary representing a user record to update
        """
        from ..patrons.listener import update_from_profile
        data.pop('roles', None)
        self._validate(data=data)
        email = data.pop('email', None)
        password = data.pop('password', None)
        user = self.user
        with db.session.begin_nested():
            if user.profile is None:
                user.profile = UserProfile(user_id=user.id)
            profile = user.profile
            for field in self.profile_fields:
                if field == 'birth_date':
                    setattr(
                        profile, field,
                        datetime.strptime(data.get(field), '%Y-%m-%d'))
                else:
                    setattr(profile, field, data.get(field, ''))
            if password:
                user.password = hash_password(password)

            if email and email != user.email:
                user.email = email
            # remove the email from user data
            elif not email and user.email:
                user.email = None
            db.session.merge(user)
        db.session.commit()
        confirm_user(user)
        update_from_profile('user', self.user.profile)
        return self

    @classmethod
    def _validate(cls, data, **kwargs):
        """Validate user record against schema."""
        if 'password' in data:
            cls._validate_password(data['password'])
        default_user_schema = get_schema_for_resource('user')
        if schema := data.pop('$schema', default_user_schema):
            _records_state.validate(
                data,
                schema,
                format_checker=ils_record_format_checker,
                cls=PartialDraft4Validator
            )
        return data

    @classmethod
    def _validate_password(cls, password):
        """Validate password."""
        try:
            password_validator(password)
        except PasswordValidatorException as e:
            raise ValidationError(str(e)) from e

    @classmethod
    def get_by_id(cls, user_id):
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
        if self.user.profile:
            for field in self.profile_fields:
                if value := getattr(self.user.profile, field):
                    if field == 'birth_date':
                        value = datetime.strftime(value, '%Y-%m-%d')
                    metadata[field] = value
        if self.user.email:
            metadata['email'] = self.user.email
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
        try:
            profile = UserProfile.get_by_username(username)
            return cls(profile.user)
        except NoResultFound:
            return None

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
