# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Organisation dumpers."""

from invenio_records.dumpers import Dumper as InvenioRecordsDumper


class OrganisationLoggedUserDumper(InvenioRecordsDumper):
    """Organisation dumper class for logged user."""

    def dump(self, record, data):
        """Dump a library instance for acquisition order notification.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        """
        data.update(
            {
                "pid": record.pid,
                "name": record.get("name"),
                "code": record.get("code"),
                "currency": record.get("default_currency"),
                "budget": {"pid": record.get("current_budget_pid")},
            }
        )
        return {k: v for k, v in data.items() if v}
