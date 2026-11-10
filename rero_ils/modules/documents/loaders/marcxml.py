# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Document loaders."""

from io import BytesIO

from dojson.contrib.marc21.utils import create_record, split_stream
from flask import abort, current_app, request

from rero_ils.modules.documents.dojson.contrib.marc21tojson.rero import marc21


def marcxml_marshmallow_loader():
    """Convert the MARCXML record of the request body into a draft document.

    Aborts with HTTP 400 when the body holds no record, several records, or a record that cannot be converted.

    Example:
        POST request with MARCXML body::

            <?xml version="1.0" encoding="UTF-8"?>
            <record xmlns="http://www.loc.gov/MARC21/slim">
                <leader>00000nam a2200000 c 4500</leader>
                <datafield tag="245" ind1="1" ind2="0">
                    <subfield code="a">Sample Title</subfield>
                </datafield>
            </record>

        Returns::

            {
                "title": [{"type": "bf:Title", "_text": "Sample Title", ...}],
                "_draft": True,
                ...
            }
    """
    # Split the XML stream into individual MARCXML records
    marcxml_records = list(split_stream(BytesIO(request.data)))
    if not marcxml_records:
        abort(400, description="No valid MARCXML record found in request data")
    if len(marcxml_records) > 1:
        abort(400, description="Multiple MARCXML records not supported; please submit one record at a time")

    # Parse MARCXML into MARC 21 dictionary structure
    marc21json_record = create_record(marcxml_records[0])

    # Transform MARC 21 to RERO ILS JSON using DoJSON rules
    json_record = marc21.do(marc21json_record)

    if not json_record:
        current_app.logger.error(
            "marcxml_marshmallow_loader: marc21.do() returned None "
            f"for record: {marc21json_record.get('001', '<no 001>')}"
        )
        abort(400, description="MARCXML record could not be converted to RERO ILS format")

    # Drafts skip validation and are excluded from searches
    json_record["_draft"] = True

    return json_record
