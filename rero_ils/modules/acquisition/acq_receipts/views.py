# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Blueprint used for AcqReceipt API."""

from flask import Blueprint, abort, jsonify
from flask import request as flask_request

from rero_ils.modules.acquisition.acq_receipts.api import AcqReceipt
from rero_ils.modules.decorators import check_logged_as_librarian, jsonify_error

api_blueprint = Blueprint("api_receipt", __name__, url_prefix="/acq_receipt", template_folder="templates")


@api_blueprint.route("/<receipt_pid>/lines", methods=["POST"])
@check_logged_as_librarian
@jsonify_error
def lines(receipt_pid):
    """HTTP POST for creating multiple acquisition receipt lines.

    Required parameters:
    :param receipt_pid: the pid of the receipt.
    :returns: a list containing the given data to build the receipt line
                with a `status` field, either `success` or the validation
                error.
                In case of `success`, the created record is returned.
                In case the line is not created, the erorr message is
                returned in the field `status`.
    """
    receipt = AcqReceipt.get_record_by_pid(receipt_pid)
    if not receipt:
        abort(404, "Acquisition receipt not found")

    receipt_lines = flask_request.get_json()
    if not receipt_lines:
        abort(400, "Missing receipt lines data.")
    created_receipt_lines = receipt.create_receipt_lines(receipt_lines=receipt_lines)
    return jsonify(response=created_receipt_lines)
