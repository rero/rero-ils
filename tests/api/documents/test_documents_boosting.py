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

"""Tests boosting query for documents."""
from flask import url_for
from utils import get_json


def test_document_boosting(client, roles, ebook_1, ebook_4):
    """Test document boosting."""
    list_url = url_for("invenio_records_rest.doc_list", q="maison")
    res = client.get(list_url)

    hits = get_json(res)["hits"]
    assert hits["total"]["value"] == 2
    data = hits["hits"][0]["metadata"]
    assert data["pid"] == ebook_1.pid

    list_url = url_for(
        "invenio_records_rest.doc_list",
        q="autocomplete_title:maison AND "
        "contribution.entity.authorized_access_point_en:James",
    )
    res = client.get(list_url)
    hits = get_json(res)["hits"]
    assert hits["total"]["value"] == 1
    data = hits["hits"][0]["metadata"]
    assert data["pid"] == ebook_1.pid
