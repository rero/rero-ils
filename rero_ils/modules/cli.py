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
import json
import os
import sys
from collections import OrderedDict
from glob import glob

import click
import yaml
from flask import current_app
from flask.cli import with_appcontext
from flask_security.confirmable import confirm_user
from invenio_accounts.cli import commit, users
from invenio_pidstore.models import PersistentIdentifier
from invenio_records.api import Record
from invenio_records_rest.utils import obj_or_import_string
from invenio_search.cli import es_version_check
from invenio_search.proxies import current_search
from sqlalchemy import MetaData, create_engine
from werkzeug.local import LocalProxy

from .holdings.api import Holding
from .items.cli import create_items, reindex_items
from .loans.cli import create_loans
from .patrons.cli import import_users

_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


def append_pid_to_table(table, pids):
    """Insert pids into an indentifier table."""
    # TODO: avoid the connection to the database, recreate code
    with current_app.app_context():
        URI = current_app.config.get('SQLALCHEMY_DATABASE_URI')
        engine = create_engine(URI)
        metadata = MetaData(engine, reflect=True)
        table_object = metadata.tables[table]
        for pid in pids:
            statement = "insert into {0} values('{1}')".format(
                table_object, pid)
            engine.execute(statement)


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
    click.secho('Testing JSON intentation.', fg='green')
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


@click.command('create')
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=True)
@click.option('-c', '--dbcommit', 'dbcommit', is_flag=True, default=True)
@click.option('-r', '--reindex', 'reindex', is_flag=True, default=False)
@click.option('-s', '--schema', 'schema', default=None)
@click.option('-a', '--append', 'append', is_flag=True, default=False)
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
    data = json.load(infile)
    count = 0
    for record in data:
        count += 1
        if schema:
            record['$schema'] = schema
        rec = record_class.create(record, dbcommit=dbcommit, reindex=reindex)
        if verbose:
            click.echo(
                '{count: <8} {pid_type} created {id}'.format(
                    count=count,
                    pid_type=pid_type,
                    id=rec.id
                )
            )
    if append:
        pids = record_class.get_all_pids()
        table = record_class.provider.identifier.__tablename__
        append_pid_to_table(table, pids)


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
