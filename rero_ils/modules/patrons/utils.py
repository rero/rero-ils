# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
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

"""Utilities functions for patrons."""
from flask import current_app
from flask_login import current_user
from marshmallow import ValidationError


def user_has_patron(user=current_user):
    """Test if user has a patron."""
    from .api import Patron
    patrons = Patron.get_patrons_by_user(user=user)
    return bool(patrons)  # true if `patrons` list isn't empty; false otherwise


def get_patron_pid_by_email(email):
    """Get patron pid by email.

    :param email: email to search.
    :return: the first patron pid found corresponding to this email.
    """
    from .api import PatronsSearch
    query = PatronsSearch().filter('term', email=email).source(['pid'])
    if hit := next(query.scan(), None):
        return hit.pid


def validate_role_changes(user, changes, raise_exc=True):
    """Validate `roles` changed depending on application configuration.

    :param user: the user requesting patron role changes.
    :param changes: the list of all role changes.
    :param raise_exc: Is the function must raise an exception or not.
    :return False if validation failed, True otherwise
    :raise ValidationError: if error has detected.
    """
    # Depending on the current logged user roles, determine which roles
    # this user can manage reading the configuration setting. If any role
    # from `role_changes` are not present in manageable role, an error
    # should be raised.
    key_config = 'RERO_ILS_PATRON_ROLES_MANAGEMENT_RESTRICTIONS'
    config_roles = current_app.config.get(key_config, {})
    manageable_roles = set()
    for role in user.roles:
        manageable_roles = manageable_roles.union(
            config_roles.get(role.name, {}))
    # If any difference are found between both sets, disallow the operation
    if role_diffs := changes.difference(manageable_roles):
        if raise_exc:
            error_roles = ', '.join(role_diffs)
            raise ValidationError(f'Unable to manage role(s): {error_roles}')
        else:
            return False
    # No problems were detected
    return True
