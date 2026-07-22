# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests serializer utilities."""

from io import BytesIO
from zipfile import ZipFile

from flask import Flask

from rero_ils.modules.serializers import utils as serializer_utils
from rero_ils.modules.serializers.response import search_responsify_file
from rero_ils.modules.serializers.utils import csv_to_xlsx
from tests.utils import assert_xlsx_response, parse_xlsx


def _assert_xlsx_autofilter(xlsx, worksheet_index, cell_range):
    """Assert the AutoFilter range of an XLSX worksheet."""
    with ZipFile(BytesIO(xlsx)) as workbook:
        worksheet = workbook.read(f"xl/worksheets/sheet{worksheet_index + 1}.xml")
    assert f'<autoFilter ref="{cell_range}"/>'.encode() in worksheet


def _assert_xlsx_frozen_header(xlsx, worksheet_index):
    """Assert that an XLSX worksheet has a frozen header row."""
    with ZipFile(BytesIO(xlsx)) as workbook:
        worksheet = workbook.read(f"xl/worksheets/sheet{worksheet_index + 1}.xml")
    assert b'ySplit="1"' in worksheet
    assert b'state="frozen"' in worksheet


def test_csv_to_xlsx():
    """Test conversion of CSV content to an XLSX workbook."""
    content = iter(['"first","second"\r\n', '"one","=literal"\r\n'])

    xlsx = csv_to_xlsx(content)
    rows = parse_xlsx(xlsx)

    assert rows == [["first", "second"], ["one", "=literal"]]
    _assert_xlsx_autofilter(xlsx, 0, "A1:B2")
    _assert_xlsx_frozen_header(xlsx, 0)


def test_csv_to_xlsx_multiple_worksheets(monkeypatch):
    """Test that oversized CSV content is partitioned without data loss."""
    monkeypatch.setattr(serializer_utils, "XLSX_MAX_ROWS", 3)
    content = iter(['"header"\r\n', '"one"\r\n', '"two"\r\n', '"three"\r\n'])

    xlsx = csv_to_xlsx(content)

    assert parse_xlsx(xlsx) == [["header"], ["one"], ["two"]]
    assert parse_xlsx(xlsx, worksheet_index=1) == [["header"], ["three"]]
    _assert_xlsx_autofilter(xlsx, 0, "A1:A3")
    _assert_xlsx_autofilter(xlsx, 1, "A1:A2")
    _assert_xlsx_frozen_header(xlsx, 0)
    _assert_xlsx_frozen_header(xlsx, 1)


def test_csv_to_xlsx_multiple_column_worksheets(monkeypatch):
    """Test that oversized CSV rows are partitioned without data loss."""
    monkeypatch.setattr(serializer_utils, "XLSX_MAX_COLUMNS", 2)
    content = iter(['"first","second","third"\r\n', '"one","two","three"\r\n'])

    xlsx = csv_to_xlsx(content)

    assert parse_xlsx(xlsx) == [["first", "second"], ["one", "two"]]
    assert parse_xlsx(xlsx, worksheet_index=1) == [["third"], ["three"]]
    _assert_xlsx_autofilter(xlsx, 0, "A1:B2")
    _assert_xlsx_autofilter(xlsx, 1, "A1:A2")


def test_search_responsify_file_with_converter():
    """Test converting output from an existing search serializer."""

    class CSVSerializer:
        def serialize_search(self, *args, **kwargs):
            return iter(['"first","second"\r\n', '"one","two"\r\n'])

    view = search_responsify_file(
        CSVSerializer(),
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "xlsx",
        file_prefix="export",
        content_converter=csv_to_xlsx,
    )

    app = Flask(__name__)
    with app.app_context():
        response = view(None, None)

    assert assert_xlsx_response(response) == [["first", "second"], ["one", "two"]]
