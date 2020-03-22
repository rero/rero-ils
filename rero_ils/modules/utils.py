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

"""Utilities for rero-ils editor."""

from datetime import time
from json import JSONDecodeError, JSONDecoder

import pytz
from dateutil import parser
from flask import current_app
from invenio_records_rest.utils import obj_or_import_string


def strtotime(strtime):
    """String to datetime."""
    splittime = strtime.split(':')
    return time(
        hour=int(splittime[0]),
        minute=int(splittime[1])
    )


def date_string_to_utc(date):
    """Converts a date of string format to a datetime utc aware."""
    parsed_date = parser.parse(date)
    if parsed_date.tzinfo:
        return parsed_date
    return pytz.utc.localize(parsed_date)


def read_json_record(json_file, buf_size=1024, decoder=JSONDecoder()):
    """Read lasy json records from file.

    :param json_file: json file handle
    :param buf_size: buffer size for file read
    :param decoder: decoder to use for decoding
    :return: record Generator
    """
    buffer = json_file.read(2).replace('\n', '')
    # we have to delete the first [ for an list of records
    if buffer.startswith('['):
        buffer = buffer[1:].lstrip()
    while True:
        block = json_file.read(buf_size)
        if not block:
            break
        buffer += block.replace('\n', '')
        pos = 0
        while True:
            try:
                buffer = buffer.lstrip()
                obj, pos = decoder.raw_decode(buffer)
            except JSONDecodeError as err:
                break
            else:
                yield obj
                buffer = buffer[pos:].lstrip()

                if len(buffer) <= 0:
                    # buffer is empty read more data
                    buffer = json_file.read(buf_size)
                if buffer.startswith(','):
                    # delete records deliminators
                    buffer = buffer[1:].lstrip()


def get_record_class_update_permission_from_route(route_name):
    """Return the record class for a given record route name."""
    endpoints = current_app.config.get('RECORDS_REST_ENDPOINTS')
    for endpoint in endpoints.items():
        record = endpoint[1]
        list_route = record.get('list_route').replace('/', '')
        if list_route == route_name:
            record_class = obj_or_import_string(record.get('record_class'))
            update_permission = obj_or_import_string(
                record.get('update_permission_factory_imp'))
            return record_class, update_permission


def get_ref_for_pid(module, pid):
    """Get the $ref for a pid.

    :param module: name of module (class name or endpoint name or module name)
    :param pid: pid for record
    :return: url for record
    """
    if not isinstance(module, str):
        # Get the pid_type for the class
        module = module.provider.pid_type
    endpoints = current_app.config.get('RECORDS_REST_ENDPOINTS')
    for endpoint in endpoints:
        search_index = endpoints[endpoint].get('search_index')
        # Try to find module in entpoints or entpoints.serch_index
        if search_index == module or endpoint == module:
            list_route = endpoints[endpoint].get('list_route')
            if list_route:
                return '{url}/api{route}{pid}'.format(
                    url=current_app.config.get('RERO_ILS_APP_BASE_URL'),
                    route=list_route,
                    pid=pid
                )
    return None
