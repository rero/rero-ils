# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Blueprint used for loading templates."""

from flask import Blueprint, jsonify

from ..decorators import check_logged_as_librarian
from ..patron_types.api import PatronType
from ..patrons.api import current_librarian

blueprint = Blueprint(
    "patron_types",
    __name__,
    template_folder="templates",
    static_folder="static",
)


@blueprint.route("/patron_types/name/validate/<name>", methods=["GET"])
@check_logged_as_librarian
def name_validate(name):
    """Patron type name validation."""
    response = {"name": None}
    if current_librarian:
        if patron_type := PatronType.exist_name_and_organisation_pid(name, current_librarian.organisation.pid):
            response = {"name": patron_type.name}
    return jsonify(response)
