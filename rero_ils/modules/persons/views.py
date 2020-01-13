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

"""Blueprint used for loading templates."""

from __future__ import absolute_import, print_function

import requests
from flask import Blueprint, Response, abort, current_app, render_template, \
    request
from invenio_records_ui.signals import record_viewed

from rero_ils.modules.organisations.api import Organisation

from ..documents.api import DocumentsSearch

# from invenio_records_ui.signals import record_viewed

blueprint = Blueprint(
    'persons',
    __name__,
    url_prefix='/<string:viewcode>/persons',
    template_folder='templates',
    static_folder='static',
)


def person_view_method(pid, record, template=None, **kwargs):
    """Display default view.

    Sends record_viewed signal and renders template.
    :param pid: PID object.
    """
    record_viewed.send(
        current_app._get_current_object(), pid=pid, record=record)

    # Get author documents
    search = DocumentsSearch().filter(
        'term',
        authors__pid=pid.pid_value)

    viewcode = kwargs['viewcode']
    if (viewcode != current_app.config.get(
        'RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'
    )):
        org_pid = Organisation.get_record_by_viewcode(viewcode)['pid']
        search = search.filter(
            'term', holdings__organisation__organisation_pid=org_pid
        )

    record['documents'] = list(search.scan())

    return render_template(
        template,
        record=record,
        viewcode=viewcode
    )


@blueprint.app_template_filter()
def person_merge_data_values(data):
    """Create merged data for values."""
    result = {}
    sources = current_app.config.get('RERO_ILS_PERSONS_SOURCES', [])
    for source in sources:
        for key, values in data.get(source, {}).items():
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
def person_label(data, language):
    """Create person label."""
    order = current_app.config.get('RERO_ILS_PERSONS_LABEL_ORDER', [])
    source_order = order.get(language, order.get(order['fallback'], []))

    for source in source_order:
        label = data.get(source, {}).get('preferred_name_for_person', None)
        if label:
            return label
    return '-'


api_blueprint = Blueprint(
    'api_persons',
    __name__
)


@api_blueprint.route('/mef/', defaults={'path': ''})
@api_blueprint.route('/mef/<path:path>')
# @api_blueprint.route('/persons/', defaults={'path': ''})
# @api_blueprint.route('/persons/<path:path>')
def mef_proxy(path):
    """Proxy to mef server."""
    resp = requests.request(
        method=request.method,
        url=request.url.replace(
            request.base_url.replace(path, ''),
            current_app.config.get('RERO_ILS_MEF_URL')
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
