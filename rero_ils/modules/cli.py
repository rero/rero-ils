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

"""Click command-line utilities."""

from __future__ import absolute_import, print_function

import difflib
import gc
import json
import logging
import multiprocessing
import os
import sys
from collections import OrderedDict
from glob import glob
from json import JSONDecodeError, JSONDecoder, loads

import click
import jsonref
import yaml
from dojson.contrib.marc21.utils import create_record, split_stream
from flask import current_app
from flask.cli import with_appcontext
from flask_security.confirmable import confirm_user
from invenio_accounts.cli import commit, users
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.api import Record
from invenio_records_rest.utils import obj_or_import_string
from invenio_search.cli import es_version_check
from invenio_search.proxies import current_search
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from lxml import etree
from pkg_resources import resource_string
from werkzeug.local import LocalProxy

from .documents.dojson.contrib.marc21tojson import marc21tojson
from .items.cli import create_items, reindex_items
from .loans.cli import create_loans
from .patrons.cli import import_users
from ..modules.providers import append_fixtures_new_identifiers

_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


@click.group()
def fixtures():
    """Fixtures management commands."""


fixtures.add_command(import_users)
fixtures.add_command(create_items)
fixtures.add_command(reindex_items)
fixtures.add_command(create_loans)


@users.command('confirm')
@click.argument('user')
@with_appcontext
@commit
def manual_confirm_user(user):
    """Confirm a user."""
    user_obj = _datastore.get_user(user)
    if user_obj is None:
        raise click.UsageError('ERROR: User not found.')
    if confirm_user(user_obj):
        click.secho('User "%s" has been confirmed.' % user, fg='green')
    else:
        click.secho('User "%s" was already confirmed.' % user, fg='yellow')


@click.group()
def utils():
    """Misc management commands."""


@utils.command('show')
@click.argument('pid_value', nargs=1)
@click.option('-t', '--pid-type', 'pid-type, default(document_id)',
              default='document_id')
@with_appcontext
def show(pid_value, pid_type):
    """Show records."""
    record = PersistentIdentifier.query.filter_by(pid_type=pid_type,
                                                  pid_value=pid_value).first()
    recitem = Record.get_record(record.object_uuid)
    click.echo(json.dumps(recitem.dumps(), indent=2))


@utils.command('check_json')
@click.argument('paths', nargs=-1)
@click.option(
    '-r', '--replace', 'replace', is_flag=True, default=False,
    help='change file in place default=False'
)
@click.option(
    '-s', '--sort-keys', 'sort_keys', is_flag=True, default=False,
    help='order keys during replacement default=False'
)
@click.option(
    '-i', '--indent', 'indent', type=click.INT, default=2,
    help='intent default=2'
)
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
def check_json(paths, replace, indent, sort_keys, verbose):
    """Check json files."""
    click.secho('Testing JSON indentation.', fg='green')
    files_list = []
    for path in paths:
        if os.path.isfile(path):
            files_list.append(path)
        elif os.path.isdir(path):
            files_list = files_list + glob(os.path.join(path, '**/*.json'),
                                           recursive=True)
    if not paths:
        files_list = glob('**/*.json', recursive=True)
    tot_error_cnt = 0
    for path_file in files_list:
        error_cnt = 0
        try:
            fname = path_file
            with open(fname, 'r') as opened_file:
                json_orig = opened_file.read().rstrip()
                opened_file.seek(0)
                json_file = json.load(opened_file,
                                      object_pairs_hook=OrderedDict)
            json_dump = json.dumps(json_file, indent=indent).rstrip()
            if json_dump != json_orig:
                error_cnt = 1
            if replace:
                with open(fname, 'w') as opened_file:
                    opened_file.write(json.dumps(json_file,
                                                 indent=indent,
                                                 sort_keys=sort_keys))
                click.echo(fname + ': ', nl=False)
                click.secho('File replaced', fg='yellow')
            else:
                if error_cnt == 0:
                    if verbose:
                        click.echo(fname + ': ', nl=False)
                        click.secho('Well indented', fg='green')
                else:
                    click.echo(fname + ': ', nl=False)
                    click.secho('Bad indentation', fg='red')
        except ValueError as e:
            click.echo(fname + ': ', nl=False)
            click.secho('Invalid JSON', fg='red', nl=False)
            click.echo(' -- ' + e.msg)
            import traceback
            traceback.print_exc()
            error_cnt = 1

        tot_error_cnt += error_cnt

    sys.exit(tot_error_cnt)


