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

import polib
from flask import Blueprint, abort, current_app, jsonify
from flask_babelex import get_domain

from rero_ils.modules.utils import cached

from .decorators import check_authentication
from .permissions import record_permissions

api_blueprint = Blueprint(
    'api_blueprint',
    __name__,
    url_prefix=''
)


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
        current_app.logger.error(f'translations for {ln} does not exist')
        abort(404)

    po_file_name = f'{path}/{ln}/LC_MESSAGES/{domain.domain}.po'
    if not os.path.isfile(po_file_name):
        abort(404)
    try:
        po = polib.pofile(po_file_name)
    except Exception:
        current_app.logger.error(f'unable to open po file: {po_file_name}')
        abort(404)
    data = {entry.msgid: entry.msgstr or entry.msgid for entry in po}
    return jsonify(data)
