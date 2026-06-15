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

from .modules.messages import Message
from .modules.utils import extracted_data_from_ref


def get_record_by_ref(ref, type="search_record"):
    """Get record by ref.

    :param ref: The json $ref. Ex: {$ref: 'xxxxx'}.
    :param type: The of record
    :return: a record
    """
    return extracted_data_from_ref(ref, data=type)


def angular_assets(package, _type="js"):
    """Generate HTML tags from an Angular application's generated index.html.

    Reads the build-tool generated index.html as the single source of truth,
    avoiding any coupling to Angular's internal output format or file naming.

    :param package: The Angular package path relative to node_modules.
    :param _type: one of 'js', 'css', 'modulepreload'.
    :return: html tags extracted from the Angular index.html
    """
    package_path = os.path.join(current_app.static_folder, "node_modules", package)
    index_path = os.path.join(package_path, "index.html")
    try:
        with open(index_path, encoding="utf-8") as f:
            content = f.read()
    except OSError as error:
        current_app.logger.warning("angular_assets: unable to read %s (%s)", index_path, error)
        content = ""

    tag_patterns = {
        "css": r'<link\b[^>]*\brel="stylesheet"[^>]*>',
        "modulepreload": r'<link\b[^>]*\brel="modulepreload"[^>]*>',
        "js": r'<script\b[^>]*\btype="module"[^>]*></script>',
    }
    static_base = f"/static/node_modules/{package}/"

    def normalize_url(tag):
        def fix(m):
            attr, url = m.group(1), m.group(2)
            if url.startswith("/static/") and "browser/" in url:
                # Correct absolute URLs whose package path may differ from the
                # installed location (e.g. wrong --deploy-url in the Angular build).
                url = static_base + url.split("browser/", 1)[1]
            elif not url.startswith(("/", "http")):
                # Relative URL: prefix with the correct static base.
                url = static_base + url
            return f'{attr}="{url}"'

        return re.sub(r'(href|src)="([^"]+)"', fix, tag)

    pattern = tag_patterns.get(_type)
    if pattern is None:
        current_app.logger.warning("angular_assets: unsupported type '%s' for package '%s'", _type, package)
        tags = []
    else:
        tags = [normalize_url(t) for t in re.findall(pattern, content)]

    class HTMLSafe:
        def __html__():
            return Markup("\n".join(tags))

    return HTMLSafe


def format_date_filter(
    date_str,
    date_format="full",
    time_format="medium",
    locale=None,
    delimiter=", ",
    timezone=None,
    timezone_default="utc",
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
    if locale == "en":
        locale += "_GB"

    tzinfo = timezone or current_app.config.get("BABEL_DEFAULT_TIMEZONE", timezone_default)

    datetimetz = format_datetime(dateparser.parse(date_str, locales=["en"]), tzinfo=tzinfo, locale="en")

    if date_format:
        date = format_date(dateparser.parse(datetimetz), format=date_format, locale=locale)
    if time_format:
        time = format_time(dateparser.parse(datetimetz), format=time_format, locale=locale)
    return delimiter.join(filter(None, [date, time]))


def to_pretty_json(value):
    """Pretty json format."""
    return json.dumps(
        value,
        sort_keys=True,
        indent=4,
        separators=(",", ": "),
        ensure_ascii=False,
    )


def jsondumps(data):
    """Override the default tojson filter to avoid escape simple quote."""
    return json.dumps(data, indent=4)


def text_to_id(text):
    """Text to id."""
    return re.sub(r"\W", "", text)


def empty_data(data, replacement_string="No data"):
    """Return default string if no data."""
    if data:
        return data
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
        tpl_file = f"rero_ils/address_block/{language}.tpl.txt"
        return render_template(tpl_file, data=metadata)
    except TemplateNotFound:
        tpl_file = "rero_ils/address_block/eng.tpl.txt"
        return render_template(tpl_file, data=metadata)


def message_filter(key):
    """Message filter.

    :param key: key of the message.
    :return: none or a json (check structure into the class Message).
    """
    return Message.get(key)


def translate(data, prefix="", separator=", "):
    """Translate data.

    :param data: the data to translate
    :param prefix: A prefix as a character string
    :param separator: A character string separator.
    :return: The translated string
    """
    if data:
        if isinstance(data, list):
            translated = [_(f"{prefix}{item}") for item in data]
            return separator.join(translated)
        if isinstance(data, str):
            return _(f"{prefix}{data}")
    return None
