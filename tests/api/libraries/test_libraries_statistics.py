# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

"""Test statistics REST-API endpoint for libraries."""
import ciso8601
from flask import url_for
from invenio_accounts.testutils import login_user_via_session

from rero_ils.modules.loans.models import LoanAction


def test_stat_document_type_repartition(
    client, document, lib_martigny, item_lib_martigny, librarian_martigny
):
    """Test document type repartition statistic endpoint."""
    login_user_via_session(client, librarian_martigny.user)
    doc_main_type = document['type'][0]['main_type']
    doc_subtype = document['type'][0]['subtype']

    # TEST#1 :: Repartition on document main type
    res = client.get(url_for(
        'api_library.document_type_repartition_statistics',
        pid_value=lib_martigny.pid
    ))
    assert res.status_code == 200
    assert res.json.get(doc_main_type) == 1

    # TEST#2 :: Repartition on document subtype
    res = client.get(url_for(
        'api_library.document_type_repartition_statistics',
        pid_value=lib_martigny.pid,
        docType=doc_main_type
    ))
    assert res.status_code == 200
    assert res.json.get(doc_subtype) == 1

    # TEST#3 :: Repartition on document main type with exclude param
    res = client.get(url_for(
        'api_library.document_type_repartition_statistics',
        pid_value=lib_martigny.pid,
        exclude=[doc_main_type]
    ))
    assert res.status_code == 200
    assert doc_main_type not in res.json


def test_stat_circulation(
    client, circulation_logs, lib_martigny, loc_public_martigny,
    loc_restricted_martigny, librarian_martigny
):
    """Test library circulation statistics endpoint."""
    login_user_via_session(client, librarian_martigny.user)

    # TEST#0 :: Test decorators
    #    - Check the URL is correct with all necessary params
    params = {'pid_value': 'dummy_lib_pid'}
    res = client.get(url_for('api_library.circulation_statistics', **params))
    assert res.status_code == 404
    params = {'pid_value': lib_martigny.pid}
    res = client.get(url_for('api_library.circulation_statistics', **params))
    assert res.status_code == 200

    # TEST#1 :: Get all circulation statistics for lib1
    params = {
        'pid_value': lib_martigny.pid,
        'from': '*'
    }
    res = client.get(url_for('api_library.circulation_statistics', **params))
    assert res.status_code == 200
    date_to_check = ciso8601 \
        .parse_datetime(circulation_logs[0]['date']) \
        .strftime('%Y-%m-%d')
    data = res.json[date_to_check]
    assert data['total'] == 3
    assert data['operations'].get(LoanAction.CHECKOUT, 0) == 1
    assert data['operations'].get(LoanAction.CHECKIN, 0) == 1
    assert data['operations'].get('extend', 0) == 1
    assert LoanAction.REQUEST not in data['operations']

    # TEST#2 :: Skip information about 'checkin'
    params = {
        'pid_value': lib_martigny.pid,
        'from': '*',
        'operation': ['checkout', 'extend']
    }
    res = client.get(url_for('api_library.circulation_statistics', **params))
    assert res.status_code == 200
    data = res.json[date_to_check]
    assert data['total'] == 2
    assert data['operations'].get(LoanAction.CHECKOUT, 0) == 1
    assert data['operations'].get(LoanAction.CHECKIN, 0) == 0
    assert data['operations'].get('extend', 0) == 1
    assert LoanAction.REQUEST not in data['operations']

    # TEST#3 :: change interval and output format
    #  * hourly interval with no output format (decorator will choose format)
    #  * hourly interval with specified format
    #  * Bad interval --> '400 - Bad request'
    #  * Fixed interval
    params = {
        'pid_value': lib_martigny.pid,
        'from': '*',
        'to': 'now-1s',
        'interval': 'hour'
    }
    res = client.get(url_for('api_library.circulation_statistics', **params))
    assert res.status_code == 200
    assert res.json['15:00']['total'] == 1
    assert res.json['15:00']['operations'][LoanAction.CHECKOUT] == 1
    assert res.json['17:00']['total'] == 1
    assert res.json['17:00']['operations']['extend'] == 1
    assert res.json['21:00']['total'] == 1
    assert res.json['21:00']['operations'][LoanAction.CHECKIN] == 1
    params = {
        'pid_value': lib_martigny.pid,
        'from': '*',
        'to': 'now-1s',
        'interval': 'hour',
        'format': 'hh'
    }
    res = client.get(url_for('api_library.circulation_statistics', **params))
    assert res.status_code == 200
    assert res.json['03']['total'] == 1
    assert res.json['03']['operations'][LoanAction.CHECKOUT] == 1
    assert res.json['05']['total'] == 1
    assert res.json['05']['operations']['extend'] == 1
    assert res.json['09']['total'] == 1
    assert res.json['09']['operations'][LoanAction.CHECKIN] == 1

    params = {
        'pid_value': lib_martigny.pid,
        'from': '*',
        'to': 'now-1s',
        'interval': 'bad_interval'
    }
    res = client.get(url_for('api_library.circulation_statistics', **params))
    assert res.status_code == 400
    assert res.json['message'] == 'Invalid interval parameter'

    params = {
        'pid_value': lib_martigny.pid,
        'from': '*',
        'to': 'now-1s',
        'interval': '2h'
    }
    res = client.get(url_for('api_library.circulation_statistics', **params))
    assert res.status_code == 200
    assert res.json['14:00']['operations'][LoanAction.CHECKOUT] == 1
    assert res.json['16:00']['operations']['extend'] == 1
    assert res.json['20:00']['operations'][LoanAction.CHECKIN] == 1


def test_stat_circulation_rate(
    client, circulation_logs, lib_martigny, loc_public_martigny,
    loc_restricted_martigny, librarian_martigny
):
    """Test library circulation rate statistics endpoint."""
    login_user_via_session(client, librarian_martigny.user)

    # TEST#1 :: Get circulation rate statistics for lib1
    params = {
        'pid_value': lib_martigny.pid,
        'from': '*',
        'interval': 60
    }
    res = client.get(
        url_for('api_library.circulation_rate_statistics', **params))
    assert res.status_code == 200
    assert res.json['15:00'][LoanAction.CHECKOUT] == 1
    assert res.json['17:00']['extend'] == 1
    assert res.json['21:00'][LoanAction.CHECKIN] == 1
