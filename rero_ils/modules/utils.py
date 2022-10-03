# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
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

import cProfile
import os
import pstats
import re
import unicodedata
from datetime import date, datetime, time
from functools import wraps
from io import StringIO
from json import JSONDecodeError, JSONDecoder, dumps
from time import sleep

import click
import psycopg2
import pytz
import requests
import sqlalchemy
from dateutil import parser
from flask import current_app, session
from flask_login import current_user
from invenio_cache.proxies import current_cache
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_rest.utils import obj_or_import_string
from lazyreader import lazyread
from lxml import etree
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


def cached(timeout=50, key_prefix='default', query_string=False):
    """Cache traffic.

    Decorator. Use this to cache a function. By default the cache key is
    view/request.path. You are able to use this decorator with any function
    by changing the key_prefix. If the token %s is located within the
    key_prefix then it will replace that with request.path

    :param timeout: Default 50. If set to an integer, will cache
    for that amount of time. Unit of time is in seconds.
    :param key_prefix: Default ‘default’. Beginning key to . use for the
    cache key. request.path will be the actual request path, or in cases
    where the make_cache_key-function is called from other views it will be the
    expected URL for the view as generated by Flask’s url_for().
    :param query_string: Default False. When True, the cache key used will
    be the result of hashing the ordered query string parameters. This avoids
    creating different caches for the same query just because the parameters
    were passed in a different order.
    """
    def caching(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            cache_fun = current_cache.cached(
                timeout=timeout,
                key_prefix=key_prefix,
                query_string=query_string
            )
            return cache_fun(f)(*args, **kwargs)
        return wrapper
    return caching


def memoized(timeout=50):
    """Memoize functions.

    Use this to cache the result of a function, taking its arguments into
    account in the cache key.

    :param timeout: Default 50. If set to an integer, will cache for that
    amount of time. Unit of time is in seconds.
    """
    def memoize(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            memoize_fun = current_cache.memoize(timeout=timeout)
            return memoize_fun(f)(*args, **kwargs)
        return wrapper
    return memoize


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
        click.echo(f' add to index: {len(uuids)}')
    from .api import IlsRecordsIndexer
    indexer = IlsRecordsIndexer()
    retry = True
    minutes = 1
    while retry:
        try:
            indexer.bulk_index(uuids, doc_type=doc_type)
            retry = False
        except Exception as exc:
            msg = f'Bulk Index Error: retry in {minutes} min {exc}'
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
            except JSONDecodeError:
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


def lazyxmlstrings(file, opening_tag, closing_tag):
    """Split xml file into sub strings.

    :param file: xml file to parse
    :param opening_tag: opening tag
    :param closing_tag: closing tag
    "returns": generator with xml strings
    """
    for doc in lazyread(file, delimiter=closing_tag):
        if opening_tag not in doc:
            continue
        # We want complete XML blocks, so look for the opening tag and
        # just return its contents
        block = doc.split(opening_tag)[-1]
        yield opening_tag + block


def lazyxml(file, opening_tag, closing_tag):
    """Split xml file into sub etrees.

    :param file: xml file to parse
    :param opening_tag: opening tag
    :param closing_tag: closing tag
    "returns": generator with etrees
    """
    for xml_string in lazyxmlstrings(file, opening_tag, closing_tag):
        yield etree.fromstring(xml_string)


def read_xml_record(xml_file):
    """Read lazy xml records from file.

    :return: record Generator
    """
    yield from lazyxml(
        file=xml_file,
        opening_tag='<record>',
        closing_tag='</record>'
    )


def get_record_class_and_permissions_from_route(route_name):
    """Get record class and permission factories for a record route name."""
    endpoints = current_app.config.get('RECORDS_REST_ENDPOINTS')
    endpoints.update(current_app.config.get('CIRCULATION_REST_ENDPOINTS', {}))
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
    * extracted_data_from_ref('http://localhost/[resource]/[pid]', data='pid')
    * extracted_data_from_ref({'$ref': 'http://localhost/[resource]/[pid]'})
    """

    def extract_part(input_string, idx=0):
        """Extract part of a $ref string."""
        parts = input_string.split('/')
        if len(parts) > abs(idx):
            return input_string.split('/')[idx]

    def get_acronym():
        """Get resource acronym for a $ref URI."""
        resource_list = extracted_data_from_ref(input, data='resource')
        endpoints = {
            endpoint.get('search_index'): acronym
            for acronym, endpoint
            in current_app.config.get('RECORDS_REST_ENDPOINTS', {}).items()
        }
        return endpoints.get(resource_list)

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

    def get_data_from_es():
        """Try to load a resource from elasticsearch."""
        pid = extracted_data_from_ref(input, data='pid')
        resource_list = extracted_data_from_ref(input, data='resource')
        if resource_list is None:
            return None
        configuration = get_endpoint_configuration(resource_list)
        if pid and configuration and configuration.get('search_class'):
            search_class = obj_or_import_string(
                configuration.get('search_class'))
            result = search_class().filter('term', pid=pid).execute()
            if len(result) == 1:
                return result[0].to_dict()

    if isinstance(input, str):
        input = {'$ref': input}
    switcher = {
        'es_record': get_data_from_es,
        'pid': lambda: extract_part(input.get('$ref'), -1),
        'resource': lambda: extract_part(input.get('$ref'), -2),
        'acronym': get_acronym,
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


def trim_item_barcode_for_record(data=None):
    """Trim the barcode for a patron or an item record.

    :param data: the patron or item record
    :return: data with trimmed barcode
    """
    if data and data.get('barcode'):
        data['barcode'] = data.get('barcode').strip()
    if data and data.get('patron', {}).get('barcode'):
        data['patron']['barcode'][0] = data['patron']['barcode'][0].strip()
    return data


def generate_item_barcode(data=None):
    """Generate a barcode for an item record that does not have one.

    The generated barcode is in the format f-YYYYMMDDHHMISSSSS.

    :param data: the item record
    :return: data with a generated barcode
    """
    if not data.get('barcode'):
        data['barcode'] = 'f-' + datetime.now().strftime('%Y%m%d%I%M%S%f')
    if data.get('patron') and not data.get('patron', {}).get('barcode'):
        data['patron']['barcode'] = [
            'f-' + datetime.now().strftime('%Y%m%d%I%M%S%f')
        ]
    return data


def get_schema_for_resource(resource):
    """Return the schema corresponding to a resources.

    :param resource: Either the resource_type shortcut as a string,
                     Either a resource class (subclass of IlsRecord

    USAGE:
      schema = get_schema_for_resource('ptrn')
      shcema = get_schema_for_resource(Patron)
    """
    if not isinstance(resource, str):
        resource = resource.provider.pid_type
    schemas = current_app.config.get('RERO_ILS_DEFAULT_JSON_SCHEMA')
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
    if PersistentIdentifier.query\
       .filter_by(pid_type=str(pid_type), pid_value=str(pid))\
       .count() == 1:
        return True
    if raise_on_error:
        from .api import IlsRecordError
        raise IlsRecordError.PidDoesNotExist(info, pid_type, pid)


def pids_exists_in_data(info, data, required=None, not_required=None):
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
        for pid_type, keys in tests.items():
            # make a list of keys
            if isinstance(keys, str):
                keys = [keys]
            for key in keys:
                data_to_test_list = data.get(key, [])
                if isinstance(data_to_test_list, dict):
                    data_to_test_list = [data_to_test_list]
                for data_to_test in data_to_test_list:
                    try:
                        list_route = endpoints[pid_type]['list_route']
                        data_pid = data_to_test.get('pid') or \
                            data_to_test.get('$ref').split(list_route)[1]
                    except Exception:
                        data_pid = None
                    if not data_pid and is_required:
                        return_value.append(f'{info}: No pid found: '
                                            f'{pid_type} {data_to_test}')
                    else:
                        if data_pid and not pid_exists(
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
                if is_required and not data_to_test_list:
                    return_value.append(
                        f'{info}: No data found: {key}')
        return return_value

    required = required or {}
    not_required = not_required or {}

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
    return '{scheme}://{host}'.format(
        scheme=current_app.config.get('RERO_ILS_APP_URL_SCHEME'),
        host=current_app.config.get('RERO_ILS_APP_HOST')
    )


def get_ref_for_pid(module, pid):
    """Get the $ref for a pid.

    :param module: name of module (class name or endpoint name or module name)
    :param pid: pid for record
    :return: url for record
    """
    configuration = get_endpoint_configuration(module)
    if module == 'loans':
        configuration = {'list_route': '/loans/'}
    if configuration and configuration.get('list_route'):
        return '{url}/api{route}{pid}'.format(
            url=get_base_url(),
            route=configuration.get('list_route'),
            pid=pid
        )


def get_record_class_from_schema_or_pid_type(schema=None, pid_type=None):
    """Get the record class from a given schema or a pid type.

    If both the schema and pid_type are given, the record_class of the
    schema will be returned.

    :param schema: record schema.
    :param pid_type: record pid type.
    :return: the record class.
    """
    if schema:
        try:
            pid_type_schema_value = schema.split('schemas')[1]
            schemas = current_app.config.get('RERO_ILS_DEFAULT_JSON_SCHEMA')
            pid_type = [key for key, value in schemas.items()
                        if value == pid_type_schema_value][0]
        except IndexError:
            pass
    return obj_or_import_string(
        current_app.config
        .get('RECORDS_REST_ENDPOINTS')
        .get(pid_type, {}).get('record_class'))


def get_patron_from_arguments(**kwargs):
    """Try to load a patron from potential arguments."""
    from .patrons.api import Patron
    required_arguments = ['patron', 'patron_barcode', 'patron_pid', 'loan']
    if all(k not in required_arguments for k in kwargs):
        return None
    return kwargs.get('patron') \
        or Patron.get_record_by_pid(kwargs.get('patron_pid')) \
        or Patron.get_record_by_pid(kwargs.get('loan').get('patron_pid'))


def set_timestamp(name, **kwargs):
    """Set timestamp in current cache.

    Allows to timestamp functionality and monitoring of the changed
    timestamps externaly via url requests.

    :param name: name of time stamp.
    :returns: time of time stamp
    """
    time_stamps = current_cache.get('timestamps')
    if not time_stamps:
        time_stamps = {}
    utc_now = datetime.utcnow()
    time_stamps[name] = {}
    time_stamps[name]['time'] = utc_now
    for key, value in kwargs.items():
        time_stamps[name][key] = value
    if not current_cache.set(key='timestamps', value=time_stamps, timeout=0):
        current_app.logger.warning(
            f'Can not set time stamp for: {name}')
    return utc_now


def settimestamp(func):
    """Set timestamp function wrapper."""
    @wraps(func)
    def wrapped(*args, **kwargs):
        result = func(*args, **kwargs)
        set_timestamp(func.__name__, result=result)
        return result
    return wrapped


def profile(output_file=None, sort_by='cumulative', lines_to_print=None,
            strip_dirs=False):
    """A time profiler decorator.

    Inspired by and modified the profile decorator of Giampaolo Rodola:
    http://code.activestate.com/recipes/577817-profile-decorator/
    Args:
        output_file: str or None. Default is None
            Path of the output file. If only name of the file is given, it's
            saved in the current directory.
            If it's None, the name of the decorated function is used.
        sort_by: str or SortKey enum or tuple/list of str/SortKey enum
            Sorting criteria for the Stats object.
            For a list of valid string and SortKey refer to:
            https://docs.python.org/3/library/profile.html#pstats.Stats.sort_stats
        lines_to_print: int or None
            Number of lines to print. Default (None) is for all the lines.
            This is useful in reducing the size of the printout, especially
            that sorting by 'cumulative', the time consuming operations
            are printed toward the top of the file.
        strip_dirs: bool
            Whether to remove the leading path info from file names.
            This is also useful in reducing the size of the printout
    Returns:
        Profile of the decorated function
    """

    def inner(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            _output_file = output_file or func.__name__ + '.prof'
            pr = cProfile.Profile()
            pr.enable()
            retval = func(*args, **kwargs)
            pr.disable()
            pr.dump_stats(_output_file)

            with open(_output_file, 'w') as f:
                ps = pstats.Stats(pr, stream=f)
                if strip_dirs:
                    ps.strip_dirs()
                if isinstance(sort_by, (tuple, list)):
                    ps.sort_stats(*sort_by)
                else:
                    ps.sort_stats(sort_by)
                ps.print_stats(lines_to_print)
            return retval

        return wrapper

    return inner


def timeit(func):
    """Output how long a function took to execute."""
    @wraps(func)
    def wrapped(*args, **kwargs):
        start_time = datetime.now()
        result = func(*args, **kwargs)
        click.echo('\t>> timeit: {time} {func_name} {args}'.format(
            time=datetime.now() - start_time,
            func_name=func,
            args=type(args[0])
        ))
        return result
    return wrapped


def get_timestamp(name):
    """Get timestamp in current cache.

    :param name: name of time stamp.
    :returns: time of time stamp
    """
    time_stamps = current_cache.get('timestamps')
    if not time_stamps:
        return None
    return time_stamps.get(name)


def csv_metadata_line(record, uuid, date):
    """Build CSV metadata table line."""
    created_date = updated_date = date
    sep = '\t'
    data = unicodedata.normalize('NFC', dumps(record, ensure_ascii=False))
    metadata = (
        created_date,
        updated_date,
        uuid,
        data,
        '1',
    )
    metadata_line = sep.join(metadata)
    return metadata_line + '\n'


def csv_pidstore_line(pid_type, pid, uuid, date):
    """Build CSV pidstore table line."""
    created_date = updated_date = date
    sep = '\t'
    pidstore_data = [
        created_date,
        updated_date,
        pid_type,
        pid,
        'R',
        'rec',
        uuid,
    ]
    pidstore_line = sep.join(pidstore_data)
    return pidstore_line + '\n'


def raw_connection():
    """Return a raw connection to the database."""
    with current_app.app_context():
        URI = current_app.config.get('SQLALCHEMY_DATABASE_URI')
        engine = sqlalchemy.create_engine(URI)
        connection = engine.raw_connection()
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return connection


def db_copy_from(buffer, table, columns, raise_exception=True):
    """Copy data from file to db."""
    connection = raw_connection()
    cursor = connection.cursor()
    try:
        cursor.copy_from(
            file=buffer,
            table=table,
            columns=columns,
            sep='\t'
        )
        connection.commit()
    except psycopg2.DataError as error:
        if raise_exception:
            raise psycopg2.DataError(error)
        else:
            current_app.logger.error('data load error: {0}'.format(error))
    connection.close()


def db_copy_to(filehandle, table, columns, raise_exception=True):
    """Copy data from db to file."""
    connection = raw_connection()
    cursor = connection.cursor()
    try:
        cursor.copy_to(
            file=filehandle,
            table=table,
            columns=columns,
            sep='\t'
        )
        cursor.connection.commit()
    except psycopg2.DataError as error:
        if raise_exception:
            raise psycopg2.DataError(error)
        else:
            current_app.logger.error('data load error: {0}'.format(error))
    cursor.execute('VACUUM ANALYSE {table}'.format(table=table))
    cursor.close()
    connection.close()


def bulk_load(pid_type, data, table, columns, bulk_count=0, verbose=False,
              reindex=False):
    """Bulk load pid_type data to table."""
    if bulk_count <= 0:
        bulk_count = current_app.config.get('BULK_CHUNK_COUNT', 100000)
    count = 0
    buffer = StringIO()
    buffer_uuid = []
    index = columns.index('id') if 'id' in columns else -1
    start_time = datetime.now()
    with open(data, 'r', encoding='utf-8', buffering=1) as input_file:
        for line in input_file:
            count += 1
            buffer.write(line.replace('\\', '\\\\'))
            if index >= 0 and reindex:
                buffer_uuid.append(line.split('\t')[index])
            if count % bulk_count == 0:
                buffer.flush()
                buffer.seek(0)
                if verbose:
                    end_time = datetime.now()
                    diff_time = end_time - start_time
                    start_time = end_time
                    click.echo(
                        '{pid_type} copy from file: {count} {time}s'.format(
                            pid_type=pid_type,
                            count=count,
                            time=diff_time.seconds
                        ),
                        nl=False
                    )
                db_copy_from(buffer=buffer, table=table, columns=columns)
                buffer.close()

                if index >= 0 and reindex:
                    do_bulk_index(uuids=buffer_uuid, doc_type=pid_type,
                                  verbose=verbose)
                    buffer_uuid.clear()
                elif verbose:
                    click.echo()
                buffer = StringIO()

        if verbose:
            end_time = datetime.now()
            diff_time = end_time - start_time
            click.echo(
                '{pid_type} copy from file: {count} {time}s'.format(
                    pid_type=pid_type,
                    count=count,
                    time=diff_time.seconds
                ),
                nl=False
            )
        buffer.flush()
        buffer.seek(0)
        db_copy_from(buffer=buffer, table=table, columns=columns)
        buffer.close()
        if index >= 0 and reindex:
            do_bulk_index(uuids=buffer_uuid, doc_type=pid_type,
                          verbose=verbose)
            buffer_uuid.clear()
        elif verbose:
            click.echo()


def bulk_load_metadata(pid_type, metadata, bulk_count=0, verbose=True,
                       reindex=False):
    """Bulk load pid_type data to metadata table."""
    record_class = get_record_class_from_schema_or_pid_type(pid_type=pid_type)
    table, identifier = record_class.get_metadata_identifier_names()
    columns = (
        'created',
        'updated',
        'id',
        'json',
        'version_id'
    )
    bulk_load(
        pid_type=pid_type,
        data=metadata,
        table=table,
        columns=columns,
        bulk_count=bulk_count,
        verbose=verbose,
        reindex=reindex
    )


def bulk_load_pidstore(pid_type, pidstore, bulk_count=0, verbose=True,
                       reindex=False):
    """Bulk load pid_type data to metadata table."""
    table = 'pidstore_pid'
    columns = (
        'created',
        'updated',
        'pid_type',
        'pid_value',
        'status',
        'object_type',
        'object_uuid',
    )
    bulk_load(
        pid_type=pid_type,
        data=pidstore,
        table=table,
        columns=columns,
        bulk_count=bulk_count,
        verbose=verbose,
        reindex=reindex
    )


def bulk_load_pids(pid_type, ids, bulk_count=0, verbose=True, reindex=False):
    """Bulk load pid_type data to id table."""
    record_class = get_record_class_from_schema_or_pid_type(pid_type=pid_type)
    metadata, identifier = record_class.get_metadata_identifier_names()
    columns = ('recid', )
    bulk_load(
        pid_type=pid_type,
        data=ids,
        table=identifier.__tablename__,
        columns=columns,
        bulk_count=bulk_count,
        verbose=verbose,
        reindex=reindex
    )
    max_pid = 0
    with open(ids) as file:
        for line in file:
            pid = int(line)
            if pid > max_pid:
                max_pid = pid
    identifier._set_sequence(max_pid)


def bulk_save(pid_type, file_name, table, columns, verbose=False):
    """Bulk save pid_type data to file."""
    with open(file_name, 'w', encoding='utf-8') as output_file:
        db_copy_to(
            filehandle=output_file,
            table=table,
            columns=columns
        )


def bulk_save_metadata(pid_type, file_name, verbose=False):
    """Bulk save pid_type data from metadata table."""
    if verbose:
        click.echo('Save {pid_type} metadata to file: {filename}'.format(
            pid_type=pid_type,
            filename=file_name
        ))
    record_class = get_record_class_from_schema_or_pid_type(pid_type=pid_type)
    metadata, identifier = record_class.get_metadata_identifier_names()
    columns = (
        'created',
        'updated',
        'id',
        'json',
        'version_id'
    )
    bulk_save(
        pid_type=pid_type,
        file_name=file_name,
        table=metadata,
        columns=columns,
        verbose=verbose
    )


def bulk_save_pidstore(pid_type, file_name, file_name_tmp, verbose=False):
    """Bulk save pid_type data from pids table."""
    if verbose:
        click.echo('Save {pid_type} pidstore to file: {filename}'.format(
            pid_type=pid_type,
            filename=file_name
        ))
    if not os.path.isfile(file_name_tmp):
        table = 'pidstore_pid'
        columns = (
            'created',
            'updated',
            'pid_type',
            'pid_value',
            'status',
            'object_type',
            'object_uuid',
        )
        bulk_save(
            pid_type=pid_type,
            file_name=file_name_tmp,
            table=table,
            columns=columns,
            verbose=verbose
        )
    # clean pid file
    with open(file_name_tmp, 'r') as file_in:
        with open(file_name, "w") as file_out:
            count = 0
            for line in file_in:
                if pid_type in line:
                    count += 1
                    file_out.write(line)
    return count


def bulk_save_pids(pid_type, file_name, verbose=False):
    """Bulk save pid_type data from id table."""
    if verbose:
        click.echo('Save {pid_type} ids to file: {filename}'.format(
            pid_type=pid_type,
            filename=file_name
        ))
    record_class = get_record_class_from_schema_or_pid_type(pid_type=pid_type)
    metadata, identifier = record_class.get_metadata_identifier_names()
    columns = ('recid', )
    bulk_save(
        pid_type=pid_type,
        file_name=file_name,
        table=identifier.__tablename__,
        columns=columns,
        verbose=verbose
    )


def number_records_in_file(json_file, type):
    """Get number of records per file."""
    count = 0
    with open(json_file, 'r',  buffering=1) as file:
        for line in file:
            if (type == 'json' and '"pid"' in line) or type == 'csv':
                count += 1
    return count


def requests_retry_session(retries=5, backoff_factor=0.5,
                           status_forcelist=(500, 502, 504), session=None):
    """Request retry session.

    :params retries: The total number of retry attempts to make.
    :params backoff_factor: Sleep between failed requests.
        {backoff factor} * (2 ** ({number of total retries} - 1))
    :params status_forcelist: The HTTP response codes to retry on..
    :params session: Session to use.

    """
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


class JsonWriter(object):
    """Json Writer."""

    count = 0

    def __init__(self, filename, indent=2):
        """Constructor.

        :params filename: File name of the file to be written.
        :param indent: indentation.
        """
        self.indent = indent
        self.file_handle = open(filename, 'w')
        self.file_handle.write('[')

    def __del__(self):
        """Destructor."""
        if self.file_handle:
            self.file_handle.write('\n]')
            self.file_handle.close()
            self.file_handle = None

    def write(self, data):
        """Write data to file.

        :param data: JSON data to write into the file.
        """
        if self.count > 0:
            self.file_handle.write(',')
        if self.indent:
            for line in dumps(data, indent=self.indent).split('\n'):
                self.file_handle.write(f'\n{" ".ljust(self.indent)}')
                self.file_handle.write(line)
        else:
            self.file_handle.write(dumps(data), separators=(',', ':'))
        self.count += 1

    def close(self):
        """Close file."""
        self.__del__()


def set_user_name(sender, user):
    """Set the username in the current flask session."""
    from .patrons.api import current_librarian, current_patrons
    user_name = None
    remove_user_name(sender, user)

    if current_librarian:
        user_name = current_librarian.formatted_name
    elif current_patrons:
        user_name = current_patrons[0].formatted_name
    else:
        try:
            user_name = current_user.email
        # AnonymousUser
        except AttributeError:
            pass
    if user_name:
        session['user_name'] = user_name


def remove_user_name(sender, user):
    """Remove the username in the current flask session."""
    if session.get('user_name'):
        del session['user_name']


def sorted_pids(query):
    """Get sorted pids from a ES query."""
    pids = [hit.pid for hit in query.source('pid').scan()]
    try:
        return sorted(pids, key=int)
    except Exception as err:
        current_app.logger.info(f'Can not sort pids from query: {err}')
    return pids


def get_objects(record_class, query):
    """Get record object from search query by record id.

    :param query: search query
    :param record_class: record_class
    :return generator of records object.
    """
    for hit in query.source().scan():
        yield record_class.get_record_by_id(hit.meta.id)


def strip_chars(string, extra=u''):
    """Remove control characters from string."""
    remove_re = re.compile(u'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F%s]' % extra)
    new_string, _ = remove_re.subn('', string)
    return new_string
