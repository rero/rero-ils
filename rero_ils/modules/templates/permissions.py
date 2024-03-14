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

"""Templates permissions."""

from flask import g
from flask_principal import RoleNeed
from invenio_access import action_factory

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

        # If user is 'full_permissions', allow write to
        # any template (private or public) in their own organisation.
        needs = {
            OrganisationNeed(record.organisation_pid),
            RoleNeed(UserRole.FULL_PERMISSIONS)
        }
        if needs.issubset(g.identity.provides):
            return required_needs

        # If the template is private and it belongs to the user,
        # allow write according to required_needs
        owner_need = OwnerNeed(record.creator_pid)
        if record.is_private and owner_need in g.identity.provides:
            return required_needs

        # Any other case, disallow operation
        return []


class TemplatePermissionPolicy(RecordPermissionPolicy):
    """Template Permission Policy used by the CRUD operations."""

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByActionTemplateReadRestriction(read_action)]
    can_create = [AllowedByActionTemplateWriteRestriction(create_action)]
    can_update = [AllowedByActionTemplateWriteRestriction(update_action)]
    can_delete = [AllowedByActionTemplateWriteRestriction(delete_action)]
