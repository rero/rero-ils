# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Blueprint used for loading templates."""

from __future__ import absolute_import, print_function

import requests
from flask import Blueprint, abort, current_app, render_template

from ..documents.api import DocumentsSearch

# from invenio_records_ui.signals import record_viewed

blueprint = Blueprint(
    'mef_persons',
    __name__,
    url_prefix='/persons',
    template_folder='templates',
    static_folder='static',
)


@blueprint.route('/<pid>')
def persons_detailed_view(pid):
    """Display default view.

    Sends record_viewed signal and renders template.
    :param pid: PID object.
    """
    # record_viewed.send(
    #     current_app._get_current_object(), pid=pid, record=record)
    mef_url = '{url}mef/{pid}'.format(
        url=current_app.config.get('RERO_ILS_MEF_URL'),
        pid=pid
    )
    response = requests.get(url=mef_url, params=dict(
        resolve=1,
        sources=1
    ))
    if response.status_code != requests.codes.ok:
        current_app.logger.info(
            'Mef Error: {status} {url}'.format(
                status=response.status_code,
                url=mef_url
            )
        )
        abort(response.status_code)
    record = response.json()
    record = record.get('metadata')
    search = DocumentsSearch()
    results = search.filter(
        'match',
        authors__pid=pid
    ).execute().hits.hits
    documents = []
    for result in results:
        documents.append(result.get('_source'))
    if documents:
        record['documents'] = documents
    return render_template(
        'rero_ils/detailed_view_persons.html',
        record=record
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
