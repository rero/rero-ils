# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

from functools import wraps

import click
from elasticsearch.exceptions import NotFoundError
from flask import Blueprint, current_app, jsonify, url_for
from flask.cli import with_appcontext
from flask_login import current_user
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_search import RecordsSearch

from ..permissions import admin_permission

api_blueprint = Blueprint(
    'api_monitoring',
    __name__,
    url_prefix='/monitoring'
)


@api_blueprint.route('/es_db_counts')
def es_db_counts():
    """Display count for elasticsearch and documents.

    Displays for all document types defind in config.py following informations:
    - index name for document type
    - count of records in database
    - count of records in elasticsearch
    - difference between the count in elasticsearch and database
    :return: jsonified count for elasticsearch and documents
    """
    return jsonify({'data': Monitoring.info()})


@api_blueprint.route('/check_es_db_counts')
def check_es_db_counts():
    """Displays health status for elasticsearch and database counts.

    If there are no problems the status in returned data will be `green`,
    otherwise the status will be `red` and in the returned error
    links will be provided with more detailed informations.
    :return: jsonified health status for elasticsearch and database counts
    """
    result = {'data': {'status': 'green'}}
    check = Monitoring.check()
    if check:
        details = []
        links = {'about': url_for(
            'api_monitoring.check_es_db_counts', _external=True)}
        for info, count in check.items():
            msg = 'There are {count} items from {info} missing in ES.'.format(
                count=count,
                info=info
            )
            details.append(msg)
            links[info] = url_for(
                'api_monitoring.missing_pids',
                doc_type=info,
                _external=True
            )
        result = {
            'data': {'status': 'red'},
            'error': {
                'id': 'DB_ES_COUNTER_MISSMATCH',
                'links': links,
                'code': 'DB_ES_COUNTER_MISSMATCH',
                'title': "DB items counts don't match ES items count.",
                'details': details
            }
        }
    return jsonify(result)


def check_authentication(func):
    """Decorator to check authentication for items HTTP API."""
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'status': 'error: Unauthorized'}), 401
        if not admin_permission.require().can():
            return jsonify({'status': 'error: Forbidden'}), 403
        return func(*args, **kwargs)

    return decorated_view


@api_blueprint.route('/missing_pids/<doc_type>')
@check_authentication
def missing_pids(doc_type):
    """Displays details of counts for document type.

    Following informations will be displayed:
    - missing pids in database
    - missing pids in elasticsearch
    - pids indexed multiple times in elasticsearch
    If possible, direct links will be provieded to the corresponding records.
    This view needs an logged in system admin.

    :param doc_type: Document type to display.
    :return: jsonified details of counts for document type
    """
    try:
        api_url = url_for(
            'invenio_records_rest.{doc_type}_list'.format(doc_type=doc_type),
            _external=True
        )
    except:
        api_url = None
    mon = Monitoring.missing(doc_type)
    if mon.get('ERROR'):
        return {
            'error': {
                'id': 'DOCUMENT_TYPE_NOT_FOUND',
                'code': 'DOCUMENT_TYPE_NOT_FOUND',
                'title': "Document type not found.",
                'details': mon.get('ERROR')
            }
        }
    else:
        data = {'DB': [], 'ES': [], 'ES duplicate': {}}
        for pid in mon.get('DB'):
            if api_url:
                data['DB'].append(
                    '{api_url}?q=pid:{pid}'.format(api_url=api_url, pid=pid))
            else:
                data['DB'].append(pid)
        for pid in mon.get('ES'):
            if api_url:
                data['ES'].append(
                    '{api_url}{pid}'.format(api_url=api_url, pid=pid))
            else:
                data['ES'].append(pid)
        for pid in mon.get('ES duplicate'):
            if api_url:
                url = '{api_url}?q=pid:{pid}'.format(api_url=api_url, pid=pid)
                count = data['ES duplicate'].setdefault(url, 0)
                data['ES duplicate'][url] = count + 1
            else:
                count = data['ES duplicate'].setdefault(pid, 0)
                data['ES duplicate'][pid] = count + 1
        return jsonify({'data': data})


