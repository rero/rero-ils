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


from flask import url_for
from invenio_access.models import ActionUsers
from invenio_access.permissions import superuser_access
from invenio_accounts.testutils import login_user_via_session
from invenio_db import db
from utils import flush_index, get_json

from rero_ils.modules.persons.api import Person, PersonsSearch


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
            'doc': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'documents'},
            'hold': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'holdings'},
            'illr': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'ill_requests'}
            'item': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'items'},
            'itty': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'item_types'},
            'lib': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'libraries'},
            'loanid': {'db': 0},
            'loc': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'locations'},
            'notif': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'notifications'},
            'org': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'organisations'},
            'pers': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'persons'},
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


def test_monitoring_check_es_db_counts(app, client, person_data,
                                       system_librarian_martigny_no_email):
    """Test monitoring check_es_db_counts."""
    res = client.get(url_for('api_monitoring.check_es_db_counts'))
    assert res.status_code == 200
    assert get_json(res) == {'data': {'status': 'green'}}

    pers = Person.create(
        data=person_data,
        delete_pid=False,
        dbcommit=True,
        reindex=False)
    flush_index(PersonsSearch.Meta.index)
    res = client.get(url_for('api_monitoring.check_es_db_counts'))
    assert res.status_code == 200
    assert get_json(res) == {
        'data': {'status': 'red'},
        'errors': [{
            'code': 'DB_ES_COUNTER_MISSMATCH',
            'details': 'There are 1 items from pers missing in ES.',
            'id': 'DB_ES_COUNTER_MISSMATCH',
            'links': {
                'about': 'http://localhost/monitoring/check_es_db_counts',
                'pers': 'http://localhost/monitoring/missing_pids/pers'
            },
            'title': "DB items counts don't match ES items count."
        }]
    }

    # this view is only accessible by admin
    res = client.get(url_for('api_monitoring.missing_pids', doc_type='pers'))
    assert res.status_code == 401

    login_user_via_session(client, system_librarian_martigny_no_email.user)
    res = client.get(
        url_for('api_monitoring.missing_pids', doc_type='pers')
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
        url_for('api_monitoring.missing_pids', doc_type='pers')
    )
    assert res.status_code == 200

    assert get_json(res) == {
        'data': {
            'DB': [],
            'ES': ['http://localhost/persons/pers1'],
            'ES duplicate': []
        }
    }
