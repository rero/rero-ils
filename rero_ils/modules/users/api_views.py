# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Blueprint used for user api."""

from flask import Blueprint, abort, current_app, jsonify, request
from invenio_records_rest.utils import obj_or_import_string

from rero_ils.modules.decorators import check_logged_as_librarian
from rero_ils.modules.utils import PasswordValidatorException

from .api import password_validator

api_blueprint = Blueprint("api_user", __name__, url_prefix="/user")


@api_blueprint.route("/password/generate", methods=["GET"])
@check_logged_as_librarian
def password_generate():
    """Generation of a password."""
    min_length = current_app.config.get("RERO_ILS_PASSWORD_MIN_LENGTH", 8)
    special_char = current_app.config.get("RERO_ILS_PASSWORD_SPECIAL_CHAR")
    length = int(request.args.get("length", min_length))
    if length < min_length:
        abort(400, f"The password must be at least {min_length} characters long.")
    generator = obj_or_import_string(current_app.config.get("RERO_ILS_PASSWORD_GENERATOR"))
    try:
        return generator(length=length, special_char=special_char)
    except Exception:
        abort(400, "Password generator error.")


@api_blueprint.route("/password/validate", methods=["POST"])
def password_validate():
    """Validation of a password."""
    password = request.get_json().get("password")
    if not password:
        abort(400, "The password must be filled in.")
    try:
        password_validator(password)
    except PasswordValidatorException as pve:
        abort(400, str(pve))
    return jsonify({"message": "Valid password"})
