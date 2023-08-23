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

"""Blueprint for document api."""

from flask import Blueprint, abort, jsonify
from flask import request as flask_request

from .api import Document
from .utils import get_remote_cover
from ..utils import cached

api_blueprint = Blueprint(
    'api_documents',
    __name__,
    url_prefix='/document'
)


@api_blueprint.route('/cover/<isbn>')
@cached(timeout=300, query_string=True)
def cover(isbn):
    """Document cover service."""
    return jsonify(get_remote_cover(isbn))


@api_blueprint.route('/<pid>/availability', methods=['GET'])
def document_availability(pid):
    """HTTP GET request for document availability."""
    if not Document.record_pid_exists(pid):
        abort(404)
    view_code = flask_request.args.get('view_code')
    if not view_code:
        view_code = 'global'
    return jsonify({
        'available': Document.is_available(pid, view_code)
    })
