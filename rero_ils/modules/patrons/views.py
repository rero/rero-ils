# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2024 RERO
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Blueprint used for loading templates."""

from __future__ import absolute_import, print_function

import datetime
import re

from flask import Blueprint, abort, current_app, jsonify, render_template
from flask import request as flask_request
from flask_babel import lazy_gettext as _
from flask_login import current_user, login_required
from flask_security import utils as security_utils
from invenio_i18n.ext import current_i18n
from invenio_oauth2server.decorators import require_api_auth

from rero_ils.modules.decorators import (
    check_logged_as_librarian,
    check_logged_user_authentication,
)
from rero_ils.modules.ill_requests.api import ILLRequestsSearch
from rero_ils.modules.loans.api import get_loans_stats_by_patron_pid, get_overdue_loans
from rero_ils.modules.loans.utils import sum_for_fees
from rero_ils.modules.organisations.dumpers import OrganisationLoggedUserDumper
from rero_ils.modules.patron_transactions.utils import (
    get_transactions_total_amount_for_patron,
)
from rero_ils.modules.patron_types.api import PatronType, PatronTypesSearch
from rero_ils.modules.patrons.api import (
    Patron,
    PatronsSearch,
    current_librarian,
    current_patrons,
)
from rero_ils.modules.patrons.permissions import get_allowed_roles_management
from rero_ils.modules.permissions import expose_actions_need_for_user
from rero_ils.modules.users.api import User
from rero_ils.modules.utils import extracted_data_from_ref, get_base_url
from rero_ils.utils import remove_empties_from_dict

api_blueprint = Blueprint(
    "api_patrons",
    __name__,
    url_prefix="/patrons",
    template_folder="templates",
    static_folder="static",
)


_PID_REGEX = re.compile(r"NOT\s+pid:\s*(\w+)\s*")
_EMAIL_REGEX = re.compile(r'email:"\s*(.*?)\s*"')
_USERNAME_REGEX = re.compile(r'username:"\s*(.*?)\s*"')


@api_blueprint.route("/<patron_pid>/circulation_informations", methods=["GET"])
@check_logged_as_librarian
def patron_circulation_informations(patron_pid):
    """Get the circulation statistics and info messages about a patron."""
    patron = Patron.get_record_by_pid(patron_pid)
    if not patron:
        abort(404, "Patron not found")
    preview_amount = sum(
        sum_for_fees(loan.get_overdue_fees) for loan in get_overdue_loans(patron.pid)
    )
    engaged_amount = get_transactions_total_amount_for_patron(patron.pid, status="open")
    statistics = get_loans_stats_by_patron_pid(patron_pid)
    statistics["ill_requests"] = ILLRequestsSearch().get_ill_requests_total_for_patron(
        patron_pid
    )
    return jsonify(
        {
            "fees": {"engaged": engaged_amount, "preview": preview_amount},
            "statistics": statistics,
            "messages": patron.get_circulation_messages(),
        }
    )


@api_blueprint.route("/<patron_pid>/overdues/preview", methods=["GET"])
@login_required
def patron_overdue_preview_api(patron_pid):
    """Get all overdue preview linked to a patron."""
    data = []
    for loan in get_overdue_loans(patron_pid):
        fees = loan.get_overdue_fees
        fees = [(fee[0], fee[1].isoformat()) for fee in fees]
        total_amount = sum_for_fees(fees)
        if total_amount > 0:
            data.append(
                {"loan": loan.dumps(), "fees": {"total": total_amount, "steps": fees}}
            )
    return jsonify(data)


blueprint = Blueprint(
    "patrons",
    __name__,
    template_folder="templates",
    static_folder="static",
)


@blueprint.route("/patrons/logged_user", methods=["GET"])
def logged_user():
    """Current logged user information in JSON."""
    config = current_app.config
    data = {
        "permissions": expose_actions_need_for_user(),
        "settings": {
            "maxFilesCount": config.get("RERO_ILS_APP_FILES_UI_MAX", 600),
            "language": current_i18n.locale.language,
            "globalView": config.get("RERO_ILS_SEARCH_GLOBAL_VIEW_CODE"),
            "baseUrl": get_base_url(),
            "agentLabelOrder": config.get("RERO_ILS_AGENTS_LABEL_ORDER", {}),
            "agentSources": config.get("RERO_ILS_AGENTS_SOURCES", []),
            "operationLogs": config.get("RERO_ILS_ENABLE_OPERATION_LOG", []),
            "documentAdvancedSearch": config.get(
                "RERO_ILS_APP_DOCUMENT_ADVANCED_SEARCH", False
            ),
            "userProfile": {
                "readOnly": config.get("RERO_PUBLIC_USERPROFILES_READONLY", False),
                "readOnlyFields": config.get(
                    "RERO_PUBLIC_USERPROFILES_READONLY_FIELDS", []
                ),
            },
        },
    }
    if not current_user.is_authenticated:
        return jsonify(data)

    user = User.get_record(current_user.id).dumps_metadata()
    user["id"] = current_user.id
    data = {**data, **user, "patrons": []}
    for patron in Patron.get_patrons_by_user(current_user):
        patron.pop("$schema", None)
        patron.pop("user_id", None)
        patron.pop("notes", None)
        patron["organisation"] = patron.organisation.dumps(
            dumper=OrganisationLoggedUserDumper()
        )
        patron["libraries"] = [{"pid": pid} for pid in patron.manageable_library_pids]
        data["patrons"].append(patron)

    return jsonify(data)


@blueprint.route("/<string:viewcode>/patrons/profile/", defaults={"path": ""})
@blueprint.route("/<string:viewcode>/patrons/profile/<path:path>")
@login_required
def profile(viewcode, path):
    """Patron Profile Page."""
    if (path not in ["user/edit", "password/edit"]) and not current_patrons:
        abort(401)
    if (path in ["user/edit", "password/edit"]) and current_app.config.get(
        "RERO_PUBLIC_USERPROFILES_READONLY"
    ):
        abort(401)
    return render_template("rero_ils/patron_profile.html", viewcode=viewcode)


@api_blueprint.route("/roles_management_permissions", methods=["GET"])
@check_logged_as_librarian
def get_roles_management_permissions():
    """Get the roles that current logged user could manage."""
    return jsonify({"allowed_roles": list(get_allowed_roles_management())})


@api_blueprint.route("/<string:patron_pid>/messages", methods=["GET"])
@check_logged_user_authentication
def get_messages(patron_pid):
    """Get messages for the current user."""
    patron = Patron.get_record_by_pid(patron_pid)
    messages = patron.get_circulation_messages(True)
    if patron.pending_subscriptions:
        messages.append(
            {"type": "warning", "content": _("You have a pending subscription fee.")}
        )
    for note in patron.get("notes", []):
        if note.get("type") == "public_note":
            messages.append({"type": "warning", "content": note.get("content")})
    prime_alert_mapping = {"warning": "warn"}
    for message in messages:
        msg_type = message["type"]
        message["type"] = prime_alert_mapping.get(msg_type, msg_type)
    return jsonify(messages)


@api_blueprint.route("/authenticate", methods=["POST"])
@check_logged_as_librarian
def patron_authenticate():
    """Patron authenticate.

    :param username - user username
    :param password - user password
    :returns: The patron's information.
    """
    json = flask_request.get_json()
    if not json or "username" not in json or "password" not in json:
        abort(400)
    username = json["username"]
    password = json["password"]
    # load user
    user = User.get_by_username_or_email(username)
    if not user:
        abort(404, "User not found.")
    # load patron
    organisation_pid = current_librarian.organisation_pid
    result = (
        PatronsSearch()
        .filter("term", user_id=user.user.id)
        .filter("term", organisation__pid=organisation_pid)
        .scan()
    )
    try:
        patron = next(result).to_dict()
    except StopIteration:
        abort(404, "User not found.")
    # Validate password
    if not security_utils.verify_password(password, user.user.password):
        abort(401, "Identification error.")
    patron_data = patron.get("patron", {})
    if not patron_data:
        abort(404, "User not found.")
    patron_type_result = (
        PatronTypesSearch()
        .filter("term", pid=patron_data.get("type", {}).get("pid"))
        .source(includes=["code"])
        .scan()
    )
    try:
        patron_type = next(patron_type_result).to_dict()
    except StopIteration:
        abort(404)
    return jsonify(
        remove_empties_from_dict(
            {
                "fullname": patron.get("first_name") + " " + patron.get("last_name"),
                "street": patron.get("street"),
                "postal_code": patron.get("postal_code"),
                "city": patron.get("city"),
                "phone": patron.get("home_phone"),
                "email": patron.get("email"),
                "birth_date": patron.get("birth_date"),
                "patron_type": patron_type.get("code"),
                "expiration_date": patron_data.get("expiration_date"),
                "blocked": patron_data.get("blocked", False),
                "blocked_note": patron_data.get("blocked_note"),
                "notes": list(
                    filter(
                        lambda note: note.get("type") == "staff_note",
                        patron.get("notes", []),
                    )
                ),
            }
        )
    )


@api_blueprint.route("/info", methods=["GET"])
@require_api_auth()
def info():
    """Get patron info."""
    token_scopes = flask_request.oauth.access_token.scopes

    data = {"user_id": current_user.id}
    # Full name
    name_parts = [
        current_user.user_profile.get("last_name", "").strip(),
        current_user.user_profile.get("first_name", "").strip(),
    ]
    fullname = ", ".join(filter(None, name_parts))
    if fullname and "fullname" in token_scopes:
        data["fullname"] = fullname
    birthdate = current_user.user_profile.get("birth_date")
    # Birthdate
    if birthdate and "birthdate" in token_scopes:
        data["birthdate"] = birthdate

    patrons = current_patrons
    if patrons:
        patron = patrons[0]
        # Barcode
        if patron.get("patron", {}).get("barcode"):
            data["barcode"] = patron["patron"]["barcode"][0]
    # Patron
    patron_types = []
    patron_infos = {}
    for patron in patrons:
        patron_type = PatronType.get_record_by_pid(
            extracted_data_from_ref(patron["patron"]["type"]["$ref"])
        )
        patron_type_code = patron_type.get("code")
        institution = patron.organisation["code"]
        expiration_date = patron.get("patron", {}).get("expiration_date")

        # old list (patron_types)
        if "patron_types" in token_scopes:
            info = {"patron_pid": patron.pid}
            if patron_type_code and "patron_type" in token_scopes:
                info["patron_type"] = patron_type_code
            if institution and "institution" in token_scopes:
                info["institution"] = institution
            if expiration_date and "expiration_date" in token_scopes:
                info["expiration_date"] = datetime.datetime.strptime(
                    expiration_date, "%Y-%m-%d"
                ).isoformat()
            patron_types.append(info)

        # new dict (patron_info)
        patron_info = {"patron_pid": patron.pid}
        if institution and "institution" in token_scopes:
            patron_info["institution"] = institution
        if patron_type_code and "patron_type" in token_scopes:
            patron_info["patron_type"] = patron_type_code
        if expiration_date and "expiration_date" in token_scopes:
            patron_info["expiration_date"] = datetime.datetime.strptime(
                expiration_date, "%Y-%m-%d"
            ).isoformat()
        patron_infos[institution] = patron_info

    if patron_types:
        data["patron_types"] = patron_types
    if patron_infos:
        data["patron_info"] = patron_infos
    return jsonify(data)


@blueprint.add_app_template_global
def patron_message():
    """Get patron message."""
    if not current_patrons:
        return
    data = {"show_info": False, "data": {}}
    for patron in current_patrons:
        if patron.is_blocked or patron.is_expired:
            data["show_info"] = True
        organisation = patron.organisation
        data["data"][organisation["code"]] = {
            "name": organisation["name"],
            "blocked": {
                "is_blocked": patron.is_blocked,
                "message": patron.get_blocked_message(public=True),
            },
            "is_expired": patron.is_expired,
        }
    return data
