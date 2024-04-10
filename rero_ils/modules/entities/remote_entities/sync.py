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

"""API for manipulating documents."""

import sys
from copy import deepcopy
from datetime import datetime
from itertools import islice

import requests
from deepdiff import DeepDiff
from invenio_db import db

from rero_ils.modules.commons.exceptions import RecordNotFound
from rero_ils.modules.documents.api import Document
from rero_ils.modules.utils import get_mef_url, get_timestamp, \
    requests_retry_session, set_timestamp

from .api import RemoteEntitiesSearch, RemoteEntity
from ..logger import create_logger


class SyncEntity:
    """Entity MEF synchronization."""

    def __init__(self, dry_run=False, verbose=False, log_dir=None,
                 from_last_date=False):
        """Constructor.

        :param dry_run: bool - if true the data are not modified
        :param verbose: bool or integer - verbose level
        :param log_dir: string - path to put the logs
        :param from_last_date: boolean - if True try to consider entity
            modified after the last run date time
        """
        self.dry_run = dry_run
        self.verbose = verbose
        self.from_date = None
        self.start_timestamp = None
        self.logger = create_logger(
            name='SyncEntity',
            file_name='sync_mef.log',
            log_dir=log_dir,
            verbose=verbose
        )
        if from_last_date:
            self._get_last_date()

    def _get_last_date(self):
        """Get the date of the last execution of the synchronization."""
        data = get_timestamp('sync_entities')
        if data and data.get('start_timestamp'):
            self.from_date = data.get('start_timestamp')

    def _entity_are_different(self, entity1, entity2):
        """Check if two entities are different.

        The comparison is done only on the common fields.

        :param entity1: a dict representing an entity to compare.
        :param entity2: a dict representing an entity to compare.
        :returns: True if they are different.
        """

        def remove_fields(entity):
            """Remove specific fields."""
            fields_to_remove = [
                '$schema', 'organisation', '_created', '_updated'
            ]
            for field in fields_to_remove:
                entity.pop(field, None)

            fields_to_remove = ['$schema', 'md5']
            for source in entity['sources']:
                for field in fields_to_remove:
                    entity[source].pop(field, None)
            return entity

        diff = DeepDiff(
            remove_fields(deepcopy(entity1)),
            remove_fields(deepcopy(entity2)),
            ignore_order=True)
        if diff:
            self.logger.debug(
                f"Entity differs: {entity1['pid']}, {entity2['pid']}",
                diff)
            return True
        return False

    def _get_latest(self, entity_type, source, pid):
        """Query the MEF server to retrieve the last MEF for a given entity id.

        :param entity_type: (string) the entity type such as
        `agents`, `concepts`
        :param source: (string) the entity source such as `idref`, `gnd`
        :param pid: (string) the entity identifier.
        :returns: dictionary representing the MEF record.
        :rtype: dictionary.
        """
        if not (base_url := get_mef_url(entity_type)):
            msg = f'Unable to find MEF base url for {entity_type}'
            raise KeyError(msg)
        url = f'{base_url}/mef/latest/{source}:{pid}'
        res = requests_retry_session().get(url)
        if res.status_code == requests.codes.ok:
            return res.json()
        self.logger.debug(f'Problem get {url}: {res.status_code}')
        return {}

    def _update_entities_in_document(self, doc_pid, pids_to_replace):
        """Updates the contribution and subjects in document.

        :param doc_pid: (string) document pid
        :param pids_to_replace: (dict) the list of object where replace the
            entities. Dictionary keys are `source` ; dictionary values are
            tuple of (old_entity_pid, new_entity_pid)
            >> {'gnd': ('entity_old1', 'entity_new1')}
        """
        # get the document from the DB
        doc = Document.get_record_by_pid(doc_pid)

        # get all entities from the document over all entity fields:
        # contribution and subjects
        remote_entities = []
        for field in ['contribution', 'subjects', 'genreForm']:
            remote_entities += [
                entity['entity']
                for entity in doc.get(field, [])
                if entity.get('entity', {}).get('$ref')
            ]
        if not remote_entities:
            self.logger.debug(f'No entity to update for document {doc.pid}')

        # update the $ref entity URL and MEF pid
        for mef_url, (old_pid, new_pid) in pids_to_replace.items():
            old_entity_url = f'{mef_url}/{old_pid}'
            new_entity_url = f'{mef_url}/{new_pid}'
            entities_to_update = filter(
                lambda c: c.get('$ref') == old_entity_url, remote_entities)
            for entity in entities_to_update:
                if old_entity_url != new_entity_url:
                    self.logger.info(
                        f'Entitiy URL changed from {old_entity_url} to '
                        f'{new_entity_url} for document {doc.pid}')
                # update the entity URL
                entity['$ref'] = new_entity_url
        # in any case we update the doc as the mef pid can be changed
        if not self.dry_run:
            doc.replace(doc, dbcommit=True, reindex=True)

    def get_entities_pids(self, query='*', from_date=None):
        """Get contributions identifiers.

        :param query: (string) a query to select the MEF record to be updated.
        :param from_date: (string) only the MEF records updated on the MEF
            server after the given date will be considered.
        :returns: the list of the contribution identifiers.
        :rtype: list of strings.
        """
        es_query = RemoteEntitiesSearch().filter('query_string', query=query)
        total = es_query.count()
        if not from_date and self.from_date:
            from_date = self.from_date
        if from_date:
            self.logger.info(f'Get records updated after: {from_date}')

        def get_mef_pids(es_query, chunk_size=1000):
            """Get the identifiers from elasticsearch.

            :param es_query: (string) the elasticsearch query to limit the
                results
            :param chunk_size: (integer) the maximum number of pid per chunk
            :returns: iterator over all pids

            The scroll is done using the slice scroll feature:
            https://www.elastic.co/guide/en/elasticsearch/reference/8.5/paginate-search-results.html#slice-scroll
            """
            self.logger.info(f'Processing: {total} MEF records')
            if total > 2*chunk_size:
                n_part = int(total/chunk_size)
                for i in range(n_part):
                    # processing the slice should be faster than 30m
                    for hit in es_query.extra(
                        slice={"id": i, "max": n_part}).params(
                            scroll='30m').source('pid').scan():
                        yield hit.pid
            # no need to slice as the part is smaller than the number
            # of results
            # the results can be in memory as it is small
            else:
                for hit in list(es_query.params(scroll='30m').scan()):
                    yield hit.pid

        # ask the MEF server to know which MEF pids has been updated
        # from a given date
        if from_date:
            def get_updated_mef(pids, chunk_size):
                """Ask the MEF server using chunks.

                :param pids - list of string: a list of MEF pids.
                :param chunk_size - integer: the chunk size
                """
                # MEF urls for updated pids
                urls = [
                    f'{get_mef_url("agents")}/mef/updated',
                    f'{get_mef_url("concepts")}/mef/updated'
                ]
                # number of provided updated MEF pids
                n_provided = 0
                try:
                    for url in urls:
                        while chunk := list(islice(iter(pids), chunk_size)):
                            # ask the mef server to return only the updated
                            # pids form a given date
                            res = requests_retry_session().post(
                                url,
                                json=dict(
                                    from_date=from_date.strftime("%Y-%m-%d"),
                                    pids=chunk
                                )
                            )
                            if res.status_code != 200:
                                requests.ConnectionError(
                                    "Expected status code 200, but got "
                                    f"{res.status_code} {url}"
                                )
                            for hit in res.json():
                                n_provided += 1
                                yield hit.get('pid')
                finally:
                    self.logger.info(f'Processed {n_provided} records.')
            if total:
                return get_updated_mef(
                    pids=get_mef_pids(es_query),
                    chunk_size=5000
                ), total
            else:
                return [], 0
        # considers all MEF pids
        else:
            return get_mef_pids(es_query), total

    def sync_record(self, pid):
        """Sync a MEF record.

        :param pid: (string) the MEF identifier.
        :returns: the number of updated document, true if the MEF record
            has been update, true if an error occurs.
        :rtype: integer, boolean, x.
        """
        # close db session to prevent psycopg2.OperationalError.
        # a new session will be open automatically.
        db.session.close()
        doc_updated = set()
        updated = error = False
        try:
            if not (entity := RemoteEntity.get_record_by_pid(pid)):
                raise RecordNotFound(RemoteEntity, pid)

            self.logger.debug(f'Processing {entity["type"]} MEF(pid: {pid})')
            # iterate over all entity sources: rero, gnd, idref
            pids_to_replace = {}
            for source in entity['sources']:
                mef = self._get_latest(
                    entity_type=entity.type,
                    source=source,
                    pid=entity[source]["pid"]
                )
                # MEF sever failed to retrieve the latest MEF record
                # for the given entity
                if not (mef_pid := mef.get('pid')):
                    raise Exception(
                        f'Error cannot get latest for '
                        f'{entity["type"]} {source}:{entity[source]["pid"]}')

                old_entity_pid = entity[source]['pid']
                new_entity_pid = mef[source]['pid']
                new_mef_pid = mef_pid
                old_mef_pid = entity.pid
                if old_entity_pid != new_entity_pid:
                    mef_url = f'{get_mef_url(entity.type)}/{source}'
                    pids_to_replace[mef_url] = (old_entity_pid, new_entity_pid)

                # can be mef pid, source pid or metadata
                if self._entity_are_different(dict(entity), mef):
                    # need a copy as we want to keep the MEF record
                    # untouched for the next entity
                    new_mef_data = deepcopy(mef)
                    fields_to_remove = ['$schema', '_created', '_updated']
                    for field in fields_to_remove:
                        new_mef_data.pop(field, None)

                    if old_mef_pid != new_mef_pid:
                        self.logger.info(
                            f'MEF pid has changed from {entity.type} '
                            f'{old_mef_pid} to {new_mef_pid} '
                            f'for {source} (pid:{old_entity_pid})'
                        )
                        if RemoteEntity.get_record_by_pid(new_mef_pid):
                            # update the new MEF - recursion
                            self.logger.info(
                                f'{entity["type"]} MEF(pid: {entity.pid}) '
                                f'recursion with (pid:{new_mef_pid})')
                            new_doc_updated, new_updated, new_error = \
                                self.sync_record(new_mef_pid)
                            # TODO: find a better way
                            doc_updated.update(new_doc_updated)
                            updated = updated or new_updated
                            error = error or new_error
                        else:
                            # if the MEF record does not exist create it
                            if not self.dry_run:
                                RemoteEntity.create(
                                    data=new_mef_data,
                                    dbcommit=True,
                                    reindex=True
                                )
                                RemoteEntitiesSearch.flush_and_refresh()
                            self.logger.info(
                                f'Create a new MEF {entity["type"]} '
                                f'record(pid: {new_mef_pid})')
                    # something changed, update the content
                    self.logger.info(
                        f'MEF {entity["type"]} record(pid: {entity.pid}) '
                        'content has been updated')
                    if not self.dry_run:
                        if old_mef_pid == new_mef_pid:
                            RemoteEntity.get_record(entity.id).replace(
                                new_mef_data, dbcommit=True, reindex=True)
                        else:
                            # as we have only the last mef but not the old one
                            # we need get it from the MEF server
                            # this is important as it can still be used by
                            # other entities
                            RemoteEntity.get_record_by_pid(pid)\
                                .update_online(dbcommit=True, reindex=True)
                    updated = True

            if updated:
                # need to update each documents
                doc_pids = entity.documents_pids()
                self.logger.info(
                    f'MEF {entity["type"]} record(pid: {entity.pid}) '
                    f' try to update documents: {doc_pids}')

                for doc_pid in doc_pids:
                    self._update_entities_in_document(
                        doc_pid=doc_pid,
                        pids_to_replace=pids_to_replace
                    )
                doc_updated = set(doc_pids)
        except Exception as err:
            self.logger.error(f'ERROR: MEF record(pid: {pid}) -> {str(err)}')
            error = True
            # uncomment to debug
            # raise
        return doc_updated, updated, error

    def start_sync(self):
        """Add logging information about the starting process."""
        self.start_timestamp = datetime.now()
        if self.dry_run:
            self.logger.info(
                '--------- Starting synchronization in dry run mode ---------')
        else:
            self.logger.info('--------- Starting synchronization ---------')

    def end_sync(self, n_doc_updated, n_mef_updated, mef_errors):
        """Add logging and cache information about the ending process."""
        self.logger.info(
            f'DONE: doc updated: {n_doc_updated}, '
            f'mef updated: {n_mef_updated}.')
        if self.dry_run:
            return
        if data := get_timestamp('sync_entities'):
            errors = data.get('errors', [])
        else:
            errors = []
        errors += mef_errors
        set_timestamp(
            'sync_entities', n_doc_updated=n_doc_updated,
            n_mef_updated=n_mef_updated, errors=errors,
            start_timestamp=self.start_timestamp)

    def sync(self, query='*', from_date=None, in_memory=False):
        """Updated the MEF records and the linked documents.

        :param query: (string) a query to select the MEF record to be updated.
        :param from_date: (string) only the MEF records updated on the MEF
            server after the given date will be considered.
        :param in_memory: (boolean) is the record could be stored in memory
            instead of using generator. Use to avoid ElasticSearch timeout
            problem in case of big data set.
        :returns: the number of updated documents, the number of updated MEF
            records, the list of MEF pids that generate an error.
        :rtype: integer, integer, list of strings.
        """
        self.start_sync()
        pids, _ = self.get_entities_pids(query, from_date=from_date)
        if in_memory:
            pids = list(pids)
        # number of document updated
        doc_updated = set()
        n_mef_updated = 0
        mef_errors = set()
        for pid in pids:
            current_doc_updated, mef_updated, error = self.sync_record(pid)
            doc_updated.update(current_doc_updated)
            if mef_updated:
                n_mef_updated += 1
            if error:
                mef_errors.add(pid)
        n_doc_updated = len(doc_updated)
        self.end_sync(n_doc_updated, n_mef_updated, mef_errors)
        return n_doc_updated, n_mef_updated, mef_errors

    def remove_unused_record(self, pid):
        """Removes MEF record if it is not linked to any documents.

        :param pid: (string) MEF identifier.
        :returns: True if the record has been deleted
        :rtype: bool
        :raises Exception: If a deletion problem occurred
        """
        entity = RemoteEntity.get_record_by_pid(pid)
        if not entity.documents_pids():
            if not self.dry_run:
                # remove from the database and the index: no tombstone
                entity.delete(True, True, True)
            self.logger.info(f'MEF {entity["type"]} record(pid: {entity.pid}) '
                             'has been deleted.')
            return True
        return False

    @classmethod
    def get_errors(cls):
        """Get all the MEF pids that causes an error."""
        return get_timestamp('sync_entities').get('errors', [])

    @classmethod
    def clear_errors(cls):
        """Removes errors in the cache information."""
        data = get_timestamp('sync_entities')
        if data.get('errors'):
            data['errors'] = []
            set_timestamp('sync_entities', **data)

    def start_clean(self):
        """Add logging information about the starting process."""
        self.start_timestamp = datetime.now()
        if self.dry_run:
            self.logger.info(
                '--------- Starting cleaning in dry run mode ---------')
        else:
            self.logger.info('--------- Starting cleaning ---------')

    def remove_unused(self, query='*'):
        """Removes MEF records that are not linked to any documents.

        :param query: (string) query to limit the record candidates.
        :returns: the number of deleted records; the list of pid that
            causes an error.
        :rtype: integer, list<str>.
        """
        self.start_clean()
        removed_entity_counter = 0
        error_entities = []
        pids, _ = self.get_entities_pids(query)
        for pid in pids:
            try:
                removed_entity_counter += int(self.remove_unused_record(pid))
            except Exception:
                error_entities.append(pid)
            sys.stdout.flush()
        self.logger.info(f'DONE: MEF deleted: {removed_entity_counter}')
        return removed_entity_counter, error_entities