@utils.command('schedules')
@with_appcontext
def schedules():
    """List harvesting schedules."""
    celery_ext = current_app.extensions.get('invenio-celery')
    for key, value in celery_ext.celery.conf.beat_schedule.items():
        click.echo(key + '\t', nl=False)
        click.echo(value)


@utils.command()
@click.option('--force', is_flag=True, default=False)
@with_appcontext
@es_version_check
def init(force):
    """Initialize registered templates, aliases and mappings."""
    # TODO: to remove once it is fixed in invenio-search module
    click.secho('Putting templates...', fg='green', bold=True, file=sys.stderr)
    with click.progressbar(
            current_search.put_templates(ignore=[400] if force else None),
            length=len(current_search.templates.keys())) as bar:
        for response in bar:
            bar.label = response
    click.secho('Creating indexes...', fg='green', bold=True, file=sys.stderr)
    with click.progressbar(
            current_search.create(ignore=[400] if force else None),
            length=current_search.number_of_indexes) as bar:
        for name, response in bar:
            bar.label = name


def read_json_record(json_file, buf_size=1024, decoder=JSONDecoder()):
    """Read lasy json records from file."""
    buffer = json_file.read(5)
    # we have to delete the first [ for an list of records
    if buffer.startswith('['):
        buffer = buffer[-1:].lstrip()
    while True:
        block = json_file.read(buf_size)
        if not block:
            break
        buffer += block
        pos = 0
        while True:
            try:
                buffer = buffer.lstrip()
                obj, pos = decoder.raw_decode(buffer)
            except JSONDecodeError as err:
                break
            else:
                yield obj
                buffer = buffer[pos:]
                if buffer.startswith(','):
                    buffer = buffer[1:]


@click.command('create')
@click.option('-a', '--append', 'append', is_flag=True, default=False)
@click.option('-r', '--reindex', 'reindex', is_flag=True, default=False)
@click.option('-c', '--dbcommit', 'dbcommit', is_flag=True, default=True)
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=True)
@click.option('-s', '--schema', 'schema', default=None)
@click.option('-p', '--pid_type', 'pid_type', default=None)
@click.argument('infile', type=click.File('r'), default=sys.stdin)
@with_appcontext
def create(infile, pid_type, schema, verbose, dbcommit, reindex, append):
    """Load REROILS record.

    infile: Json file
    reindex: reindex record by record
    dbcommit: commit record to database
    pid_type: record type
    schema: recoord schema
    """
    click.secho(
        'Loading {pid_type} records from {file_name}.'.format(
            pid_type=pid_type,
            file_name=infile.name
        ),
        fg='green'
    )
    record_class = obj_or_import_string(
        current_app.config
        .get('RECORDS_REST_ENDPOINTS')
        .get(pid_type).get('record_class', Record))
    count = 0
    error_records = []
    pids = []
    for record in read_json_record(infile):
        count += 1
        if schema:
            record['$schema'] = schema
        try:
            rec = record_class.create(record, dbcommit=dbcommit,
                                      reindex=reindex)
            if append:
                pids.append(rec.pid)
            if verbose:
                click.echo(
                    '{count: <8} {pid_type} created {pid}:{id}'.format(
                        count=count,
                        pid_type=pid_type,
                        pid=rec.pid,
                        id=rec.id
                    )
                )
        except Exception as err:
            error_records.append(record)
            click.secho(
                '{count: <8} {pid_type} creat error {pid}: {err}'.format(
                    count=count,
                    pid_type=pid_type,
                    pid=record.get('pid', '???'),
                    err=err.args[0]
                ),
                err=True,
                fg='red'
                )

    if error_records:
        err_file_name = '{pid_type}_error.json'.format(pid_type=pid_type)
        with open(err_file_name, 'w') as error_file:
            error_file.write('[\n')
            for error_record in error_records:
                for line in json.dumps(error_record, indent=2).split('\n'):
                    error_file.write('  ' + line + '\n')
            error_file.write(']')

    if append:
        identifier = record_class.provider.identifier
        try:
            append_fixtures_new_identifiers(identifier, sorted(pids), pid_type)
        except Exception as err:
            pass


