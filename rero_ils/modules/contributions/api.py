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

import traceback
from functools import partial

import click
import requests
from elasticsearch_dsl import A
from elasticsearch_dsl.query import Q
from flask import current_app
from invenio_db import db
from requests import codes as requests_codes
from requests.exceptions import RequestException

from .models import ContributionIdentifier, ContributionMetadata, \
    ContributionUpdateStatus
from ..api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from ..documents.api import DocumentsIndexer, DocumentsSearch
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..providers import Provider
from ..utils import sorted_pids
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


class ContributionType:
    """Class holding all availabe contribution types."""

    ORGANISATION = 'bf:Organisation'
    PERSON = 'bf:Person'


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
        contribution = None
        if ref_type == 'mef':
            contribution = cls.get_record_by_pid(ref_pid)
        else:
            if ref_type == 'viaf':
                result = ContributionsSearch().filter(
                    'term', viaf_pid=ref_pid
                ).source('pid').scan()
            else:
                result = ContributionsSearch().filter(
                    {'term': {f'{ref_type}.pid': ref_pid}}
                ).source('pid').scan()
            try:
                pid = next(result).pid
                contribution = cls.get_record_by_pid(pid)
            except StopIteration:
                pass
        return contribution

    @classmethod
    def get_record_by_ref(cls, ref):
        """Get a record from DB.

        If the record dos not exist get it from MEF and create it.
        """
        online = False
        ref_split = ref.split('/')
        ref_type = ref_split[-2]
        ref_pid = ref_split[-1]
        db.session.begin_nested()
        contribution = cls.get_contribution(ref_type, ref_pid)
        if not contribution:
            # We dit not find the record in DB get it from MEF and create it.
            metadata = None
            try:
                data = cls._get_mef_data_by_type(ref_pid, ref_type)
                metadata = data['metadata']
                # Register MEF contribution
                metadata.pop('$schema', None)
                # we have to commit because create
                # uses db.session.begin_nested
                contribution = cls.create(metadata, dbcommit=True,
                                          reindex=True)
                online = True
            except Exception as err:
                db.session.rollback()
                if metadata:
                    contribution = cls.get_record_by_pid(metadata.get('pid'))
                if not contribution:
                    current_app.logger.error(
                        f'Get MEF record: {ref_type}:{ref_pid} >>{err}<<'
                    )
                    # import traceback
                    # traceback.print_exc()
                return contribution, online
        db.session.commit()
        return contribution, online

    def dumps_for_document(self):
        """Transform the record into document contribution format."""
        return self._get_contribution_for_document()

    @classmethod
    def _get_mef_data_by_type(cls, pid, pid_type, verbose=False):
        """Request MEF REST API in JSON format."""
        url = current_app.config.get('RERO_ILS_MEF_AGENTS_URL')
        if pid_type == 'mef':
            mef_url = f'{url}/mef/?q=pid:"{pid}"'
        else:
            if pid_type == 'viaf':
                mef_url = f'{url}/mef/?q=viaf_pid:{pid}'
            else:
                mef_url = f'{url}/mef/?q={pid_type}.pid:{pid}'
        request = requests.get(url=mef_url, params=dict(resolve=1, sources=1))
        status = request.status_code
        if request.status_code == requests_codes.ok:
            try:
                data = request.json().get('hits', {}).get('hits', [None])
                if len(data) > 1:
                    current_app.logger.warning(
                        f'MEF multiple results found: {mef_url}')
                return data[0]
            except Exception as err:
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
                value = self[source].get(key, default)
                if value:
                    return value

    def _get_mef_localized_value(self, key, language):
        """Get the 1st localized value for given key among MEF source list."""
        order = current_app.config.get(
            'RERO_ILS_CONTRIBUTIONS_LABEL_ORDER', [])
        source_order = order.get(language, order.get(order['fallback'], []))
        for source in source_order:
            value = self.get(source, {}).get(key, None)
            if value:
                return value
        return self.get(key, None)

    def _get_contribution_for_document(self):
        """Get contribution for document."""
        agent = {
            'pid': self.pid
        }
        for agency in current_app.config['RERO_ILS_CONTRIBUTIONS_SOURCES']:
            if self.get(agency):
                agent['type'] = self[agency]['bf:Agent']
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
        organisations = set()
        search = DocumentsSearch().filter(
            'term', contribution__agent__pid=self.pid)
        size = current_app.config.get(
            'RERO_ILS_AGGREGATION_SIZE'
        ).get('organisations')
        agg = A('terms',
                field='holdings.organisation.organisation_pid', size=size)
        search.aggs.bucket('organisation', agg)
        results = search.execute()
        for result in results.aggregations.organisation.buckets:
            if result.doc_count:
                organisations.add(result.key)
        return list(organisations)

    def get_authorized_access_point(self, language):
        """Get localized authorized_access_point.

        :param language: language for authorized access point.
        :returns: authorized access point in given lamguage.
        """
        return self._get_mef_localized_value(
            key='authorized_access_point',
            language=language
        )

    def md5_changed(self, new_data):
        """Test if md5 changed in idref, gnd or rero.

        :param new_data: new data to test with.
        :return: True if different
        """
        md5s = {}
        old_data = dict(self)
        new_data = dict(new_data)
        sources = current_app.config.get('RERO_ILS_CONTRIBUTIONS_SOURCES', [])
        for source in sources:
            old_md5 = old_data.get(source, {}).get('md5')
            new_md5 = new_data.get(source, {}).get('md5')
            if old_md5 != new_md5:
                return True
        return False

    def update_online(self, dbcommit=False, reindex=False, replace=True,
                      debug=False):
        """Update record online.

        :param reindex: reindex record by record
        :param dbcommit: commit record to database
        :param replace: replace contribution
        :param debug: debug prints
        :return: updated record status and updated record
        """
        msg = ''
        doc_count = 0
        status = ContributionUpdateStatus.UP_TO_DATE
        try:
            data = self._get_mef_data_by_type(self.pid, 'mef').get('metadata')
            data['$schema'] = self['$schema']
            if self.md5_changed(data):
                status = ContributionUpdateStatus.UPDATED
                self.replace(data=data, dbcommit=dbcommit, reindex=reindex)
                if reindex:
                    doc_count = self.reindex_documents()
        except Exception as err:
            if debug:
                traceback.print_exc()
            # Try to find the new contribution.
            source, data = self.find_new_contribution()
            if source and data:
                status = ContributionUpdateStatus.REPLACED
                new_pid = data['pid']
                if dbcommit and replace:
                    _, online = Contribution.get_record_by_ref(
                        f'/mef/{new_pid}')
                    msg = f'new contribution: {new_pid:>10} online:{online}'
                    doc_count = self.replace_ref_in_documents(
                        source=source, new_data=data, debug=debug)
                    # delete old contribution
                    self.delete(dbcommit=dbcommit, delindex=dbcommit)
                else:
                    msg = f'new contribution: {new_pid:>10}'
            else:
                status = ContributionUpdateStatus.ERROR
                msg = str(err)
        return self, status, doc_count, msg

    def query_documents(self):
        """Elastic Search query to find all documents attached."""
        return DocumentsSearch().filter(
            Q('bool', should=[
                Q('term', contribution__agent__pid=self.pid),
                Q('term', subjects__pid=self.pid)
            ])
        )

    def get_links_to_me(self, get_pids=False):
        """Record links.

        :param get_pids: if True list of linked pids
                         if False count of linked records
        """
        links = {}
        query = self.query_documents()
        if get_pids:
            documents = sorted_pids(query)
        else:
            documents = query.count()
        if documents:
            links['documents'] = documents
        return links

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        cannot_delete = {}
        links = self.get_links_to_me()
        if links:
            cannot_delete['links'] = links
        return cannot_delete

    def reindex_documents(self):
        """Reindex all attached documents."""
        query = self.query_documents()
        ids = [hit.meta.id for hit in query.source('pid').scan()]
        indexer = DocumentsIndexer()
        indexer.bulk_index(ids)
        indexer.process_bulk_queue()
        return query.count()

    def is_deleted(self):
        """Test has deleted."""
        deleted = {}
        if self.get('deleted'):
            deleted['mef'] = self.get('deleted')
        sources = current_app.config.get('RERO_ILS_CONTRIBUTIONS_SOURCES', [])
        for source in sources:
            deleted_data = self.get(source, {}).get('deleted')
            if deleted_data:
                deleted[source] = deleted_data
        return deleted

    def find_new_contribution(self):
        """Find new contribution."""
        sources = current_app.config.get('RERO_ILS_CONTRIBUTIONS_SOURCES', [])
        for source in sources:
            pid = self.get(source, {}).get('pid')
            if pid:
                try:
                    data = Contribution._get_mef_data_by_type(
                        pid, source)['metadata']
                    return source, data
                except Exception:
                    pass
        return None, None

    def replace_ref_in_documents(self, source, new_data, debug=False):
        """Replace $ref with new contribution.

        :param source: source to replace.
        :param new_data: New data to use.
        """
        from ..documents.api import Document

        def get_source_and_pid(agent):
            """Get source and pid."""
            ref = agent.get('$ref')
            if agent.get('$ref'):
                parts = ref.split('/')
                return parts[-2], parts[-1]
            return None, None

        def replace_pid_in_ref(ref, new_pid):
            """Replace pid in ref."""
            parts = ref.split('/')
            parts[-1] = new_pid
            return '/'.join(parts)

        count = 0
        try:
            query = self.query_documents()
            for hit in query.source('pid').scan():
                doc = Document.get_record_by_pid(hit.pid)
                changed = False
                if debug:
                    click.echo(f'  doc: {doc.pid}')
                for contribution in doc.get('contribution', []):
                    source, pid = get_source_and_pid(contribution['agent'])
                    if source:
                        if pid == new_data.get(source, {}).get('pid'):
                            ref = contribution['agent'].get('$ref')
                            if ref:
                                new_ref = replace_pid_in_ref(
                                    ref, new_data.get(source, {}).get('pid'))
                                if debug:
                                    click.echo(f'    contribution: {ref} '
                                               f'new: {new_ref}')
                                contribution['agent']['$ref'] = new_ref
                                changed = True
                for subject in doc.get('subjects', []):
                    source, agent_pid = get_source_and_pid(subject)
                    if source:
                        if agent_pid == new_data.get(source, {}).get('pid'):
                            ref = subject.get('$ref')
                            if ref:
                                new_ref = replace_pid_in_ref(
                                    ref, new_data.get(source, {}).get('pid'))
                                if debug:
                                    click.echo(f'    subject      : {ref} '
                                               f'new: {new_ref}')
                                subject['$ref'] = new_ref
                                changed = True
                if changed:
                    count += 1
                    doc.update(data=doc, dbcommit=True, reindex=True)
        except Exception as err:
            # import traceback
            # traceback.print_exc()
            return -1
        return count


class ContributionsIndexer(IlsRecordsIndexer):
    """Contribution indexing class."""

    record_cls = Contribution

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='cont')
