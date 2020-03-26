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

from datetime import date, time
from json import JSONDecodeError, JSONDecoder
from time import sleep

import click
import pytz
from dateutil import parser
from flask import current_app
from invenio_records_rest.utils import obj_or_import_string

from .api import IlsRecordIndexer


def strtotime(strtime):
    """String to datetime."""
    splittime = strtime.split(':')
    return time(
        hour=int(splittime[0]),
        minute=int(splittime[1])
    )


def do_bulk_index(uuids, doc_type='rec', process=False, verbose=False):
    """Bulk index records."""
    if verbose:
        click.echo(' add to index: {count}'.format(count=len(uuids)))
    indexer = IlsRecordIndexer()
    retry = True
    minutes = 1
    while retry:
        try:
            indexer.bulk_index(uuids, doc_type=doc_type)
            retry = False
        except Exception as exc:
            msg = 'Bulk Index Error: retry in {minutes} min {exc}'.format(
                exc=exc,
                minutes=minutes
            )
            current_app.logger.error(msg)
            if verbose:
                click.secho(msg, fg='red')
            sleep(minutes * 60)
            retry = True
            minutes *= 2
    if process:
        indexer.process_bulk_queue()


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


def add_years(initial_date, years):
    """Return a date that's `years` years after the date (or datetime) object.

    Return the same calendar date (month and day) in the destination year,
    if it exists, otherwise use the following day (thus changing February 29
    to March 1).

    source: https://stackoverflow.com/a/15743908/5595377
    """
    try:
        return initial_date.replace(year=initial_date.year + years)
    except ValueError:
        return initial_date + (date(initial_date.year + years, 1, 1) -
                               date(initial_date.year, 1, 1))


def trim_barcode_for_record(data=None):
    """Trim the barcode for a patron or an item record.

    :param data: the patron or item record
    :return: data with trimmed barcode
    """
    if data and data.get('barcode'):
        data['barcode'] = data.get('barcode').strip()
    return data
