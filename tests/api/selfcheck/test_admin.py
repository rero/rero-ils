# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
# Copyright (C) 2021 UCLouvain
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

"""Tests Selfcheck admin."""

from __future__ import absolute_import, print_function

from flask import url_for
from flask_admin import Admin
from invenio_db import db

from rero_ils.modules.selfcheck.admin import selfcheck_terminal_adminview


def test_admin_view(app):
    """Test flask-admin interface."""
    assert isinstance(selfcheck_terminal_adminview, dict)

    assert 'model' in selfcheck_terminal_adminview
    assert 'modelview' in selfcheck_terminal_adminview

    admin = Admin(app, name="Test")

    selfcheck_user_adminview_copy = dict(selfcheck_terminal_adminview)
    selfcheck_user_model = selfcheck_user_adminview_copy.pop('model')
    selfcheck_user_view = selfcheck_user_adminview_copy.pop('modelview')
    admin.add_view(selfcheck_user_view(selfcheck_user_model, db.session,
                                       **selfcheck_user_adminview_copy))

    with app.test_request_context():
        request_url = url_for('selfcheckterminal.index_view')

    with app.app_context():
        with app.test_client() as client:
            res = client.get(
                request_url,
                follow_redirects=True
            )
            assert res.status_code == 200
            assert b'Name' in (res.get_data())
            assert b'Access Token' in (res.get_data())
            assert b'Organisation Pid' in (res.get_data())
            assert b'Library Pid' in (res.get_data())
            assert b'Location Pid' in (res.get_data())


def test_admin_createuser(app, client, loc_public_martigny):
    """Test flask-admin user creation."""

    create_view_url = url_for('selfcheckterminal.create_view')

    # test required values
    babel = app.extensions.get('babel')
    print('>>>>>', babel, type(babel))
    res = client.post(
        create_view_url,
        data={},
        follow_redirects=True
    )
    assert b'This field is required.' in res.data
    assert res.data.count(b'This field is required.') == 3

    # test create selfcheck user
    res = client.post(
        create_view_url,
        data={
            'name': 'test_user',
            'access_token': 'TESTACCESSTOKEN',
            'location_pid': 'loc1',
        },
        follow_redirects=True
    )
    assert b'Record was successfully created.' in res.data

    # test create selfcheck user whith same username
    res = client.post(
        create_view_url,
        data={
            'name': 'test_user',
            'access_token': 'TESTACCESSTOKEN',
            'location_pid': 'loc1',
        },
        follow_redirects=True
    )
    assert b'Already exists.' in res.data
