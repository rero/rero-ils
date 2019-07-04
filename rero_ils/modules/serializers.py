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

"""Record serialization."""

from flask import current_app, json, request, url_for
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_records_rest import current_records_rest
from invenio_records_rest.schemas import \
    RecordSchemaJSONV1 as _RecordSchemaJSONV1
from invenio_records_rest.serializers.json import \
    JSONSerializer as _JSONSerializer
from invenio_records_rest.serializers.response import record_responsify, \
    search_responsify
from invenio_records_rest.utils import obj_or_import_string
from marshmallow import fields


class RecordSchemaJSONV1(_RecordSchemaJSONV1):
    """Schema for records RERO ILS in JSON.

    Add a permissions field.
    """

    permissions = fields.Raw()
    explanation = fields.Raw()


class JSONSerializer(_JSONSerializer):
    """Mixin serializing records as JSON."""

    def preprocess_record(self, pid, record, links_factory=None, **kwargs):
        """Prepare a record and persistent identifier for serialization."""
        rec = record
        if request and request.args.get('resolve') == '1':
            rec = record.replace_refs()
        data = super(JSONSerializer, self).preprocess_record(
            pid=pid, record=rec, links_factory=links_factory, kwargs=kwargs)

        return JSONSerializer.add_item_links_and_permissions(record, data, pid)

    @staticmethod
    def preprocess_search_hit(pid, record_hit, links_factory=None, **kwargs):
        """Prepare a record hit from Elasticsearch for serialization."""
        from invenio_records.api import Record
        from invenio_pidstore.models import PersistentIdentifier
        data = super(JSONSerializer, JSONSerializer).preprocess_search_hit(
                     pid=pid, record_hit=record_hit,
                     links_factory=links_factory, kwargs=kwargs)
        record_class = obj_or_import_string(
            current_app.config
            .get('RECORDS_REST_ENDPOINTS')
            .get(pid.pid_type).get('record_class', Record))
        try:
            persistent_identifier = PersistentIdentifier.get(
                pid.pid_type, pid.pid_value)
            record = record_class.get_record(
                persistent_identifier.object_uuid
            )
            json = JSONSerializer.add_item_links_and_permissions(
                record, data, pid
            )
            permissions = json.get('permissions')
        except PIDDoesNotExistError:
            permissions = {
                'cannot_update': {'permisson': 'permission denied'},
                'cannot_delete': {'permisson': 'permission denied'}
            }
        search_hit = dict(
            pid=pid,
            metadata=record_hit['_source'],
            links=links_factory(pid, record_hit=record_hit, **kwargs),
            revision=record_hit['_version'],
            permissions=permissions
        )
        if record_hit.get('_explanation'):
            search_hit['explanation'] = record_hit.get('_explanation')
        return search_hit

    @staticmethod
    def add_item_links_and_permissions(record, data, pid):
        """Update the record with action links and permissions."""
        actions = [
            'update',
            'delete'
        ]
        permissions = {}
        action_links = {}
        for action in actions:
            permission = JSONSerializer.get_permission(action, pid.pid_type)
            if permission:
                can = permission(record, credentials_only=True).can()
                if can:
                    action_links[action] = url_for(
                        'invenio_records_rest.{pid_type}_item'.format(
                            pid_type=pid.pid_type),
                        pid_value=pid.pid_value, _external=True)
                else:
                    action_key = 'cannot_{action}'.format(action=action)
                    permissions[action_key] = {
                        'permission': "permission denied"}
        if not record.can_delete:
            permissions.setdefault(
                'cannot_delete',
                {}
            ).update(record.reasons_not_to_delete())
        data['links'].update(action_links)
        data['permissions'] = permissions
        return data

    @staticmethod
    def get_permission(action, pid_type):
        """Get the permission given an action."""
        default_action = getattr(
            current_records_rest,
            '{action}_permission_factory'.format(action=action))
        permission = obj_or_import_string(
            current_app.config
            .get('RECORDS_REST_ENDPOINTS')
            .get(pid_type)
            .get(
                '{action}_permission_factory_imp'.format(action=action),
                default_action))
        return permission

    def post_process_serialize_search(self, results, pid_fetcher):
        """Post process the search results."""
        pid_type = pid_fetcher('foo', dict(pid='1')).pid_type
        # add facet settings
        facet_config = current_app.config.get(
            'RERO_ILS_APP_CONFIG_FACETS', {}
        )
        facet_config = facet_config.get(pid_type, {})
        results['aggregations']['_settings'] = facet_config

        # add permissions and links actions
        permission = self.get_permission('create', pid_type)
        permissions = {}
        links = {}
        if permission:
            can = permission(record=None).can()
            if can:
                links['create'] = url_for(
                    'invenio_records_rest.{pid_type}_list'.format(
                        pid_type=pid_type), _external=True)
            else:
                permissions['create'] = {
                    'permission': "permission denied"}
        results['permissions'] = permissions
        results['links'].update(links)
        return results

    def serialize_search(self, pid_fetcher, search_result, links=None,
                         item_links_factory=None, **kwargs):
        """Serialize a search result.

        :param pid_fetcher: Persistent identifier fetcher.
        :param search_result: Elasticsearch search result.
        :param links: Dictionary of links to add to response.
        """
        results = dict(
            hits=dict(
                hits=[self.transform_search_hit(
                    pid_fetcher(hit['_id'], hit['_source']),
                    hit,
                    links_factory=item_links_factory,
                    **kwargs
                ) for hit in search_result['hits']['hits']],
                total=search_result['hits']['total'],
            ),
            links=links or {},
            aggregations=search_result.get('aggregations', dict()),
        )

        return json.dumps(
            self.post_process_serialize_search(
                results, pid_fetcher), **self._format_args())


json_v1 = JSONSerializer(RecordSchemaJSONV1)
"""JSON v1 serializer."""

json_v1_search = search_responsify(json_v1, 'application/json')
json_v1_response = record_responsify(json_v1, 'application/json')
