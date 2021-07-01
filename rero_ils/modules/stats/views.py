# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
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

import arrow
from flask import Blueprint, render_template

from .api import StatsForPricing, StatsSearch
from .permissions import check_logged_as_admin

blueprint = Blueprint(
    'stats',
    __name__,
    url_prefix='/stats',
    template_folder='templates',
    static_folder='static',
)


@blueprint.route('/', methods=['GET'])
@check_logged_as_admin
def stats():
    """Show the list of the first 100 items on the stats list."""
    s = StatsSearch().sort('-_created').source(['pid', '_created'])
    hits = s[0:100].execute().to_dict()
    return render_template(
        'rero_ils/stats_list.html', records=hits['hits']['hits'])


@blueprint.route('/live', methods=['GET'])
@check_logged_as_admin
def live_stats():
    """Show the current stats values."""
    now = arrow.utcnow()
    stats = StatsForPricing(to_date=now).collect()
    return render_template(
        'rero_ils/detailed_view_stats.html',
        record=dict(created=now, values=stats))
