# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Document loaders."""

from io import BytesIO

from dojson.contrib.marc21.utils import create_record, split_stream
from flask import abort, current_app, request

from rero_ils.modules.documents.dojson.contrib.marc21tojson.rero import marc21


def marcxml_marshmallow_loader():
    """Load and convert MARCXML from HTTP request to RERO ILS JSON format.

    This loader processes MARCXML data from the request body and converts it
    to RERO ILS internal JSON format using DoJSON transformations. It is designed
    for single-record imports via the REST API.

    The conversion process:
        1. Extracts raw MARCXML from request.data
        2. Splits the XML stream into individual records
        3. Parses each MARCXML record into MARC 21 structure
        4. Transforms MARC 21 to RERO ILS JSON using DoJSON
        5. Marks the record as draft (_draft=True)

    The loader enforces single-record processing:
        - If multiple MARCXML records are detected, returns HTTP 400 error
        - This ensures controlled imports and proper validation

    Returns:
        dict: RERO ILS JSON document with the following structure:
            - Standard RERO ILS document fields (title, contributions, etc.)
            - _draft=True: Marks the record as a draft for review

    Raises:
        werkzeug.exceptions.BadRequest: When multiple MARCXML records are
            detected in the request data (HTTP 400).

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

    Note:
        Records imported via this loader are automatically marked as drafts
        to prevent accidental publication of unvalidated data.
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

    # Mark imported records as drafts to prevent immediate publication
    # and ensure they go through the validation workflow
    json_record["_draft"] = True

    return json_record
