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

"""Blueprint about remote entities."""

from __future__ import absolute_import, print_function

from flask import Blueprint, abort, current_app, render_template
from flask_babelex import gettext as translate
from invenio_records_ui.signals import record_viewed

from rero_ils.modules.decorators import check_logged_as_librarian
from rero_ils.modules.documents.api import DocumentsSearch
from rero_ils.modules.organisations.api import Organisation
from rero_ils.theme.views import url_active

from .api import RemoteEntity
from ..models import EntityType
from .proxy import MEFProxyFactory

blueprint = Blueprint(
    'remote_entities',
    __name__,
    url_prefix='/<string:viewcode>',
    template_folder='templates',
    static_folder='static',
)

api_blueprint = Blueprint(
    'api_remote_entities',
    __name__
)


def remote_entity_proxy(viewcode, pid, entity_type):
    """Proxy for entities.

    :param viewcode: viewcode of html request
    :param pid: pid of contribution
    :param entity_type: type of the entity
    :returns: entity template
    """
    entity = RemoteEntity.get_record_by_pid(pid)
    if not entity or entity.get('type') != entity_type:
        abort(404, 'Record not found')
    return remote_entity_view_method(
        pid=entity.persistent_identifier,
        record=entity,
        template='rero_ils/detailed_view_entity.html',
        viewcode=viewcode
    )


def remote_entity_view_method(pid, record, template=None, **kwargs):
    """Display default view.

    Sends record_viewed signal and renders template.

    :param pid: PID object.
    :param record: the `Entity` record,
    :param template: the template to use to render the entity
    """
    record_viewed.send(
        current_app._get_current_object(), pid=pid, record=record)

    # Get contribution persons documents
    search = DocumentsSearch()\
        .filter('term', contribution__entity__pid=pid.pid_value)

    viewcode = kwargs['viewcode']
    if viewcode != current_app.config.get('RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'):
        org_pid = Organisation.get_record_by_viewcode(viewcode)['pid']
        search = search \
            .filter('term', holdings__organisation__organisation_pid=org_pid)
    search = search \
        .params(preserve_order=True)\
        .sort({'sort_title': {'order': 'asc'}})

    record['documents'] = list(search.scan())
    return render_template(template, record=record, viewcode=viewcode)


@blueprint.route('/persons/<pid>', methods=['GET'])
def persons_proxy(viewcode, pid):
    """Proxy person for entity."""
    return remote_entity_proxy(viewcode, pid, EntityType.PERSON)


@blueprint.route('/corporate-bodies/<pid>', methods=['GET'])
def corporate_bodies_proxy(viewcode, pid):
    """Proxy corporate bodies for entity."""
    return remote_entity_proxy(viewcode, pid, EntityType.ORGANISATION)


@api_blueprint.route('/remote_entities/search/<term>',
                     defaults={'entity_type': 'agents'})
@api_blueprint.route('/remote_entities/search/<entity_type>/<term>')
@api_blueprint.route('/remote_entities/search/<entity_type>/<term>/')
@check_logged_as_librarian
def remote_search_proxy(entity_type, term):
    """Proxy to search entities on remote server.

    Currently, we only search on MEF remote servers. If multiple remote sources
    are possible to search, a request must be sent to each remote API and
    all result must be unified into a common response.

    :param entity_type: The type of entities to search.
    :param term: the searched term.
    """
    try:
        return MEFProxyFactory.create_proxy(entity_type).search(term)
    except ValueError as err:
        abort(400, str(err))


# TEMPLATE JINJA FILTERS ======================================================
@blueprint.app_template_filter()
def entity_merge_data_values(data):
    """Create merged data for values."""
    sources = current_app.config.get('RERO_ILS_AGENTS_SOURCES', [])
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
def entity_label(data, language):
    """Create contribution label."""
    order = current_app.config.get('RERO_ILS_AGENTS_LABEL_ORDER', [])
    source_order = order.get(language, order.get(order['fallback'], []))
    for source in source_order:
        if label := data.get(source, {}).get('authorized_access_point', None):
            return label
    return '-'


@blueprint.app_template_filter()
def translat_unified(data, prefix=''):
    """Translate the keys of an dictionary.

    :param data: dictionary to translate
    :param prefix: prefix to add to keys
    :returns: dictionary with translated keys
    """
    return {
        translate(f'{prefix}{key}'): value
        for key, value
        in data.items()
    }


@blueprint.app_template_filter()
@api_blueprint.app_template_filter()
def translat(data, prefix='', seperator=', '):
    """Translate data."""
    if data:
        if isinstance(data, list):
            translated = [translate(f'{prefix}{item}') for item in data]
            return seperator.join(translated)
        elif isinstance(data, str):
            return translate(f'{prefix}{data}')


@blueprint.app_template_filter('biographicaUrl')
def biographical_url(biographicals):
    """Add link url on text if http detected."""
    return {
        url_active(biographical, '_blank'): biographicals[biographical]
        for biographical in biographicals
    }
