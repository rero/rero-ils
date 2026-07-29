# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Serializer utilities."""

import csv
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from functools import partial

from babel.numbers import get_decimal_symbol, get_group_symbol
from flask import current_app, stream_with_context
from invenio_i18n.ext import current_i18n


def _excel_number(value, decimal_separator, thousands_separator):
    """Return a SpreadsheetML-compatible number or ``None``."""
    number = str(value).strip()
    number = number.replace("\u202f", "").replace("\xa0", "").replace(" ", "")
    number = number.replace("\u2019", "").replace("'", "")
    if "," in number:
        if "." in number:
            if number.rfind(",") > number.rfind("."):
                number = number.replace(".", "").replace(",", ".")
            else:
                number = number.replace(",", "")
        elif decimal_separator == ",":
            number = number.replace(",", ".")
        elif thousands_separator == ",":
            number = number.replace(",", "")
    try:
        Decimal(number)
    except InvalidOperation:
        return None
    return number


def _excel_datetime(value):
    """Return a SpreadsheetML-compatible date or ``None``."""
    value = str(value).strip()
    try:
        parsed = date.fromisoformat(value) if "T" not in value else datetime.fromisoformat(value)
    except ValueError:
        return None
    if isinstance(parsed, datetime):
        return parsed.replace(tzinfo=None).isoformat(timespec="milliseconds")
    return f"{parsed.isoformat()}T00:00:00.000"


def csv_to_excel_xml(
    csv_rows,
    template_name,
    worksheet_name="Export",
):
    """Stream serialized CSV rows through an Excel XML template."""
    rows = iter(csv.reader(csv_rows))
    header = next(rows, [])
    template = current_app.jinja_env.get_template(template_name)
    locale = current_i18n.locale
    return stream_with_context(
        template.generate(
            header=header,
            data_generator=rows,
            worksheet_name=worksheet_name,
            excel_datetime=_excel_datetime,
            excel_number=partial(
                _excel_number,
                decimal_separator=get_decimal_symbol(locale),
                thousands_separator=get_group_symbol(locale),
            ),
        )
    )


def excel_xml_converter(template_name, worksheet_name="Export"):
    """Create a CSV-to-Excel-XML converter for a template."""
    return partial(
        csv_to_excel_xml,
        template_name=template_name,
        worksheet_name=worksheet_name,
    )
