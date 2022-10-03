# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2020 RERO
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

"""API for manipulating local_fields."""

from functools import partial

from elasticsearch_dsl import Q
from flask_babelex import gettext as _

from .models import LocalFieldIdentifier, LocalFieldMetadata
from ..api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from ..documents.api import Document
from ..fetchers import id_fetcher
from ..items.api import Item
from ..minters import id_minter
from ..providers import Provider
from ...modules.utils import extracted_data_from_ref

# provider
LocalFieldProvider = type(
    'LocalFieldProvider',
    (Provider,),
    dict(identifier=LocalFieldIdentifier, pid_type='lofi')
)
# minter
local_field_id_minter = partial(id_minter, provider=LocalFieldProvider)
# fetcher
local_field_id_fetcher = partial(id_fetcher, provider=LocalFieldProvider)


class LocalFieldsSearch(IlsRecordsSearch):
    """LocalFieldsSearch."""

    class Meta:
        """Search only on local_field index."""

        index = 'local_fields'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class LocalField(IlsRecord):
    """LocalField class."""

    minter = local_field_id_minter
    fetcher = local_field_id_fetcher
    provider = LocalFieldProvider
    model_cls = LocalFieldMetadata

    def extended_validation(self, **kwargs):
        """Extended validation."""
        # check if a local_fields resource exists for this document
        p_type = extracted_data_from_ref(self.get('parent'), data='acronym')
        p_pid = extracted_data_from_ref(self.get('parent'))
        organisation_pid = extracted_data_from_ref(self.get('organisation'))
        count = LocalFieldsSearch()\
            .filter('term', parent__type=p_type)\
            .filter('term', parent__pid=p_pid)\
            .filter('term', organisation__pid=organisation_pid)\
            .exclude('term', pid=self['pid'])\
            .count()
        if count > 0:
            return _('Local fields already exist for this document.')

        # check if all fields are empty.
        if len(self.get('fields', {}).keys()) == 0:
            return _('Missing fields.')
        return True

    @classmethod
    def get_local_fields_by_resource(cls, type, pid, organisation_pid=None):
        """Get all local fields linked to a resource.

        :param type: type of record (Ex: doc).
        :param pid: pid of record type.
        :param organisation_pid: current organisation pid.
        :return: list of local fields record.
        """
        queryFilters = [
            Q('term', parent__type=type),
            Q('term', parent__pid=pid)
        ]
        if (organisation_pid):
            queryFilters.append(Q('term', organisation__pid=organisation_pid))
        query = LocalFieldsSearch()\
            .query('bool', filter=queryFilters)\
            .sort(
                {'organisation__pid': {'order': 'asc'}},
                {'parent__type': {'order': 'asc'}}
            )\
            .source(['organisation', 'fields']).scan()
        local_fields = []
        for local_field in query:
            data = local_field.to_dict()
            local_fields.append({
                'organisation_pid': data['organisation']['pid'],
                'fields': data['fields']
            })
        return local_fields


class LocalFieldsIndexer(IlsRecordsIndexer):
    """Local fields indexing class."""

    record_cls = LocalField

    def index(self, record):
        """Reindex a resource (documents, items, holdings).

        :param record: Record instance.
        """
        return_value = super().index(record)
        resource = extracted_data_from_ref(record['parent']['$ref'], 'record')
        if isinstance(resource, Document) or isinstance(resource, Item):
            resource.reindex()
        return return_value

    def delete(self, record):
        """Reindex a resource (documents, items, holdings).

        :param record: Record instance.
        """
        return_value = super().delete(record)
        resource = extracted_data_from_ref(record['parent']['$ref'], 'record')
        if isinstance(resource, Document) or isinstance(resource, Item):
            resource.reindex()
        return return_value

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='lofi')
