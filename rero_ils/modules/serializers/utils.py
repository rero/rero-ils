# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Serializer utilities."""

import csv
from dataclasses import dataclass
from tempfile import TemporaryFile

import xlsxwriter

XLSX_MAX_ROWS = 1_048_576
XLSX_MAX_COLUMNS = 16_384


def _split_row(row):
    """Split a CSV row into chunks that fit in an XLSX worksheet."""
    for start in range(0, max(1, len(row)), XLSX_MAX_COLUMNS):
        yield start // XLSX_MAX_COLUMNS, row[start : start + XLSX_MAX_COLUMNS]


@dataclass
class _WorksheetState:
    """Track the data range written to a worksheet."""

    worksheet: object
    last_row: int = 0
    last_column: int = -1

    def write_row(self, row_index, row):
        """Write a row and update the worksheet data range."""
        if not 0 <= row_index < XLSX_MAX_ROWS or len(row) > XLSX_MAX_COLUMNS:
            raise ValueError("XLSX worksheet limits exceeded")
        if self.worksheet.write_row(row_index, 0, row) != 0:
            raise RuntimeError("Unable to write XLSX row")

        self.last_row = max(self.last_row, row_index)
        self.last_column = max(self.last_column, len(row) - 1)

    def add_autofilter(self):
        """Add an AutoFilter when the worksheet contains data rows."""
        if self.last_row > 0 and self.last_column >= 0:
            self.worksheet.autofilter(
                0,
                0,
                self.last_row,
                self.last_column,
            )


class _XlsxWorksheetWriter:
    """Write CSV rows across one or more XLSX worksheets."""

    def __init__(self, workbook, header):
        self.workbook = workbook
        self.header = header
        self.row_part = 0
        self.active_worksheets = {}
        self.created_worksheets = []
        self.header_worksheet_count = sum(1 for _ in _split_row(header))
        self.start_new_row_part()

    def start_new_row_part(self):
        """Start a worksheet group when the XLSX row limit is reached."""
        self.row_part += 1
        self.active_worksheets = {}
        for column_part in range(self.header_worksheet_count):
            self._get_worksheet(column_part)

    def write_row(self, row_index, row):
        """Write a CSV row across as many worksheets as necessary."""
        for column_part, values in _split_row(row):
            self._get_worksheet(column_part).write_row(row_index, values)

    def add_autofilters(self):
        """Add an AutoFilter to every worksheet containing data."""
        for worksheet in self.created_worksheets:
            worksheet.add_autofilter()

    def _get_worksheet(self, column_part):
        """Return the requested worksheet, creating it when necessary."""
        if column_part not in self.active_worksheets:
            suffix = f"-{column_part + 1}" if column_part else ""
            worksheet = self.workbook.add_worksheet(f"Export {self.row_part}{suffix}")
            worksheet.freeze_panes(1, 0)

            start = column_part * XLSX_MAX_COLUMNS
            header = self.header[start : start + XLSX_MAX_COLUMNS]
            state = _WorksheetState(worksheet)
            state.write_row(0, header)
            self.active_worksheets[column_part] = state
            self.created_worksheets.append(state)

        return self.active_worksheets[column_part]


def _write_csv_to_worksheets(workbook, csv_rows):
    """Write CSV rows across worksheets without dropping values."""
    reader = iter(csv.reader(csv_rows))
    header = next(reader, None)
    if header is None:
        workbook.add_worksheet("Export 1")
        return

    worksheets = _XlsxWorksheetWriter(workbook, header)
    row_index = 1

    for row in reader:
        if row_index == XLSX_MAX_ROWS:
            worksheets.start_new_row_part()
            row_index = 1

        worksheets.write_row(row_index, row)
        row_index += 1

    worksheets.add_autofilters()


def csv_to_xlsx(csv_rows):
    """Convert CSV content to XLSX without changing its values."""
    with TemporaryFile() as output:
        workbook = xlsxwriter.Workbook(
            output,
            {
                "constant_memory": True,
                "strings_to_formulas": False,
                "strings_to_urls": False,
            },
        )
        _write_csv_to_worksheets(workbook, csv_rows)

        workbook.close()
        output.seek(0)
        return output.read()
