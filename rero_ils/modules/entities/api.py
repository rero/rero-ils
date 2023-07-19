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

from elasticsearch_dsl import Q, A
from flask import current_app

from rero_ils.modules.api import IlsRecord
from rero_ils.modules.documents.api import DocumentsSearch


class Entity(IlsRecord, ABC):
    """Entity class."""

    @abstractmethod
    def get_authorized_access_point(self, language):
        """Get localized authorized_access_point.

        :param language: language for authorized access point.
        :returns: authorized access point in given language.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def resource_type(self):
        """Get the entity type."""
        raise NotImplementedError

    @property
    def organisation_pids(self):
        """Get organisations pids."""
        search = self._search_documents()
        agg = A(
            'terms',
            field='holdings.organisation.organisation_pid',
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

    def _search_documents(
        self, with_subjects=True, with_subjects_imported=True,
        with_genre_forms=True
    ):
        """Get ES query to search documents containing this entity.

        :param with_subjects: search also on `subjects` ?
        :param with_subjects_imported: search also on `subject_imported` ?
        :param with_genre_forms: search also on `genreForm` ?
        """
        contribution_key = f'contribution.entity.pids.{self.resource_type}'
        filters = Q('term', **{contribution_key: self.pid})
        if with_subjects:
            search_field = f'subjects.entity.pids.{self.resource_type}'
            filters |= Q('term', **{search_field: self.pid})
        if with_subjects_imported:
            search_field = f'subjects_imported.pids.{self.resource_type}'
            filters |= Q('term', **{search_field: self.pid})
        if with_genre_forms:
            search_field = f'genreForm.entity.pids.{self.resource_type}'
            filters |= Q('term', **{search_field: self.pid})

        return DocumentsSearch().filter(filters)

    def documents_pids(
        self, with_subjects=True, with_subjects_imported=True,
        with_genre_forms=True
    ):
        """Get documents pids."""
        search = self._search_documents(
            with_subjects=with_subjects,
            with_subjects_imported=with_subjects_imported,
            with_genre_forms=with_genre_forms
        ).source('pid')
        return [hit.pid for hit in search.scan()]

    def documents_ids(
        self, with_subjects=True, with_subjects_imported=True,
        with_genre_forms=True
    ):
        """Get documents ids."""
        search = self._search_documents(
            with_subjects=with_subjects,
            with_subjects_imported=with_subjects_imported,
            with_genre_forms=with_genre_forms
        ).source(False)
        return [hit.meta.id for hit in search.scan()]
