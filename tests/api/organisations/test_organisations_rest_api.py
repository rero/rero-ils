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

"""Tests REST API organisations."""

import json

import pytest
from flask import url_for
from utils import login_user, postdata

from rero_ils.modules.organisations.api import Organisation


def test_get_record_by_viewcode(org_martigny):
    """Test Organisation.get_record_by_viewcode."""
    data = Organisation.get_record_by_viewcode('org1')
    assert data['pid'] == org_martigny.pid
    with pytest.raises(Exception):
        assert Organisation.get_record_by_viewcode('dummy')


def test_get_record_by_online_harvested_source(org_martigny):
    """Test get_record_by_online_harvested_source."""
    source = org_martigny.get('online_harvested_source')[0]
    org = Organisation.get_record_by_online_harvested_source(source)
    assert org.pid == org_martigny.pid
    assert Organisation.get_record_by_online_harvested_source('dummy') is None


def test_organisation_secure_api_update(client, json_header, org_martigny,
                                        librarian_martigny,
                                        system_librarian_martigny,
                                        librarian_sion,
                                        org_martigny_data):
    """Test organisation secure api create."""
    login_user(client, system_librarian_martigny)
    record_url = url_for('invenio_records_rest.org_item',
                         pid_value=org_martigny.pid)

    data = org_martigny_data
    data['name'] = 'New Name 1'
    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200

    list_url = url_for('invenio_records_rest.org_list')
    client.get(list_url)
    assert res.status_code == 200

    login_user(client, librarian_martigny)
    data['name'] = 'New Name 2'
    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 403

    # Sion
    login_user(client, librarian_sion)

    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 403


def test_organisation_can_delete(client, org_martigny, lib_martigny,
                                 acq_receipt_fiction_martigny):
    """Test can delete an organisation."""
    can, reasons = org_martigny.can_delete
    assert not can
    assert reasons['links']['libraries']
    assert reasons['links']['acq_receipts']


def test_organisation_secure_api(client, json_header, org_martigny,
                                 librarian_martigny,
                                 librarian_sion):
    """Test organisation secure api access."""
    # Martigny
    login_user(client, librarian_martigny)
    record_url = url_for('invenio_records_rest.org_item',
                         pid_value=org_martigny.pid)

    res = client.get(record_url)
    assert res.status_code == 200

    # Sion
    login_user(client, librarian_sion)
    record_url = url_for('invenio_records_rest.org_item',
                         pid_value=org_martigny.pid)


def test_organisation_secure_api_create(client, json_header, org_martigny,
                                        librarian_martigny,
                                        librarian_sion,
                                        org_martigny_data):
    """Test organisation secure api create."""
    # Martigny
    login_user(client, librarian_martigny)
    post_entrypoint = 'invenio_records_rest.org_list'

    del org_martigny_data['pid']
    res, _ = postdata(
        client,
        post_entrypoint,
        org_martigny_data
    )
    assert res.status_code == 403

    # Sion
    login_user(client, librarian_sion)

    res, _ = postdata(
        client,
        post_entrypoint,
        org_martigny_data
    )
    assert res.status_code == 403


def test_organisation_secure_api_delete(client, json_header, org_martigny,
                                        librarian_martigny,
                                        librarian_sion,
                                        org_martigny_data):
    """Test organisation secure api delete."""
    login_user(client, librarian_martigny)
    record_url = url_for('invenio_records_rest.org_item',
                         pid_value=org_martigny.pid)

    res = client.delete(record_url)
    assert res.status_code == 403

    # Sion
    login_user(client, librarian_sion)

    res = client.delete(record_url)
    assert res.status_code == 403
