# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

"""Blueprint used for libraries API."""

from __future__ import absolute_import, print_function

from datetime import datetime, timedelta

from flask import Blueprint, abort, jsonify, request

from rero_ils.modules.decorators import check_logged_as_librarian
from rero_ils.modules.libraries.api import Library
from rero_ils.modules.utils import add_years, date_string_to_utc

api_blueprint = Blueprint(
    'api_library',
    __name__,
    url_prefix='/library'
)


@api_blueprint.route('/<library_pid>/closed_dates', methods=['GET'])
@check_logged_as_librarian
def list_closed_dates(library_pid):
    """HTTP GET request to get the closed dates for a given library pid.

    USAGE : /api/libraries/<pid>/closed_dates?from=<from>&until=<until>
    optional parameters:
      * from: the lower interval date limit as 'YYYY-MM-DD' format.
              default value are sysdate - 1 month
      * until: the upper interval date limit as 'YYYY-MM-DD' format.
               default value are sysdate + 1 year

    :param library_pid: the library pid to search.
    """
    library = Library.get_record_by_pid(library_pid)
    if not library:
        abort(404)

    # get start date from 'from' parameter from query string request
    start_date = request.args.get('from', datetime.now() - timedelta(days=31))
    if isinstance(start_date, str):
        start_date = date_string_to_utc(start_date)
    start_date = start_date.replace(tzinfo=library.get_timezone())
    # get end date from 'until' parameter from query string request
    end_date = request.args.get('until', add_years(datetime.now(), 1))
    if isinstance(end_date, str):
        end_date = date_string_to_utc(end_date)
    end_date = end_date.replace(tzinfo=library.get_timezone())
    delta = end_date - start_date

    # compute closed date
    closed_date = []
    for i in range(delta.days + 1):
        tmp_date = start_date + timedelta(days=i)
        if not library.is_open(date=tmp_date, day_only=True):
            closed_date.append(tmp_date.strftime('%Y-%m-%d'))

    return jsonify({
        'params': {
            'from': start_date.strftime('%Y-%m-%d'),
            'until': end_date.strftime('%Y-%m-%d')
        },
        'closed_dates': closed_date
    })
