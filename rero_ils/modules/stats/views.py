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

import csv
import datetime
from io import StringIO

import arrow
import jinja2
import pytz
from elasticsearch_dsl import Q
from flask import Blueprint, abort, make_response, render_template, request

from .api.api import Stat, StatsSearch
from .api.pricing import StatsForPricing
from .models import StatType
from .permissions import check_logged_as_admin, check_logged_as_librarian
from .serializers import StatCSVSerializer


def stats_view_method(pid, record, template=None, **kwargs):
    """Display the detail view..

    :param pid: PID object.
    :param record: Record object.
    :param template: Template to render.
    :param **kwargs: Additional view arguments based on URL rule.
    :return: The rendered template.
    """
    # We make a `dumps` to trigger the extension on the statistical record
    # that allows to filter the libraries.
    record = record.dumps()
    return render_template(
        template,
        record=record
    )


blueprint = Blueprint(
    'stats',
    __name__,
    url_prefix='/stats',
    template_folder='templates',
    static_folder='static',
)


@blueprint.route('/', methods=['GET'])
@check_logged_as_admin
def stats_billing():
    """Show the list of the first 100 items on the billing stats list.

    Note: includes old statistics where the field type was absent.
    """
    f = ~Q('exists', field='type') | Q('term', type=StatType.BILLING)
    search = StatsSearch().filter('bool', must=[f]).sort('-_created')\
        .source(['pid', '_created'])
    hits = search[0:100].execute().to_dict()
    return render_template(
        'rero_ils/stats_list.html', records=hits['hits']['hits'],
        type=StatType.BILLING)


@blueprint.route('/live', methods=['GET'])
@check_logged_as_admin
def live_stats_billing():
    """Show the current billing stats values."""
    now = arrow.utcnow()
    stats = StatsForPricing(to_date=now).collect()
    return render_template(
        'rero_ils/detailed_view_stats.html',
        record=dict(created=now, values=stats))


@blueprint.route('/librarian', methods=['GET'])
@check_logged_as_librarian
def stats_librarian():
    """Show the list of the first 100 items on the librarian stats list."""
    search = StatsSearch()\
        .filter('term', type=StatType.LIBRARIAN).sort('-_created')\
        .source(['pid', '_created', 'date_range'])
    hits = search[0:100].execute().to_dict()
    return render_template(
        'rero_ils/stats_list.html', records=hits['hits']['hits'],
        type='librarian')


@blueprint.route('/librarian/<record_pid>/csv')
@check_logged_as_librarian
def stats_librarian_queries(record_pid):
    """Download specific statistic query into csv file.

    :param record_pid: statistics pid
    :return: response object, the csv file
    """
    queries = ['loans_of_transaction_library_by_item_location']
    query_id = request.args.get('query_id', None)
    if query_id not in queries:
        abort(404)

    record = Stat.get_record_by_pid(record_pid)
    if not record:
        abort(404)
    # Filter the record to keep only values about connected user
    # note : This is done by the `pre_dump` extension from `Stats` record,
    record = record.dumps()

    _from = record['date_range']['from'].split('T')[0]
    _to = record['date_range']['to'].split('T')[0]
    filename = f'{query_id}_{_from}_{_to}.csv'

    data = StringIO()
    w = csv.writer(data)

    if query_id == 'loans_of_transaction_library_by_item_location':
        fieldnames = ['Transaction library', 'Item library',
                      'Item location', 'Checkins', 'Checkouts']
        w.writerow(fieldnames)
        for result in record['values']:
            transaction_library = \
                f"{result['library']['pid']}: {result['library']['name']}"

            if not result[query_id]:
                w.writerow((transaction_library, '-', '-', 0, 0))
            else:
                for location in result[query_id]:
                    result_loc = result[query_id][location]
                    location_name = result_loc['location_name']
                    item_library =\
                        location.replace(f' - {location_name}', '')
                    w.writerow((
                        transaction_library,
                        item_library,
                        location_name,
                        result_loc['checkin'],
                        result_loc['checkout']))

    output = make_response(data.getvalue())
    output.headers["Content-Disposition"] = f'attachment; filename={filename}'
    output.headers["Content-type"] = "text/csv"
    return output


# JINJA FILTERS ===============================================================

@jinja2.pass_context
@blueprint.app_template_filter()
def yearmonthfilter(context, value, format="%Y-%m-%dT%H:%M:%S"):
    """Convert datetime in local timezone.

    value: datetime
    returns: year and month of datetime
    """
    utc = pytz.timezone('UTC')
    value = datetime.datetime.strptime(value, format)
    value = utc.localize(value, is_dst=None).astimezone(pytz.utc)
    datetime_object = datetime.datetime.strptime(str(value.month), "%m")
    month_name = datetime_object.strftime("%b")
    return f"{month_name} {value.year}"


@jinja2.pass_context
@blueprint.app_template_filter()
def stringtodatetime(context, value, format="%Y-%m-%dT%H:%M:%S"):
    """Convert string to datetime.

    value: string
    returns: datetime object
    """
    return datetime.datetime.strptime(value, format)


@jinja2.pass_context
@blueprint.app_template_filter()
def sort_dict_by_key(context, dictionary):
    """Sort dict by dict of keys.

    dictionary: dict to sort
    returns: list of tuples
    :rtype: list
    """
    return StatCSVSerializer.sort_dict_by_key(dictionary)


@jinja2.pass_context
@blueprint.app_template_filter()
def sort_dict_by_library(context, dictionary):
    """Sort dict by library name.

    dictionary: dict to sort
    returns: sorted dict
    :rtype: dict
    """
    return sorted(dictionary, key=lambda v: v['library']['name'])


@jinja2.pass_context
@blueprint.app_template_filter()
def process_data(context, value):
    """Process data.

    Create key library name and library id, delete key library.
    value: dict to process
    returns: processed dict
    :rtype: dict
    """
    if 'library' in value:
        updated_dict = {'library id': value['library']['pid'],
                        'library name': value['library']['name']}
        updated_dict.update(value)
        updated_dict.pop('library')
    return updated_dict
