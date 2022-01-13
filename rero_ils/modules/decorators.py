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

"""Shared module decorators."""
import contextlib
import re
from functools import wraps

from flask import abort, current_app, jsonify, redirect, request
from flask_login import current_user
from invenio_access import Permission
from invenio_records_rest.utils import make_comma_list_a_list
from werkzeug.exceptions import HTTPException

from rero_ils.permissions import librarian_permission, login_and_librarian, \
    login_and_patron

from .permissions import PermissionContext


def check_authentication(fn):
    """Decorator to check authentication for permissions HTTP API."""
    @wraps(fn)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'status': 'error: Unauthorized'}), 401
        if not librarian_permission.require().can():
            return jsonify({'status': 'error: Forbidden'}), 403
        return fn(*args, **kwargs)

    return decorated_view


def check_logged_as_librarian(fn):
    """Decorator to check if the current logged user is logged as librarian.

    If no user is connected: return 401 (unauthorized)
    If current logged user isn't `librarian`: return 403 (forbidden)
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        login_and_librarian()
        return fn(*args, **kwargs)
    return wrapper


def check_logged_as_patron(fn):
    """Decorator to check if the current logged user is logged as patron.

    If no user is connected: redirect the user to sign-in page
    If current logged user isn't `patron`: return 403 (forbidden)
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        status, code, redirect_url = login_and_patron()
        if status:
            return fn(*args, **kwargs)
        elif redirect_url:
            return redirect(redirect_url)
        else:
            abort(code)
    return wrapper


def check_logged_user_authentication(func):
    """Decorator to check authentication for user HTTP API."""
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'status': 'error: Unauthorized'}), 401
        return func(*args, **kwargs)

    return decorated_view