fixtures.add_command(create)


@utils.command('check_license')
@click.argument('configfile', type=click.File('r'), default=sys.stdin)
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@click.option('-p', '--progress', 'progress', is_flag=True, default=False)
def check_license(configfile, verbose, progress):
    """Check licenses."""
    click.secho('Testing licenses in files.', fg='green')

    def get_files(paths, extensions, recursive=True):
        """Get files from paths."""
        files_list = []
        for path in paths:
            if os.path.isfile(path):
                files_list.append(path)
            elif os.path.isdir(path):
                for extension in extensions:
                    files_list += glob(
                        os.path.join(path, '**/*.{extension}'.format(
                            extension=extension
                        )),
                        recursive=recursive
                    )
        return files_list

    def delete_prefix(prefix, line):
        """Delete prefix from line."""
        if prefix:
            line = line.replace(prefix, "")
        return line.strip()

    def is_copyright(copyrides, line):
        """Delete prefix from line."""
        for copyride in copyrides[1:]:
            if line == copyride:
                return True
        return False

    def show_diff(linenbr, text, n_text):
        """Show string diffs."""
        seqm = difflib.SequenceMatcher(
            None,
            text.replace(' ', '◼︎'),
            n_text.replace(' ', '◼︎')
        )
        click.echo('{linenbr}: '.format(linenbr=linenbr), nl=False)
        for opcode, a0, a1, b0, b1 in seqm.get_opcodes():
            if opcode == 'equal':
                click.echo(seqm.a[a0:a1], nl=False)
            elif opcode == 'insert':
                click.secho(seqm.b[b0:b1], fg='red', nl=False)
            elif opcode == 'delete':
                click.secho(seqm.a[a0:a1], fg='blue', nl=False)
            elif opcode == 'replace':
                # seqm.a[a0:a1] -> seqm.b[b0:b1]
                click.secho(seqm.b[b0:b1], fg='green', nl=False)
        click.echo()

    def test_file(file_name, extensions, extension, copyrights, license_lines,
                  verbose, progress):
        """Test the license in file."""
        if progress:
            click.secho('License test: ', fg='green', nl=False)
            click.echo('{file_name}'.format(file_name=file_name))
        with open(file_name, 'r') as file:
            result = test_license(
                file=file,
                extension=extensions[extension],
                copyrights=config['copyrights'],
                license_lines=license_lines,
                verbose=verbose
            )
            if result != []:
                click.secho(
                    'License error in {file} in lines {lines}'.format(
                        file=file_name,
                        lines=result
                    ),
                    fg='red'
                )
                # We have an error
                return 1
        # No error found
        return 0

    def test_license(file, extension, copyrights, license_lines, verbose):
        """Test the license in file."""
        linenbr = 1
        lines_with_errors = []
        line = file.readline()
        while line[:2] == '#!':
            # get over Shebang
            line = file.readline()
            linenbr += 1
        if extension.get('top'):
            # read the top
            line = delete_prefix(extension.get('prefix'), line)
            if line not in extension.get('top'):
                if verbose:
                    for t in extension['top']:
                        show_diff(linenbr, t, line)
                lines_with_errors.append(linenbr)
            line = file.readline()
            linenbr += 1
        for license_line in license_lines:
            # compare the license lines
            line = delete_prefix(extension.get('prefix'), line)
            while is_copyright(copyrights, line):
                line = file.readline()
                linenbr += 1
                line = delete_prefix(extension.get('prefix'), line)
            if license_line != line:
                if verbose:
                    show_diff(linenbr, license_line, line)
                lines_with_errors.append(linenbr)
            line = file.readline()
            linenbr += 1
        return lines_with_errors

    config = yaml.safe_load(configfile)
    file_extensions = config['file_extensions']
    extensions = {}
    for file_extension in file_extensions:
        for ext in file_extension.split(','):
            extensions.setdefault(ext.strip(), file_extensions[file_extension])
    # create recursive file list
    files_list = get_files(
        paths=config['directories']['recursive'],
        extensions=extensions,
        recursive=True
    )
    # add flat file list
    files_list += get_files(
        paths=config['directories']['flat'],
        extensions=extensions,
        recursive=False
    )
    # remove excluded files
    exclude_list = []
    for ext in config['directories']['exclude']:
        exclude_list += get_files(
            paths=config['directories']['exclude'][ext],
            extensions=[ext],
            recursive=True
        )
    files_list = list(set(files_list) - set(exclude_list))

    license_lines = config['license_text'].split('\n')
    tot_error_cnt = 0
    for file_name in files_list:
        # test every file
        extension = os.path.splitext(file_name)[1][1:]
        tot_error_cnt += test_file(
            file_name=file_name,
            extensions=extensions,
            extension=extension,
            copyrights=config['copyrights'],
            license_lines=license_lines,
            verbose=verbose,
            progress=progress
        )
    for extension in config['files']:
        # test every files
        for file_name in config['files'][extension]:
            tot_error_cnt += test_file(
                file_name=file_name,
                extensions=extensions,
                extension=extension,
                copyrights=config['copyrights'],
                license_lines=license_lines,
                verbose=verbose,
                progress=progress
            )

    sys.exit(tot_error_cnt)


