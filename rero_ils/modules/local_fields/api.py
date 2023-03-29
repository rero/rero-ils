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

"""API for manipulating local_fields."""

from functools import partial

from elasticsearch_dsl import Q
from flask_babel import gettext as _

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

    def get_local_fields(self, parent_type, parent_pid, organisation_pid=None):
        """Get local fields related to a resource.

        :param parent_type: the parent record type.
        :param parent_pid: the parent record pid.
        :param organisation_pid: organisation pid filter value.
        :return: a list of ElasticSearch hit.
        """
        filters = Q('term', parent__type=parent_type)
        filters &= Q('term', parent__pid=parent_pid)
        if organisation_pid:
            filters &= Q('term', organisation__pid=organisation_pid)
        return self.filter(filters)


class LocalField(IlsRecord):
    """LocalField class."""

    minter = local_field_id_minter
    fetcher = local_field_id_fetcher
    provider = LocalFieldProvider
    model_cls = LocalFieldMetadata

    def extended_validation(self, **kwargs):
        """Extended validation."""
        # parent reference must exists
        parent = extracted_data_from_ref(self.get('parent'), data='record')
        if not parent:
            return _("Parent record doesn't exists.")
        # check if a local_fields resource exists for this document
        query = LocalFieldsSearch().get_local_fields(
            parent.provider.pid_type, parent.pid,
            extracted_data_from_ref(self.get('organisation'))
        )
        if query.exclude('term', pid=self['pid']).count():
            return _('Local fields already exist for this resource.')
        # check if all fields are empty.
        if len(self.get('fields', {}).keys()) == 0:
            return _('Missing fields.')
        return True

    @staticmethod
    def get_local_fields_by_id(parent_type, parent_pid, organisation_pid=None):
        """Get local fields related to a parent record.

        :param parent_type: the parent record type.
        :param parent_pid: the parent record pid.
        :param organisation_pid: organisation pid filter value.
        :returns: a generator of `LocalField` records.
        """
        search = LocalFieldsSearch()\
            .get_local_fields(parent_type, parent_pid, organisation_pid)\
            .source(False)
        for hit in search.scan():
            yield LocalField.get_record(hit.meta.id)

    @staticmethod
    def get_local_fields(parent, organisation_pid=None):
        """Get local fields related to a parent record.

        :param parent: the parent record.
        :param organisation_pid: organisation pid filter value.
        :returns: a generator of `LocalField` records.
        """
        return LocalField.get_local_fields_by_id(
            parent.provider.pid_type,
            parent.pid,
            organisation_pid
        )


class LocalFieldsIndexer(IlsRecordsIndexer):
    """Local fields indexing class."""

    record_cls = LocalField

    @staticmethod
    def _reindex_parent_resource(record):
        """Reindex the parent resource.

        :param record: the `LocalField` instance.
        """
        resource = extracted_data_from_ref(record['parent']['$ref'], 'record')
        if isinstance(resource, (Document, Item)):
            resource.reindex()

    def index(self, record):
        """Reindex a `LocalField` resource.

        :param record: `LocalField` record instance.
        """
        return_value = super().index(record)
        LocalFieldsIndexer._reindex_parent_resource(record)
        return return_value

    def delete(self, record):
        """Delete a `LocalField` record.

        :param record: `LocalField` record instance.
        """
        return_value = super().delete(record)
        LocalFieldsIndexer._reindex_parent_resource(record)
        return return_value

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='lofi')
