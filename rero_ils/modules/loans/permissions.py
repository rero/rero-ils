# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Permissions for loans."""

from invenio_access import action_factory, any_user
from invenio_records_permissions.generators import Generator

from rero_ils.modules.loans.api import Loan
from rero_ils.modules.permissions import (
    AllowedByActionRestrictByOwnerOrOrganisation,
    RecordPermissionPolicy,
)

# Actions to control Loan policy
search_action = action_factory("loan-search")
read_action = action_factory("loan-read")
access_action = action_factory("loan-access")


class DisallowedIfAnonymized(Generator):
    """Disallow if the record is anonymized."""

    def excludes(self, record=None, *args, **kwargs):
        """Disallows the given action.

        :param record: the record to check.
        :param kwargs: extra arguments.
        :returns: a list of needs to disabled access.
        """
        return [any_user] if record and record.get("to_anonymize") else []


class LoanPermissionPolicy(RecordPermissionPolicy):
    """Loan Permission Policy used by the CRUD operations."""

    can_search = [AllowedByActionRestrictByOwnerOrOrganisation(search_action, record_mapper=lambda r: Loan(r))]
    can_read = [
        DisallowedIfAnonymized(),
        AllowedByActionRestrictByOwnerOrOrganisation(read_action, record_mapper=lambda r: Loan(r)),
    ]