@utils.command('validate')
@click.argument('jsonfile', type=click.File('r'))
@click.argument('type', default='documents')
@click.argument('schema', default='document-v0.0.1.json')
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@click.option('-e', '--error_file', 'error_file', type=click.File('w'),
              default=None)
@click.option('-o', '--ok_file', 'ok_file', type=click.File('w'), default=None)
def check_validate(jsonfile, type, schema, verbose, error_file, ok_file):
    """Check record validation."""
    click.secho('Testing json schema for file', fg='green')
    schema_in_bytes = resource_string(
        'rero_ils.modules.{type}.jsonschemas'.format(type=type),
        '{type}/{schema}'.format(
            type=type,
            schema=schema
        )
    )
    schema = loads(schema_in_bytes.decode('utf8'))
    datas = json.load(jsonfile)
    count = 0
    for data in datas:
        count += 1
        if verbose:
            click.echo('\tTest record: {count}'.format(count=count))
        if not data.get("$schema"):
            # create dummy schema in data
            data["$schema"] = 'dummy'
        if not data.get("pid"):
            # create dummy pid in data
            data["pid"] = 'dummy'
        try:
            validate(data, schema)
            if ok_file:
                if data["pid"] == 'dummy':
                    del data["pid"]
                ok_file.write(json.dumps(data, indent=2))
        except ValidationError as err:
            if error_file:
                error_file.write(json.dumps(data, indent=2))
            click.secho(
                'Error validate in record: {count}'.format(count=count),
                fg='red')
            click.secho(str(err))


@utils.command('compile_json')
@click.argument('src_jsonfile', type=click.File('r'))
@click.option('-o', '--output', 'output', type=click.File('w'), default=None)
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
def compile_json(src_jsonfile, output, verbose):
    """Compile source json file (resolve $ref)."""
    click.secho('Compile json file (resolve $ref): ', fg='green', nl=False)
    click.secho(src_jsonfile.name)
    data = jsonref.load(src_jsonfile)
    if not output:
        output = sys.stdout
    json.dump(data, fp=output, indent=2)


def do_worker(marc21records, results, pid_required):
    """Worker for marc21 to json transformation."""
    schema_in_bytes = resource_string(
        'rero_ils.modules.documents.jsonschemas',
        'documents/document-v0.0.1.json'
    )
    schema = loads(schema_in_bytes.decode('utf8'))
    for data in marc21records:
        data_json = data['json']
        pid = data_json.get('001', '???')
        try:
            record = marc21tojson.do(data_json)
            if not record.get("$schema"):
                # create dummy schema in data
                record["$schema"] = 'dummy'
            if not pid_required:
                if not record.get("pid"):
                    # create dummy pid in data
                    record["pid"] = 'dummy'
            validate(record, schema)
            if record["$schema"] == 'dummy':
                del record["$schema"]
            if not pid_required:
                if record["pid"] == 'dummy':
                    del record["pid"]
            results.append({
                'status': True,
                'data': record
            })
        except Exception as err:
            msg = 'ERROR:\t{pid}\t{err}'.format(pid=pid, err=err.args[0])
            click.secho(msg, err=True, fg='red')
            # import traceback
            # traceback.print_exc()
            results.append({
                'pid': pid,
                'status': False,
                'data': data['xml']
            })


