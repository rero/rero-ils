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

"""Permissions for all modules."""
import contextlib
import re
from copy import deepcopy
from functools import partial

from flask import current_app, g, jsonify
from flask_principal import ActionNeed, Need
from invenio_access import ActionRoles, ActionSystemRoles, ActionUsers, \
    Permission, action_factory, any_user, current_access
from invenio_accounts.models import Role
from invenio_db import db
from invenio_records_permissions import \
    RecordPermissionPolicy as _RecordPermissionPolicy
from invenio_records_permissions.generators import Disable, Generator

from rero_ils.modules.patrons.api import current_librarian, current_patrons
from rero_ils.modules.utils import get_record_class_and_permissions_from_route

# SPECIFIC ACTIONS ============================================================
#    Some actions are not related to a specific resource. For this case, we
#    can create a specific action in this root permission module.

# Is the user can manage permissions
permission_management = ActionNeed('permission-management')
# Is the user can access to the professional interface
access_ui_admin = action_factory('admin-ui-access')
# Is the user can access to circulation module. This is use for granting access
# to the `checkin/checkout` component
access_circulation = action_factory('access-circulation')
# Is the user can view the debug button into the admin interface
can_use_debug_mode = action_factory('can-use-debug-mode')


# Basics access without permission check
allow_access = type('Allow', (), {'can': lambda self: True})()
deny_access = type('Deny', (), {'can': lambda self: False})()


LibraryNeed = partial(Need, "library")
OrganisationNeed = partial(Need, "organisation")
OwnerNeed = partial(Need, "owner")


class PermissionContext:
    """List of permission context."""

    BY_ROLE = 'role'
    BY_SYSTEM_ROLE = 'system_role'
    BY_USER = 'user'


def manage_role_permissions(method, action_name, role_name):
    """Allow to manage a permission by role.

    :param method: 'allow' or 'deny'.
    :param action_name: the action name corresponding to the permission.
    :param role_name: the role name to allow/deny.
    """
    role = Role.query.filter(Role.name == role_name).first()
    action = current_access.actions.get(action_name)
    if not role:
        raise NameError(f'{role_name} not found')
    if not action:
        raise NameError(f'{action_name} not found')

    current_access.delete_action_cache(Permission._cache_key(action))
    with db.session.begin_nested():
        ActionRoles\
            .query_by_action(action)\
            .filter(ActionRoles.role == role)\
            .delete(synchronize_session=False)
        if method == 'allow':
            db.session.add(ActionRoles.allow(action, role=role))
    db.session.commit()


def record_permissions(record_pid=None, route_name=None):
    """Return record permissions.

    This function allow to return all permissions for a specific record.
    :param record_pid: the record PID to check. If None, only 'create'
                       permission should be available.
    :param route_name: the 'list' route nome of the resource.
    :return: a JSON object containing permissions for the requested resource.
    """
    try:
        rec_class, record_permissions_factory = \
            get_record_class_and_permissions_from_route(route_name)

        permissions = {
            'list': {'can': True},
            'create': {'can': True}
        }
        # To check create and list permissions, we don't need to check if the
        # record_pid exists. Just call the create permission (if exists) with
        # `None` value as record.
        for action in ['list', 'create']:
            if record_permissions_factory[action]:
                permissions[action]['can'] = \
                    record_permissions_factory[action](record=None).can()

        # If record_pid is not None, we can check about others permissions
        # (read, update, delete)
        if record_pid:
            permissions.update({
                'read': {'can': True},
                'update': {'can': True},
                'delete': {'can': True}
            })

            if hasattr(rec_class, 'get_record_by_pid'):
                # standard ILS case
                record = rec_class.get_record_by_pid(record_pid)
            else:
                # invenio records resources case
                record = rec_class.pid.resolve(record_pid)
            if not record:
                return jsonify({'status': 'error: Record not found.'}), 404

            # To check if the record could be update, just call the update
            # permission factory to get the answer
            permissions['read']['can'] = \
                record_permissions_factory['read'](record=record).can()
            permissions['update']['can'] = \
                record_permissions_factory['update'](record=record).can()

            # We have two behaviors for 'can_delete'. Either the record has
            # linked resources and so children resources should be deleted
            # before ; either the `delete_permissions_factory` for this record
            # should be called. If this call send 'False' then the
            # reason_not_to_delete should be "permission denied"
            if hasattr(record, 'can_delete'):
                # standard ILS case
                can_delete, reasons = record.can_delete
                permissions['delete']['can'] = \
                    can_delete and \
                    record_permissions_factory['delete'](record=record).can()
                if not permissions['delete']['can'] and not reasons:
                    # in this case, it's because config delete factory return
                    # `False`, so the reason is 'Permission denied'
                    reasons = {'others': {'permission': 'permission denied'}}
                permissions['delete']['reasons'] = reasons
            else:
                # invenio records resource case
                permissions['delete']['can'] = \
                    record_permissions_factory['delete'](record=record).can()

        return jsonify(permissions)
    except Exception as error:
        # uncomment this line when you have troubles with permissions API
        # raise error
        return jsonify({'status': 'error: Bad request'}), 400


