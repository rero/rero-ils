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

from datetime import date, datetime, time
from json import JSONDecodeError, JSONDecoder
from time import sleep

import click
import pytz
from dateutil import parser
from flask import current_app
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_rest.utils import obj_or_import_string

from .api import IlsRecordError, IlsRecordsIndexer


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
    indexer = IlsRecordsIndexer()
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


def get_record_class_and_permissions_from_route(route_name):
    """Get record class and permission factories for a record route name."""
    endpoints = current_app.config.get('RECORDS_REST_ENDPOINTS')
    for endpoint in endpoints.items():
        record = endpoint[1]
        list_route = record.get('list_route').replace('/', '')
        if list_route == route_name:
            record_class = obj_or_import_string(record.get('record_class'))
            permissions = dict(
                read=obj_or_import_string(
                    record.get('read_permission_factory_imp')),
                list=obj_or_import_string(
                    record.get('list_permission_factory_imp')),
                create=obj_or_import_string(
                    record.get('create_permission_factory_imp')),
                update=obj_or_import_string(
                    record.get('update_permission_factory_imp')),
                delete=obj_or_import_string(
                    record.get('delete_permission_factory_imp'))
            )
            return record_class, permissions


def get_endpoint_configuration(module):
    """Search into configuration file to find configuration for a module.

    :param module: name of module (class name or endpoint name or module name)
    :return: The configuration dictionary of the resource. 'None' if resource
             is not found.
    """
    if not isinstance(module, str):
        # Get the pid_type for the class
        module = module.provider.pid_type
    endpoints = current_app.config.get('RECORDS_REST_ENDPOINTS', {})
    for idx, endpoint in endpoints.items():
        search_index = endpoint.get('search_index')
        if search_index == module or idx == module:
            return endpoint


def extracted_data_from_ref(input, data='pid'):
    """Extract a data from a `$ref` string.

    :param input: string where to search data, or a dict containing '$ref' key
    :param data: the data to found. Allowed values are :
        * 'pid': the pid from the input
        * 'resource': the resource search_index from input
        * 'record_class': the record class to used to manage the input
        * 'record': the record represented by the input

    USAGE :
      * extract_pid_from_ref('http://localhost/[resource]/[pid]', data='pid')
      * extract_pid_from_ref({'$ref': 'http://localhost/[resource]/[pid]'})
    """

    def extract_part(input_string, idx=0):
        """Extract part of a $ref string."""
        parts = input_string.split('/')
        if len(parts) > abs(idx):
            return input_string.split('/')[idx]

    def get_record_class():
        """Search about a record_class name for a $ref URI."""
        resource_list = extracted_data_from_ref(input, data='resource')
        if resource_list is None:
            return None
        configuration = get_endpoint_configuration(resource_list)
        if configuration and configuration.get('record_class'):
            return obj_or_import_string(configuration.get('record_class'))

    def get_record():
        """Try to load a resource corresponding to a $ref URI."""
        pid = extracted_data_from_ref(input, data='pid')
        record_class = extracted_data_from_ref(input, data='record_class')
        if record_class and pid:
            return record_class.get_record_by_pid(pid)

    if isinstance(input, str):
        input = {'$ref': input}
    switcher = {
        'pid': lambda: extract_part(input.get('$ref'), -1),
        'resource': lambda: extract_part(input.get('$ref'), -2),
        'record_class': get_record_class,
        'record': get_record
    }
    if data in switcher:
        return switcher.get(data)()


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


def generate_item_barcode(data=None):
    """Generate a barcode for an item record that does not have one.

    The generated barcode is in the format f-YYYYMMDDHHMISSSSS.

    :param data: the item record
    :return: data with a generated barcode
    """
    if not data.get('barcode'):
        data['barcode'] = 'f-{}'.format(
            datetime.now().strftime('%Y%m%d%I%M%S%f'))
    return data


