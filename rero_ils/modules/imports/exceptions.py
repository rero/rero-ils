# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""RERO-ILS imports exceptions."""

from invenio_rest.errors import RESTException


class ResultNotFoundOnTheRemoteServer(RESTException):
    """Non existent remote record."""

    code = 404
    description = "Record not found on the remote server."
