# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
# Copyright (C) 2020 UCLouvain
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
import re
import shutil
import sys
import traceback
from collections import OrderedDict
from glob import glob

import click
import jsonref
import polib
import pycountry
import requests
import xmltodict
import yaml
from babel import Locale, core
from dojson.contrib.marc21.utils import create_record, split_stream
from flask import current_app
from flask.cli import with_appcontext
from flask_security.confirmable import confirm_user
from invenio_accounts.cli import commit, users
from invenio_app.factory import static_folder
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

from .api import IlsRecordsIndexer
from .documents.dojson.contrib.marc21tojson import marc21
from .holdings.cli import create_patterns
from .items.cli import create_items, reindex_items
from .loans.cli import create_loans
from .patrons.cli import import_users
from .tasks import process_bulk_queue
from .utils import read_json_record
from ..modules.providers import append_fixtures_new_identifiers

_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


def abort_if_false(ctx, param, value):
    """Abort command is value is False."""
    if not value:
        ctx.abort()


@click.group()
def fixtures():
    """Fixtures management commands."""


fixtures.add_command(import_users)
fixtures.add_command(create_items)
fixtures.add_command(reindex_items)
fixtures.add_command(create_loans)
fixtures.add_command(create_patterns)


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
    help='indent default=2'
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
        except ValueError as error:
            click.echo(fname + ': ', nl=False)
            click.secho('Invalid JSON', fg='red', nl=False)
            click.echo(' -- ' + error.msg)
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
            length=len(current_search.templates)) as bar:
        for response in bar:
            bar.label = response
    click.secho('Creating indexes...', fg='green', bold=True, file=sys.stderr)
    with click.progressbar(
            current_search.create(ignore=[400] if force else None),
            length=len(current_search.mappings)) as bar:
        for name, response in bar:
            bar.label = name


@click.command('create')
@click.option('-a', '--append', 'append', is_flag=True, default=False)
@click.option('-r', '--reindex', 'reindex', is_flag=True, default=False)
@click.option('-c', '--dbcommit', 'dbcommit', is_flag=True, default=False)
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=True)
@click.option('-s', '--schema', 'schema', default=None)
@click.option('-p', '--pid_type', 'pid_type', default=None)
@click.option('-l', '--lazy', 'lazy', is_flag=True, default=False)
@click.option('-o', '--dont-stop', 'dont_stop_on_error',
              is_flag=True, default=False)
@click.option('-P', '--pid-check', 'pid_check',
              is_flag=True, default=False)
