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

"""Test REST API monitoring."""

import time

from flask import url_for
from invenio_access.models import ActionUsers
from invenio_access.permissions import superuser_access
from invenio_accounts.testutils import login_user_via_session
from invenio_db import db
from utils import flush_index, get_json

from rero_ils.modules.contributions.api import Contribution, \
    ContributionsSearch
from rero_ils.modules.utils import get_timestamp, set_timestamp


def test_monitoring_es_db_counts(client):
    """Test monitoring es_db_counts."""
    res = client.get(url_for('api_monitoring.es_db_counts'))
    assert res.status_code == 200
    assert get_json(res) == {
        'data': {
            'acac': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'acq_accounts'},
            'acin': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'acq_invoices'},
            'acol': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'acq_order_lines'},
            'acor': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'acq_orders'},
            'budg': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'budgets'},
            'cipo': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'circ_policies'},
            'coll': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'collections'},
            'cont': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'contributions'},
            'doc': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'documents'},
            'hold': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'holdings'},
            'illr': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'ill_requests'},
            'item': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'items'},
            'itty': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'item_types'},
            'lib': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'libraries'},
            'loanid': {'db': 0},
            'loc': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'locations'},
            'lofi': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'local_fields'},
            'notif': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'notifications'},
            'oplg': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'operation_logs'},
            'org': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'organisations'},
            'ptre': {'db': 0, 'db-es': 0, 'es': 0,
                     'index': 'patron_transaction_events'},
            'ptrn': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'patrons'},
            'pttr': {'db': 0, 'db-es': 0, 'es': 0,
                     'index': 'patron_transactions'},
            'ptty': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'patron_types'},
            'tmpl': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'templates'},
            'vndr': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'vendors'},
        }
    }


def test_monitoring_check_es_db_counts(app, client, contribution_person_data,
                                       system_librarian_martigny_no_email):
    """Test monitoring check_es_db_counts."""
    res = client.get(url_for('api_monitoring.check_es_db_counts'))
    assert res.status_code == 200
    assert get_json(res) == {'data': {'status': 'green'}}

    pers = Contribution.create(
        data=contribution_person_data,
        delete_pid=False,
        dbcommit=True,
        reindex=False)
    flush_index(ContributionsSearch.Meta.index)
    res = client.get(url_for('api_monitoring.check_es_db_counts'))
    assert res.status_code == 200
    assert get_json(res) == {
        'data': {'status': 'red'},
        'errors': [{
            'code': 'DB_ES_COUNTER_MISSMATCH',
            'details': 'There are 1 items from cont missing in ES.',
            'id': 'DB_ES_COUNTER_MISSMATCH',
            'links': {
                'about': 'http://localhost/monitoring/check_es_db_counts',
                'cont': 'http://localhost/monitoring/missing_pids/cont'
            },
            'title': "DB items counts don't match ES items count."
        }]
    }

    # this view is only accessible by admin
    res = client.get(url_for('api_monitoring.missing_pids', doc_type='cont'))
    assert res.status_code == 401

    login_user_via_session(client, system_librarian_martigny_no_email.user)
    res = client.get(
        url_for('api_monitoring.missing_pids', doc_type='cont')
    )
    assert res.status_code == 403

    # give user superuser admin rights
    db.session.add(
        ActionUsers.allow(
            superuser_access,
            user=system_librarian_martigny_no_email.user
        )
    )
    db.session.commit()
    res = client.get(
        url_for('api_monitoring.missing_pids', doc_type='cont')
    )
    assert res.status_code == 200

    assert get_json(res) == {
        'data': {
            'DB': [],
            'ES': ['http://localhost/contributions/cont_pers'],
            'ES duplicate': []
        }
    }


def test_timestamps(app, client):
    """Test timestamps"""
    time_stamp = set_timestamp('test', msg='test msg')
    assert get_timestamp('test') == {'time': time_stamp, 'msg': 'test msg'}
    res = client.get(url_for('api_monitoring.timestamps'))
    assert res.status_code == 401

    ds = app.extensions['invenio-accounts'].datastore
    user = ds.create_user(
        email='monitoring@rero.ch',
        password='1234',
        active=True
    )
    role = ds.create_role(name='monitoring', description='Monitoring Group')
    ds.add_role_to_user(user, role)
    ds.commit()
    user = ds.get_user('monitoring@rero.ch')
    login_user_via_session(client, user)
    res = client.get(url_for('api_monitoring.timestamps'))
    assert res.status_code == 200
    assert get_json(res) == {
        'data': {
            'test': {
                'msg': 'test msg',
                'unixtime': time.mktime(time_stamp.timetuple()),
                'utctime': time_stamp.strftime("%Y-%m-%d %H:%M:%S")
            }
        }
    }
