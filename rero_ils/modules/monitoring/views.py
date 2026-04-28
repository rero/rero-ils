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
from redis.exceptions import RedisError

from ...permissions import monitoring_permission
from .api import DB_CONNECTION_COUNTS_QUERY, DB_CONNECTIONS_QUERY, Monitoring

api_blueprint = Blueprint("api_monitoring", __name__, url_prefix="/monitoring")


def check_authentication(func):
    """Decorator to check authentication for items HTTP API."""

    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"status": "error: Unauthorized"}), 401
        if not monitoring_permission.require().can():
            return jsonify({"status": "error: Forbidden"}), 403
        return func(*args, **kwargs)

    return decorated_view


@api_blueprint.route("/db_connection_counts")
@check_authentication
def db_connection_counts():
    """Display DB connection counts.

    :return: jsonified count for db connections
    """
    try:
        max_conn, used, res_for_super, free = db.session.execute(DB_CONNECTION_COUNTS_QUERY).first()
    except Exception as error:
        return jsonify({"ERROR": error})
    return jsonify(
        {
            "data": {
                "max": max_conn,
                "used": used,
                "res_super": res_for_super,
                "free": free,
            }
        }
    )


@api_blueprint.route("/db_connections")
@check_authentication
def db_connections():
    """Display DB connections.

    :return: jsonified connections for db
    """
    try:
        results = db.session.execute(DB_CONNECTIONS_QUERY).fetchall()
    except Exception as error:
        return jsonify({"ERROR": error})
    data = {
        pid: {
            "application_name": application_name,
            "client_addr": client_addr,
            "client_port": client_port,
            "backend_start": backend_start,
            "xact_start": xact_start,
            "query_start": query_start,
            "wait_event": wait_event,
            "state": state,
            "left": left,
        }
        for pid, application_name, client_addr, client_port, backend_start, xact_start, query_start, wait_event, state, left in results
    }
    return jsonify({"data": data})


@api_blueprint.route("/search_db_counts")
def search_db_counts():
    """Display count for search index and documents.

    Displays for all document types defined in config.py following information:
    - index name for document type
    - count of records in database
    - count of records in search index
    - difference between the count in search index and database
    :return: jsonified count for search index and documents
    """
    difference_db_search = request.args.get("diff", False)
    with_deleted = request.args.get("deleted", False)
    time_delta = request.args.get("delay", 1)
    mon = Monitoring(time_delta=time_delta)
    return jsonify({"data": mon.info(with_deleted=with_deleted, difference_db_search=difference_db_search)})


@api_blueprint.route("/check_search_db_counts")
def check_search_db_counts():
    """Displays health status for search index and database counts.

    If there are no problems the status in returned data will be `green`,
    otherwise the status will be `red` and in the returned error
    links will be provided with more detailed information.
    :return: jsonified health status for search index and database counts
    """
    result = {"data": {"status": "green"}}
    difference_db_search = request.args.get("diff", False)
    with_deleted = request.args.get("deleted", False)
    time_delta = request.args.get("delay", 1)
    mon = Monitoring(time_delta=time_delta)
    checks = mon.check(with_deleted=with_deleted, difference_db_search=difference_db_search)
    if checks:
        result = {"data": {"status": "red"}}
        errors = []
        for doc_type, doc_type_data in checks.items():
            links = {"about": url_for("api_monitoring.check_search_db_counts", _external=True)}
            for info, count in doc_type_data.items():
                if info == "db_search":
                    msg = f"There are {count} items from {doc_type} missing in search."
                    links[doc_type] = url_for("api_monitoring.missing_pids", doc_type=doc_type, _external=True)
                    errors.append(
                        {
                            "id": "DB_SEARCH_COUNTER_MISMATCH",
                            "links": links,
                            "code": "DB_SEARCH_COUNTER_MISMATCH",
                            "title": "DB items counts don't match search items count.",
                            "details": msg,
                        }
                    )
                elif info == "db-":
                    msg = f"There are {count} items from {doc_type} missing in DB."
                    links[doc_type] = url_for("api_monitoring.missing_pids", doc_type=doc_type, _external=True)
                    errors.append(
                        {
                            "id": "DB_SEARCH_UNEQUAL",
                            "links": links,
                            "code": "DB_SEARCH_UNEQUAL",
                            "title": "DB items unequal search items.",
                            "details": msg,
                        }
                    )
                elif info == "search-":
                    msg = f"There are {count} items from {doc_type} missing in search."
                    links[doc_type] = url_for("api_monitoring.missing_pids", doc_type=doc_type, _external=True)
                    errors.append(
                        {
                            "id": "DB_SEARCH_UNEQUAL",
                            "links": links,
                            "code": "DB_SEARCH_UNEQUAL",
                            "title": "DB items unequal search items.",
                            "details": msg,
                        }
                    )
        result["errors"] = errors
    return jsonify(result)