def check_permission(actions):
    """Decorator to check if current connected user has access to an action.

    :param actions: List of `ActionNeed` to test. If one permission failed
        then the access should be unauthorized.
    """
    def inner(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for action in actions:
                permission = Permission(action)
                if not permission.can():
                    return jsonify({'status': 'error: Unauthorized'}), 401
            return func(*args, **kwargs)
        return wrapper
    return inner


def parse_permission_payload(func):
    """Decorator parsing payload from permission management request.

    Analyze the JSON data from request payload to extract all required
    parameters depending on the permission management context. Extracted
    parameters will be added to keyword arguments from decorated function.

    :raises KeyError - If a required parameter isn't available.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        data = request.get_json() or {}
        kwargs['method'] = 'deny' if request.method == 'DELETE' else 'allow'
        # define required parameters depending on request context.
        required_arguments = ['context', 'permission']
        if data.get('context') == PermissionContext.BY_ROLE:
            required_arguments.extend(['role_name'])
        # check parameter exists and fill the keyword argument with them.
        for param_name in required_arguments:
            try:
                kwargs[param_name] = data[param_name]
            except KeyError:
                abort(400, f"'{param_name}' argument required")
        return func(*args, **kwargs)
    return wrapper


def jsonify_error(func):
    """Jsonify errors."""
    @wraps(func)
    def decorated_view(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HTTPException as httpe:
            return jsonify({'message': f'{httpe}'}), httpe.code
        except Exception as error:
            # raise error
            # current_app.logger.error(str(error))
            return jsonify({'message': f'{error}'}), 400
    return decorated_view


# STATISTICS DECORATORS =======================================================

def query_string_extract_operations_param(func):
    """Decorator to extract `operations` parameter from request query string.

    Extract from the request query string `operation` parameters and pass  all
    of them as new named arguments for decorated function. At the end of the
    decorator, operation values will be added into `operations` kwargs
    argument.
    """
    @wraps(func)
    def decorated_view(*args, **kwargs):
        operations = make_comma_list_a_list(request.args.getlist('operation'))
        operations = [op for op in operations if op] or \
            current_app.config.get('CIRCULATION_BASIC_OPERATIONS')
        kwargs['operations'] = operations
        return func(*args, **kwargs)
    return decorated_view


def query_string_extract_time_range_boundary(func):
    """Decorator to extract `from|to` parameters from request query string.

    Extract from the request query string `from` and `to` parameters and pass
    all of them as new named arguments for decorated function.
    """
    @wraps(func)
    def decorated_view(*args, **kwargs):
        for arg_name in ['from', 'to']:
            if arg_name in request.args:
                kwargs[arg_name] = request.args[arg_name]
        return func(*args, **kwargs)
    return decorated_view


def query_string_extract_histogram_interval_param(func):
    """Extract interval and format to use to build statistics.

    The interval and format parameter is related together. If we ask an
    interval of 1 minutes, the timestamp format should be coherent with
    this parameter to return correct data.

    The interval parameter should be defined using the standard
    ElasticSearch date histogram parameter into `interval` query string
    parameter. Depending on the specified interval, this function will
    determine if `calendar_interval` or `fixed_interval` interval type
    will be used.

    The format parameter allow to specify how the interval timestamp
    stamp will be formatted. User could either specify a format using
    `format` query string parameter (as ElasticSearch format pattern),
    either let the function determine the best format to use depending on
    interval previous parameter.
    """
    @wraps(func)
    def decorated_view(*args, **kwargs):
        params = {
            'interval': ('calendar_interval', '1d'),
            'format': 'yyyy-MM-dd',
            'from': 'now-1w',
            'to': 'now'
        }

        # if no query string params is specified :: no need to continue, return
        # with default settings
        if not any(param for param in params if param in request.args):
            kwargs.update(params)
            return func(*args, **kwargs)
        if qs_interval := request.args.get('interval'):
            # calendar_interval check
            regexp = r'^(minute|hour|day|week|month|quarter|year|1[mhdwMqy])$'
            calendar_regexp = re.compile(regexp)
            calendar_match = calendar_regexp.match(qs_interval)
            fixed_regexp = re.compile(r'^\d*(ms|[smhd])$')
            fixed_match = fixed_regexp.match(qs_interval)
            if calendar_match:
                params['interval'] = ('calendar_interval', qs_interval)
            # fixed_interval check
            elif fixed_match:
                params['interval'] = ('fixed_interval', qs_interval)
            # invalid interval
            else:
                abort(400, 'Invalid interval parameter')
        # check for `format` query string parameter. If not present, then
        # determine the best possible format to use based on interval params.
        if 'format' in request.args:
            params['format'] = request.args['format']
        else:
            format_switcher = {
                r'^\d+ms$': ('HH:mm:ss.SSS', 'now-1s'),
                r'^\d+s$': ('HH:mm:ss', 'now-1s'),
                r'^(\d*m|minute)$': ('HH:mm', 'now-1h'),
                r'^(\d*h|hour)$': ('HH:00', 'now-1d'),
                r'^(\d*d|day)$': ('yyyy-MM-dd', 'now-1w'),
                r'^(1w|week)$': ('yyyy-MM-dd', 'now-1M'),
                r'^(1M|month)$': ('yyyy-MM', 'now-1y'),
                r'^(1q|quarter)$': ('yyyy-MM', 'now-1y'),
                r'^(1y|year)$': ('yyyy', '*')
            }
            for regexp, (tstamp_format, from_date) in format_switcher.items():
                if re.match(regexp, params['interval'][1]):
                    params['format'] = tstamp_format
                    params['from'] = from_date
                    break
        # force query string `from|to` parameter if specified
        if 'from' in request.args:
            params['from'] = request.args['from']
        if 'to' in request.args:
            params['to'] = request.args['to']
        kwargs.update(params)
        return func(*args, **kwargs)

    return decorated_view


def query_string_extract_interval_param(default_value=None):
    """Decorator to extract `interval` parameter from request query string.

    Extract from the request query string the `interval` parameter as a simple
    numeric value. If the parameter isn't valid, the default value will be
    returned. At the end of the decorator, the interval will be available
    into `interval` kwargs argument.

    :param default_value: the default value to use if `interval` query string
        parameter doesn't exist or isn't a valid interval.
    """
    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            interval = default_value
            if 'interval' in request.args:
                with contextlib.suppress(ValueError):
                    interval = int(request.args.get('interval'))
            if interval:
                kwargs['interval'] = interval
            return func(*args, **kwargs)
        return decorated_function
    return decorator
