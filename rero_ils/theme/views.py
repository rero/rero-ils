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

"""Blueprint used for loading templates."""

from __future__ import absolute_import, print_function

import copy
import re
from copy import deepcopy
from functools import wraps
from urllib.parse import urlparse

from flask import Blueprint, Response, abort, current_app, jsonify, redirect, \
    render_template, request, session, url_for
from invenio_jsonschemas import current_jsonschemas
from invenio_jsonschemas.errors import JSONSchemaNotFound
from invenio_jsonschemas.proxies import current_refresolver_store

from rero_ils.modules.organisations.api import Organisation
from rero_ils.modules.utils import cached
from rero_ils.permissions import can_access_professional_view

from .menus import init_menu_lang, init_menu_profile, init_menu_tools

blueprint = Blueprint(
    'rero_ils',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.before_app_first_request
def init_menu():
    """Create the header menus."""
    init_menu_tools()
    init_menu_lang()
    init_menu_profile()


def check_organisation_viewcode(fn):
    """Check if viewcode parameter is defined."""
    @wraps(fn)
    def decorated_view(*args, **kwargs):
        viewCodes = Organisation.all_code()
        # Add default view code
        viewCodes.append(current_app.config.get(
            'RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'))
        if kwargs['viewcode'] not in viewCodes:
            abort(404)
        return fn(*args, **kwargs)

    return decorated_view


@blueprint.route('/error')
def error():
    """Error to generate exception for test purposes."""
    raise Exception('this is an error for test purposes')


@blueprint.route('/robots.txt')
@cached()
def robots(timeout=60*60):  # 1 hour timeout
    """Robots.txt generate response."""
    response = current_app.config['RERO_ILS_ROBOTS']
    response = Response(
        response=response,
        status=200, mimetype="text/plain")
    response.headers["Content-Type"] = "text/plain; charset=utf-8"
    return response


@blueprint.route('/')
def index():
    """Home Page."""
    return render_template('rero_ils/frontpage.html',
                           organisations=Organisation.get_all(),
                           viewcode=current_app.config.get(
                               'RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'))


@blueprint.route('/<string:viewcode>')
@blueprint.route('/<string:viewcode>/')
@check_organisation_viewcode
def index_with_view_code(viewcode):
    """Home Page."""
    if viewcode == current_app.config.get('RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'):
        return redirect(url_for(
            'rero_ils.index'
        ))
    else:
        return render_template(
            'rero_ils/frontpage.html',
            organisations=Organisation.get_all(),
            viewcode=viewcode
        )


@blueprint.route('/language', methods=['POST', 'PUT'])
def set_language():
    """Set language in session.

    The call should be a POST or a PUT HTTP request with a JSON body as follow:

    .. code-block:: json

        {
            "lang": "fr"
        }
    """
    data = request.get_json()
    if not data or not data.get('lang'):
        return jsonify(
            {'errors': [{'code': 400, 'title': 'missing lang property'}]}), 400
    lang_code = data.get('lang')
    languages = dict(current_app.extensions['invenio-i18n'].get_languages())
    if lang_code not in languages:
        return jsonify(
            {'errors': [{'code': 400, 'title': 'unsupported language'}]}), 400
    session[current_app.config['I18N_SESSION_KEY']] = lang_code.lower()
    return jsonify({'lang': lang_code})


@blueprint.route('/<string:viewcode>/search/<recordType>')
@check_organisation_viewcode
def search(viewcode, recordType):
    """Search page ui."""
    return render_template(current_app.config.get('RERO_ILS_SEARCH_TEMPLATE'),
                           viewcode=viewcode)


@blueprint.app_template_filter()
def nl2br(string):
    """Replace return to <br>."""
    return string.replace("\n", "<br>")


@blueprint.app_template_filter('urlActive')
def url_active(string, target):
    """Add link url on text if http detected."""
    result = re.findall('(https?://[\\w|.|\\-|\\/]+)', string)
    for link in result:
        if link:
            string = string.replace(
                link,
                f'<a href="{link}" target="{target}">{link}</a>'
            )
    return string


@blueprint.app_template_filter('viewOrganisationName')
def view_organisation_name(viewcode):
    """Get view name."""
    if viewcode != current_app.config.get('RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'):
        if org := Organisation.get_record_by_viewcode(viewcode):
            return org['name']
    return current_app.config.get('RERO_ILS_SEARCH_GLOBAL_NAME', '')


def prepare_jsonschema(schema):
    """Json schema prep."""
    schema = copy.deepcopy(schema)
    schema.pop('$schema', None)
    if 'pid' in schema.get('required', []):
        schema['required'].remove('pid')
    default_country = current_app.config.get('USERPROFILES_DEFAULT_COUNTRY')
    # users
    field = schema.get('properties', {}).get('country')
    # patrons: allOf does not works to remove property
    if not field:
        field = schema.get('properties', {}).get('second_address', {}).get(
            'properties', {}).get('country')
    if field and default_country:
        field['default'] = default_country
    return schema


@blueprint.route('/schemas/<document_type>')
def schemaform(document_type):
    """Return schema and form options for the editor."""
    doc_type = document_type
    doc_type = re.sub('ies$', 'y', doc_type)
    doc_type = re.sub('s$', '', doc_type)
    doc_type = re.sub('s_cfg$', '_cfg', doc_type)
    data = {}
    schema = None
    schema_name = None
    try:
        if current_app.debug:
            current_jsonschemas.get_schema.cache_clear()
        schema_name = f'{document_type}/{doc_type}-v0.0.1.json'
        schema = current_jsonschemas.get_schema(schema_name, with_refs=True)
        data['schema'] = prepare_jsonschema(schema)
    except JSONSchemaNotFound:
        abort(404)

    return jsonify(data)


def replace_ref_url(schema, new_host):
    """Replace all $refs with local $refs.

    :param: schema: Schema to replace the $refs
    :param: new_host: The host to replace the $ref with.
    :returns: modified schema.
    """
    jsonschema_host = current_app.config.get('JSONSCHEMAS_HOST')
    for k, v in schema.items():
        if isinstance(v, dict):
            schema[k] = replace_ref_url(
                schema=schema[k],
                new_host=new_host
            )
    if '$ref' in schema and isinstance(schema['$ref'], str):
        schema['$ref'] = schema['$ref'] \
            .replace(jsonschema_host, new_host)
    # Todo: local://
    return schema


@blueprint.route('/schemas/<path>/<schema>')
def get_schema(path, schema):
    """Retrieve a schema."""
    schema_path = f'{path}/{schema}'
    try:
        schema = deepcopy(current_refresolver_store[f'local://{schema_path}'])
    except KeyError:
        abort(404)
    resolved = request.args.get(
        "resolved", current_app.config.get("JSONSCHEMAS_RESOLVE_SCHEMA"),
        type=int
    )
    new_host = urlparse(request.base_url).netloc
    # Change schema['properties']['$schema']['default'] URL
    if default := schema.get(
            'properties', {}).get('$schema', {}).get('default'):
        schema['properties']['$schema']['default'] = default.replace(
            current_app.config.get('JSONSCHEMAS_HOST'), new_host)
    # Change $refs
    schema = replace_ref_url(
        schema=schema,
        new_host=new_host
    )
    if resolved:
        if current_app.debug:
            current_jsonschemas.get_schema.cache_clear()
        schema = deepcopy(
            current_jsonschemas.get_schema(schema_path, with_refs=True))
    return jsonify(schema)


@blueprint.route('/professional/', defaults={'path': ''})
@blueprint.route('/professional/<path:path>')
@can_access_professional_view
def professional(path):
    """Return professional view."""
    return render_template('rero_ils/professional.html')