def has_superuser_access():
    """Check if current user has access to super admin panel.

    This function is used in app context and can be called in all templates.
    """
    if current_app.config.get('RERO_ILS_APP_DISABLE_PERMISSION_CHECKS'):
        return True
    # TODO : create a super_user role
    #   ... superuser_access_permission = Permission(ActionNeed('superuser'))
    #   ... return superuser_access.can()
    return deny_access.can()


# =============================================================================
#   EXPOSE NEEDS
# =============================================================================
def expose_actions_need_for_user():
    """Expose basics permissions for the current logged user.

    This method will list all action_needs defined in the current application,
    and expose if the current logged user provides necessary condition to
    validate them.
    Some action_needs are not-relevant without checking them with a record (
    read, update, delete) ; so these needs will be removed from result.
    """
    actions = current_access.actions
    # filter needs for keep only relevant
    config = current_app.config.get('RERO_ILS_EXPOSED_NEED_FILTER')
    if regexp := config.get('regexp'):
        regexp = re.compile(regexp)
        actions = {
            key: need for key, need in actions.items()
            if regexp.match(key)
        }
    # check each needs regarding current logged user profile.
    actions = [key for key, need in actions.items() if Permission(need).can()]
    return actions


def expose_action_needs_by_role(roles=None):
    """Expose RERO-ILS actions (permissions) by role.

    :param roles: a list of roles to expose. Each entry is a tuple containing
                  two values: the role name and the role type.
    :return: the permission matrix corresponding to roles.
    """

    def _perform_system_role(role_names):
        if not role_names:
            return
        query = ActionSystemRoles.query \
            .filter(ActionSystemRoles.role_name.in_(role_names)) \
            .all()
        for row in query:
            matrix.setdefault(row.role_name, {
                'type': 'system_role',
                'actions': deepcopy(actions_list)
            })['actions'][row.action] = not row.exclude

    def _perform_account_roles(role_names):
        if not role_names:
            return
        roles_query = Role.query.filter(Role.name.in_(role_names))
        role_ids = [r.id for r in roles_query.all()]
        query = ActionRoles.query \
            .filter(ActionRoles.role_id.in_(role_ids)) \
            .all()
        for row in query:
            matrix.setdefault(row.role.name, {
                'type': 'role',
                'actions': deepcopy(actions_list)
            })['actions'][row.action] = not row.exclude

    actions_list = {action: None for action in current_access.actions}
    matrix = {}
    roles_types = {}
    for role in roles:
        roles_types.setdefault(role[1], []).append(role[0])
    _perform_system_role(roles_types.get('system_role'))
    _perform_account_roles(roles_types.get('role'))
    return matrix


def expose_action_needs_by_patron(patron):
    """Expose RERO-ILS actions (permissions) for a specific patron.

    :param patron: the patron to expose.
    :return: the permission matrix corresponding to patron.
    """
    # Init reasons dictionary used to explain why a permission is allowed or
    # denied. This dictionary has entry for :
    #   - each user role
    #   - 'any_user' and 'authenticated_user' roles (system_role)
    #   - special entry for specific user permissions.
    base_reasons = {role: None for role in patron.get('roles', [])}
    base_reasons.update({
        'user': None,
        'any_user': None,
        'authenticated_user': None
    })

    permissions_matrix = {
        action: {
            'name': action,
            'can': False,
            'reasons': deepcopy(base_reasons)
        }
        for action in current_access.actions
    }

    # Load specific ActionRoles permissions from Invenio-access and store them
    # into the permission_matrix.
    roles_query = Role.query.filter(Role.name.in_(patron.get('roles', [])))
    role_ids = [r.id for r in roles_query.all()]
    query = ActionRoles.query \
        .filter(ActionRoles.role_id.in_(role_ids))
    for row in query.all():
        with contextlib.suppress(KeyError):
            permissions_matrix[row.action]['reasons'][row.role.name] = \
                not row.exclude

    # Load specific ActionUsers permission from Invenio-access and store them
    # into the permission_matrix.
    query = ActionUsers.query \
        .filter(ActionUsers.user_id == patron.user.id)
    for row in query.all():
        permissions_matrix[row.action]['reasons']['user'] = not row.exclude

    # Load specific ActionSystemRoles permissions form Invenio-access and store
    # them into the permission_matrix.
    system_roles_to_check = ['any_user', 'authenticated_user']
    query = ActionSystemRoles.query\
        .filter(ActionSystemRoles.role_name.in_(system_roles_to_check))
    for row in query.all():
        with contextlib.suppress(KeyError):
            permissions_matrix[row.action]['reasons'][row.role_name] = \
                not row.exclude

    # Compute general permissions
    #   Now we load each permission data, search into the reasons list to
    #   determine the global access permission flag.
    #   1) If one `False` reason (aka. exclude) is defined --> global is FALSE
    #   2) Else if one `True` reason is defined --> global is TRUE
    #   3) Otherwise (all is null - no roles give specific access) --> global
    #      is false (this is already the default value of 'can')
    for permission in permissions_matrix.values():
        values = set(permission['reasons'].values())
        permission['can'] = True in values and False not in values

    return [v for k, v in permissions_matrix.items()]


