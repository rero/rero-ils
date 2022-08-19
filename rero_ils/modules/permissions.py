# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
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
from abc import ABC
from functools import partial

from flask import current_app, g, jsonify
from flask_login import current_user
from flask_principal import Need
from invenio_records_permissions import \
    RecordPermissionPolicy as _RecordPermissionPolicy
from invenio_records_permissions.generators import Disable, Generator

from rero_ils.modules.patrons.api import current_librarian
from rero_ils.modules.utils import get_record_class_and_permissions_from_route

# Basics access without permission check
allow_access = type('Allow', (), {'can': lambda self: True})()
deny_access = type('Deny', (), {'can': lambda self: False})()


OrganisationNeed = partial(Need, "organisation")
LibraryNeed = partial(Need, "library")


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
            record = rec_class.get_record_by_pid(record_pid)
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
            can_delete, reasons = record.can_delete
            permissions['delete']['can'] = \
                can_delete and \
                record_permissions_factory['delete'](record=record).can()
            if not permissions['delete']['can'] and not reasons:
                # in this case, it's because config delete factory return
                # `False`, so the reason is 'Permission denied'
                reasons = {'others': {'permission': 'permission denied'}}
            permissions['delete']['reasons'] = reasons
        return jsonify(permissions)
    except Exception as error:
        # uncomment this line when you have troubles with permissions API
        # raise error
        return jsonify({'status': 'error: Bad request'}), 400


def record_permission_factory(record=None, action=None, cls=None):
    """Record permission factory.

    :param record: Record against which to check permission.
    :param action: Action to check.
    :param cls: Class of the permission.
    :return: Permission object.
    """
    # Permission is allowed for all actions.
    if current_app.config.get('RERO_ILS_APP_DISABLE_PERMISSION_CHECKS'):
        return allow_access
    # No specific class, the base record permission class is taken.
    if not cls:
        cls = RecordPermission
    return cls.create_permission(record, action)


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


class RecordPermission:
    """Record permissions for CRUD operations."""

    list_actions = ['list']
    create_actions = ['create']
    read_actions = ['read']
    update_actions = ['update']
    delete_actions = ['delete']

    def __init__(self, record, func, user):
        """Initialize a file permission object.

        :param record: Record to check.
        :param func: method of the class to call.
        :param user: Object representing current logged user.
        """
        self.record = record
        self.func = func
        self.user = user or current_user

    def can(self):
        """Return the permission object determining if the action can be done.

        :return: Permission object.
        """
        return self.func(self.user, self.record)

    @classmethod
    def create_permission(cls, record, action, user=None):
        """Create a record permission.

        :param record: The record to check.
        :param action: Action to check.
        :param user: Logged user.
        :return: Permission object.
        """
        if action in cls.list_actions:
            return cls(record, cls.list, user)
        if action in cls.create_actions:
            return cls(record, cls.create, user)
        if action in cls.read_actions:
            return cls(record, cls.read, user)
        if action in cls.update_actions:
            return cls(record, cls.update, user)
        if action in cls.delete_actions:
            return cls(record, cls.delete, user)
        # Deny access by default
        return deny_access

    @classmethod
    def list(cls, user, record=None):
        """List permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        if user.is_anonymous:
            return False
        return has_superuser_access()

    @classmethod
    def create(cls, user, record=None):
        """Create permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        if user.is_anonymous:
            return False
        return has_superuser_access()

    @classmethod
    def read(cls, user, record):
        """Read permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        if user.is_anonymous:
            return False
        return has_superuser_access()

    @classmethod
    def update(cls, user, record):
        """Update permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        if user.is_anonymous:
            return False
        return has_superuser_access()

    @classmethod
    def delete(cls, user, record):
        """Delete permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        if user.is_anonymous:
            return False
        return has_superuser_access()


class AcquisitionPermission(RecordPermission, ABC):
    """Record permissions for acquisition records."""

    @classmethod
    def list(cls, user, record=None):
        """List permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        # List organisation allowed only for staff members (lib, sys_lib)
        return bool(current_librarian)

    @classmethod
    def read(cls, user, record):
        """Read permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        # user should be authenticated
        if not current_librarian:
            return False
        # 'lib' can only update account linked to its own library
        if current_librarian.has_full_permissions:
            return current_librarian.organisation_pid == \
                record.organisation_pid
        else:
            return current_librarian.library_pids and \
                record.library_pid in current_librarian.library_pids

    @classmethod
    def create(cls, user, record=None):
        """Create permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        # user should be authenticated
        if not current_librarian:
            return False
        if not record:
            return True
        else:
            # Same as update
            return cls.update(user, record)

    @classmethod
    def _rolled_over(cls, record):
        """Check if record attached to a rolled over budget.

        :param record: Record to check.
        :return: True if action can be done.
        """
        raise NotImplementedError()

    @classmethod
    def update(cls, user, record):
        """Update permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        # only staff members (lib, sys_lib) can update acq_account
        # record cannot be null
        if not current_librarian or not record:
            return False
        # no updates is possible for accounts related to rolled over budgets.
        if not cls._rolled_over(record):
            return False
        # 'sys_lib' can update all account
        if current_librarian.has_full_permissions:
            return current_librarian.organisation_pid == \
                record.organisation_pid
        # 'lib' can only update account linked to its own library
        return current_librarian.library_pids and \
            record.library_pid in current_librarian.library_pids

    @classmethod
    def delete(cls, user, record):
        """Delete permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True if action can be done.
        """
        # Same as update
        return cls.update(user, record)


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
    """Allow if the user and the record have the same organisation."""

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
