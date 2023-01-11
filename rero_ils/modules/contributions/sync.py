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

import logging
import os
import sys
from copy import deepcopy
from datetime import datetime
from itertools import islice
from logging.config import dictConfig

import requests
from deepdiff import DeepDiff
from elasticsearch_dsl import Q
from flask import current_app

from rero_ils.modules.contributions.api import Contribution, \
    ContributionsSearch
from rero_ils.modules.documents.api import Document, DocumentsSearch
from rero_ils.modules.utils import get_timestamp, set_timestamp


class SyncAgent(object):
    """Agent MEF synchronization."""

    def __init__(self, dry_run=False, verbose=False, log_dir=None,
                 from_last_date=False):
        """Constructor.

        :param dry_run: bool - if true the data are not modified
        :param verbose: bool or integer - verbose level
        :param log_dir: string - path to put the logs
        :param from_last_date: boolean - if True try to consider agent modified
            after the last run date time
        """
        self.dry_run = dry_run
        self.verbose = verbose
        self.from_date = None
        self.start_timestamp = None
        self._init_logger(verbose, log_dir)
        if from_last_date:
            self._get_last_date()

    def _get_last_date(self):
        """Get the date of the last execution of the synchronization."""
        data = get_timestamp('sync_agents')
        if data and data.get('start_timestamp'):
            self.from_date = data.get('start_timestamp')

    def _init_logger(self, verbose, log_dir):
        """Initialize the module logger."""
        # default value
        if not log_dir:
            log_dir = current_app.config.get(
                'RERO_ILS_MEF_SYNC_LOG_DIR',
                os.path.join(current_app.instance_path, 'logs')
            )
        # create the log directory if does not exists
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        verbose_level = ['ERROR', 'INFO', 'DEBUG']
        logging_config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': '%(asctime)s [%(levelname)s] :: %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'standard',
                    'level': verbose_level[min(verbose, 2)]
                },
                'file': {
                    'class': 'logging.handlers.TimedRotatingFileHandler',
                    'filename': os.path.join(log_dir, 'sync_mef.log'),
                    'when': 'D',
                    'interval': 7,
                    'backupCount': 10,
                    'formatter': 'standard'
                }
            },
            'loggers': {
                # for the current module
                self.__module__: {
                    'handlers': ['console', 'file'],
                    'level': 'INFO',
                    'propagate': False
                }
            }
        }
        dictConfig(logging_config)
        self.logger = logging.getLogger(__name__)
        self.log_dir = log_dir

    def agent_are_different(self, agent1, agent2):
        """Check if two agent are different.

        The comparison is done only on the common fields.

        :param agent1: a dict representing an agent to compare.
        :param agent2: a dict representing an agent to compare.
        :returns: True if they are different.
        """

        def remove_fields(agent):
            """Remove specific fields."""
            fields_to_remove = [
                '$schema', 'organisation', '_created', '_updated'
            ]
            for field in fields_to_remove:
                agent.pop(field, None)

            fields_to_remove = ['$schema', 'md5']
            for source in agent['sources']:
                for field in fields_to_remove:
                    agent[source].pop(field, None)
            return agent

        diff = DeepDiff(
            remove_fields(deepcopy(agent1)),
            remove_fields(deepcopy(agent2)),
            ignore_order=True)
        if diff:
            self.logger.debug(
                f"Agent differs: {agent1['pid']}, {agent2['pid']}",
                diff)
            return True
        return False

    def _get_latest(self, source, pid):
        """Query the MEF server to retrieve the last MEF for a given agent id.

        :param source - string: the agent source such as idref, gnd.
        :param pid - string: the identifier of the agent.
        :returns: a dict of the MEF record.
        :rtype: dictionary.
        """
        mef_url = current_app.config.get('RERO_ILS_MEF_AGENTS_URL')
        url = f'{mef_url}/mef/latest/{source}:{pid}'
        return requests.get(url).json()

    def update_agents_in_document(
        self,
        doc_pid,
        pids_to_replace
    ):
        """Updates the contribution and subjects in document.

        :param doc_pid - string: document pid
        :param source - string: agent source i.e. gnd, rero, mef
        :param old_agent_pid - string: old agent pid from the database
        :param new_agent_pid - string: new agent pid from the mef server
        :param new_mef_pid - string: new MEF pid
        """
        # get the document from the DB
        doc = Document.get_record_by_pid(doc_pid)

        # build the $ ref urls
        mef_url = current_app.config.get('RERO_ILS_MEF_AGENTS_URL')

        # get all agents from the document over all agent fields:
        # contribution and subjects
        agents = [
            subject for subject in doc.get('subjects', [])
            if subject.get('$ref')
        ]
        agents += [
            contrib['agent'] for contrib in doc.get('contribution', [])
            if contrib.get('agent', {}).get('$ref')
        ]
        if not agents:
            self.logger.debug(f'No agent to update for document {doc.pid}')

        # update the $ref agent URL and MEF pid
        for source, pids in pids_to_replace.items():
            old_agent_url = f'{mef_url}/{source}/{pids[0]}'
            new_agent_url = f'{mef_url}/{source}/{pids[1]}'
            agents_to_update = filter(
                lambda c: c.get('$ref') == old_agent_url, agents)
            for agent in agents_to_update:
                if old_agent_url != new_agent_url:
                    self.logger.info(
                        f'Agent URL changed from {old_agent_url} to '
                        f'{new_agent_url} for document {doc.pid}')
                # update the agent URL
                agent['$ref'] = new_agent_url
        # in any case we update the doc as the mef pid can be changed
        if not self.dry_run:
            doc.replace(doc, dbcommit=True, reindex=True)

    def get_documents_pids_from_mef(self, pid):
        """Retrieve all the linked documents to a MEF record.

        :param pid - string: a MEF identifier.
        :returns: a list of identifiers.
        :rtype: list of strings.
        """
        # the MEF link can be in contribution or subjects
        es_query = DocumentsSearch()
        filters = Q('term', contribution__agent__pid=pid)
        filters |= Q('term', subjects__pid=pid)
        es_query = es_query.filter('bool', must=[filters]).source('pid')
        # can be a list as the should not be too big
        return [d.pid for d in es_query.params(scroll='30m').scan()]

    def get_contributions_pids(self, query='*', from_date=None):
        """Get contributions identifiers.

        :param query - string: a query to select the MEF record to be updated.
        :param from_date - string: only the MEF updated on the MEF server after
                                   the given date will be considered.
        :returns: the list of the contribution identifiers.
        :rtype: list of strings.
        """
        logging.basicConfig(filename='myfile.log', level=logging.DEBUG)
        mef_url = current_app.config.get('RERO_ILS_MEF_AGENTS_URL')
        url = f'{mef_url}/mef/updated'
        es_query = ContributionsSearch().filter('query_string', query=query)
        total = es_query.count()
        if not from_date and self.from_date:
            from_date = self.from_date
        if from_date:
            self.logger.info(f'Get records updated after: {from_date}')

        def get_mef_pids(es_query, chunk_size=1000):
            """Get the identifiers from elasticsearch.

            :param es_query: string - the elasticsearch query to limit the
                results
            :param chunk_size: integer - the maximum number of pid per chunk
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
                # number of provided updated MEF pids
                n_provided = 0
                try:
                    while chunk := list(islice(iter(pids), chunk_size)):
                        # ask the mef server to return only the updated
                        # pids form a given date
                        res = requests.post(
                            url,
                            json=dict(
                                from_date=from_date.strftime("%Y-%m-%d"),
                                pids=chunk
                            )
                        )
                        if res.status_code != 200:
                            raise Exception
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

        :param pid - string: the MEF identifier.
        :returns: the number of updated document, true if the MEF record
                  has been update, true if an error occurs.
        :rtype: integer, boolean, boolean.
        """
        doc_updated = set()
        updated = error = False
        try:
            # get contribution in db
            agent = Contribution.get_record_by_pid(pid)
            if not agent:
                raise Exception(f'ERROR MEF {pid} does not exists in db.')
            self.logger.debug(f'Processing MEF(pid: {pid})')
            # iterate over all agent sources: rero, gnd, idref
            doc_pids = self.get_documents_pids_from_mef(agent.pid)
            pids_to_replace = {}
            for source in agent['sources']:
                mef = self._get_latest(source, agent[source]["pid"])
                # MEF sever failed to retrieve the latest MEF record
                # for the given agent
                if not mef.get('pid'):
                    raise Exception(
                        f'Error cannot get latest for '
                        '{source}:{agent[source]["pid"]}')

                old_agent_pid = agent[source]["pid"]
                new_agent_pid = mef[source]['pid']
                new_mef_pid = mef.get('pid')
                old_mef_pid = agent.pid
                if old_agent_pid != new_agent_pid:
                    pids_to_replace[source] = (old_agent_pid, new_agent_pid)

                # can be mef pid, source pid or metadata
                if self.agent_are_different(dict(agent), mef):
                    # need a copy as we want to keep the MEF record
                    # untouched for the next agent
                    new_mef_data = deepcopy(mef)
                    fields_to_remove = ['$schema', '_created', '_update']
                    for field in fields_to_remove:
                        new_mef_data.pop(field, None)

                    if old_mef_pid != new_mef_pid:
                        self.logger.info(
                            f'MEF pid has changed from {old_mef_pid} to '
                            f'{new_mef_pid} for {source} (pid:{old_agent_pid})'
                        )
                        # if the MEF record does not exists create it
                        new_agent = Contribution.get_record_by_pid(new_mef_pid)

                        if not new_agent:
                            if not self.dry_run:
                                Contribution.create(
                                    data=new_mef_data,
                                    dbcommit=True,
                                    reindex=True
                                )
                            self.logger.info(
                                f'Create a new MEF record(pid: {new_mef_pid})')
                        else:
                            # update the new MEF
                            # recursion
                            self.logger.info(
                                f'MEF(pid: {agent.pid}) recursion with'
                                f' (pid:{new_mef_pid})')
                            new_doc_updated, new_updated, new_error = \
                                self.sync_record(new_mef_pid)
                            # TODO: find a better way
                            doc_updated.update(new_doc_updated)
                            updated = updated or new_updated
                            error = error or new_error
                    # something changed
                    # update the content
                    self.logger.info(
                        f'MEF(pid: {agent.pid}) content has been '
                        f'updated')
                    if not self.dry_run:
                        if old_mef_pid == new_mef_pid:
                            Contribution.get_record(agent.id).replace(
                                new_mef_data, dbcommit=True, reindex=True)
                        else:
                            # as we have only the last mef but not the old one
                            # we need get it from the MEF server
                            # this is important as it can still be used by
                            # other agents
                            Contribution.get_record_by_pid(
                                pid).update_online(dbcommit=True, reindex=True)
                    updated = True

            if updated:
                # for each documents
                self.logger.info(
                    f'MEF(pid: {agent.pid}) try to update '
                    f'documents: {doc_pids}')
                for doc_pid in doc_pids:
                    self.update_agents_in_document(
                        doc_pid=doc_pid,
                        pids_to_replace=pids_to_replace
                    )
                doc_updated = set(doc_pid)
        except Exception as e:
            self.logger.error(f'ERROR: MEF(pid:{pid}) -> {e}')
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
        data = get_timestamp('sync_agents')
        errors = []
        if data:
            errors = data.get('errors', [])
        errors += mef_errors
        set_timestamp(
            'sync_agents', n_doc_updated=n_doc_updated,
            n_mef_updated=n_mef_updated, errors=errors,
            start_timestamp=self.start_timestamp)

    def sync(self, query="*", from_date=None, in_memory=False):
        """Updated the MEF records and the linked documents.

        :param query - string: a query to select the MEF record to be updated.
        :param from_date - string: only the MEF updated on the MEF server after
                                   the given date will be considered.
        :returns: the number of updated documents, the number of updated MEF
                  records, the list of MEF pids that generate an error.
        :rtype: integer, integer, list of strings.
        """
        self.start_sync()
        pids, _ = self.get_contributions_pids(query, from_date=from_date)
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
        return len(doc_updated), n_mef_updated, mef_errors

    def remove_unused_record(self, pid):
        """Removes MEF record if it is not linked to documents.

        :param pid - string: MEF identifier.
        :returns: true if the record has been deleted, true if an error occurs.
        :rtype: boolean, boolean
        """
        try:
            doc_pids = self.get_documents_pids_from_mef(pid)
            if len(doc_pids) == 0:
                # get the contribution for the database
                contrib = Contribution.get_record_by_pid(pid)
                if not self.dry_run:
                    # remove from the database and the index: no tombstone
                    contrib.delete(True, True, True)
                self.logger.info(f'MEF(pid:{contrib.pid}) has been deleted.')
                # removed, no error
                return True, False
        except Exception as e:
            self.logger.error(f'MEF (pid: {pid}) -> {e}')
            # no removed, error
            return False, True
        # no removed, no error
        return False, False

    @classmethod
    def get_errors(cls):
        """Get all the MEF pids that causes an error."""
        data = get_timestamp('sync_agents')
        return data.get('errors', [])

    @classmethod
    def clear_errors(cls):
        """Removes errors in the cache information."""
        data = get_timestamp('sync_agents')
        if data.get('errors'):
            data['errors'] = []
            set_timestamp('sync_agents', **data)

    def start_clean(self):
        """Add logging information about the starting process."""
        self.start_timestamp = datetime.now()
        if self.dry_run:
            self.logger.info(
                '--------- Starting cleaning in dry run mode ---------')
        else:
            self.logger.info('--------- Starting cleaning ---------')

    def remove_unused(self, query="*"):
        """Removes MEF records that are not linked to documents.

        :param query - string: query to limit the record candidates.
        :returns: the number of deleted records, the list of pid that
                  causes an error.
        :rtype: integer, list of strings.
        """
        self.start_clean()
        n_removed = 0
        err_pids = []
        pids, _ = self.get_contributions_pids(query)
        for pid in pids:
            removed, error = self.remove_unused_record(pid)
            if removed:
                n_removed += 1
            if error:
                err_pids.append(pid)
            sys.stdout.flush()
        self.logger.info(f'DONE: MEF deleted: {n_removed}')
        return n_removed, err_pids
