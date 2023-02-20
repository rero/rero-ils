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

import time
from functools import wraps

from flask import Blueprint, current_app, jsonify, request, url_for
from flask_login import current_user
from invenio_cache import current_cache
from invenio_db import db
from invenio_search import current_search_client
from redis import Redis

from .api import Monitoring, db_connection_counts_query, db_connections_query
from ...permissions import monitoring_permission

api_blueprint = Blueprint(
    'api_monitoring',
    __name__,
    url_prefix='/monitoring'
)


def check_authentication(func):
    """Decorator to check authentication for items HTTP API."""
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'status': 'error: Unauthorized'}), 401
        if not monitoring_permission.require().can():
            return jsonify({'status': 'error: Forbidden'}), 403
        return func(*args, **kwargs)
    return decorated_view


@api_blueprint.route('/db_connection_counts')
@check_authentication
def db_connection_counts():
    """Display DB connection counts.

    :return: jsonified count for db connections
    """
    try:
        max_conn, used, res_for_super, free = db.session.execute(
            db_connection_counts_query).first()
    except Exception as error:
        return jsonify({'ERROR': error})
    return jsonify({'data': {
        'max': max_conn,
        'used': used,
        'res_super': res_for_super,
        'free': free
    }})


@api_blueprint.route('/db_connections')
@check_authentication
def db_connections():
    """Display DB connections.

    :return: jsonified connections for db
    """
    try:
        results = db.session.execute(db_connections_query).fetchall()
    except Exception as error:
        return jsonify({'ERROR': error})
    data = {}
    for pid, application_name, client_addr, client_port, backend_start, \
            xact_start, query_start, wait_event, state, left in results:
        data[pid] = {
            'application_name': application_name,
            'client_addr': client_addr,
            'client_port': client_port,
            'backend_start': backend_start,
            'xact_start': xact_start,
            'query_start': query_start,
            'wait_event': wait_event,
            'state': state,
            'left': left
        }
    return jsonify({'data': data})


@api_blueprint.route('/es_db_counts')
def es_db_counts():
    """Display count for elasticsearch and documents.

    Displays for all document types defined in config.py following information:
    - index name for document type
    - count of records in database
    - count of records in elasticsearch
    - difference between the count in elasticsearch and database
    :return: jsonified count for elasticsearch and documents
    """
    difference_db_es = request.args.get('diff', False)
    with_deleted = request.args.get('deleted', False)
    time_delta = request.args.get('delay', 1)
    mon = Monitoring(time_delta=time_delta)
    return jsonify({'data': mon.info(
        with_deleted=with_deleted,
        difference_db_es=difference_db_es
    )})


@api_blueprint.route('/check_es_db_counts')
def check_es_db_counts():
    """Displays health status for elasticsearch and database counts.

    If there are no problems the status in returned data will be `green`,
    otherwise the status will be `red` and in the returned error
    links will be provided with more detailed information.
    :return: jsonified health status for elasticsearch and database counts
    """
    result = {'data': {'status': 'green'}}
    difference_db_es = request.args.get('diff', False)
    with_deleted = request.args.get('deleted', False)
    time_delta = request.args.get('delay', 1)
    mon = Monitoring(time_delta=time_delta)
    checks = mon.check(
        with_deleted=with_deleted,
        difference_db_es=difference_db_es
    )
    if checks:
        result = {'data': {'status': 'red'}}
        errors = []
        for doc_type, doc_type_data in checks.items():
            links = {'about': url_for(
                'api_monitoring.check_es_db_counts', _external=True)}
            for info, count in doc_type_data.items():
                if info == 'db_es':
                    msg = f'There are {count} items ' \
                          f'from {doc_type} missing in ES.'
                    links[doc_type] = url_for(
                        'api_monitoring.missing_pids',
                        doc_type=doc_type,
                        _external=True
                    )
                    errors.append({
                        'id': 'DB_ES_COUNTER_MISMATCH',
                        'links': links,
                        'code': 'DB_ES_COUNTER_MISMATCH',
                        'title': "DB items counts don't match ES items count.",
                        'details': msg
                    })
                elif info == 'db-':
                    msg = f'There are {count} items ' \
                          f'from {doc_type} missing in DB.'
                    links[doc_type] = url_for(
                        'api_monitoring.missing_pids',
                        doc_type=doc_type,
                        _external=True
                    )
                    errors.append({
                        'id': 'DB_ES_UNEQUAL',
                        'links': links,
                        'code': 'DB_ES_UNEQUAL',
                        'title': "DB items unequal ES items.",
                        'details': msg
                    })
                elif info == 'es-':
                    msg = f'There are {count} items ' \
                          f'from {doc_type} missing in ES.'
                    links[doc_type] = url_for(
                        'api_monitoring.missing_pids',
                        doc_type=doc_type,
                        _external=True
                    )
                    errors.append({
                        'id': 'DB_ES_UNEQUAL',
                        'links': links,
                        'code': 'DB_ES_UNEQUAL',
                        'title': "DB items unequal ES items.",
                        'details': msg
                    })
        result['errors'] = errors
    return jsonify(result)


