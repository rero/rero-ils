# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
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

import polib
import requests
from flask import Blueprint, abort, current_app, jsonify, make_response, \
    request

from rero_ils.modules.utils import cached, get_all_roles

from .decorators import check_authentication, check_logged_as_librarian, \
    check_permission, parse_permission_payload
from .patrons.api import Patron
from .permissions import PermissionContext, expose_action_needs_by_patron, \
    expose_action_needs_by_role, manage_role_permissions
from .permissions import permission_management as permission_management_action
from .permissions import record_permissions

api_blueprint = Blueprint(
    'api_blueprint',
    __name__,
    url_prefix=''
)


# PERMISSIONS APIS' ===========================================================

@api_blueprint.route('/permissions/<route_name>', methods=['GET'])
@api_blueprint.route('/permissions/<route_name>/<record_pid>', methods=['GET'])
@cached(timeout=10, query_string=True)
@check_authentication
def permissions(route_name, record_pid=None):
    """HTTP GET request for record permissions.

    :param route_name : the list route of the resource
    :param record_pid : the record pid
    :return a JSON object with create/update/delete permissions for this
            record/resource
    """
    return record_permissions(record_pid=record_pid, route_name=route_name)


@api_blueprint.route('/permission/management', methods=['POST', 'DELETE'])
@check_permission([permission_management_action])
@parse_permission_payload
def permission_management(context, permission, method='allow', **kwargs):
    """Manage permissions.

    This API allows to manage RERO-ILS permission to allow/disallow any action
    for a user, a role or a system_role.

    :param context: the permission context request (role, system_role, user)
    :param permission: the name of the permission to manage.
    :param method: 'allow' or 'deny' this permission.
    :param kwargs: additional argument depending on the context
      for "role" :: `role_name`: the role name allowed/disallowed.
    :return: 200+json :: if the permission has been allowed.
             204+json :: if the permission has been disallowed.
             400 :: Missing or bad arguments
    """
    # TODO :: implements other SYSTEM_ROLE and USER context
    if context != PermissionContext.BY_ROLE:
        abort(501, 'This permission context management isn\'t yet implemented')

    try:
        if context == PermissionContext.BY_ROLE:
            role_name = kwargs.get('role_name')
            manage_role_permissions(method, permission, role_name)
    except NameError as ne:
        abort(400, str(ne))
    except Exception as e:
        abort(500, str(e))

    return jsonify({
        'context': context,
        'permission': permission,
        'method': method
    } | kwargs), 204 if method == 'deny' else 200


@api_blueprint.route('/permissions/by_role', methods=['GET'])
@check_permission([permission_management_action])
def permissions_by_role():
    """Expose permissions by roles.

    You could choose to filter the result to some roles using the `role`
    query string argument (repetitive).

    ..USAGE :
    `/api/permissions/by_role[?role=all]`
        --> all permissions for roles allowed for `Patron` resource.
    `/api/permissions/by_role?role=admin&role=pro_read_only`
        --> all permissions for "admin" and "pro_read_only" roles.
    """
    filtered_roles = get_all_roles()
    if role_names := request.args.getlist('role'):
        if 'all' not in role_names:
            filtered_roles = [r for r in filtered_roles if r[0] in role_names]

    return jsonify(expose_action_needs_by_role(filtered_roles))


@api_blueprint.route('/permissions/by_patron/<patron_pid>', methods=['GET'])
@check_permission([permission_management_action])
def permissions_by_patron(patron_pid):
    """Expose permissions for a specific user.

    :param patron_pid: the patron pid to expose.
    """
    patron = Patron.get_record_by_pid(patron_pid)
    if not patron:
        abort(404, 'Patron not found')
    return jsonify(expose_action_needs_by_patron(patron))


# PROXY APIS' =================================================================
@api_blueprint.route('/proxy')
@check_logged_as_librarian
def proxy():
    """Proxy to get record metadata from MEF server."""
    if not (url := request.args.get('url')):
        abort(400, "Missing `url` parameter")
    response = requests.get(url)
    return make_response(response.content, response.status_code)


# TRANSLATIONS APIS' ==========================================================

@api_blueprint.route('/translations/<ln>.json')
def translations(ln):
    """Exposes translations in JSON format.

    :param ln: language ISO 639-1 Code (two chars).
    """
    babel = current_app.extensions['babel']
    paths = babel.default_directories
    try:
        path = next(p for p in paths if p.find('rero_ils') > -1)
    except StopIteration:
        current_app.logger.error(f'translations for {ln} does not exist')
        abort(404)

    po_file_name = f'{path}/{ln}/LC_MESSAGES/{babel.default_domain}.po'
    if not os.path.isfile(po_file_name):
        abort(404)
    try:
        po = polib.pofile(po_file_name)
    except Exception:
        current_app.logger.error(f'unable to open po file: {po_file_name}')
        abort(404)
    data = {entry.msgid: entry.msgstr or entry.msgid for entry in po}
    return jsonify(data)
