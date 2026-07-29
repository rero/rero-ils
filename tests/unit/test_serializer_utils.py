# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests serializer utilities."""

from pathlib import Path
from types import SimpleNamespace

import pytest
from babel import Locale
from flask import Flask
from jinja2 import FileSystemLoader
from rero_invenio_base.modules.export import xlsx_converter

import rero_ils
from tests.utils import inspect_xlsx


def _create_app(locale="en"):
    """Create a minimal application with an active export locale."""
    app = Flask(__name__)
    template_path = Path(rero_ils.__file__).parent / "theme" / "templates"
    app.jinja_loader = FileSystemLoader(template_path)
    app.extensions["invenio-i18n"] = SimpleNamespace(locale=Locale.parse(locale))
    return app


def _xlsx_bytes(template_name, csv_data, locale="en", worksheet_name="Test"):
    """Convert CSV text to XLSX bytes in a request context."""
    app = _create_app(locale)
    converter = xlsx_converter(
        f"rero_ils/exports/{template_name}",
        worksheet_name=worksheet_name,
    )
    with app.test_request_context():
        return b"".join(converter(iter(csv_data.splitlines(keepends=True))))


@pytest.mark.parametrize(
    ("template_name", "csv_data", "expected_types", "locale"),
    [
        (
            "loans.xml",
            '"pid","checkout_date","item_barcode"\r\n"12","2026-07-29","000123"\r\n',
            ["n", "d", "s"],
            "en",
        ),
        (
            "fees.xml",
            (
                '"amount","transaction_date","document_pid"\r\n'
                '"1\u202f234,50","2026-07-29T14:30:45.123456+02:00","42"\r\n'
            ),
            ["n", "d", "n"],
            "fr_CH",
        ),
        (
            "acquisition_accounts.xml",
            ('"account_pid","account_allocated_amount","account_number"\r\n"12","1500.50","000123"\r\n'),
            ["n", "n", "s"],
            "en",
        ),
        (
            "acquisition_orders.xml",
            ('"order_pid","order_date","ordered_quantity","account_number"\r\n"12","2026-07-29","3","000123"\r\n'),
            ["n", "d", "n", "s"],
            "en",
        ),
        (
            "statistics.xml",
            '"label","dynamic total","library id"\r\n"Total","12","lib1"\r\n',
            ["s", "n", "s"],
            "en",
        ),
        (
            "librarian_query.xml",
            '"Transaction library","Checkins","Checkouts"\r\n"Library","2","3"\r\n',
            ["s", "n", "n"],
            "en",
        ),
    ],
)
def test_xlsx_template_column_types(template_name, csv_data, expected_types, locale):
    """Test the column types configured by each export template."""
    raw_data = _xlsx_bytes(template_name, csv_data, locale)
    workbook = inspect_xlsx(raw_data)

    assert [cell["type"] for cell in workbook["rows"][1]] == expected_types


def test_statistics_report_xlsx_template_uses_raw_cells():
    """Test statistics reports do not treat their first row as headings."""
    csv_data = '"Library A","12"\r\n"Library B","8"\r\n'
    workbook = inspect_xlsx(_xlsx_bytes("statistics_report.xml", csv_data))

    assert workbook["freeze_pane"] is None
    assert workbook["auto_filter"] is None
    assert workbook["widths"] == []
    assert not any(cell["bold"] for cell in workbook["rows"][0])
    assert [[cell["value"] for cell in row] for row in workbook["rows"]] == [
        ["Library A", "12"],
        ["Library B", "8"],
    ]
