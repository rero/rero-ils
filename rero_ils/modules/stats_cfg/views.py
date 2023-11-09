# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
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

from flask import Blueprint, abort, jsonify

from rero_ils.modules.stats.api.report import StatsReport
from rero_ils.modules.stats.permissions import check_logged_as_librarian

from .api import StatConfiguration

api_blueprint = Blueprint(
    'stats_cfg',
    __name__,
    url_prefix='/stats_cfg',
    template_folder='templates',
    static_folder='static',
)


@api_blueprint.route('/live/<pid>', methods=['GET'])
@check_logged_as_librarian
def live_stats_reports(pid):
    """Preview of the stats report values.

    :param pid: pid value of the configuration.
    """
    cfg = StatConfiguration.get_record_by_pid(pid)
    if not cfg:
        abort(404, f'Configuration not found for pid {pid}.')
    res = StatsReport(cfg).collect(force=True)
    return jsonify(res)