def get_schema_for_resource(resource):
    """Return the schema corresponding to a resources.

    :param resource: Either the resource_type shortcut as a string,
                     Either a resource class (subclass of IlsRecord

    USAGE:
      schema = get_schemas_for_resource('ptrn')
      shcema = get_schemas_for_resource(Patron)
    """
    if not isinstance(resource, str):
        resource = resource.provider.pid_type
    schemas = current_app.config.get('RECORDS_JSON_SCHEMA')
    if resource in schemas:
        return '{scheme}://{url}{endpoint}{schema}'.format(
            scheme=current_app.config.get('JSONSCHEMAS_URL_SCHEME'),
            url=current_app.config.get('JSONSCHEMAS_HOST'),
            endpoint=current_app.config.get('JSONSCHEMAS_ENDPOINT'),
            schema=schemas[resource]
        )


def pid_exists(info, pid_type, pid, raise_on_error=False):
    """Test pid exist in pid_type.

    :param pid_type: Pid type to test the pid for.
    :param pid: Pid to search for.
    :param raise_on_error: Raise PidDoesNotExist exception if enabled.
    :return: True if pid was found. Otherwise False.
    """
    if PersistentIdentifier.query.filter_by(
        pid_type=str(pid_type), pid_value=str(pid)
    ).count() == 1:
        return True
    else:
        if raise_on_error:
            raise IlsRecordError.PidDoesNotExist(info, pid_type, pid)
        return False


def pids_exists_in_data(info, data, required={}, not_required={}):
    """Test pid or $ref has valid pid.

    :param info:  Info to add to errors description.
    :param data: data with information to test.
    :param required: dictionary with required pid types and key in data to
        test. example {'doc', 'document'}
    :param not_required: dictionary with not required pid types and keys
        in data to test. example {'item', 'item'}
    :return: True if all requirements  Otherwise False.
    """
    def pids_exists_in_data_test(info, data, tests, is_required):
        """Test the pids exists."""
        return_value = []
        endpoints = current_app.config['RECORDS_REST_ENDPOINTS']
        for pid_type, key in tests.items():
            data_to_test = data.get(key)
            if data_to_test:
                try:
                    list_route = endpoints[pid_type]['list_route']
                    data_pid = data_to_test.get('pid') or \
                        data_to_test.get('$ref').split(list_route)[1]
                except:
                    data_pid = None
                if not data_pid and is_required:
                    return_value.append(
                        '{info}: No pid found: {pid_type} {data}'.format(
                            info=info,
                            pid_type=pid_type,
                            data=data_to_test
                        )
                    )
                else:
                    if not pid_exists(
                        info=info,
                        pid_type=pid_type,
                        pid=data_pid
                    ):
                        return_value.append(
                            '{info}: {text} {pid_type} {pid}'.format(
                                info=info,
                                text='Pid does not exist:',
                                pid_type=pid_type,
                                pid=data_pid
                            )
                        )
            else:
                if is_required:
                    return_value.append(
                        '{info}: {text} {key}'.format(
                            info=info,
                            text='No data found:',
                            key=key
                        )
                    )
        return return_value

    return_value_required = pids_exists_in_data_test(
        info=info,
        data=data,
        tests=required,
        is_required=True
    )
    return_value_not_required = pids_exists_in_data_test(
        info=info,
        data=data,
        tests=not_required,
        is_required=False
    )
    return return_value_required + return_value_not_required


def get_base_url():
    """Get base url."""
    base_url = '{scheme}://{host}'.format(
        scheme=current_app.config.get('RERO_ILS_APP_URL_SCHEME'),
        host=current_app.config.get('RERO_ILS_APP_HOST')
    )
    return base_url


def get_ref_for_pid(module, pid):
    """Get the $ref for a pid.

    :param module: name of module (class name or endpoint name or module name)
    :param pid: pid for record
    :return: url for record
    """
    configuration = get_endpoint_configuration(module)
    if configuration and configuration.get('list_route'):
        return '{url}/api{route}{pid}'.format(
            url=get_base_url(),
            route=configuration.get('list_route'),
            pid=pid
        )
