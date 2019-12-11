# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""Jinja filters."""

import json
import re

import babel
import dateparser


def format_date_filter(date_str, format='medium', locale='en'):
    """Format the date to the given locale."""
    form_date = dateparser.parse(str(date_str), locales=[locale, 'en'])
    if format == 'full':
        format = "EEEE, d. MMMM y"
    elif format == 'medium':
        format = "EE dd.MM.y"
    elif format == 'medium_date':
        format = "dd MMMM y"
    elif format == 'short_date':
        format = "dd.MM.y"
    elif format == 'timestamp':
        format = "dd.MM.y HH:mm"
    elif format == 'day_month':
        format = "dd.MM"
    return babel.dates.format_datetime(form_date, format, locale=locale)


def to_pretty_json(value):
    """Pretty json format."""
    return json.dumps(
        value,
        sort_keys=True,
        indent=4,
        separators=(',', ': '),
        ensure_ascii=False,
    )


def jsondumps(data):
    """Override the default tojson filter to avoid escape simple quote."""
    return json.dumps(data, indent=4)


def text_to_id(text):
    """Text to id."""
    return re.sub(r'\W', '', text)
