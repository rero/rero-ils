# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
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
from flask import current_app, render_template
from flask_babel import gettext as _
from invenio_i18n.ext import current_i18n
from jinja2 import TemplateNotFound
from markupsafe import Markup

from .modules.message import Message
from .modules.utils import extracted_data_from_ref


def get_record_by_ref(ref, type='es_record'):
    """Get record by ref.

    :param ref: The json $ref. Ex: {$ref: 'xxxxx'}.
    :param type: The of record
    :return: a record
    """
    return extracted_data_from_ref(ref, data=type)


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
        html_code = f'<script {tags} src="{value}"></script>'
        # styles
        if _type == 'css':
            html_code = f'<link {tags} href="{value}" rel="stylesheet">'
        return html_code
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

    # Date formatting in GB English (DD/MM/YYYY)
    if locale == 'en':
        locale += '_GB'

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
        msg = f'<em class="no-data">{replacement_string}</em>'
        return Markup(msg)


def address_block(metadata, language=None):
    """Format an address depending of language.

    The address metadata should be structured as a dictionary using structure:
    { name: string,
      email: string (optional),
      phone: string (optional),
      address: {
        street: string,
        zip_code: string,
        city: string,
        country: string (iso 2-alpha code)
      }
    }

    :param metadata: the address metadata dict to format.
    :param language: the language to use to format the block.
    :return: the formatted address.
    """
    try:
        tpl_file = f'rero_ils/address_block/{language}.tpl.txt'
        return render_template(tpl_file, data=metadata)
    except TemplateNotFound:
        tpl_file = 'rero_ils/address_block/eng.tpl.txt'
        return render_template(tpl_file, data=metadata)


def message_filter(key):
    """Message filter.

    :param key: key of the message.
    :return: none or a json (check structure into the class Message).
    """
    return Message.get(key)


def translate(data, prefix='', separator=', '):
    """Translate data.

    :param data: the data to translate
    :param prefix: A prefix as a character string
    :param separator: A character string separator.
    :return: The translated string
    """
    if data:
        if isinstance(data, list):
            translated = [_(f'{prefix}{item}') for item in data]
            return separator.join(translated)
        elif isinstance(data, str):
            return _(f'{prefix}{data}')
