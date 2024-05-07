# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
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

"""Tests REST API documents."""

from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json

from rero_ils.modules.utils import get_ref_for_pid


def test_document_files(
    client,
    document_with_files,
    document_with_issn,
    org_martigny,
    json_header,
    librarian_martigny,
):
    """Test document files."""

    list_url = url_for(
        "invenio_records_rest.doc_list",
        q=f"_exists_:files",
    )
    res = client.get(list_url)
    hits = get_json(res)["hits"]
    aggregations = get_json(res)["aggregations"]["organisation"]
    assert aggregations['buckets'][0]['doc_count'] == 1
    assert hits["total"]["value"] == 1

    # check for collections
    list_url = url_for(
        "invenio_records_rest.doc_list",
        q=f"_exists_:files.collections",
    )
    res = client.get(list_url)
    hits = get_json(res)["hits"]
    assert hits["total"]["value"] == 1

    # check for collections
    list_url = url_for(
        "invenio_records_rest.doc_list",
        q=f"_exists_:files",
        view=org_martigny.pid
    )
    res = client.get(list_url)
    hits = get_json(res)["hits"]
    assert hits["total"]["value"] == 1
    file_data = hits["hits"][0]["metadata"]["files"][0]
    assert file_data["collections"]

    login_user_via_session(client, librarian_martigny.user)
    # Update file metadata
    res = client.put(
        f"/records/{file_data['rec_id']}",
        headers=json_header,
        json={
            "metadata": {
                "collections": ["new col"],
                "library": {'$ref': get_ref_for_pid('lib', 'lib1')},
                "document": {'$ref': get_ref_for_pid('doc', 'doc1')},
            }
        },
    )
    assert res.status_code == 200
    res = client.get(f"/records/{file_data['rec_id']}", headers=json_header)
    assert res.status_code == 200
    assert res.json['metadata'] == {
        'collections': ['new col'],
        'document': {'$ref': 'https://bib.rero.ch/api/documents/doc1'},
        'library': {'$ref': 'https://bib.rero.ch/api/libraries/lib1'}
    }

    res = client.get(f"/records?q={file_data['rec_id']}", headers=json_header)
    assert res.status_code == 200
    metadata = res.json['hits']['hits'][0]['metadata']
    assert set(metadata.keys()) == {
        'collections', 'document', 'file_size', 'library', 'n_files'
    }
    assert metadata['library'] == {'pid': 'lib1', 'type': 'lib'}
    assert metadata['document'] == {'pid': 'doc1', 'type': 'doc'}

    # check for modifications in document
    res = client.get(list_url)
    hits = get_json(res)["hits"]
    assert hits["total"]["value"] == 1
    file_data = hits["hits"][0]["metadata"]["files"][0]
    assert file_data["collections"] == ["new col"]
