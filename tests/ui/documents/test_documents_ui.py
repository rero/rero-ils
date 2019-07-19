#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

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
