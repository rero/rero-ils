# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Errors for circulation policy module."""

from invenio_records.errors import RecordsError


class OrganisationDoesNotExist(RecordsError):
    """Error raised when organisation record doest not exist."""


class PolicyNameAlreadyExists(RecordsError):
    """Error raised when the name of the new policy record exists."""


class InvalidRecordID(RecordsError):
    """Error raised when the ID of record is invalid."""


class MissingRequiredParameterError(RecordsError):
    """Exception raised when required parameter is missing."""


class RegularReceiveNotAllowed(Exception):
    """Holdings of type serials and irregular frequency."""


class NoCirculationAction(RecordsError):
    """Exception raised when no circulation action is performed."""


class NoCirculationActionIsPermitted(RecordsError):
    """Exception raised when the circulation action is not forbidden."""


class ItemBarcodeNotFound(RecordsError):
    """Exception raised when an item barcode is not found."""


class PatronBarcodeNotFound(RecordsError):
    """Exception raised when an patron barcode is not found."""
