# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
# Copyright (C) 2020 UCLouvain
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

"""API for manipulating documents."""

import contextlib
from functools import partial

import requests
from elasticsearch_dsl import A
from elasticsearch_dsl.query import Q
from flask import current_app
from invenio_db import db
from requests import codes as requests_codes
from requests.exceptions import RequestException

from .models import ContributionIdentifier, ContributionMetadata, \
    ContributionUpdateAction
from ..api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from ..documents.api import DocumentsIndexer, DocumentsSearch
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..providers import Provider
from ...utils import get_i18n_supported_languages

# provider
ContributionProvider = type(
    'ContributionProvider',
    (Provider,),
    dict(identifier=ContributionIdentifier, pid_type='cont')
)
# minter
contribution_id_minter = partial(id_minter, provider=ContributionProvider)
# fetcher
contribution_id_fetcher = partial(id_fetcher, provider=ContributionProvider)


class ContributionsSearch(IlsRecordsSearch):
    """Mef contribution search."""

    class Meta():
        """Meta class."""

        index = 'contributions'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class Contribution(IlsRecord):
    """Mef contribution class."""

    minter = contribution_id_minter
    fetcher = contribution_id_fetcher
    provider = ContributionProvider
    model_cls = ContributionMetadata

    @classmethod
    def get_contribution(cls, ref_type, ref_pid):
        """Get contribution."""
        if ref_type == 'mef':
            return cls.get_record_by_pid(ref_pid)
        if ref_type == 'viaf':
            query = ContributionsSearch() \
                .filter('term', viaf_pid=ref_pid)
        else:
            query = ContributionsSearch() \
                .filter({'term': {f'{ref_type}.pid': ref_pid}})
        with contextlib.suppress(StopIteration):
            pid = next(query.source('pid').scan()).pid
            return cls.get_record_by_pid(pid)

    @classmethod
    def get_type_and_pid_from_ref(cls, ref):
        """Extract agent type and pid form the MEF URL.

        :params ref: MEF URL.
        :returns: the ref type such as idref, and the pid value.
        """
        ref_split = ref.split('/')
        ref_type = ref_split[-2]
        ref_pid = ref_split[-1]
        return ref_type, ref_pid

    @classmethod
    def get_record_by_ref(cls, ref):
        """Get a record from DB.

        If the record dos not exist get it from MEF and create it.
        """
        online = False
        ref_type, ref_pid = cls.get_type_and_pid_from_ref(ref)
        contribution = cls.get_contribution(ref_type, ref_pid)
        if not contribution:
            # We dit not find the record in DB get it from MEF and create it.
            nested = db.session.begin_nested()
            try:
                data = cls._get_mef_data_by_type(
                    pid=ref_pid,
                    pid_type=ref_type,
                )
                # TODO: create or update
                contribution = cls.create(
                    data=data,
                    dbcommit=False,
                    reindex=False
                )
                online = True
                nested.commit()
                # TODO: reindex in the document indexing
                contribution.reindex()
            except Exception as err:
                nested.rollback()
                current_app.logger.error(
                    f'Get MEF record: {ref_type}:{ref_pid} >>{err}<<'
                )
                contribution = None
        return contribution, online

    @classmethod
    def _get_mef_data_by_type(cls, pid, pid_type, verbose=False,
                              with_deleted=True, resolve=True, sources=True):
        """Request MEF REST API in JSON format.

        :param language: language for authorized access point.
        :returns: authorized access point in given language.
        """
        url = current_app.config.get('RERO_ILS_MEF_AGENTS_URL')
        if pid_type == 'mef':
            mef_url = f'{url}/mef/?q=pid:"{pid}"'
        else:
            if pid_type == 'viaf':
                mef_url = f'{url}/mef/?q=viaf_pid:"{pid}"'
            else:
                mef_url = f'{url}/mef/?q={pid_type}.pid:"{pid}"'
        request = requests.get(
            url=mef_url,
            params=dict(
                with_deleted=int(with_deleted),
                resolve=int(resolve),
                sources=int(sources)
            )
        )
        status = request.status_code
        if status == requests_codes.ok:
            try:
                data = request.json().get('hits', {}).get('hits', [None])[0]
                metadata = data['metadata']
                metadata.pop('$schema', None)
                sources = current_app.config.get(
                    'RERO_ILS_CONTRIBUTIONS_SOURCES', [])
                for source in sources:
                    if source in metadata:
                        metadata[source].pop('$schema', None)
                return metadata
            except Exception:
                msg = f'MEF resolver no metadata: {mef_url}'
                if verbose:
                    current_app.logger.warning(msg)
                raise ValueError(msg)
        else:
            msg = f'Mef http error: {status} {mef_url}'
            if verbose:
                current_app.logger.error(msg)
            raise RequestException(msg)

    def get_first(self, key, default=None):
        """Get the first value for given key among MEF source list."""
        value = None
        sources = current_app.config.get('RERO_ILS_CONTRIBUTIONS_SOURCES', [])
        for source in sources:
            if source in self:
                if value := self[source].get(key, default):
                    return value

    def _get_mef_localized_value(self, key, language):
        """Get the 1st localized value for given key among MEF source list."""
        order = current_app.config.get(
            'RERO_ILS_CONTRIBUTIONS_LABEL_ORDER', [])
        source_order = order.get(language, order.get(order['fallback'], []))
        for source in source_order:
            if value := self.get(source, {}).get(key, None):
                return value
        return self.get(key, None)

    def dumps_for_document(self):
        """Transform the record into document contribution format."""
        agent = {'pid': self.pid}
        for agency in current_app.config['RERO_ILS_CONTRIBUTIONS_SOURCES']:
            if self.get(agency):
                agent['type'] = self[agency]['bf:Agent']
                agent[f'id_{agency}'] = self[agency]['pid']
        for language in get_i18n_supported_languages():
            value = self._get_mef_localized_value(
                'authorized_access_point', language)
            agent[f'authorized_access_point_{language}'] = value
        variant_access_points = []
        parallel_access_points = []
        for source in self.get('sources'):
            variant_access_points += self[source].get(
                'variant_access_point', [])
            parallel_access_points += self[source].get(
                'parallel_access_point', [])
        if variant_access_points:
            agent['variant_access_point'] = variant_access_points
        if parallel_access_points:
            agent['parallel_access_point'] = parallel_access_points
        return agent

    @property
    def organisation_pids(self):
        """Get organisations pids."""
        search = DocumentsSearch().filter(
            'term', contribution__agent__pid=self.pid)
        size = current_app.config.get(
            'RERO_ILS_AGGREGATION_SIZE'
        ).get('organisations')
        agg = A('terms',
                field='holdings.organisation.organisation_pid', size=size)
        search.aggs.bucket('organisation', agg)
        results = search.execute()
        organisations = {
            result.key for result in results.aggregations.organisation.buckets
            if result.doc_count
        }
        return list(organisations)

    def get_authorized_access_point(self, language):
        """Get localized authorized_access_point.

        :param language: language for authorized access point.
        :returns: authorized access point in given language.
        """
        return self._get_mef_localized_value(
            key='authorized_access_point',
            language=language
        )

    def _search_documents(self, with_subjects=True,
                          with_subjects_imported=True):
        """Get documents pids."""
        search_filters = Q("term", contribution__agent__pid=self.pid)
        if with_subjects:
            subject_filters = Q("term", subjects__pid=self.pid) & \
                Q("terms", subjects__type=['bf:Person', 'bf:Organisation'])
            search_filters = search_filters | subject_filters
        if with_subjects_imported:
            subject_filters = Q("term", subjects_imported__pid=self.pid) & \
                Q("terms", subjects__type=['bf:Person', 'bf:Organisation'])
            search_filters = search_filters | subject_filters

        return DocumentsSearch() \
            .query('bool', filter=[search_filters])

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
        ).source('pid')
        return [hit.meta.id for hit in search.scan()]

    def update_online(self, dbcommit=False, reindex=False, verbose=False):
        """Update record online.

        :param reindex: reindex record by record
        :param dbcommit: commit record to database
        :param verbose: verbose print
        :return: updated record status and updated record
        """
        action = ContributionUpdateAction.UPTODATE
        pid = self.get('pid')
        try:
            if data := self._get_mef_data_by_type(
                    pid=pid, pid_type='mef', verbose=verbose):
                data['$schema'] = self['$schema']
                if data.get('deleted'):
                    current_app.logger.warning(
                        f'UPDATE ONLINE {pid}: was deleted')
                    action = ContributionUpdateAction.ERROR
                elif not data.get('sources'):
                    current_app.logger.warning(
                        f'UPDATE ONLINE {pid}: has no sources')
                    action = ContributionUpdateAction.ERROR
                elif not data.get('type'):
                    current_app.logger.warning(
                        f'UPDATE ONLINE {pid}: has no type')
                    action = ContributionUpdateAction.ERROR
                elif dict(self) != data:
                    action = ContributionUpdateAction.REPLACE
                    self.replace(data=data, dbcommit=dbcommit, reindex=reindex)
                    if reindex:
                        indexer = DocumentsIndexer()
                        indexer.bulk_index(self.documents_ids())
                        indexer.process_bulk_queue()
        except Exception as err:
            action = ContributionUpdateAction.ERROR
            current_app.logger.warning(f'UPDATE ONLINE {pid}: {err}')
        return action, self

    def source_pids(self):
        """Get agents pids."""
        sources = current_app.config.get('RERO_ILS_CONTRIBUTIONS_SOURCES', [])
        return {
            source: self[source]['pid'] for source in sources
            if source in self}


class ContributionsIndexer(IlsRecordsIndexer):
    """Contribution indexing class."""

    record_cls = Contribution

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='cont')
