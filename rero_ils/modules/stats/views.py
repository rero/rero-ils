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

import datetime

import arrow
import jinja2
import pytz
from elasticsearch_dsl import Q
from flask import Blueprint, render_template

from .api import StatsForPricing, StatsSearch
from .permissions import check_logged_as_admin, check_logged_as_librarian

# from pytz import timezone

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
    f = ~Q('exists', field='type') | Q('term', type='billing')
    search = StatsSearch().filter('bool', must=[f]).sort('-_created')\
        .source(['pid', '_created'])
    hits = search[0:100].execute().to_dict()
    return render_template(
        'rero_ils/stats_list.html', records=hits['hits']['hits'],
        type='billing')


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
    search = StatsSearch().filter('term', type='librarian').sort('-_created')\
        .source(['pid', '_created', 'date_range'])
    hits = search[0:100].execute().to_dict()
    return render_template(
        'rero_ils/stats_list.html', records=hits['hits']['hits'],
        type='librarian')


@jinja2.contextfilter
@blueprint.app_template_filter()
def yearmonthfilter(context, value, format="%Y-%m-%dT%H:%M:%S"):
    """Convert datetime in local timezone.

    value: datetime
    returns: year and month of datetime
    """
    tz = pytz.timezone('Europe/Zurich')
    utc = pytz.timezone('UTC')
    value = datetime.datetime.strptime(value, format)
    value = utc.localize(value, is_dst=None).astimezone(pytz.utc)
    datetime_object = datetime.datetime.strptime(str(value.month), "%m")
    month_name = datetime_object.strftime("%b")
    return "{} {}".format(month_name, value.year)


@jinja2.contextfilter
@blueprint.app_template_filter()
def stringtodatetime(context, value, format="%Y-%m-%dT%H:%M:%S"):
    """Convert string to datetime.

    value: string
    returns: datetime object
    """
    datetime_object = datetime.datetime.strptime(value, format)
    return datetime_object