@api_blueprint.route("/missing_pids/<doc_type>")
@check_authentication
def missing_pids(doc_type):
    """Displays details of counts for document type.

    Following information will be displayed:
    - missing pids in database
    - missing pids in search index
    - pids indexed multiple times in search index
    If possible, direct links will be provided to the corresponding records.
    This view needs an logged in system admin.

    :param doc_type: Document type to display.
    :return: jsonified details of counts for document type
    """
    try:
        api_url = url_for(f"invenio_records_rest.{doc_type}_list", _external=True)
    except Exception:
        api_url = None
    time_delta = request.args.get("delay", 1)
    mon = Monitoring(time_delta=time_delta)
    res = mon.missing(doc_type)
    if res.get("ERROR"):
        return {
            "error": {
                "id": "DOCUMENT_TYPE_NOT_FOUND",
                "code": "DOCUMENT_TYPE_NOT_FOUND",
                "title": "Document type not found.",
                "details": res.get("ERROR"),
            }
        }
    data = {"DB": [], "search": [], "search duplicate": []}
    for pid in res.get("DB"):
        if api_url:
            data["DB"].append(f'{api_url}?q=pid:"{pid}"')
        else:
            data["DB"].append(pid)
    for pid in res.get("search"):
        if api_url:
            data["search"].append(f"{api_url}{pid}")
        else:
            data["search"].append(pid)
    for pid in res.get("search duplicate"):
        if api_url:
            data["search duplicate"].append(f'{api_url}?q=pid:"{pid}"')
        else:
            data["search duplicate"].append(pid)
    return jsonify({"data": data})


@api_blueprint.route("/redis")
@check_authentication
def redis():
    """Displays redis info for all configured instances.

    :return: jsonified redis info keyed by instance name.
    """
    data = {}
    for name, client in current_app.extensions.get("rero_ils_redis_instances", {}).items():
        try:
            data[name] = {"name": name, **client.info()}
        except RedisError:
            data[name] = {"name": name, "status": "error"}
    return jsonify({"data": data})


@api_blueprint.route("/es")
@check_authentication
def elastic_search():
    """Displays search index cluster info.

    :return: jsonified search index cluster info.
    """
    info = current_search_client.cluster.health()
    return jsonify({"data": info})


@api_blueprint.route("/search_indices")
@check_authentication
def search_indices():
    """Displays search index indices info.

    :return: jsonified search index indices info.
    """
    info = current_search_client.cat.indices(bytes="b", format="json", s="index")
    info = {data["index"]: data for data in info}
    return jsonify({"data": info})


@api_blueprint.route("/timestamps")
@check_authentication
def timestamps():
    """Get time stamps from current cache.

    Makes the saved timestamps accessible via url requests.

    :return: jsonified timestamps.
    """
    data = {}
    if time_stamps := current_cache.get("timestamps"):
        for name, values in time_stamps.items():
            # make the name safe for JSON export
            name = name.replace("-", "_")
            data[name] = {}
            for key, value in values.items():
                if key == "time":
                    data[name]["utctime"] = value.strftime("%Y-%m-%d %H:%M:%S")
                    data[name]["unixtime"] = time.mktime(value.timetuple())
                else:
                    data[name][key] = value

    return jsonify({"data": data})
