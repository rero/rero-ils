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

from rero_ils.modules.documents.api import DocumentsSearch


class Entity(ABC):
    """Entity class."""

    @abstractmethod
    def get_authorized_access_point(self, language):
        """Get localized authorized_access_point.

        :param language: language for authorized access point.
        :returns: authorized access point in given language.
        """
        raise NotImplementedError

    @property
    def unique_key(self):
        """Get the unique key.

        As entity subclasses doesn't share pid generation sequence, pid
        overlapping can occur. To prevent this, use `unique_key` to point
        specific entity.

        Example:
            <RemoteEntity#1> => `remote_1`
            <LocalEntity#1> => `local_1`
        """
        return f'{self.resource_type}_{self.pid}'

    def _search_documents(self, with_subjects=True,
                          with_subjects_imported=True):
        """Get search documents."""
        filters = Q('term', contribution__entity__unique_key=self.unique_key)

        if with_subjects:
            filters |= \
                Q('term', subjects__entity__unique_key=self.unique_key)
        if with_subjects_imported:
            filters |= \
                Q('term',
                  subjects_imported__entity__unique_key=self.unique_key)
        return DocumentsSearch().filter(filters)

    def documents_pids(self, with_subjects=True, with_subjects_imported=True):
        """Get documents pids."""
        search = self._search_documents(
            with_subjects=with_subjects,
            with_subjects_imported=with_subjects_imported
        ).source('pid')
        return [hit.pid for hit in search.scan()]

    def documents_ids(self, with_subjects=True, with_subjects_imported=True):
        """Get documents ids."""
        search = self._search_documents(
            with_subjects=with_subjects,
            with_subjects_imported=with_subjects_imported
        ).source()
        return [hit.meta.id for hit in search.scan()]

    @property
    def organisation_pids(self):
        """Get organisations pids."""
        # TODO :: Should be linked also on other fields ?
        #    ex: subjects, genre_form, ...
        #    Seems only use to filer entities by viewcode.
        search = self._search_documents()
        agg = A(
            'terms',
            field='holdings.organisation.organisation_pid',
            min_doc_count=1,
            size=current_app.config
                            .get('RERO_ILS_AGGREGATION_SIZE')
                            .get('organisations')
        )
        search.aggs.bucket('organisation', agg)
        results = search.execute()
        return list({
            result.key
            for result in results.aggregations.organisation.buckets
        })