class Monitoring(object):
    """Monitoring class.

    The main idea here is to check the consistency between the database and
    the search index. We need to check that all documents presents in the
    database are also present in the search index and vice versa.
    """

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
        msg_head = 'DB - ES  {doc_type:>6} {count_db:>10}'.format(
            doc_type='type',
            count_db='count'
        )
        msg_head += '  {index:>25} {count_es:>10}\n'.format(
            index='index',
            count_es='count'
        )
        msg_head += '{:-^64s}\n'.format('')

        for doc_type, info in sorted(self.info().items()):
            msg = '{db_es:>7}  {doc_type:>6} {count_db:>10}'.format(
                db_es=info.get('db-es', ''),
                doc_type=doc_type,
                count_db=info.get('db', ''),
            )
            index = info.get('index', '')
            if index:
                msg += '  {index:>25} {count_es:>10}'.format(
                    index=index,
                    count_es=info.get('es', '')
                )
            result += msg + '\n'
        return msg_head + result

    @classmethod
    def get_db_count(cls, doc_type, with_deleted=False):
        """Get database count.

        Get count of items in the database for the given document type.

        :param doc_type: document type.
        :param with_deleted: count also deleted items.
        :return: item count.
        """
        if not current_app.config.get('RECORDS_REST_ENDPOINTS').get(doc_type):
            return 'No >>{doc_type}<< in DB'.format(doc_type=doc_type)
        query = PersistentIdentifier.query.filter(
            PersistentIdentifier.pid_type == doc_type
        )
        if not with_deleted:
            query = query.filter_by(status=PIDStatus.REGISTERED)
        return query.count()

    @classmethod
    def get_es_count(cls, index):
        """Get elasticsearch count.

        Get count of items in elasticsearch for the given index.

        :param index: index.
        :return: items count.
        """
        try:
            result = RecordsSearch(index=index).query().count()
        except NotFoundError:
            result = 'No >>{index}<< in ES'.format(index=index)
        return result

    @classmethod
    def info(cls, with_deleted=False):
        """Info.

        Get count details for all records rest endpoints in json format.

        :param with_deleted: count also deleted items in database.
        :return: dictionair with database, elasticsearch and databse minus
        elasticsearch count informations.
        """
        info = {}
        for doc_type, endpoint in current_app.config.get(
            'RECORDS_REST_ENDPOINTS'
        ).items():
            info[doc_type] = {}
            count_db = cls.get_db_count(doc_type, with_deleted=with_deleted)
            info[doc_type]['db'] = count_db
            index = endpoint.get('search_index', '')
            if index:
                count_es = cls.get_es_count(index)
                db_es = count_db - count_es
                info[doc_type]['index'] = index
                info[doc_type]['es'] = count_es
                info[doc_type]['db-es'] = db_es
        return info

    @classmethod
    def check(cls, with_deleted=False):
        """Compaire elasticsearch with database counts.

        :param with_deleted: count also deleted items in database.
        :return: dictionair with all document types with a difference in
        databse and elasticsearch counts.
        """
        checks = {}
        for info, data in cls.info(with_deleted=with_deleted).items():
            db_es = data.get('db-es', '')
            if db_es not in [0, '']:
                checks[info] = db_es
        return checks

    @classmethod
    def missing(cls, doc_type):
        """Get missing pids.

        Get missing pids in database and elasticsearch and find duplicate
        pids in elasticsearch.

        :param doc_type: doc type to get missing pids.
        :return: dictionair with all missing pids.
        """
        endpoint = current_app.config.get(
            'RECORDS_REST_ENDPOINTS'
        ).get(doc_type, {})
        index = endpoint.get('search_index', '')
        if index:
            pids_es = [
                v.pid for v in RecordsSearch(index=index).source(
                    ['pid']
                ).scan()
            ]
            pids_db = [
                v.pid_value for v in PersistentIdentifier.query.filter(
                    PersistentIdentifier.pid_type == doc_type
                ).all()
            ]
            missing_in_db = set(pids_es).difference(set(pids_db))
            missing_in_es = set(pids_db).difference(set(pids_es))
            return {
                'DB': list(missing_in_db),
                'ES': list(missing_in_es),
                'ES duplicate': [x for x in pids_es if pids_es.count(x) > 1]
            }
        else:
            return {'ERROR': 'Document type not found: {doc_type}'.format(
                doc_type=doc_type
            )}

    @classmethod
    def print_missing(cls, doc_type):
        """Print missing pids for the given document type.

        :param doc_type: doc type to print.
        """
        for info, data in cls.missing(doc_type=doc_type).items():
            if data:
                if info == 'ES duplicate':
                    msg = 'duplicate in ES'
                else:
                    msg = 'pids missing in {info}'.format(info=info)
                click.secho(
                    '{doc_type}: {msg}:'.format(doc_type=doc_type, msg=msg),
                    fg='red'
                )
                if info == 'ES duplicate':
                    pid_counts = {}
                    for pid in data:
                        pid_count = pid_counts.setdefault(pid, 0)
                        pid_counts[pid] = pid_count + 1
                    index = 0
                    for pid, count in pid_counts.items():
                        index += 1
                        if index > 1:
                            click.echo(', ', nl=False)
                        click.echo(
                            '{pid}: {count}'.format(count=count, pid=pid),
                            nl=False
                        )
                    click.echo('')
                else:
                    click.echo(', '.join(data))


@click.group()
def monitoring():
    """Monitoring commands."""


@monitoring.command('es_db_counts')
@click.option('-m', '--missing', 'missing', is_flag=True, default=False,
              help='display missing pids')
@with_appcontext
def es_db_counts_cli(missing):
    """Print ES and DB counts.

    Prints a table representation of database and elasticsearch counts.
    Columes:
    1. database count minus elasticsearch count
    2. document type
    3. database count
    4. elasticsearch index
    5. elasticsearch count
    """
    missing_doc_types = []
    mon = Monitoring()
    msg_head = 'DB - ES  {doc_type:>6} {count_db:>10}'.format(
        doc_type='type',
        count_db='count'
    )
    msg_head += '  {index:>25} {count_es:>10}\n'.format(
        index='index',
        count_es='count'
    )
    msg_head += '{:-^64s}'.format('')
    click.echo(msg_head)
    info = mon.info()
    for doc_type in sorted(info):
        db_es = info[doc_type].get('db-es', '')
        msg = '{db_es:>7}  {doc_type:>6} {count_db:>10}'.format(
            db_es=db_es,
            doc_type=doc_type,
            count_db=info[doc_type].get('db', ''),
        )
        index = info[doc_type].get('index', '')
        if index:
            msg += '  {index:>25} {count_es:>10}'.format(
                index=index,
                count_es=info[doc_type].get('es', '')
            )
        if db_es not in [0, '']:
            click.secho(msg, fg='red')
        else:
            click.echo(msg)
        if missing and db_es not in [0, '']:
            missing_doc_types.append(doc_type)
    for missing_doc_type in missing_doc_types:
        mon.print_missing(missing_doc_type)


@monitoring.command('es_db_missing')
@click.argument('doc_type')
@with_appcontext
def es_db_missing_cli(doc_type):
    """Print missing pids informations."""
    Monitoring().print_missing(doc_type)
