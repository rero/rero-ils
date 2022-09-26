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

"""Tests UI view for documents."""


from flask import url_for


def test_documents_detailed_view(client, loc_public_martigny, document):
    """Test document detailed view."""
    # check redirection
    res = client.get(url_for(
        'invenio_records_ui.doc', viewcode='global', pid_value='doc1'))
    assert res.status_code == 200


def tests_document_item_filter_detailed_view(
        client, loc_public_martigny, document):
    """Test document detailed view with items filter."""
    res = client.get(url_for(
        'invenio_records_ui.doc', viewcode='org1', pid_value='doc1'))
    assert res.status_code == 200


def tests_document_export_formats(client, document):
    """Test document export view format."""
    for format in ['raw', 'ris']:
        url = url_for(
            'invenio_records_ui.doc_export',
            viewcode='global',
            pid_value=document.pid,
            format=format)
        res = client.get(url)
        assert res.status_code == 200
