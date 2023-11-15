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

"""Blueprint used for entities."""
from flask import Blueprint, abort, current_app, render_template
from flask_babel import lazy_gettext as _
from invenio_i18n.ext import current_i18n

from rero_ils.modules.entities.models import EntityType

from .local_entities.api import LocalEntity
from .remote_entities.api import RemoteEntity

blueprint = Blueprint(
    'entities',
    __name__,
    url_prefix='/<string:viewcode>/entities',
    template_folder='templates',
    static_folder='static',
)


@blueprint.route('/<string:type>/<string:pid>')
def entity_detailed_view(viewcode, type, pid):
    """Display entity view (local or remote).

    :param: viewcode: The current view code.
    :param: type: Resource type.
    :param: pid: Resource PID.
    :returns: The html rendering of the resource.
    """
    if type not in ['local', 'remote']:
        abort(404)
    entity_class = LocalEntity if type == 'local' else RemoteEntity
    if not (record := entity_class.get_record_by_pid(pid)):
        abort(404, _('Entity not found.'))

    return render_template(
        f'rero_ils/entity_{type}.html',
        record=record,
        viewcode=viewcode,
        search_link=search_link(record)
    )


@blueprint.app_template_filter()
def entity_icon(type):
    """Selects the right icon according to type.

    :param: type: Resource type.
    :returns: string, The class of the selected icon.
    """
    icons = {
        EntityType.ORGANISATION: 'fa-building-o',
        EntityType.PERSON: 'fa-user-o',
        EntityType.PLACE: 'fa-map-marker',
        EntityType.TEMPORAL: 'fa-calendar',
        EntityType.TOPIC: 'fa-tag',
        EntityType.WORK: 'fa-book'
    }
    return icons.get(type, 'fa-question-circle-o')


@blueprint.app_template_filter()
def extract_data_from_remote_entity(record):
    """Data extraction based on language and resource type.

    Used only on remote entity.

    :param: record: the json record
    :returns: source and the dictionary of the resource selected.
    """
    locale = current_i18n.locale.language
    agent_order = current_app.config.get('RERO_ILS_AGENTS_LABEL_ORDER')
    if locale not in agent_order:
        locale = agent_order.get('fallback', {})
    sources = agent_order.get(locale)
    for source in sources:
        if data := record.get(source):
            return source, data


@blueprint.app_template_filter()
def entity_label(data, language):
    """Create contribution label.

    :param data: The record metadata.
    :param language: The current language.
    :returns: The contribution label.
    """
    order = current_app.config.get('RERO_ILS_AGENTS_LABEL_ORDER', [])
    source_order = order.get(language, order.get(order['fallback'], []))
    for source in source_order:
        if label := data.get(source, {}).get('authorized_access_point', None):
            return label
    return '-'


@blueprint.app_template_filter()
def sources_link(data):
    """Extract sources link.

    :param data: The record metadata.
    :returns A dict with the source and link.
    """
    links = {}
    sources_link = list(filter(lambda source: source not in
                               current_app.config.get(
                                   'RERO_ILS_AGENTS_SOURCES_EXCLUDE_LINK', []),
                               data.get('sources', [])))

    for source in sources_link:
        if identifier := data.get(source, {}).get('identifier'):
            links[source] = identifier
    return links


def search_link(metadata):
    """Generate Link for search entities.

    :param metadata: the record metadata.
    :returns: the search link.
    """
    fields_config = current_app.config.get(
        'RERO_ILS_APP_ENTITIES_TYPES_FIELDS', {})
    fields_ref = current_app.config.get(
        'RERO_ILS_APP_ENTITIES_FIELDS_REF', [])
    entity_type = metadata['type']
    fields = fields_config[entity_type] if (entity_type in fields_config) \
        else fields_ref
    queries = []
    for field in fields:
        if 'sources' in metadata:
            # Remote entities
            source, data = extract_data_from_remote_entity(metadata)
            entity_id = data.get('pid')
        else:
            # Local entities
            source = 'local'
            entity_id = metadata.get('pid')
        queries.append(f'{field}.entity.pids.{source}:{entity_id}')
    return " OR ".join(queries) + "&simple=0"
