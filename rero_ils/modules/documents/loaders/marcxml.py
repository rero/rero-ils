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

"""Document loaders."""

from dojson.contrib.marc21.utils import create_record, split_stream
from flask import abort, request
from six import BytesIO

from rero_ils.modules.documents.dojson.contrib.marc21tojson.rero import marc21


def marcxml_marshmallow_loader():
    """Marshmallow loader for MARCXML requests.

    The method convert only one record, otherwise will return a bad request.
    :return: converted marc21 json record.
    """
    marcxml_records = split_stream(BytesIO(request.data))
    number_of_xml_records = 0
    json_record = {}
    for marcxml_record in marcxml_records:
        marc21json_record = create_record(marcxml_record)
        json_record = marc21.do(marc21json_record)
        # converted records are considered as draft
        json_record['_draft'] = True
        if number_of_xml_records > 0:
            abort(400)
        number_of_xml_records += 1
    return json_record