class Marc21toJson():
    """Class for Marc21 recorts to Json transformation."""

    __slots__ = ['xml_file', 'json_file_ok', 'xml_file_error', 'parallel',
                 'chunk', 'verbose', 'debug', 'pid_required',
                 'count', 'count_ok', 'count_ko', 'ctx',
                 'results', 'active_buffer', 'buffer', 'first_result']

    def __init__(self, xml_file, json_file_ok, xml_file_error,
                 parallel=8, chunk=5000,
                 verbose=False, debug=False, pid_required=False):
        """Constructor."""
        self.count = 0
        self.count_ok = 0
        self.count_ko = 0
        self.xml_file = xml_file
        self.json_file_ok = json_file_ok
        self.xml_file_error = xml_file_error
        self.parallel = parallel
        self.chunk = chunk
        self.verbose = verbose
        self.first_result = True
        if verbose:
            click.echo('Main process pid: {pid}'.format(
                pid=multiprocessing.current_process().pid
            ))
        self.debug = debug
        if debug:
            multiprocessing.log_to_stderr(logging.DEBUG)
        self.pid_required = pid_required
        self.ctx = multiprocessing.get_context("spawn")
        manager = self.ctx.Manager()
        self.results = manager.list()
        self.active_buffer = 0
        self.buffer = []
        for index in range(parallel):
            self.buffer.append({'process': None, 'records': []})
        self.start()

    def counts(self):
        """Get the counters."""
        return self.count, self.count_ok, self.count_ko

    def write_results(self):
        """Write results from multiprocess to file."""
        while self.results:
            value = self.results.pop(0)
            status = value.get('status')
            data = value.get('data')
            if status:
                self.count_ok += 1
                if self.first_result:
                    self.first_result = False
                else:
                    self.json_file_ok.write(',')
                for line in json.dumps(data, indent=2).split('\n'):
                    self.json_file_ok.write('\n  ' + line)
            else:
                self.count_ko += 1
                self.xml_file_error.write(data)
        # free memory from garbage collector
        gc.collect()

    def wait_free_process(self):
        """Wait for next process to finish."""
        index = (self.active_buffer + 1) % self.parallel
        process = self.buffer[index]['process']
        if process:
            process.join()
        # reset data for finished jobs
        for index in range(self.parallel):
            process = self.buffer[index].get('process')
            if process and process.exitcode is not None:
                del self.buffer[index]['process']
                self.buffer[index].clear()
                self.buffer[index] = {'process': None, 'records': []}

    def next_active_buffer(self):
        """Set the next active buffer index."""
        self.active_buffer = (self.active_buffer + 1) % self.parallel

    def wait_all_free_process(self):
        """Wait for all processes to finish."""
        for index in range(self.parallel):
            self.wait_free_process()
            self.next_active_buffer()

    def start_new_process(self):
        """Start a new process in context."""
        new_process = self.ctx.Process(
            target=do_worker,
            args=(self.active_records, self.results, self.pid_required)
        )
        self.wait_free_process()
        new_process.start()
        self.active_process = new_process
        if self.verbose:
            if self.count < self.chunk:
                start = 1
            else:
                start = self.count - len(self.active_records) + 1
            click.echo('Start process: {pid} records: {start}..{end}'.format(
                pid=new_process.pid,
                start=start,
                end=self.count
            ))
        self.next_active_buffer()

    def write_start(self):
        """Write initial lines to files."""
        self.json_file_ok.write('[')
        self.xml_file_error.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        self.xml_file_error.write(
            b'<collection xmlns="http://www.loc.gov/MARC21/slim">\n\n'
        )

    def write_stop(self):
        """Write finishing lines to files."""
        self.json_file_ok.write('\n]')
        self.xml_file_error.write(b'\n</collection>')

    def start(self):
        """Start the transformation."""
        self.write_start()
        for marc21xml in split_stream(self.xml_file):
            marc21json_record = create_record(marc21xml)
            self.active_records.append({
                'json': marc21json_record,
                'xml': etree.tostring(
                    marc21xml,
                    pretty_print=True,
                    encoding='UTF-8'
                ).strip()
            })
            self.count += 1
            if len(self.active_records) % self.chunk == 0:
                self.write_results()
                self.start_new_process()

        # process the remaining records
        self.write_results()
        if self.active_records:
            self.start_new_process()
        self.wait_all_free_process()
        self.write_results()
        self.write_stop()
        return self.count, self.count_ok, self.count_ko

    @property
    def active_process(self):
        """Get the active process."""
        return self.buffer[self.active_buffer]['process']

    @active_process.setter
    def active_process(self, process):
        """Set the active process."""
        self.buffer[self.active_buffer]['process'] = process

    @property
    def active_records(self):
        """Get the active records."""
        return self.buffer[self.active_buffer]['records']


