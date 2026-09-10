# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Blueprint used for loans."""

from flask import Blueprint, abort, jsonify, request
from flask_login import login_required

from rero_ils.modules.decorators import (
    check_library_in_organisation,
    check_logged_as_librarian,
)
from rero_ils.modules.items.api import Item
from rero_ils.modules.items.models import ItemCirculationAction
from rero_ils.modules.items.views.api_views import (
    check_logged_user_authentication,
    jsonify_error,
)
from rero_ils.modules.libraries.api import Library
from rero_ils.modules.loans.api import Loan
from rero_ils.modules.loans.serializers import (
    csv_requests_search,
    json_requests_search,
    requests_to_validate_rows,
    xlsx_requests_search,
)
from rero_ils.modules.loans.utils import get_circ_policy, sum_for_fees
from rero_ils.modules.patrons.api import current_librarian, current_patrons

api_blueprint = Blueprint("api_loan", __name__, url_prefix="/loan")


@api_blueprint.route("/requests/<library_pid>", methods=["GET"])
@check_logged_as_librarian
@check_library_in_organisation
def requests_export(library_pid):
    """HTTP GET request to export the requests to validate of a library.

    The exported requests are the same as the ones listed by the professional
    interface. The output format is given by the `format` argument.
    """
    serializers = {"csv": csv_requests_search, "json": json_requests_search, "xlsx": xlsx_requests_search}
    if not (serializer := serializers.get(request.args.get("format", "csv"))):
        abort(400, "Unsupported export format")
    library = Library.get_record_by_pid(library_pid)
    return serializer(None, requests_to_validate_rows(library) if library else [])


@api_blueprint.route("/<loan_pid>/circulation_policy", methods=["GET"])
@check_logged_as_librarian
def dump_loan_current_circulation_policy(loan_pid):
    """Search and dump the current circulation policy related to a loan."""
    # NOTE : It's possible than the returned CIPO wasn't the same CIPO used
    #        for a circulation operation on this loan because data could
    #        changed (Patron.patron_type, Item.item_type, ...)
    loan = Loan.get_record_by_pid(loan_pid)
    if not loan:
        abort(404, "Loan not found")
    return jsonify(get_circ_policy(loan))


@api_blueprint.route("/<loan_pid>/overdue/preview", methods=["GET"])
@login_required
def preview_loan_overdue(loan_pid):
    """HTTP GET request for overdue preview about a loan."""
    loan = Loan.get_record_by_pid(loan_pid)
    if not loan:
        abort(404, "Loan not found")
    current_patrons_pids = [patron.pid for patron in current_patrons]
    # if the logged user is a patron the pid should be his own
    # otherwise the user should be a librarian
    if loan.get("patron_pid") not in current_patrons_pids and not current_librarian:
        abort(403)
    fees = loan.get_overdue_fees
    fees = [(fee[0], fee[1].isoformat()) for fee in fees]  # format date
    return jsonify({"total": sum_for_fees(fees), "steps": fees})


@api_blueprint.route("/<loan_pid>/can_extend", methods=["GET"])
@check_logged_user_authentication
@jsonify_error
def can_extend(loan_pid):
    """Loan can extend."""
    loan = Loan.get_record_by_pid(loan_pid)
    item_pid = loan.get("item_pid", {}).get("value")
    can_extend = {"can": False, "reasons": []}
    if item_pid:
        item = Item.get_record_by_pid(item_pid)
        can, reasons = item.can(ItemCirculationAction.EXTEND, loan=loan)
        can_extend = {"can": can, "reasons": reasons}
    return jsonify(can_extend)
