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

"""API for manipulating entities."""

from abc import ABC, abstractmethod

from elasticsearch_dsl import A
from flask import current_app

from rero_ils.modules.api import IlsRecord, IlsRecordsSearch
from rero_ils.modules.documents.api import DocumentsSearch
from rero_ils.modules.entities.remote_entities.utils import \
    extract_data_from_mef_uri
from rero_ils.modules.utils import extracted_data_from_ref, sorted_pids


class EntitiesSearch(IlsRecordsSearch):
    """Entities search class."""

    class Meta:
        """Meta class."""

        index = 'entities'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class Entity(IlsRecord, ABC):
    """Entity class."""

    @classmethod
    def get_record_by_ref(cls, ref):
        """."""
        from .remote_entities.api import RemoteEntity
        if entity := extracted_data_from_ref(ref, 'record'):
            return entity
        _, _type, _pid = extract_data_from_mef_uri(ref)
        return RemoteEntity.get_entity(_type, _pid)

    @abstractmethod
    def get_authorized_access_point(self, language):
        """Get localized authorized_access_point.

        :param language: language for authorized access point.
        :returns: authorized access point in given language.
        """
        raise NotImplementedError

    @abstractmethod
    def get_links_to_me(self, get_pids=False):
        """Get links to other resources.

        :param get_pids: related resource pids are included into response ;
            otherwise the count of related resources are specified.
        :returns: list of related resource to this entity.
        :rtype: dict.
        """
        document_query = DocumentsSearch().by_entity(self)
        documents = sorted_pids(document_query) if get_pids \
            else document_query.count()
        links = {
            'documents': documents
        }
        return {k: v for k, v in links.items() if v}

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        cannot_delete = {}
        if links := self.get_links_to_me():
            cannot_delete['links'] = links
        return cannot_delete

    @property
    @abstractmethod
    def resource_type(self):
        """Get the entity type."""
        raise NotImplementedError

    @property
    def organisation_pids(self):
        """Get organisation pids related with this entity."""
        search = DocumentsSearch().by_entity(self)[:0]
        agg = A(
            'terms',
            field='organisation_pid',
            min_doc_count=1,
            size=current_app.config
                            .get('RERO_ILS_AGGREGATION_SIZE', {})
                            .get('organisations', 10)
        )
        search.aggs.bucket('organisation', agg)
        results = search.execute()
        return list({
            result.key
            for result in results.aggregations.organisation.buckets
        })

    def documents_pids(
        self, with_subjects=True, with_subjects_imported=True,
        with_genre_forms=True
    ):
        """Get documents pids related to this entity.

        :param with_subjects: is the document `subject` field must be analyzed.
        :param with_subjects_imported: is the document `subject_imported` field
            must be analyzed.
        :param with_genre_forms: is the document `genre_forms` field must be
            analyzed.
        :returns: document pids related to this entity.
        :rtype: list<str>
        """
        search = DocumentsSearch().by_entity(
            self,
            subjects=with_subjects,
            imported_subjects=with_subjects_imported,
            genre_forms=with_genre_forms
        )
        return [hit.pid for hit in search.source('pid').scan()]

    def documents_ids(
        self, with_subjects=True, with_subjects_imported=True,
        with_genre_forms=True
    ):
        """Get document ID's/UUID related to this entity.

        :param with_subjects: is the document `subject` field must be analyzed.
        :param with_subjects_imported: is the document `subject_imported` field
            must be analyzed.
        :param with_genre_forms: is the document `genre_forms` field must be
            analyzed.
        :returns: document ID's/UUID related to this entity.
        :rtype: list<str>
        """
        search = DocumentsSearch().by_entity(
            self,
            subjects=with_subjects,
            imported_subjects=with_subjects_imported,
            genre_forms=with_genre_forms
        ).source(False)
        return [hit.meta.id for hit in search.scan()]