@utils.command('marc21tojson')
@click.argument('xml_file', type=click.File('rb'))
@click.argument('json_file_ok', type=click.File('w'))
@click.argument('xml_file_error', type=click.File('wb'))
@click.option('-p', '--parallel', 'parallel', default=8)
@click.option('-c', '--chunk', 'chunk', default=5000)
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@click.option('-d', '--debug', 'debug', is_flag=True, default=False)
@click.option('-r', '--pidrequired', 'pid_required', is_flag=True,
              default=False)
def marc21json(xml_file, json_file_ok, xml_file_error, parallel, chunk,
               verbose, debug, pid_required):
    """Convert xml file to json with dojson."""
    click.secho('Marc21 to Json transform: ', fg='green', nl=False)
    if pid_required and verbose:
        click.secho(' (validation tests pid) ', nl=False)
    click.secho(xml_file.name)

    transform = Marc21toJson(xml_file, json_file_ok, xml_file_error,
                             parallel, chunk, verbose, debug, pid_required)

    count, count_ok, count_ko = transform.counts()

    click.secho('Total records: ', fg='green', nl=False)
    click.secho(str(count), nl=False)
    click.secho('-', nl=False)
    click.secho(str(count_ok + count_ko))

    click.secho('Records transformed: ', fg='green', nl=False)
    click.secho(str(count_ok))
    if count_ko:
        click.secho('Records with errors: ', fg='red', nl=False)
        click.secho(str(count_ko))


@utils.command('reserve_pid_range')
@click.option('-p', '--pid_type', 'pid_type', default=None,
              help='pid type of the resource')
@click.option('-n', '--records_number', 'records_number', default=None,
              help='Number of records to load')
@click.option('-u', '--unused', 'unused', is_flag=True, default=False,
              help='Set unused (gaps) pids status to NEW ')
@with_appcontext
def reserve_pid_range(pid_type, records_number, unused):
    """Reserve a range of pids for future records loading.

    reserved pids will have the status RESERVED.
    - pid_type: the pid type of the resource as configured in config.py
    - records_number: number of new records(with pids) to load.
    - unused: set that the status of unused (gaps) pids to NEW.
    """
    click.secho('Reserving pids for loading "%s" records' %
                pid_type, fg='green')
    try:
        records_number = int(records_number)
    except ValueError:
        raise ValueError('Parameter records_number must be integer.')

    try:
        record_class = obj_or_import_string(
            current_app.config
            .get('RECORDS_REST_ENDPOINTS')
            .get(pid_type).get('record_class', Record))
    except AttributeError:
        raise AttributeError('Invalid pid type.')

    identifier = record_class.provider.identifier
    reserved_pids = []
    for number in range(0, records_number):
        pid = identifier.next()
        reserved_pids.append(pid)
        record_class.provider.create(pid_type, pid_value=pid,
                                     status=PIDStatus.RESERVED)
        db.session.commit()
    click.secho(
        ('reserved_pids range, from: {min} to: {max}').format(
            min=min(reserved_pids), max=max(reserved_pids)
        ))
    if unused:
        for pid in range(1, identifier.max()):
            if not db.session.query(
                    identifier.query.filter(identifier.recid == pid).exists()
            ).scalar():
                record_class.provider.create(pid_type, pid_value=pid,
                                             status=PIDStatus.NEW)
                db.session.add(identifier(recid=pid))
            db.session.commit()
