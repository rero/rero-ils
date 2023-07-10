# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
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

"""Monitoring utilities."""

from datetime import datetime, timedelta

import click
from elasticsearch.exceptions import NotFoundError
from flask import current_app
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_search import RecordsSearch
from sqlalchemy import text

db_connection_counts_query = """
        select
            max_conn, used, res_for_super,
            max_conn-used-res_for_super res_for_normal
        from
            (
                select count(*) used
                from pg_stat_activity
            ) t1,
            (
                select setting::int res_for_super
                from pg_settings
                where name=$$superuser_reserved_connections$$
            ) t2,
            (
                select setting::int max_conn
                from pg_settings
                where name=$$max_connections$$
            ) t3
        """


db_connections_query = """
        SELECT
            pid, application_name, client_addr, client_port, backend_start,
            xact_start, query_start,  wait_event, state, left(query, 64)
        FROM
            pg_stat_activity
        ORDER BY query_start DESC
    """


class Monitoring(object):
    """Monitoring class.

    The main idea here is to check the consistency between the database and
    the search index. We need to check that all documents presents in the
    database are also present in the search index and vice versa.
    Furthermore, timestamps could be accessed for monitoring of execution
    times of selected functions.
    """

    has_no_db = ['oplg', 'ent']

    def __init__(self, time_delta=1):
        """Constructor.

        :param time_delta: Minutes to subtract from DB ES creation time.
        """
        self.time_delta = int(time_delta)

    def __str__(self):
        """Table representation of database and elasticsearch differences.

        :return: string representation of database and elasticsearch
        differences. Following columns are in the string:
            1. database count minus elasticsearch count
            2. document type
            3. database count
            4. elasticsearch index
            5. elasticsearch count
        """
        result = ''
        msg_head = f'DB - ES{"type":>8}{"count":>11}{"index":>27}{"count":>11}'
        msg_head += f'\n{"":-^64s}\n'
        for doc_type, info in sorted(self.info().items()):
            db_es = info.get('db-es', '')
            count_db = info.get('db', '')
            msg = f'{db_es:>7}  {doc_type:>6} {count_db:>10}'
            if index := info.get('index', ''):
                msg += f'  {index:>25} {info.get("es", ""):>10}'
            result += msg + '\n'
        return msg_head + result

    @classmethod
    def get_db_count(cls, doc_type, with_deleted=False, date=None):
        """Get database count.

        Get count of items in the database for the given document type.

        :param doc_type: document type.
        :param with_deleted: count also deleted items.
        :return: item count.
        """
        if not current_app.config.get(
                'RECORDS_REST_ENDPOINTS').get(doc_type):
            return f'No >>{doc_type}<< in DB'
        query = PersistentIdentifier.query.filter_by(pid_type=doc_type)
        if not with_deleted:
            query = query.filter_by(status=PIDStatus.REGISTERED)
        if date:
            query = query.filter(PersistentIdentifier.created < date)
        return query.count()

    @classmethod
    def get_es_count(cls, index, date=None):
        """Get elasticsearch count.

        Get count of items in elasticsearch for the given index.

        :param index: index.
        :return: items count.
        """
        try:
            query = RecordsSearch(index=index).query()
            if date:
                query = query.filter('range', _created={'lte': date})
            result = query.count()
        except NotFoundError:
            result = f'No >>{index}<< in ES'
        return result

    @classmethod
    def get_all_pids(cls, doc_type, with_deleted=False, limit=100000,
                     date=None):
        """Get all doc_type pids. Return a generator iterator.

        :param with_deleted: get also deleted pids.
        :param limit: Limit sql query to count size.
        :param date: Get all pids <= date.
        :returns: pid generator.
        """
        query = PersistentIdentifier.query.filter_by(pid_type=doc_type)
        if not with_deleted:
            query = query.filter_by(status=PIDStatus.REGISTERED)
        if date:
            query = query.filter(PersistentIdentifier.created < date)
        if limit:
            count = query.count()
            # slower, less memory
            query = query.order_by(text('pid_value')).limit(limit)
            offset = 0
            while offset < count:
                for identifier in query.offset(offset):
                    yield identifier.pid_value
                offset += limit
        else:
            # faster, more memory
            for identifier in query:
                yield identifier.pid_value

    def get_es_db_missing_pids(self, doc_type, with_deleted=False):
        """Get ES and DB counts."""
        endpoint = current_app.config.get(
            'RECORDS_REST_ENDPOINTS'
        ).get(doc_type, {})
        index = endpoint.get('search_index')
        pids_es_double = []
        pids_es = []
        pids_db = []
        if index and doc_type not in self.has_no_db:
            date = datetime.utcnow() - timedelta(minutes=self.time_delta)
            pids_es = {}
            es_query = RecordsSearch(index=index) \
                .filter('range', _created={'lte': date})
            for hit in es_query.source('pid').scan():
                if pids_es.get(hit.pid):
                    pids_es_double.append(hit.pid)
                pids_es[hit.pid] = 1
            pids_db = []
            for pid in self.get_all_pids(
                doc_type,
                with_deleted=with_deleted,
                date=date
            ):
                if pids_es.get(pid):
                    pids_es.pop(pid)
                else:
                    pids_db.append(pid)
        return list(pids_es), pids_db, pids_es_double, index

    def info(self, with_deleted=False, difference_db_es=False):
        """Info.

        Get count details for all records rest endpoints in json format.

        :param with_deleted: count also deleted items in database.
        :return: dictionary with database, elasticsearch and database minus
        elasticsearch count information.
        """
        info = {}
        for doc_type, endpoint in current_app.config.get(
            'RECORDS_REST_ENDPOINTS'
        ).items():
            info[doc_type] = {}
            date = datetime.utcnow() - timedelta(minutes=self.time_delta)
            if doc_type not in self.has_no_db:
                count_db = self.get_db_count(
                    doc_type, with_deleted=with_deleted, date=date)
                count_db = count_db if isinstance(count_db, int) else 0
                info[doc_type]['db'] = count_db
            if index := endpoint.get('search_index', ''):
                count_es = self.get_es_count(index, date=date)
                count_es = count_es if isinstance(count_es, int) else 0
                db_es = count_db - count_es
                info[doc_type]['index'] = index
                info[doc_type]['es'] = count_es
                if doc_type not in self.has_no_db:
                    info[doc_type]['db-es'] = db_es
                    if db_es == 0 and difference_db_es:
                        missing_in_db, missing_in_es, pids_es_double, index = \
                            self.get_es_db_missing_pids(
                                doc_type=doc_type,
                                with_deleted=with_deleted
                            )
                        if index:
                            if missing_in_db:
                                info[doc_type]['db-'] = list(missing_in_db)
                            if missing_in_es:
                                info[doc_type]['es-'] = list(missing_in_es)
                else:
                    info[doc_type]['db'] = 0
                    info[doc_type]['db-es'] = 0
        return info

    def check(self, with_deleted=False, difference_db_es=False):
        """Compare elasticsearch with database counts.

        :param with_deleted: count also deleted items in database.
        :return: dictionary with all document types with a difference in
        database and elasticsearch counts.
        """
        checks = {}
        for info, data in self.info(
            with_deleted=with_deleted,
            difference_db_es=difference_db_es
        ).items():
            db_es = data.get('db-es', '')
            if db_es and db_es not in [0, '']:
                checks.setdefault(info, {})
                checks[info]['db_es'] = db_es
            if data.get('db-'):
                checks.setdefault(info, {})
                checks[info]['db-'] = len(data.get('db-'))
            if data.get('es-'):
                checks.setdefault(info, {})
                checks[info]['es-'] = len(data.get('es-'))
        return checks

    def missing(self, doc_type, with_deleted=False):
        """Get missing pids.

        Get missing pids in database and elasticsearch and find duplicate
        pids in elasticsearch.

        :param doc_type: doc type to get missing pids.
        :return: dictionary with all missing pids.
        """
        missing_in_db, missing_in_es, pids_es_double, index =\
            self.get_es_db_missing_pids(
                doc_type=doc_type,
                with_deleted=with_deleted
            )
        if index:
            return {
                'DB': list(missing_in_db),
                'ES': list(missing_in_es),
                'ES duplicate': pids_es_double
            }
        else:
            return {'ERROR': f'Document type not found: {doc_type}'}

    def print_missing(self, doc_type):
        """Print missing pids for the given document type.

        :param doc_type: doc type to print.
        """
        missing = self.missing(doc_type=doc_type)
        if 'ERROR' in missing:
            click.secho(f'Error: {missing["ERROR"]}', fg='yellow')
        else:
            if 'ES duplicate' in missing and missing["ES duplicate"]:
                click.secho(
                    f'ES duplicate {doc_type}:'
                    f' {", ".join(missing["ES duplicate"])}',
                    fg='red'
                )
            if 'ES' in missing and missing["ES"]:
                click.secho(
                    f'ES missing {doc_type}: {", ".join(missing["ES"])}',
                    fg='red'
                )
            if 'DB' in missing and missing["DB"]:
                click.secho(
                    f'DB missing {doc_type}: {", ".join(missing["DB"])}',
                    fg='red'
                )
