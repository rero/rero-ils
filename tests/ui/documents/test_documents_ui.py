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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Tests UI view for documents."""


from flask import url_for

from rero_ils.modules.documents.utils import document_items_filter


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

# TODO: add search view


def test_document_items_filter(
    org_martigny, item_lib_martigny, item2_lib_martigny, item_lib_sion_org2
):
    """Test document items filter."""
    result = document_items_filter(
        org_martigny.pid, [item_lib_martigny, item2_lib_martigny])
    assert len(result) == 2

    result = document_items_filter(
        org_martigny.pid, [item_lib_martigny, item_lib_sion_org2])
    assert len(result) == 1
