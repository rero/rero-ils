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

import glob
import json
import os
import re

import dateparser
from babel.dates import format_date, format_datetime, format_time
from flask import current_app
from invenio_i18n.ext import current_i18n
from markupsafe import Markup


def node_assets(package, patterns=[
        'runtime*.js', 'polyfills*.js', 'main*.js'], _type='js', tags=''):
    """Generate the node assets html code.

    :param package: The node package path relative to node_modules.
    :param patters: list of glob bash like partterns.
    "param _type: string one of ['js', 'css'].
    "param tags: additional script, link, html tags such as 'defer', etc.
    "return" html link, script code
    """
    package_path = os.path.join(
        current_app.static_folder, 'node_modules', package)

    def to_html(value):
        value = re.sub(r'(.*?)\/static', '/static', value)
        # default: js
        html_code = '<script {tags} src="{value}"></script>'
        # styles
        if _type == 'css':
            html_code = '<link {tags} href="{value}" rel="stylesheet">'
        return html_code.format(
                value=value,
                tags=tags
            )
    output_files = []
    for pattern in patterns:
        files = glob.glob(os.path.join(package_path, pattern))
        output_files.extend([to_html(v) for v in files])

    class HTMLSafe:
        def __html__():
            return Markup('\n'.join(output_files))
    return HTMLSafe


def format_date_filter(
    date_str, date_format='full', time_format='medium',
    locale=None, delimiter=', ', timezone=None,
    timezone_default='utc'
):
    """Format the date to the given locale.

    :param date_str: The date and time string
    :param date_format: The date format, ex: 'full', 'medium', 'short'
                        or custom
    :param time_format: The time format, ex: 'medium', 'short' or custom
    :param locale: The locale to fix the language format
    :param delimiter: The date/time Separator Characters
    :param timezone: The timezone to fix the date and time offset
                     ex: 'Europe/Zurich'
    :param timezone_default: The default timezone
    :return: Return the formatted date and/or time
    """
    date = None
    time = None
    # TODO: Using the library or organisation timezone in the future
    if not locale:
        locale = current_i18n.locale.language

    if timezone:
        tzinfo = timezone
    else:
        tzinfo = current_app.config.get(
            'BABEL_DEFAULT_TIMEZONE', timezone_default)

    datetimetz = format_datetime(dateparser.parse(
        date_str, locales=['en']), tzinfo=tzinfo, locale='en')

    if date_format:
        date = format_date(
            dateparser.parse(datetimetz), format=date_format, locale=locale)
    if time_format:
        time = format_time(
            dateparser.parse(datetimetz), format=time_format, locale=locale)
    return delimiter.join(filter(None, [date, time]))


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


def empty_data(data, replacement_string='No data'):
    """Return default string if no data."""
    if data:
        return data
    else:
        msg = '<em class="no-data">{0}</em>'.format(replacement_string)
        return Markup(msg)
