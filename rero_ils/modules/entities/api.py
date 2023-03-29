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

import contextlib
from functools import partial

import requests
from elasticsearch_dsl import A
from elasticsearch_dsl.query import Q
from flask import current_app
from invenio_db import db
from requests import codes as requests_codes
from requests.exceptions import RequestException

from rero_ils.modules.api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from rero_ils.modules.documents.api import DocumentsIndexer, DocumentsSearch
from rero_ils.modules.fetchers import id_fetcher
from rero_ils.modules.minters import id_minter
from rero_ils.modules.providers import Provider
from rero_ils.utils import get_i18n_supported_languages

from .models import EntityIdentifier, EntityMetadata, EntityUpdateAction

# provider
EntityProvider = type(
    'EntityProvider',
    (Provider,),
    dict(identifier=EntityIdentifier, pid_type='ent')
)
# minter
entity_id_minter = partial(id_minter, provider=EntityProvider)
# fetcher
entity_id_fetcher = partial(id_fetcher, provider=EntityProvider)


class EntitiesSearch(IlsRecordsSearch):
    """Mef contribution search."""

    class Meta:
        """Meta class."""

        index = 'entities'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class Entity(IlsRecord):
    """Mef contribution class."""

    minter = entity_id_minter
    fetcher = entity_id_fetcher
    provider = EntityProvider
    model_cls = EntityMetadata

    @classmethod
    def get_entity(cls, ref_type, ref_pid):
        """Get contribution."""
        if ref_type == 'mef':
            return cls.get_record_by_pid(ref_pid)

        es_filter = Q('term', **{f'{ref_type}.pid': ref_pid})
        if ref_type == 'viaf':
            es_filter = Q('term', viaf_pid=ref_pid)

        # in case of multiple results get the more recent
        query = EntitiesSearch() \
            .params(preserve_order=True) \
            .sort({'_created': {'order': 'desc'}})\
            .filter(es_filter)

        with contextlib.suppress(StopIteration):
            pid = next(query.source('pid').scan()).pid
            return cls.get_record_by_pid(pid)

    @classmethod
    def get_type_and_pid_from_ref(cls, ref):
        """Extract agent type and pid form the MEF URL.

        :params ref: MEF URI.
        :returns: the ref type such as idref, and the pid value.
        """
        ref_split = ref.split('/')
        return ref_split[-2], ref_split[-1]

    @classmethod
    def get_record_by_ref(cls, ref):
        """Get a record from DB.

        If the record dos not exist get it from MEF and create it.

        :param ref: MEF URI
        :returns: the corresponding `Entity` class instance
        """
        online = False
        ref_type, ref_pid = cls.get_type_and_pid_from_ref(ref)
        contribution = cls.get_entity(ref_type, ref_pid)
        if not contribution:
            # We dit not find the record in DB get it from MEF and create it.
            nested = db.session.begin_nested()
            try:
                if not (data := cls._get_mef_data_by_type(
                    pid_type=ref_type,
                    pid=ref_pid
                )):
                    raise Exception('NO DATA')
                # Try to get the contribution from DB maybe it was not indexed.
                if contribution := Contribution.get_record_by_pid(
                    data['pid']
                ):
                    contribution = contribution.replace(
                        data=data,
                        dbcommit=False,
                        reindex=False
                    )
                else:
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
    def remove_schema(cls, data):
        """Removes in place the $schema values.

        Removes the root and the sources $schema.

        :param data - dict: the data representation of the current
                            contribution.
        :returns: the modified data.
        :rtype: dict.
        """
        data.pop('$schema', None)
        for source in current_app.config.get('RERO_ILS_AGENTS_SOURCES', []):
            if source in data:
                data[source].pop('$schema', None)
        return data

    @classmethod
    def _get_mef_data_by_type(cls, pid_type, pid, verbose=False,
                              with_deleted=True, resolve=True, sources=True):
        """Request MEF REST API in JSON format.

        :param language: language for authorized access point.
        :returns: authorized access point in given language.
        """
        url = current_app.config.get('RERO_ILS_MEF_AGENTS_URL')
        if pid_type == 'mef':
            mef_url = f'{url}/mef/?q=pid:"{pid}"'
        elif pid_type == 'viaf':
            mef_url = f'{url}/mef/?q=viaf_pid:"{pid}"'
        else:
            mef_url = f'{url}/mef/latest/{pid_type}:{pid}'
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
                json_data = request.json()
                if 'hits' in json_data:
                    # we got an ES response
                    data = request.json().get('hits', {}).get(
                        'hits', [None])[0].get('metadata', {})
                else:
                    # we got an DB response
                    data = json_data
                    data.pop('_created', None)
                    data.pop('_updated', None)
                return cls.remove_schema(data)
            except Exception as err:
                msg = f'MEF resolver no metadata: {mef_url} {err}'
                if verbose:
                    current_app.logger.warning(msg)
                raise ValueError(msg)
        else:
            msg = f'Mef http error: {status} {mef_url}'
            if verbose:
                current_app.logger.error(msg)
            raise RequestException(msg)

    def _get_mef_localized_value(self, key, language):
        """Get the 1st localized value for given key among MEF source list."""
        order = current_app.config.get('RERO_ILS_AGENTS_LABEL_ORDER', [])
        source_order = order.get(language, order.get(order['fallback'], []))
        for source in source_order:
            if value := self.get(source, {}).get(key, None):
                return value
        return self.get(key, None)

    def dumps_for_document(self):
        """Transform the record into document contribution format."""
        agent = {'pid': self.pid}
        for agency in current_app.config['RERO_ILS_AGENTS_SOURCES']:
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
        search = DocumentsSearch()\
            .filter('term', contribution__entity__pid=self.pid)
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
        filters = Q('term', contribution__entity__pid=self.pid)
        if with_subjects:
            filters |= \
                Q('term', subjects__pid=self.pid) & \
                Q('terms', subjects__type=['bf:Person', 'bf:Organisation'])
        if with_subjects_imported:
            filters |= \
                Q('term', subjects_imported__pid=self.pid) & \
                Q('terms', subjects__type=['bf:Person', 'bf:Organisation'])
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
        ).source('pid')
        return [hit.meta.id for hit in search.scan()]

    def update_online(
        self, dbcommit=False, reindex=False, verbose=False,
        reindex_doc=True
    ):
        """Update record online.

        :param reindex: reindex record by record
        :param dbcommit: commit record to database
        :param verbose: verbose print
        :param reindex_doc: is the related document should be reindex ?
        :return: updated record status and updated record
        """
        action = EntityUpdateAction.UPTODATE
        pid = self.get('pid')
        try:
            if data := self._get_mef_data_by_type(
                    pid_type='mef', pid=pid, verbose=verbose):
                data['$schema'] = self['$schema']
                if data.get('deleted'):
                    current_app.logger.warning(
                        f'UPDATE ONLINE {pid}: was deleted')
                    action = EntityUpdateAction.ERROR
                elif not data.get('sources'):
                    current_app.logger.warning(
                        f'UPDATE ONLINE {pid}: has no sources')
                    action = EntityUpdateAction.ERROR
                elif not data.get('type'):
                    current_app.logger.warning(
                        f'UPDATE ONLINE {pid}: has no type')
                    action = EntityUpdateAction.ERROR
                elif dict(self) != data:
                    action = EntityUpdateAction.REPLACE
                    self.replace(data=data, dbcommit=dbcommit, reindex=reindex)
                    if reindex and reindex_doc:
                        indexer = DocumentsIndexer()
                        indexer.bulk_index(self.documents_ids())
                        indexer.process_bulk_queue()
        except Exception as err:
            action = EntityUpdateAction.ERROR
            current_app.logger.warning(f'UPDATE ONLINE {pid}: {err}')
        return action, self

    def source_pids(self):
        """Get agents pids."""
        sources = current_app.config.get('RERO_ILS_AGENTS_SOURCES', [])
        return {
            source: self[source]['pid']
            for source in sources
            if source in self
        }


class EntitiesIndexer(IlsRecordsIndexer):
    """Entity indexing class."""

    record_cls = Entity

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='ent')