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

"""Blueprint used for loading templates for all modules."""

from __future__ import absolute_import, print_function

import os
from functools import wraps

import polib
from flask import Blueprint, abort, current_app, jsonify
from flask_babelex import get_domain
from flask_login import current_user

from .patrons.api import Patron
from .permissions import record_permissions
from ..accounts_views import LoginView
from ..permissions import librarian_permission

api_blueprint = Blueprint(
    'api_blueprint',
    __name__,
    url_prefix=''
)


def check_authentication(func):
    """Decorator to check authentication for permissions HTTP API."""
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'status': 'error: Unauthorized'}), 401
        if not librarian_permission.require().can():
            return jsonify({'status': 'error: Forbidden'}), 403
        return func(*args, **kwargs)

    return decorated_view


@api_blueprint.route('/permissions/<route_name>', methods=['GET'])
@api_blueprint.route('/permissions/<route_name>/<record_pid>', methods=['GET'])
@check_authentication
def permissions(route_name, record_pid=None):
    """HTTP GET request for record permissions.

    :param route_name : the list route of the resource
    :param record_pid : the record pid
    :return a JSON object with create/update/delete permissions for this
            record/resource
    """
    return record_permissions(record_pid=record_pid, route_name=route_name)


@api_blueprint.route('/translations/<ln>.json')
def translations(ln):
    """Exposes translations in JSON format.

    :param ln: language ISO 639-1 Code (two chars).
    """
    domain = get_domain()
    paths = domain.paths
    try:
        path = next(p for p in paths if p.find('rero_ils') > -1)
    except StopIteration:
        current_app.logger.error(
            'translations for {ln} does not exist'.format(ln=ln))
        abort(404)

    po_file_name = '{path}/{ln}/LC_MESSAGES/{domain}.po'.format(
        path=path, ln=ln, domain=domain.domain)
    if not os.path.isfile(po_file_name):
        abort(404)
    data = {}
    try:
        po = polib.pofile(po_file_name)
    except Exception:
        current_app.logger.error(
            'unable to open po file: {po}'.format(po=po_file_name))
        abort(404)
    for entry in po:
        data[entry.msgid] = entry.msgstr or entry.msgid
    return jsonify(data)


@api_blueprint.route('/user_info/<email_or_username>')
@check_authentication
def user_info(email_or_username):
    """Get user info for the professionnal view."""
    user = LoginView.get_user(email_or_username)
    if not user:
        return jsonify({})
    patron = Patron.get_patron_by_user(user)
    if patron:
        # TODO: after the multiple org support return this only if the patron
        # is not used in the current organisation
        return jsonify({})
    data = {
        'id': user.id,
    }
    if user.email:
        data['email'] = user.email
    profile_attrs = ['username', 'first_name', 'last_name', 'city']
    if user.profile:
        for attr in profile_attrs:
            attr_value = getattr(user.profile, attr)
            if attr_value:
                data[attr] = attr_value
    return jsonify(data)
