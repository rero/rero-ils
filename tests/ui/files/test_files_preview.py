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


def test_file_preview(client, document_with_files):
    """Test document detailed view."""
    record_file = next(document_with_files.get_records_files())
    files = [
        f for f in record_file.files
        if f.endswith('.pdf') or f.endswith('.png')
    ]
    res = client.get(url_for(
        'invenio_records_ui.recid_preview',
        pid_value='foo',
        filename='foo.pdf'
    ))

    assert res.status_code == 404

    res = client.get(url_for(
        'invenio_records_ui.recid_preview',
        pid_value=record_file['id'],
        filename='foo.pdf'
    ))
    assert res.status_code == 404

    for fname in files:
        res = client.get(url_for(
            'invenio_records_ui.recid_preview',
            pid_value=record_file['id'],
            filename=fname
        ))
        assert res.status_code == 200
