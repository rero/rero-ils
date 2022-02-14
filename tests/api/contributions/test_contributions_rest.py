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

"""Tests REST API contributions."""

# import json
# from utils import get_json, to_relative_url

from flask import url_for
from utils import get_json, postdata, to_relative_url

from rero_ils.modules.contributions.models import ContributionType


def test_contributions_permissions(client, contribution_person, json_header):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.cont_item', pid_value='cont_pers')

    res = client.get(item_url)
    assert res.status_code == 200

    res, _ = postdata(
        client,
        'invenio_records_rest.cont_list',
        {}
    )
    assert res.status_code == 401

    res = client.put(
        url_for('invenio_records_rest.cont_item', pid_value='cont_pers'),
        data={},
        headers=json_header
    )

    res = client.delete(item_url)
    assert res.status_code == 401


def test_contributions_get(client, contribution_person):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.cont_item', pid_value='cont_pers')

    res = client.get(item_url)
    assert res.status_code == 200

    assert res.headers['ETag'] == '"{}"'.format(
        contribution_person.revision_id)

    data = get_json(res)
    assert contribution_person.dumps() == data['metadata']
    assert contribution_person.dumps() == data['metadata']

    # Check metadata
    for k in ['created', 'updated', 'metadata', 'links']:
        assert k in data

    # Check self links
    res = client.get(to_relative_url(data['links']['self']))
    assert res.status_code == 200
    assert data == get_json(res)
    assert contribution_person.dumps() == data['metadata']

    list_url = url_for('invenio_records_rest.cont_list', pid='cont_pers')
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    contribution_person = contribution_person.replace_refs()
    contribution_person['organisations'] = \
        contribution_person.organisation_pids
    contribution_person['type'] = ContributionType.PERSON
    contribution_person['type'] = ContributionType.PERSON

    assert data['hits']['hits'][0]['metadata'] == \
        contribution_person.replace_refs()