@click.argument('infile', type=click.File('r'), default=sys.stdin)
@with_appcontext
def create(infile, append, reindex, dbcommit, verbose, schema, pid_type, lazy,
           dont_stop_on_error, pid_check):
    """Load REROILS record.

    :param infile: Json file
    :param append: appends pids to database
    :param reindex: reindex record by record
    :param dbcommit: commit record to database
    :param pid_type: record type
    :param schema: recoord schema
    :param lazy: lazy reads file
    :param dont_stop_on_error: don't stop on error
    :param pidcheck: check pids
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
    if lazy:
        # try to lazy read json file (slower, better memory management)
        records = read_json_record(infile)
    else:
        # load everything in memory (faster, bad memory management)
        records = json.load(infile)
    for record in records:
        count += 1
        if schema:
            record['$schema'] = schema
        try:
            rec = record_class.create(record, dbcommit=dbcommit,
                                      reindex=reindex, pidcheck=pid_check)
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
                '{count: <8} {pid_type} create error {pid}: {err}'.format(
                    count=count,
                    pid_type=pid_type,
                    pid=record.get('pid', '???'),
                    err=err
                ),
                err=True,
                fg='red'
            )
            if not dont_stop_on_error:
                sys.exit(1)
        db.session.flush()
    db.session.commit()
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
            append_fixtures_new_identifiers(
                identifier,
                sorted(pids, key=lambda x: int(x)),
                pid_type
            )
        except Exception as err:
            click.secho(
                "ERROR append fixtures new identifiers: {err}".format(
                    err=err
                ),
                fg='red'
            )


fixtures.add_command(create)


@click.command('count')
@click.option('-l', '--lazy', 'lazy', is_flag=True, default=False)
@click.argument('infile', type=click.File('r'), default=sys.stdin)
def count(infile, lazy):
    """Count records in file.

    :param infile: Json file
    :param lazy: lazy reads file
    :return: count of records
    """
    click.secho(
        'Count records from {file_name}.'.format(
            file_name=infile.name
        ),
        fg='green'
    )
    if lazy:
        # try to lazy read json file (slower, better memory management)
        records = read_json_record(infile)
    else:
        # load everything in memory (faster, bad memory management)
        records = json.load(infile)
    count = 0
    for record in records:
        count += 1
    click.echo('Count: {count}'.format(count=count))


fixtures.add_command(count)


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

    def is_copyright(line):
        """Line is copyright."""
        if line.startswith('Copyright (C)'):
            return True
        return False

    def get_line(lines, index, prefix):
        """Get line on index."""
        line = delete_prefix(prefix, lines[index])
        return line, index+1

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

    def test_file(file_name, extensions, extension, license_lines,
                  verbose, progress):
        """Test the license in file."""
        if progress:
            click.secho('License test: ', fg='green', nl=False)
            click.echo('{file_name}'.format(file_name=file_name))
        with open(file_name, 'r') as file:
            result = test_license(
                file=file,
                extension=extensions[extension],
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

    def is_slash_directive(file, line):
        is_js_file = file.name.split('.')[-1] == 'js'
        if is_js_file and re.search(triple_slash, line):
            return True
        return False

    def test_license(file, extension, license_lines, verbose):
        """Test the license in file."""
        lines_with_errors = []
        lines = [line.rstrip() for line in file]
        linenbr = 0
        linemaxnbr = len(lines)
        prefix = extension.get('prefix')
        line, linenbr = get_line(lines, linenbr, prefix)
        # Get over Shebang lines or Triple-Slash Directives (for Javascript
        # files)
        while lines[linenbr-1].startswith('#!') or \
                is_slash_directive(file, lines[linenbr-1]):
            # get over Shebang
            line, linenbr = get_line(lines, linenbr, prefix)
        if extension.get('top'):
            # read the top
            if line not in extension.get('top'):
                if verbose:
                    for t in extension['top']:
                        show_diff(linenbr, t, line)
                lines_with_errors.append(linenbr+1)
        line, linenbr = get_line(lines, linenbr, prefix)
        for license_line in license_lines:
            # compare the license lines
            if is_copyright(license_line):
                while is_copyright(line):
                    line, linenbr = get_line(lines, linenbr, prefix)
                linenbr -= 1
                line = 'Copyright (C)'
            if license_line != line:
                if verbose:
                    show_diff(linenbr, license_line, line)
                lines_with_errors.append(linenbr)
            # Fix crash while testing a file with only comments.
            if linenbr >= linemaxnbr:
                continue
            line, linenbr = get_line(lines, linenbr, prefix)
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

    # set regexp expression for Triple-Slash directives
    triple_slash = r'^/// <reference \w*=\"\w*\" />$'

    license_lines = config['license_text'].split('\n')
    tot_error_cnt = 0
    for file_name in files_list:
        # test every file
        extension = os.path.splitext(file_name)[1][1:]
        tot_error_cnt += test_file(
            file_name=file_name,
            extensions=extensions,
            extension=extension,
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
    schema = jsonref.loads(schema_in_bytes.decode('utf8'))
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


def do_worker(marc21records, results, pid_required, debug):
    """Worker for marc21 to json transformation."""
    schema_in_bytes = resource_string(
        'rero_ils.modules.documents.jsonschemas',
        'documents/document-v0.0.1.json'
    )
    schema = jsonref.loads(schema_in_bytes.decode('utf8'))
    for data in marc21records:
        data_json = data['json']
        pid = data_json.get('001', '???')
        try:
            record = marc21.do(data_json)
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
            if debug:
                traceback.print_exc()
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
            args=(self.active_records, self.results, self.pid_required,
                  self.debug)
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


@utils.command('runindex')
@click.option(
    '--delayed', '-d', is_flag=True, help='Run indexing in background.')
@click.option(
    '--concurrency', '-c', default=1, type=int,
    help='Number of concurrent indexing tasks to start.')
@click.option(
    '--with_stats', is_flag=True, default=False,
    help='report number of successful and list failed error response.')
@click.option('--queue', '-q', type=str,
              help='Name of the celery queue used to put the tasks into.')
@click.option('--version-type', help='Elasticsearch version type to use.')
@click.option(
    '--raise-on-error/--skip-errors', default=True,
    help='Controls if Elasticsearch bulk indexing errors raise an exception.')
@with_appcontext
def run(delayed, concurrency, with_stats, version_type=None, queue=None,
        raise_on_error=True):
    """Run bulk record indexing."""
    if delayed:
        celery_kwargs = {
            'kwargs': {
                'version_type': version_type,
                'es_bulk_kwargs': {'raise_on_error': raise_on_error},
                'stats_only': not with_stats
            }
        }
        click.secho(
            'Starting {0} tasks for indexing records...'.format(concurrency),
            fg='green')
        if queue is not None:
            celery_kwargs.update({'queue': queue})
        for c in range(0, concurrency):
            process_bulk_queue.apply_async(**celery_kwargs)
    else:
        click.secho('Indexing records...', fg='green')
        indexed, error = IlsRecordsIndexer(version_type=version_type)\
            .process_bulk_queue(
                es_bulk_kwargs={'raise_on_error': raise_on_error},
                stats_only=not with_stats
        )
        click.secho('indexed: {indexed}, error: {error}'.format(
            indexed=indexed, error=error), fg='yellow')


@utils.command('reindex')
@click.option('--yes-i-know', is_flag=True, callback=abort_if_false,
              expose_value=False,
              prompt='Do you really want to reindex all records?')
@click.option('-t', '--pid-type', multiple=True, required=True)
@click.option('-n', '--no-info', 'no_info', is_flag=True, default=True)
@with_appcontext
def reindex(pid_type, no_info):
    """Reindex all records.

    :param pid_type: Pid type.
    """
    for type in pid_type:
        click.secho(
            'Sending {type} to indexing queue ...'.format(type=type),
            fg='green'
        )

        query = (x[0] for x in PersistentIdentifier.query.filter_by(
            object_type='rec', status=PIDStatus.REGISTERED
        ).filter(
            PersistentIdentifier.pid_type == type
        ).values(
            PersistentIdentifier.object_uuid
        ))
        IlsRecordsIndexer().bulk_index(query, doc_type=type)
    if no_info:
        click.secho(
            'Execute "runindex" command to process the queue!',
            fg='yellow'
        )


def get_loc_languages(verbose=False):
    """Get languages from LOC."""
    languages = {}
    url = 'https://www.loc.gov/standards/codelists/languages.xml'
    response = requests.get(url)
    root = xmltodict.parse(response.content)
    for language in root['codelist']['languages']['language']:
        if isinstance(language['name'], OrderedDict):
            name = language['name']['#text']
        else:
            name = language['name']
        code = language['code']
        if isinstance(code, OrderedDict):
            if code['@status'] == 'obsolete':
                code = None
            else:
                code = code['#text']
        if code:
            if verbose:
                click.echo('{code}: {name}'.format(name=name, code=code))
            languages[code] = name
    return languages


@utils.command('translate')
@click.argument('translate_to', type=str)
@click.option('-c', '--change', 'change', is_flag=True, default=False)
@click.option('-t', '--title_map', 'title_map', is_flag=True, default=False)
@click.option('-l', '--no_loc_en', 'no_loc_en', is_flag=True, default=True)
@click.option('-a', '--angular', 'angular', is_flag=True, default=False)
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
def translate(translate_to, change, title_map, no_loc_en, angular, verbose):
    """Automatic language, country, canton, language scrip translations."""
    def print_title_map(name, values):
        """Print out a title map."""
        if title_map:
            click.secho('Titel map {name}:'.format(name=name), fg='green')
            click.echo('"titleMap": [')
            for value in values:
                click.echo('\t{')
                click.echo('\t\t"value": "{value}",'.format(value=value))
                click.echo('\t\t"name": "{value}"'.format(value=value))
                if value == values[-1]:
                    click.echo('\t}')
                else:
                    click.echo('\t},')
            click.echo(']')

    def change_po(po, values):
        """Change values in message po."""
        for entry in po:
            if entry.msgid in values:
                click.echo(
                    'Translate: {name} -> {trans}'.format(
                        name=entry.msgid,
                        trans=values[entry.msgid]
                    )
                )
                entry.msgstr = values[entry.msgid]
                if entry.fuzzy:
                    entry.flags.remove('fuzzy')

    try:
        locale = Locale(translate_to)

        click.secho('Translate country codes to: {translate_to}'.format(
                translate_to=translate_to
            ),
            fg='green'
        )
        document = ('./rero_ils/modules/documents/jsonschemas/'
                    'documents/document-v0.0.1_src.json')

        if change:
            file_name = (
                './rero_ils/translations/{translate_to}/LC_MESSAGES/'
                'messages.po'.format(translate_to=translate_to)
            )
            # try to open file. polib.pofile is not raising a good error
            test_file = open(file_name)
            test_file.close()
            po = polib.pofile(file_name)

        if no_loc_en and translate_to == 'en':
            loc_languages = get_loc_languages()

        with open(document, 'r') as opened_file:
            data = json.load(opened_file)

            definitions = data.get('definitions', {})
            # languages
            languages = definitions.get('language', {}).get('enum')
            print_title_map('language', languages)
            translated_languages = {}
            for lang in languages:
                # get language specification:
                trans_name = None
                if no_loc_en and translate_to == 'en':
                    trans_name = loc_languages.get(lang, None)
                else:
                    lang_info = pycountry.languages.get(alpha_3=lang)
                    if lang_info:
                        try:
                            # try to get translated name with alpha_2
                            trans_name = locale.languages.get(
                                lang_info.alpha_2
                            )
                        except:
                            # try with alpha_3
                            trans_name = locale.languages.get(
                                lang_info.alpha_3
                            )
                if trans_name:
                    translated_languages[lang] = trans_name
                if verbose and trans_name:
                    click.echo('Language {code}: {translated}'.format(
                        code=lang,
                        translated=trans_name
                    ))
            if change:
                change_po(po, translated_languages)

            # countries
            countries = definitions.get('country', {}).get('enum')
            print_title_map('country', countries)
            # translated_countries = {}
            # for country_code in countries:
            #     try:
            #         country = pycountry.countries.lookup(country_code)
            #         trans_name = locale.territories[country.alpha_2]
            #         translated_countries[country_code] = trans_name
            #         if verbose:
            #             click.echo('Country {code}: {translated}'.format(
            #                 code=country_code,
            #                 translated=trans_name
            #             ))
            #     except:
            #         pass
            # if change:
            #     change_po(po, translated_countries)

            # language_script
            language_scripts = definitions.get(
                'language_script', {}
            ).get('enum')
            print_title_map('language_script', language_scripts)
            # TODO: translation

            # language_script
            cantons = definitions.get('canton', {}).get('enum')
            print_title_map('canton', cantons)
            # TODO: translation

        if angular:
            click.secho('Add to manual_translation.ts', fg='yellow')
            click.secho('// Languages translations')
            for language in languages:
                click.secho("_('{language}')".format(language=language))
            click.secho(
                'Add to i18n/{translate_to}.ts'.format(
                    translate_to=translate_to
                ),
                fg='yellow'
            )
            file_po = (
                './rero_ils/translations/{translate_to}/LC_MESSAGES/'
                'messages.po'.format(translate_to=translate_to)
            )
            # try to open file. polib.pofile is not raising a good error
            test_file = open(file_po)
            test_file.close()
            po_angular = polib.pofile(file_po)
            for entry in po_angular:
                if entry.msgid in languages:
                    trans = entry.msgid
                    if entry.msgstr:
                        trans = entry.msgstr
                    click.secho('  "{language}": "{trans}",'.format(
                        language=entry.msgid,
                        trans=trans
                    ))

        if change:
            po.save(file_name)
        click.echo('Languages: {count} translated: {t_count}'.format(
            count=len(languages),
            t_count=len(translated_languages)
        ))
        # click.echo('Countries: {count} translated: {t_count}'.format(
        #     count=len(countries),
        #     t_count=len(translated_countries)
        # ))
    except core.UnknownLocaleError as err:
        click.secho(
            'Unknown locale: {translate_to}'.format(translate_to=translate_to),
            fg='red'
        )
    except FileNotFoundError as err:
        click.secho(str(err), fg='red')


@utils.command('check_pid_dependencies')
@click.option('-i', '--dependency_file', 'dependency_file',
              type=click.File('r'), default='./data/pid_dependencies.json')
@click.option('-d', '--directory', 'directory', default='./data')
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
def check_pid_dependencies(dependency_file, directory, verbose):
    """Check record dependencies."""
    class Dependencies():
        """Class for dependencies checking."""

        test_data = {}

        def __init__(self, directory, verbose=False):
            """Init dependency class."""
            self.directory = directory
            self.verbose = verbose
            self.record = {}
            self.name = ''
            self.pid = '0'
            self.dependencies_pids = []
            self.dependencies = set()
            self.missing = 0
            self.not_found = 0

        def get_pid(self, data):
            """Get pid from end of $ref string."""
            return data['$ref'].split('/')[-1]

        def get_ref_pids(self, data, dependency_name):
            """Get pids from data."""
            pids = []
            try:
                if isinstance(data[dependency_name], list):
                    for dat in data[dependency_name]:
                        pids.append(self.get_pid(dat))
                else:
                    pids = [self.get_pid(data[dependency_name])]
            except Exception as err:
                pass
            return pids

        def add_pids_to_dependencies(self, dependency_name, pids, optional):
            """Add pids to dependoencies_pid."""
            if not (pids or optional):
                click.secho(
                    '{name}: dependencie not found: {dependency_name}'.format(
                        name=self.name,
                        dependency_name=dependency_name
                    ),
                    fg='red'
                )
                self.not_found += 1
            else:
                self.dependencies_pids.append({
                    dependency_name: pids
                })
                self.dependencies.add(dependency_name)

        def set_dependencies_pids(self, dependencies):
            """Get all dependencies and pids."""
            self.dependencies_pids = []
            for dependency in dependencies:
                dependency_ref = dependency.get('ref')
                if not dependency_ref:
                    dependency_ref = dependency['name']
                sublist = dependency.get('sublist', [])
                for sub in sublist:
                    datas = self.record.get(dependency['name'], [])
                    if not(datas or dependency.get('optional')):
                        click.secho(
                            ('{name}: sublist not found:'
                             ' {dependency_name}').format(
                                name=self.name,
                                dependency_name=dependency['name']
                            ),
                            fg='red'
                        )
                        self.not_found += 1
                    else:
                        for data in datas:
                            dependency_ref = sub.get('ref')
                            if not dependency_ref:
                                dependency_ref = sub['name']
                            self.add_pids_to_dependencies(
                                dependency_ref,
                                self.get_ref_pids(data, sub['name']),
                                sub.get('optional')
                            )
                if not sublist:
                    self.add_pids_to_dependencies(
                        dependency_ref,
                        self.get_ref_pids(self.record, dependency['name']),
                        dependency.get('optional')
                    )

        def test_dependencies(self):
            """Test all dependencies."""
            for dependency in self.dependencies_pids:
                for key, values in dependency.items():
                    for value in values:
                        try:
                            self.test_data[key][value]
                        except Exception as err:
                            click.secho(
                                ('{name}: {pid} missing '
                                 '{ref_name}: {ref_pid}').format(
                                    ref_name=key,
                                    ref_pid=value,
                                    name=self.name,
                                    pid=self.pid
                                ),
                                fg='red'
                            )
                            self.missing += 1

        def init_and_test_data(self, test):
            """Init data and test data."""
            self.name = test['name']
            file_name = os.path.join(self.directory, test['filename'])
            self.test_data.setdefault(self.name, {})
            with open(file_name, 'r') as infile:
                if self.verbose:
                    click.echo('{name}: {file_name}'.format(
                        name=self.name,
                        file_name=file_name
                    ))
                records = read_json_record(infile)
                for self.record in records:
                    self.pid = self.record['pid']
                    if self.test_data[self.name].get(self.pid):
                        click.secho(
                            'Double pid in {name}: {pid}'.format(
                                name=self.name,
                                pid=self.pid
                            ),
                            fg='red'
                        )
                    else:
                        self.test_data[self.name][self.pid] = {}
                        self.set_dependencies_pids(
                            test.get('dependencies', [])
                        )
                        self.test_dependencies()
                if self.verbose:
                    for dependency in self.dependencies:
                        click.echo(
                            '\tTested dependency: {dependency}'.format(
                                dependency=dependency
                            )
                        )

        def run_tests(self, tests):
            """Run the tests."""
            for test in tests:
                self.init_and_test_data(test)
            if self.missing:
                click.secho(
                    'Missing relations: {nbr}'.format(nbr=self.missing),
                    fg='red'
                )
            if self.not_found:
                click.secho(
                    'Relation not found: {nbr}'.format(nbr=self.not_found),
                    fg='red'
                )

    # start of tests
    click.secho(
        'Check dependencies {dependency_file}: {directory}'.format(
            dependency_file=dependency_file,
            directory=directory
        ),
        fg='green'
    )
    dependency_tests = Dependencies(directory, verbose=verbose)
    tests = json.load(dependency_file)
    dependency_tests.run_tests(tests)

    sys.exit(dependency_tests.missing + dependency_tests.not_found)


@utils.command('dump_es_mappings')
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@click.option('-o', '--outfile', 'outfile', type=click.File('w'), default=None)
@with_appcontext
def dump_es_mappings(verbose, outfile):
    """Dumps ES mappings."""
    click.secho('Dump ES mappings:', fg='green')
    aliases = current_search.client.indices.get_alias('*')
    mappings = current_search.client.indices.get_mapping()
    for alias in sorted(aliases):
        if alias[0] != '.':
            mapping = mappings.get(alias, {}).get('mappings')
            click.echo('{alias}'.format(alias=alias))
            if verbose or not outfile:
                print(json.dumps(mapping, indent=2))
            if outfile:
                json.dump(mapping, outfile, indent=2)
                outfile.write('\n')


@utils.command('export')
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@click.option('-p', '--pid_type', 'pid_type', default='doc')
@click.option('-o', '--outfile', 'outfile', required=True,
              type=click.File('w'))
@click.option('-i', '--pidfile', 'pidfile', type=click.File('r'),
              default=None)
@click.option('-I', '--indent', 'indent', type=click.INT, default=2)
@click.option('-s', '--schema', 'schema', is_flag=True, default=False)
@with_appcontext
def export(verbose, pid_type, outfile, pidfile, indent, schema):
    """Load REROILS record.

    :param verbose: verbose
    :param pid_type: record type
    :param outfile: Json output file
    :param pidfile: files with pids to extract
    :param indent: indent for output
    :param schema: do not delete $schema
    """
    click.secho(
        'Export {pid_type} records: {file_name}'.format(
            pid_type=pid_type,
            file_name=outfile.name
        ),
        fg='green'
    )

    record_class = obj_or_import_string(
        current_app.config
        .get('RECORDS_REST_ENDPOINTS')
        .get(pid_type).get('record_class', Record))

    if pidfile:
        pids = pidfile
    else:
        pids = record_class.get_all_pids()

    count = 0
    output = '['
    offset = '{character:{indent}}'.format(character=' ', indent=indent)
    for pid in pids:
        try:
            rec = record_class.get_record_by_pid(pid)
            count += 1
            if verbose:
                msg = '{count: <8} {pid_type} export {pid}:{id}'.format(
                    count=count,
                    pid_type=pid_type,
                    pid=rec.pid,
                    id=rec.id
                )
                click.echo(msg)

            outfile.write(output)
            if count > 1:
                outfile.write(',')
            if not schema:
                del rec['$schema']
                persons_sources = current_app.config.get(
                    'RERO_ILS_PERSONS_SOURCES', [])
                for persons_source in persons_sources:
                    try:
                        del rec[persons_source]['$schema']
                    except:
                        pass
            output = ''
            lines = json.dumps(rec, indent=indent).split('\n')
            for line in lines:
                output += '\n{offset}{line}'.format(offset=offset, line=line)
        except Exception as err:
            click.echo(err)
            click.echo('ERROR: Can not export pid:{pid}'.format(pid=pid))
    outfile.write(output)
    outfile.write('\n]\n')


@utils.command('set_test_static_folder')
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@with_appcontext
def set_test_static_folder(verbose):
    """Creates a static folder link for tests."""
    click.secho('Create symlink for static folder', fg='green')
    test_static_folder = os.path.join(sys.prefix, 'var/instance/static')
    my_static_folder = static_folder()
    if verbose:
        msg = '\t{src} --> {dst}'.format(
            src=my_static_folder,
            dst=test_static_folder
        )
        click.secho(msg)
    try:
        os.unlink(test_static_folder)
    except:
        pass
    os.makedirs(test_static_folder, exist_ok=True)
    shutil.rmtree(test_static_folder, ignore_errors=True)
    os.symlink(my_static_folder, test_static_folder)
