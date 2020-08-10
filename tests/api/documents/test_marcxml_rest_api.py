# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""Tests POST REST API for MARC21 documents."""


import mock
from utils import VerifyRecordPermissionPatch, postdata


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_marcxml_documents_create(
        client, document_marcxml, documents_marcxml, rero_marcxml_header):
    """Test post of marcxml document."""
    res, data = postdata(
        client,
        'invenio_records_rest.doc_list',
        document_marcxml,
        headers=rero_marcxml_header,
        force_data_as_json=False
    )
    assert res.status_code == 201
    assert data['metadata']['_draft']

    #  test fails when multiple xml records are sent.
    res, data = postdata(
        client,
        'invenio_records_rest.doc_list',
        documents_marcxml,
        headers=rero_marcxml_header,
        force_data_as_json=False
    )
    assert res.status_code == 400
