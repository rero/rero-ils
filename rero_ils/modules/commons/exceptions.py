# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Common exceptions for RERO-ILS resources."""


class RecordNotFound(Exception):
    """Record can't be found into Invenio."""

    def __init__(self, record_cls, record_pid):
        """Initialization method.

        :param record_cls: (IlsRecord) the resource class.
        :param record_pid: (string) the resource pid.
        """
        self.record_cls = record_cls
        self.record_pid = record_pid

    def __repr__(self):
        """String representation of the exception."""
        return f"{self.record_cls.__name__}#{self.record_pid} not found"


class MissingDataException(KeyError):
    """Exception when a data is missing."""

    def __init__(self, missing_data):
        """Initialization method.

        :param missing_data: list of missing data field names.
        :type missing_data: str|list<str>
        """
        if not isinstance(missing_data, list):
            missing_data = [missing_data]
        self.missing_data = missing_data

    def __repr__(self):
        """String representation of the exception."""
        return f"Missing data :: {', '.join(self.missing_data)}"
