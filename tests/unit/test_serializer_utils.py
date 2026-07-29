# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests serializer utilities."""

from pathlib import Path
from types import SimpleNamespace
from xml.etree import ElementTree

import pytest
from babel import Locale
from flask import Flask
from jinja2 import FileSystemLoader

import rero_ils
from rero_ils.modules.serializers.utils import excel_xml_converter
from tests.utils import parse_excel_xml


def _create_app(locale="en"):
    """Create a minimal application with an active export locale."""
    app = Flask(__name__)
    template_path = Path(rero_ils.__file__).parent / "theme" / "templates"
    app.jinja_loader = FileSystemLoader(template_path)
    app.extensions["invenio-i18n"] = SimpleNamespace(locale=Locale.parse(locale))
    return app


@pytest.mark.parametrize(
    ("template_name", "csv_data", "expected_types", "locale"),
    [
        (
            "loans.xml",
            '"pid","checkout_date","item_barcode"\r\n"12","2026-07-29","000123"\r\n',
            ["Number", "DateTime", "String"],
            "en",
        ),
        (
            "fees.xml",
            (
                '"amount","transaction_date","document_pid"\r\n'
                '"1\u202f234,50","2026-07-29T14:30:45.123456+02:00","42"\r\n'
            ),
            ["Number", "DateTime", "Number"],
            "fr_CH",
        ),
        (
            "acquisition_accounts.xml",
            ('"account_pid","account_allocated_amount","account_number"\r\n"12","1500.50","000123"\r\n'),
            ["Number", "Number", "String"],
            "en",
        ),
        (
            "acquisition_orders.xml",
            ('"order_pid","order_date","ordered_quantity","account_number"\r\n"12","2026-07-29","3","000123"\r\n'),
            ["Number", "DateTime", "Number", "String"],
            "en",
        ),
        (
            "statistics.xml",
            '"label","dynamic total","library id"\r\n"Total","12","lib1"\r\n',
            ["String", "Number", "String"],
            "en",
        ),
        (
            "librarian_query.xml",
            '"Transaction library","Checkins","Checkouts"\r\n"Library","2","3"\r\n',
            ["String", "Number", "Number"],
            "en",
        ),
    ],
)
def test_excel_xml_template_column_types(template_name, csv_data, expected_types, locale):
    """Test the column types configured by each export template."""
    app = _create_app(locale)
    converter = excel_xml_converter(
        f"rero_ils/exports/{template_name}",
        worksheet_name="Test",
    )

    with app.test_request_context():
        xml = "".join(converter(iter(csv_data.splitlines(keepends=True))))

    namespace = "{urn:schemas-microsoft-com:office:spreadsheet}"
    workbook = ElementTree.fromstring(xml)
    data_cells = workbook.findall(f".//{namespace}Row")[1].findall(f"{namespace}Cell")
    assert [cell.find(f"{namespace}Data").get(f"{namespace}Type") for cell in data_cells] == expected_types


def test_excel_xml_converter_streams_csv_rows():
    """Test that Excel XML conversion does not consume all CSV rows upfront."""
    app = _create_app()
    consumed = []

    def csv_rows():
        consumed.append("header")
        yield (
            '"document_pid","item_pid","item_holding_pid","item_price","item_acquisition_date",'
            '"issue_regular","item_barcode","document_publication_year",'
            '"document_title"\r\n'
        )
        consumed.append("data")
        yield '"123","456","789","23.2","2026-07-29","True","000123","2020 - 2022","R&D <test>"\r\n'
        consumed.append("non-numeric-pids")
        yield '"doc1","item1","holding1","","","","","",""\r\n'

    converter = excel_xml_converter(
        "rero_ils/exports/inventory.xml",
        worksheet_name="Test",
    )

    with app.test_request_context():
        content = converter(csv_rows())
        assert consumed == ["header"]
        xml = "".join(content)

    assert consumed == ["header", "data", "non-numeric-pids"]
    namespace = "{urn:schemas-microsoft-com:office:spreadsheet}"
    excel_namespace = "{urn:schemas-microsoft-com:office:excel}"
    workbook = ElementTree.fromstring(xml)
    parsed_rows = parse_excel_xml(xml)
    columns = workbook.findall(f".//{namespace}Worksheet/{namespace}Table/{namespace}Column")
    assert len(columns) == 9
    assert all(column.get(f"{namespace}AutoFitWidth") == "0" for column in columns)
    assert [int(column.get(f"{namespace}Width")) for column in columns] == [
        len(header) * 6 + 12 for header in parsed_rows[0]
    ]
    data_cells = workbook.findall(f".//{namespace}Row")[1].findall(f"{namespace}Cell")
    assert [cell.find(f"{namespace}Data").get(f"{namespace}Type") for cell in data_cells] == [
        "Number",
        "Number",
        "Number",
        "Number",
        "DateTime",
        "Boolean",
        "String",
        "String",
        "String",
    ]
    fallback_cells = workbook.findall(f".//{namespace}Row")[2].findall(f"{namespace}Cell")
    assert [cell.find(f"{namespace}Data").get(f"{namespace}Type") for cell in fallback_cells[:3]] == [
        "String",
        "String",
        "String",
    ]
    worksheet_options = workbook.find(f".//{excel_namespace}WorksheetOptions")
    assert worksheet_options.find(f"{excel_namespace}FreezePanes") is not None
    assert worksheet_options.findtext(f"{excel_namespace}SplitHorizontal") == "1"
    assert worksheet_options.findtext(f"{excel_namespace}TopRowBottomPane") == "1"
    auto_filter = workbook.find(f".//{excel_namespace}AutoFilter")
    assert auto_filter.get(f"{excel_namespace}Range") == "R1C1:R3C9"
    assert parsed_rows == [
        [
            "document_pid",
            "item_pid",
            "item_holding_pid",
            "item_price",
            "item_acquisition_date",
            "issue_regular",
            "item_barcode",
            "document_publication_year",
            "document_title",
        ],
        [
            "123",
            "456",
            "789",
            "23.2",
            "2026-07-29T00:00:00.000",
            "1",
            "000123",
            "2020 - 2022",
            "R&D <test>",
        ],
        ["doc1", "item1", "holding1", "", "", "", "", "", ""],
    ]


@pytest.mark.parametrize(
    ("locale", "value", "expected_type", "expected_value"),
    [
        ("en", "1,234", "Number", "1234"),
        ("fr_CH", "1\u202f234,50", "Number", "1234.50"),
        ("de", "1.234,50", "Number", "1234.50"),
        ("de_CH", "1\u2019234.50", "Number", "1234.50"),
        ("en", "invalid", "String", "invalid"),
    ],
)
def test_excel_xml_number_uses_export_locale(locale, value, expected_type, expected_value):
    """Test that localized numbers use the active export locale."""
    app = _create_app(locale)
    converter = excel_xml_converter(
        "rero_ils/exports/fees.xml",
        worksheet_name="Test",
    )

    with app.test_request_context():
        csv_data = f'"amount"\r\n"{value}"\r\n'
        xml = "".join(converter(iter(csv_data.splitlines(keepends=True))))

    namespace = "{urn:schemas-microsoft-com:office:spreadsheet}"
    workbook = ElementTree.fromstring(xml)
    data = workbook.findall(f".//{namespace}Row")[1].find(f"{namespace}Cell/{namespace}Data")
    assert data.get(f"{namespace}Type") == expected_type
    assert data.text == expected_value
