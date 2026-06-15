# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Blueprint used for loading templates."""

from flask import Blueprint, abort, jsonify

from rero_ils.modules.stats.api.report import StatsReport
from rero_ils.modules.stats.permissions import check_logged_as_librarian

from .api import StatConfiguration

api_blueprint = Blueprint(
    "stats_cfg",
    __name__,
    url_prefix="/stats_cfg",
    template_folder="templates",
    static_folder="static",
)


@api_blueprint.route("/live/<pid>", methods=["GET"])
@check_logged_as_librarian
def live_stats_reports(pid):
    """Preview of the stats report values.

    :param pid: pid value of the configuration.
    """
    cfg = StatConfiguration.get_record_by_pid(pid)
    if not cfg:
        abort(404, f"Configuration not found for pid {pid}.")
    res = StatsReport(cfg).collect(force=True)
    return jsonify(res)