# =============================================================================
#   RECORD PERMISSION POLICIES
# =============================================================================
class RecordPermissionPolicy(_RecordPermissionPolicy):
    """The record base permission policy.

    All permissions are deny by default. This should be compatible with
    invenio-records-rest and invenio-records-resources.
    """

    can_search = [Disable()]
    can_read = [Disable()]
    can_create = [Disable()]
    can_update = [Disable()]
    can_delete = [Disable()]

    # Associated files permissions (which are really bucket permissions)
    can_read_files = [Disable()]
    can_update_files = [Disable()]


class AllowedByAction(Generator):
    """Allows if the logged user can perform the given action."""

    def __init__(self, action):
        """Constructor.

        :param action: Need - the ``ActionNeed`` to allow.
        """
        self.action = action

    def needs(self, *args, **kwargs):
        """Allows the given action.

        :param args: extra arguments.
        :param kwargs: extra named arguments.
        :returns: a list of action permission.
        """
        return [self.action]


class AllowedByActionRestrictByOrganisation(AllowedByAction):
    """Allow if the user and the record have the same organisation."""

    def needs(self, record=None, *args, **kwargs):
        """Allows the given action.

        :param record: the record to check.
        :param args: extra arguments.
        :param kwargs: extra named arguments.
        :returns: a list of Needs to validate access.
        """
        if record:
            # Check if the record organisation match an ``OrganisationNeed``
            required_need = OrganisationNeed(record.organisation_pid)
            if required_need not in g.identity.provides:
                return []
        return super().needs(record, **kwargs)


class AllowedByActionRestrictByManageableLibrary(AllowedByAction):
    """Allow if the user and the record have the same library."""

    def __init__(self, action, callback=None):
        """Constructor.

        :param action: Need - the ``ActionNeed`` to allow.
        :param callback: the function used to retrieve the library pid related
            to the record that we need to check. By default, the
            ``library_pid`` record attribute will be used.
        """
        self.callback = callback or (lambda r: getattr(r, 'library_pid', None))
        super().__init__(action)

    def needs(self, record=None, *args, **kwargs):
        """Allows the given action.

        :param record: the record to check.
        :param kwargs: extra arguments.
        :returns: a list of Needs to validate access.
        """
        if record and (library_pid := self.callback(record)):
            # Check if the record library match an ``LibraryNeed``
            required_need = LibraryNeed(library_pid)
            if required_need not in g.identity.provides:
                return []
        return super().needs(record, **kwargs)


class AllowedByActionRestrictByOwnerOrOrganisation(AllowedByAction):
    """Allow if user and record are same or belong the same organisation.

    If the current user is a `patron` then, we allow only their own record.
    If the current user is a `staff_member` then, we allow record for the same
    organisation.
    """

    def __init__(self, action, patron_callback=None, record_mapper=None):
        """Constructor.

        :param action: Need - the ``ActionNeed`` to allow.
        :param patron_callback: the function used to retrieve the patron pid
            related to the record that we need to check. By default, the
            ``patron_pid`` record attribute will be used.
        :param record_mapper: A function used to transform the record.
        """
        self.patron_callback = patron_callback or \
            (lambda r: getattr(r, 'patron_pid', None))
        self.record_mapper = record_mapper
        super().__init__(action)

    def needs(self, record=None, *args, **kwargs):
        """Allows the given action.

        :param record: the record to check.
        :param kwargs: extra arguments.
        :returns: a list of Needs to validate access.
        """
        if record:
            if self.record_mapper:
                record = self.record_mapper(record)
            required_need = set()
            if current_patrons:
                required_need.add(OwnerNeed(self.patron_callback(record)))
            if current_librarian:
                required_need.add(OrganisationNeed(record.organisation_pid))
            if required_need and not required_need.intersection(
                    g.identity.provides):
                return []

        return super().needs(record, **kwargs)


class DisallowedIfRollovered(Generator):
    """Disallow if the record is considerate roll-overed."""

    def __init__(self, record_cls, callback=None):
        """Constructor.

        :param record_cls: the record class to build a resource if record is
            received is only dict/data.
        :param callback: the function to use to know if the resource is
            rollovered. This function should return a boolean value. By default
            the ``is_active`` record property will be returned if exists ;
            otherwise True.
        """
        self.record_cls = record_cls
        self.is_rollovered = callback \
            or (lambda record: not getattr(record, 'is_active', True))

    def excludes(self, record=None, **kwargs):
        """Disallow operation check.

        :param record; the record to check.
        :param kwargs: extra named arguments.
        :returns: a list of Needs to disable access.
        """
        if record:
            if not isinstance(record, self.record_cls):
                record = self.record_cls(record)
            if self.is_rollovered(record):
                return [any_user]
        return []
