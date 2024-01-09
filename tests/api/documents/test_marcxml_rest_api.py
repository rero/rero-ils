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


from click.testing import CliRunner
from utils import login_user_via_session, postdata

from rero_ils.modules.cli.utils import token_create


def test_marcxml_documents_create(
        client, document_marcxml, documents_marcxml, rero_marcxml_header,
        librarian_martigny):
    """Test post of marcxml document for logged users."""
    res, data = postdata(
        client,
        'invenio_records_rest.doc_list',
        document_marcxml,
        headers=rero_marcxml_header,
        force_data_as_json=False
    )
    assert res.status_code == 401

    login_user_via_session(client, librarian_martigny.user)
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


def test_marcxml_documents_create_with_a_token(
        app, client, document_marcxml, rero_marcxml_header,
        librarian_martigny, script_info):
    """Test post of marcxml document with an access token."""
    runner = CliRunner()
    res = runner.invoke(
        token_create,
        ['-n', 'test', '-u', librarian_martigny.dumps().get('email'),
         '-t', 'my_token'],
        obj=script_info
    )
    access_token = res.output.strip().split('\n')[0]
    res, data = postdata(
        client,
        'invenio_records_rest.doc_list',
        document_marcxml,
        url_data={'access_token': access_token},
        headers=rero_marcxml_header,
        force_data_as_json=False
    )
    assert res.status_code == 201
    assert data['metadata']['_draft']
