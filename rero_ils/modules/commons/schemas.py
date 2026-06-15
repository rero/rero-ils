# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Common marshmallow schema for RERO-ILS project."""

from functools import wraps

from flask import request
from invenio_records_rest.schemas.fields import SanitizedUnicode
from marshmallow import Schema
from marshmallow.validate import Length


def http_applicable_method(*http_methods):
    """Skip the decorated function if HTTP request method isn't applicable.

    :param http_methods: the list of HTTP method for which the decorated
        function will be applicable. If request method isn't in this list, the
        decorated function will be skipped/uncalled.
    """

    def inner(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if request.method in http_methods:
                return func(*args, **kwargs)
            return None

        return wrapper

    return inner


class RefSchema(Schema):
    """Schema to describe a reference to another resources."""

    # TODO : find a way to validate the `$ref` using a variable pattern.
    ref = SanitizedUnicode(data_key="$ref", attribute="$ref")


class NoteSchema(Schema):
    """Schema to describe a note."""

    type = SanitizedUnicode()
    content = SanitizedUnicode(validate=Length(1, 2000))
