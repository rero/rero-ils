# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2024 RERO
# Copyright (C) 2019-2024 UCLouvain
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

from functools import cmp_to_key

from flask import Blueprint, abort, current_app, jsonify
from flask import request as flask_request
from invenio_jsonschemas import current_jsonschemas
from invenio_jsonschemas.errors import JSONSchemaNotFound

from rero_ils.modules.decorators import check_logged_as_librarian

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


@api_blueprint.route('/advanced-search-config')
@cached(timeout=300, query_string=True)
@check_logged_as_librarian
def advanced_search_config():
    """Advanced search config."""

    def sort_medias(a, b):
        """Sort only media start with rda in label."""
        a, b = a['label'], b['label']
        if a.startswith('rda') and b.startswith('rda'):
            return a > b
        elif a.startswith('rda'):
            return -1
        elif b.startswith('rda'):
            return 1
        else:
            return a > b

    try:
        cantons = current_jsonschemas.get_schema('common/cantons-v0.0.1.json')
        countries = current_jsonschemas.get_schema(
            'common/countries-v0.0.1.json')
        medias = current_jsonschemas.get_schema(
            'documents/document_content_media_carrier-v0.0.1.json')
    except JSONSchemaNotFound:
        abort(404)

    media_items = medias['contentMediaCarrier']['items']['oneOf']
    media_types = []
    carrier_types = []
    for item in media_items:
        if rda_type := item.get('properties', {}).get('mediaType', {}):
            data = rda_type.get('title')
            media_types.append({'label': data, 'value': data})
        if rda_type := item.get('properties', {}).get('carrierType', {}):
            for option in rda_type.get('widget', {}).get('formlyConfig', {})\
                    .get('props', []).get('options'):
                if option not in carrier_types:
                    carrier_types.append(option)
    return jsonify({
        'fieldsConfig': current_app.config.get(
            'RERO_ILS_APP_ADVANCED_SEARCH_CONFIG', []),
        'fieldsData': {
            'country': countries['country']['widget']['formlyConfig']
            ['props']['options'],
            'canton': cantons['canton']['widget']['formlyConfig']
            ['props']['options'],
            'rdaContentType': medias['definitions']['contentType']['items']
            ['widget']['formlyConfig']['props']['options'],
            'rdaMediaType': sorted(media_types, key=cmp_to_key(sort_medias)),
            'rdaCarrierType': sorted(
                carrier_types, key=cmp_to_key(sort_medias))
        }
    })
