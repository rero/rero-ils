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

import requests
from flask import Blueprint, Response, abort, current_app, render_template, \
    request
from flask_babelex import gettext as translate
from invenio_records_ui.signals import record_viewed

from .api import Contribution
from .models import ContributionType
from ..documents.api import DocumentsSearch
from ..organisations.api import Organisation
from ...theme.views import url_active

blueprint = Blueprint(
    'contributions',
    __name__,
    url_prefix='/<string:viewcode>',
    template_folder='templates',
    static_folder='static',
)

api_blueprint = Blueprint(
    'api_contributions',
    __name__
)


def contribution_proxy(viewcode, pid, contribution_type):
    """Proxy for contributions.

    :param viewcode: viewcode of html request
    :param pid: pid of contribution
    :param contribution_type: type of contribution
    :returns: contribution template
    """
    contribution = Contribution.get_record_by_pid(pid)
    if not contribution or contribution.get('type') != contribution_type:
        abort(404, 'Record not found')
    return contribution_view_method(
        pid=contribution.persistent_identifier,
        record=contribution,
        template='rero_ils/detailed_view_contribution.html',
        viewcode=viewcode
    )


@blueprint.route('/persons/<pid>', methods=['GET'])
def persons_proxy(viewcode, pid):
    """Proxy person for contribution."""
    return contribution_proxy(viewcode, pid, ContributionType.PERSON)


@blueprint.route('/corporate-bodies/<pid>', methods=['GET'])
def corporate_bodies_proxy(viewcode, pid):
    """Proxy corporate bodies for contribution."""
    return contribution_proxy(viewcode, pid, 'bf:Organisation')


def contribution_view_method(pid, record, template=None, **kwargs):
    """Display default view.

    Sends record_viewed signal and renders template.
    :param pid: PID object.
    """
    record_viewed.send(
        current_app._get_current_object(), pid=pid, record=record)

    # Get contribution persons documents
    search = DocumentsSearch().filter(
        'term', contribution__agent__pid=pid.pid_value
    )

    viewcode = kwargs['viewcode']
    if (viewcode != current_app.config.get(
        'RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'
    )):
        org_pid = Organisation.get_record_by_viewcode(viewcode)['pid']
        search = search \
            .filter('term', holdings__organisation__organisation_pid=org_pid)
    search = search \
        .params(preserve_order=True)\
        .sort({'sort_title': {"order": "asc"}})

    record['documents'] = list(search.scan())
    return render_template(
        template,
        record=record,
        viewcode=viewcode
    )


@blueprint.app_template_filter()
def contribution_merge_data_values(data):
    """Create merged data for values."""
    sources = current_app.config.get('RERO_ILS_CONTRIBUTIONS_SOURCES', [])
    result = {}
    for source in sources:
        if data.get(source):
            result[source] = {
                'pid': data[source]['pid'],
                'identifier': data[source]['identifier']
            }
        for key, values in data.get(source, {}).items():
            if key == 'conference':
                result['conference'] = data[source]['conference']
            else:
                if key not in result:
                    result[key] = {}
                if isinstance(values, str):
                    values = [values]
                for value in values:
                    if value in result[key]:
                        result[key][value].append(source)
                    else:
                        result[key][value] = [source]
    return result


@blueprint.app_template_filter()
def contribution_label(data, language):
    """Create contribution label."""
    order = current_app.config.get('RERO_ILS_CONTRIBUTIONS_LABEL_ORDER', [])
    source_order = order.get(language, order.get(order['fallback'], []))

    for source in source_order:
        label = data.get(source, {}).get('authorized_access_point', None)
        if label:
            return label
    return '-'


@blueprint.app_template_filter()
def translat_unified(data, prefix=''):
    """Translate the keys of an dictionary.

    :param data: dictionary to translate
    :param prefix: prefix to add to keys
    :returns: dictionary with translated keys
    """
    translated_data = {}
    for key, value in data.items():
        translated_data[translate('{prefix}{key}'.format(
            prefix=prefix, key=key))] = value
    return translated_data


@blueprint.app_template_filter()
@api_blueprint.app_template_filter()
def translat(data, prefix='', seperator=', '):
    """Translate data."""
    translated = None
    if data:
        if isinstance(data, list):
            translated = []
            for item in data:
                translated.append(translate('{prefix}{item}'.format(
                    prefix=prefix, item=item)))
            translated = seperator.join(translated)
        elif isinstance(data, str):
            translated = translate('{prefix}{data}'.format(
                prefix=prefix, data=data))
    return translated


@blueprint.app_template_filter('biographicaUrl')
def biographical_url(biographicals):
    """Add link url on text if http detected."""
    output = dict()
    for biographical in biographicals:
        output[url_active(biographical, '_blank')] = \
            biographicals[biographical]
    return output


@api_blueprint.route('/mef/', defaults={'path': ''})
@api_blueprint.route('/mef/<path:path>')
def mef_proxy(path):
    """Proxy to mef server."""
    resp = requests.request(
        method=request.method,
        url=request.url.replace(
            request.base_url.replace(path, ''),
            f'{current_app.config.get("RERO_ILS_MEF_AGENTS_URL")}/mef/'
        ),
        headers={
            key: value for (key, value) in request.headers if key != 'Host'
        },
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=True
    )
    excluded_headers = ['content-encoding', 'content-length',
                        'transfer-encoding', 'connection']
    headers = [
        (name, value) for (name, value) in resp.raw.headers.items()
        if name.lower() not in excluded_headers
    ]

    response = Response(resp.content, resp.status_code, headers)
    if response.status_code != requests.codes.ok:
        abort(response.status_code)
    return response
