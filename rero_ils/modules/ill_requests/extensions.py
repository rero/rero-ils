# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""ILL request record extensions."""

import contextlib

from rero_ils.modules.operation_logs.extensions import OperationLogObserverExtension


class IllRequestOperationLogObserverExtension(OperationLogObserverExtension):
    """Observer on ``ILLRequest`` to build operation log when it changes."""

    def get_additional_informations(self, record):
        """Additional information about Ill request operation log.

        :param record: the observed record.
        :return a dict with additional informations.
        """
        data = {"ill_request": {"status": record.get("status")}}
        # if the location or library doesn't exist anymore,
        # we do not inject the library pid in the operation log
        with contextlib.suppress(Exception):
            data["ill_request"]["library_pid"] = record.get_library().pid
        if loan_status := record.get("loan_status"):
            data["ill_request"]["loan_status"] = loan_status
        return data
