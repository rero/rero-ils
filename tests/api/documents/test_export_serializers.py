# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
# Copyright (C) 2022 UCLouvain
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

"""Tests Serializers."""

from flask import url_for


def test_ris_formatter(client, ris_header, document, export_document):
    """Test RIS formatter"""
    ris_tag = [
        'TY -', 'ID -', 'TI -', 'T2 -', 'AU -', 'A2 -', 'DA -', 'SP -', 'EP -',
        'CY -', 'LA -', 'PB -', 'SN -', 'UR -', 'KW -', 'ET -', 'DO -', 'VL -',
        'IS -', 'PP -', 'Y1 -', 'PY -', 'ER -'
    ]
    list_url = url_for('invenio_records_rest.doc_list',
                       q='pid:doc8')
    response = client.get(list_url, headers=ris_header)
    assert response.status_code == 200
    ris_data = response.get_data(as_text=True)
    assert all(tag in ris_data for tag in ris_tag)
