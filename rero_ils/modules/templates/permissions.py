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

"""Templates permissions."""

from flask import g, request
from invenio_access import action_factory, any_user
from invenio_records_permissions.generators import Generator

from rero_ils.modules.patrons.api import current_librarian
from rero_ils.modules.permissions import AllowedByAction, LibraryNeed, \
    OrganisationNeed, OwnerNeed, RecordPermissionPolicy
from rero_ils.modules.templates.api import Template
from rero_ils.modules.users.models import UserRole

# Actions to control Templates policies for CRUD operations
search_action = action_factory('tmpl-search')
read_action = action_factory('tmpl-read')
create_action = action_factory('tmpl-create')
update_action = action_factory('tmpl-update')
delete_action = action_factory('tmpl-delete')
access_action = action_factory('tmpl-access')


class AllowedByActionTemplateReadRestriction(AllowedByAction):
    """Allows by action with special template specification for read."""

    def needs(self, record=None, *args, **kwargs):
        """Allows the given action.

        :param record: the record to analyze
        :param args: extra arguments.
        :param kwargs: extra named arguments.
        :returns: a list of action permission.
        """
        required_needs = super().needs(record, **kwargs)
        if record and not isinstance(record, Template):
            record = Template(record)
        # if record isn't a `Template` resource, we can't continue any other
        # check, just return the already known `required_needs`
        if not record:
            return required_needs

        # if current logged user isn't a staff member then protect the template
        # by only its owner. If permission matrix is correctly build, it should
        # never happen.
        owner_need = OwnerNeed(record.creator_pid)
        if not current_librarian and owner_need not in g.identity.provides:
            return []  # empty array == disable operation

        # By default, users can only perform operations on template for its
        # own organisation ; it could be more restrictive for private templates
        # but this special case will be analyzed below
        provided_needs = g.identity.provides
        if OrganisationNeed(record.organisation_pid) not in provided_needs:
            return []  # empty array == disable operation

        # If template is private, restriction are more complex and depend on
        # the user roles :
        #   - full_permission : no additional restrictions.
        #   - library_administration : only templates for user belonging to
        #       its library
        #   - other : only own templates.
        if (roles := current_librarian.get('roles')) and record.is_private:
            if UserRole.FULL_PERMISSIONS in roles:
                pass
            elif UserRole.LIBRARY_ADMINISTRATOR in roles:
                if all(LibraryNeed(lib_pid) not in provided_needs
                       for lib_pid in current_librarian.library_pids):
                    return []  # empty array == disable operation
            elif OwnerNeed(record.creator_pid) not in provided_needs:
                return []  # empty array == disable operation

        return required_needs


class AllowedByActionTemplateWriteRestriction(AllowedByAction):
    """Allows by action with special template specification for write."""

    def needs(self, record, **kwargs):
        """Allows the given action.

        :param record: the record to analyze
        :param kwargs: extra named arguments.
        :returns: a list of action permission.
        """
        required_needs = super().needs(record, **kwargs)
        if record and not isinstance(record, Template):
            record = Template(record)
        # if record isn't a `Template` resource, we can't continue any other
        # check, just return the already known `required_needs`
        if not record:
            return required_needs

        # if current logged user isn't a staff member then protect the template
        # by only its owner. If permission matrix is correctly build, it should
        # never happen.
        owner_need = OwnerNeed(record.creator_pid)
        if not current_librarian and owner_need not in g.identity.provides:
            return []  # empty array == disable operation

        # * If template is public, only 'full_permission' user can perform
        #   create/update/delete operations on such record for record of its
        #   own organisation.
        # * If template is private, only owner can perform create/update/delete
        #   operations on such record.
        user_roles = current_librarian.get('roles', [])
        if record.is_public:
            org_need = OrganisationNeed(record.organisation_pid)
            if UserRole.FULL_PERMISSIONS not in user_roles or \
               org_need not in g.identity.provides:
                return []  # empty array == disable operation
        elif record.is_private and owner_need not in g.identity.provides:
            return []  # empty array == disable operation

        return required_needs


class DisableTemplateVisibilityChanges(Generator):
    """Disable template visibility changes with conditions."""

    allowed_roles = [UserRole.FULL_PERMISSIONS, UserRole.LIBRARY_ADMINISTRATOR]

    def excludes(self, record=None, **kwargs):
        """Disallow `visibility` field changes depending on user roles.

        Any changes on the `visibility` can be operated only by a user
        having 'full-permission' or 'librarian-administrator' role.

        :param record; the record to check.
        :param kwargs: extra named arguments.
        :returns: a list of Needs to disable access.
        """
        if record:
            incoming_record = request.get_json(silent=True) or {}
            if incoming_record and \
               record.get('visibility') != incoming_record.get('visibility'):
                if not current_librarian:
                    return [any_user]
                user_roles = set(current_librarian.get('roles'))
                if not user_roles.intersection(self.allowed_roles):
                    return [any_user]
        return []


class TemplatePermissionPolicy(RecordPermissionPolicy):
    """Template Permission Policy used by the CRUD operations."""

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByActionTemplateReadRestriction(read_action)]
    can_create = [AllowedByActionTemplateWriteRestriction(create_action)]
    can_update = [
        AllowedByActionTemplateWriteRestriction(update_action),
        DisableTemplateVisibilityChanges()
    ]
    can_delete = [AllowedByActionTemplateWriteRestriction(delete_action)]
