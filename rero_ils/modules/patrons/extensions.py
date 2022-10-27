# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

"""Patron record extensions."""
from flask import current_app
from flask_login import current_user
from invenio_records.extensions import RecordExtension
from jsonschema.exceptions import ValidationError

from rero_ils.modules.users.api import User


class UserDataExtension(RecordExtension):
    """Add related user data extension."""

    def pre_dump(self, record, data, dumper=None):
        """Add user data.

        :param record: the record metadata.
        :param data: The dumped data dictionary.
        :param dumper: Dumper to use when dumping the record.
        :return the future dumped data.
        """
        user = User.get_by_id(record.get('user_id'))
        user_info = user.dumps_metadata()
        return data.update(user_info)


class PatronRoleManagementValidatorExtension(RecordExtension):
    """Check about patron role management."""

    def _validate(self, record, **kwargs):
        """Validate changes on the record.

        :param record: the record containing data to validate.
        :param **kwargs: any other named arguments.
        :raises ValidationError: If an error is detected during the validation
            check. This error could be serialized to get the error message.
        """
        # First, determine if a user is connected. If not, no check must be
        # done about role management (probably it's a console script/user).
        if not current_user:
            return

        # Now determine the roles difference between original record and
        # the record that is updated. If no changes are detected, no more
        # check will be done
        original_record = record.db_record() or {}
        record_roles = set(record.get('roles', []))
        original_roles = set(original_record.get('roles', []))
        role_changes = original_roles.symmetric_difference(record_roles)
        if not role_changes:
            return

        # Depending on the current logged user roles, determine which roles
        # this user can manage reading the configuration setting. If any role
        # from `role_changes` are not present in manageable role, an error
        # should be raised.
        key_config = 'RERO_ILS_PATRON_ROLES_MANAGEMENT_RESTRICTIONS'
        config_roles = current_app.config.get(key_config, {})
        manageable_roles = set()
        for role in current_user.roles:
            manageable_roles = manageable_roles.union(
                config_roles.get(role.name, {}))
        # If any difference are found between both sets, disallow the operation
        if role_diffs := role_changes.difference(manageable_roles):
            error_roles = ', '.join(role_diffs)
            raise ValidationError(f'Unable to manage role(s) : {error_roles}')

    validate = _validate
    pre_delete = _validate
