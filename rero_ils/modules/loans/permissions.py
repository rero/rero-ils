# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022-2022 RERO
# Copyright (C) 2019-2022-2022 UCLouvain
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

"""Permissions for loans."""
from invenio_access import action_factory, any_user
from invenio_records_permissions.generators import Generator

from rero_ils.modules.loans.api import Loan
from rero_ils.modules.permissions import \
    AllowedByActionRestrictByOwnerOrOrganisation, RecordPermissionPolicy

# Actions to control Loan policy
search_action = action_factory('loan-search')
read_action = action_factory('loan-read')
access_action = action_factory('loan-access')


class DisallowedIfAnonymized(Generator):
    """Disallow if the record is anonymized."""

    def excludes(self, record=None, *args, **kwargs):
        """Disallows the given action.

        :param record: the record to check.
        :param kwargs: extra arguments.
        :returns: a list of needs to disabled access.
        """
        return [any_user] if record and record.get('to_anonymize') else []


class LoanPermissionPolicy(RecordPermissionPolicy):
    """Loan Permission Policy used by the CRUD operations."""

    can_search = [
        AllowedByActionRestrictByOwnerOrOrganisation(
            search_action,
            record_mapper=lambda r: Loan(r)
        )
    ]
    can_read = [
        DisallowedIfAnonymized(),
        AllowedByActionRestrictByOwnerOrOrganisation(
            read_action,
            record_mapper=lambda r: Loan(r)
        )
    ]
