# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Blueprint used for loading templates."""

from flask import Blueprint, jsonify

from ..circ_policies.api import CircPolicy
from ..decorators import check_logged_as_librarian
from ..patrons.api import current_librarian

blueprint = Blueprint(
    "circ_policies",
    __name__,
    template_folder="templates",
    static_folder="static",
)


@blueprint.route("/circ_policies/name/validate/<name>", methods=["GET"])
@check_logged_as_librarian
def name_validate(name):
    """Circulation policy name validation."""
    response = {"name": None}
    if circ_policy := CircPolicy.exist_name_and_organisation_pid(name, current_librarian.organisation.pid):
        response = {"name": circ_policy.name}
    return jsonify(response)
