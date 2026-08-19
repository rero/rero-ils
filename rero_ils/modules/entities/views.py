# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Blueprint used for entities."""

from flask import Blueprint, abort, current_app, render_template
from flask_babel import lazy_gettext as _
from invenio_i18n.ext import current_i18n

from rero_ils.modules.entities.models import EntityType

from .local_entities.api import LocalEntity
from .remote_entities.api import RemoteEntity

blueprint = Blueprint(
    "entities",
    __name__,
    url_prefix="/<string:viewcode>/entities",
    template_folder="templates",
)


@blueprint.route("/<string:type>/<string:pid>")
def entity_detailed_view(viewcode, type, pid):
    """Display entity view (local or remote).

    :param: viewcode: The current view code.
    :param: type: Resource type.
    :param: pid: Resource PID.
    :returns: The html rendering of the resource.
    """
    if type not in ["local", "remote"]:
        abort(404)
    entity_class = LocalEntity if type == "local" else RemoteEntity
    if not (record := entity_class.get_record_by_pid(pid)):
        abort(404, _("Entity not found."))

    return render_template(
        f"rero_ils/entity_{type}.html",
        record=record,
        viewcode=viewcode,
        search_link=search_link(record),
    )


@blueprint.app_template_filter()
def entity_icon(type):
    """Selects the right icon according to type.

    :param: type: Resource type.
    :returns: string, The class of the selected icon.
    """
    icons = {
        EntityType.ORGANISATION: "fa-regular fa-building",
        EntityType.PERSON: "fa-regular fa-user",
        EntityType.PLACE: "fa-solid fa-location-dot",
        EntityType.TEMPORAL: "fa-solid fa-calendar-day",
        EntityType.TOPIC: "fa-solid fa-tag",
        EntityType.WORK: "fa-solid fa-book",
    }
    return icons.get(type, "fa-solid fa-circle-question")


@blueprint.app_template_filter()
def extract_data_from_remote_entity(record):
    """Data extraction based on language and resource type.

    Used only on remote entity.

    :param: record: the json record
    :returns: source and the dictionary of the resource selected.
    """
    locale = current_i18n.locale.language
    agent_order = current_app.config.get("RERO_ILS_AGENTS_LABEL_ORDER")
    if locale not in agent_order:
        locale = agent_order.get("fallback", {})
    sources = agent_order.get(locale)
    for source in sources:
        if data := record.get(source):
            return source, data
    return None


@blueprint.app_template_filter()
def entity_label(data, language):
    """Create contribution label.

    :param data: The record metadata.
    :param language: The current language.
    :returns: The contribution label.
    """
    order = current_app.config.get("RERO_ILS_AGENTS_LABEL_ORDER", [])
    source_order = order.get(language, order.get(order["fallback"], []))
    for source in source_order:
        if label := data.get(source, {}).get("authorized_access_point", None):
            return label
    return "-"


@blueprint.app_template_filter()
def sources_link(data):
    """Extract sources link.

    :param data: The record metadata.
    :returns A dict with the source and link.
    """
    links = {}
    sources_link = list(
        filter(
            lambda source: source not in current_app.config.get("RERO_ILS_AGENTS_SOURCES_EXCLUDE_LINK", []),
            data.get("sources", []),
        )
    )

    for source in sources_link:
        if identifier := data.get(source, {}).get("identifier"):
            links[source] = identifier
    return links


def search_link(metadata):
    """Generate Link for search entities.

    :param metadata: the record metadata.
    :returns: the search link.
    """
    fields_config = current_app.config.get("RERO_ILS_ENTITIES_TYPES_FIELDS", {})
    fields_ref = current_app.config.get("RERO_ILS_ENTITIES_FIELDS_REF", [])
    entity_type = metadata["type"]
    fields = fields_config.get(entity_type, fields_ref)
    queries = []
    for field in fields:
        if "sources" in metadata:
            # Remote entities
            source, data = extract_data_from_remote_entity(metadata)
            entity_id = data.get("pid")
        else:
            # Local entities
            source = "local"
            entity_id = metadata.get("pid")
        queries.append(f"{field}.entity.pids.{source}:{entity_id}")
    return " OR ".join(queries) + "&simple=0"