@api_blueprint.route('/missing_pids/<doc_type>')
@check_authentication
def missing_pids(doc_type):
    """Displays details of counts for document type.

    Following information will be displayed:
    - missing pids in database
    - missing pids in elasticsearch
    - pids indexed multiple times in elasticsearch
    If possible, direct links will be provided to the corresponding records.
    This view needs an logged in system admin.

    :param doc_type: Document type to display.
    :return: jsonified details of counts for document type
    """
    try:
        api_url = url_for(
            f'invenio_records_rest.{doc_type}_list',
            _external=True
        )
    except Exception:
        api_url = None
    time_delta = request.args.get('delay', 1)
    mon = Monitoring(time_delta=time_delta)
    res = mon.missing(doc_type)
    if res.get('ERROR'):
        return {
            'error': {
                'id': 'DOCUMENT_TYPE_NOT_FOUND',
                'code': 'DOCUMENT_TYPE_NOT_FOUND',
                'title': "Document type not found.",
                'details': res.get('ERROR')
            }
        }
    data = {'DB': [], 'ES': [], 'ES duplicate': []}
    for pid in res.get('DB'):
        if api_url:
            data['DB'].append(f'{api_url}?q=pid:"{pid}"')
        else:
            data['DB'].append(pid)
    for pid in res.get('ES'):
        if api_url:
            data['ES'].append(f'{api_url}{pid}')
        else:
            data['ES'].append(pid)
    for pid in res.get('ES duplicate'):
        if api_url:
            data['ES duplicate'].append(f'{api_url}?q=pid:"{pid}"')
        else:
            data['ES duplicate'].append(pid)
    return jsonify({'data': data})


@api_blueprint.route('/redis')
@check_authentication
def redis():
    """Displays redis info.

    :return: jsonified redis info.
    """
    url = current_app.config.get('ACCOUNTS_SESSION_REDIS_URL',
                                 'redis://localhost:6379')
    redis = Redis.from_url(url)
    info = redis.info()
    return jsonify({'data': info})


@api_blueprint.route('/es')
@check_authentication
def elastic_search():
    """Displays Elasticsearch cluster info.

    :return: jsonified Elasticsearch cluster info.
    """
    info = current_search_client.cluster.health()
    return jsonify({'data': info})


@api_blueprint.route('/es_indices')
@check_authentication
def elastic_search_indices():
    """Displays Elasticsearch indices info.

    :return: jsonified Elasticsearch indices info.
    """
    info = current_search_client.cat.indices(
        bytes='b', format='json', s='index')
    info = {data['index']: data for data in info}
    return jsonify({'data': info})


@api_blueprint.route('/timestamps')
@check_authentication
def timestamps():
    """Get time stamps from current cache.

    Makes the saved timestamps accessible via url requests.

    :return: jsonified timestamps.
    """
    data = {}
    if time_stamps := current_cache.get('timestamps'):
        for name, values in time_stamps.items():
            # make the name safe for JSON export
            name = name.replace('-', '_')
            data[name] = {}
            for key, value in values.items():
                if key == 'time':
                    data[name]['utctime'] = value.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    data[name]['unixtime'] = time.mktime(value.timetuple())
                else:
                    data[name][key] = value

    return jsonify({'data': data})
