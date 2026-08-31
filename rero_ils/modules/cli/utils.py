# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Click command-line utilities."""

import itertools
import json
import os
import subprocess
import sys
import traceback
from collections import OrderedDict
from glob import glob
from time import sleep

import click
from celery import current_app as current_celery
from flask import current_app
from flask.cli import with_appcontext
from invenio_db import db
from invenio_jsonschemas.proxies import current_jsonschemas
from invenio_oauth2server.cli import process_scopes, process_user
from invenio_oauth2server.models import Client, Token
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.api import Record
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from lxml import etree
from werkzeug.local import LocalProxy
from werkzeug.security import gen_salt

from rero_ils.modules.entities.remote_entities.api import RemoteEntity
from rero_ils.modules.files.cli import load_files
from rero_ils.modules.loans.tasks import (
    delete_loans_created as task_delete_loans_created,
)
from rero_ils.modules.patrons.cli import users_validate
from rero_ils.modules.selfcheck.cli import (
    create_terminal,
    list_terminal,
    update_terminal,
)
from rero_ils.modules.utils import (
    JsonWriter,
    get_record_class_from_schema_or_pid_type,
    get_schema_for_resource,
    read_json_record,
    read_xml_record,
)

_records_state = LocalProxy(lambda: current_app.extensions["invenio-records"])


def abort_if_false(ctx, param, value):
    """Abort command if value is False."""
    if not value:
        ctx.abort()


def queue_count():
    """Count tasks in celery."""
    inspector = current_celery.control.inspect()
    task_count = 0
    if reserved := inspector.reserved():
        for values in reserved.values():
            task_count += len(values)
    if active := inspector.active():
        for values in active.values():
            task_count += len(values)
    return task_count


def wait_empty_tasks(delay, verbose=False):
    """Wait for tasks to be empty."""
    if verbose:
        spinner = itertools.cycle(["-", "\\", "|", "/"])
        click.echo(f"Waiting: {next(spinner)}\r", nl=False)
    count = queue_count()
    sleep(5)
    count += queue_count()
    while count:
        if verbose:
            click.echo(f"Waiting: {next(spinner)}\r", nl=False)
        sleep(delay)
        count = queue_count()
        sleep(5)
        count += queue_count()


@click.group()
def utils():
    """Utils management commands."""


utils.add_command(users_validate)
utils.add_command(load_files)
utils.add_command(create_terminal)
utils.add_command(list_terminal)
utils.add_command(update_terminal)


@utils.command("wait_empty_tasks")
@click.option("-d", "--delay", "delay", default=3)
@with_appcontext
def wait_empty_tasks_cli(delay):
    """Wait for tasks to be empty."""
    wait_empty_tasks(delay=delay, verbose=True)
    click.secho("No active celery tasks.", fg="green")


@utils.command("show")
@click.argument("pid_value", nargs=1)
@click.option("-t", "--pid-type", "pid-type, default(document_id)", default="document_id")
@with_appcontext
def show(pid_value, pid_type):
    """Show records."""
    record = PersistentIdentifier.query.filter_by(pid_type=pid_type, pid_value=pid_value).first()
    recitem = Record.get_record(record.object_uuid)
    click.echo(json.dumps(recitem.dumps(), indent=2))


@utils.command("check_json")
@click.argument("paths", nargs=-1)
@click.option(
    "-r",
    "--replace",
    "replace",
    is_flag=True,
    default=False,
    help="change file in place default=False",
)
@click.option(
    "-s",
    "--sort-keys",
    "sort_keys",
    is_flag=True,
    default=False,
    help="order keys during replacement default=False",
)
@click.option("-i", "--indent", "indent", type=click.INT, default=2, help="indent default=2")
@click.option("-v", "--verbose", "verbose", is_flag=True, default=False)
def check_json(paths, replace, indent, sort_keys, verbose):
    """Check json files."""
    click.secho("Testing JSON indentation.", fg="green")
    files_list = []
    for path in paths:
        if os.path.isfile(path):
            files_list.append(path)
        elif os.path.isdir(path):
            files_list = files_list + glob(os.path.join(path, "**/*.json"), recursive=True)
    if not paths:
        files_list = glob("**/*.json", recursive=True)
    tot_error_cnt = 0
    for path_file in files_list:
        error_cnt = 0
        try:
            fname = path_file
            with open(fname) as opened_file:
                json_orig = opened_file.read().rstrip()
                opened_file.seek(0)
                json_file = json.load(opened_file, object_pairs_hook=OrderedDict)
            json_dump = json.dumps(json_file, indent=indent).rstrip()
            if json_dump != json_orig:
                error_cnt = 1
            if replace:
                with open(fname, "w") as opened_file:
                    opened_file.write(json.dumps(json_file, indent=indent, sort_keys=sort_keys))
                click.echo(fname + ": ", nl=False)
                click.secho("File replaced", fg="yellow")
            else:
                if error_cnt == 0:
                    if verbose:
                        click.echo(fname + ": ", nl=False)
                        click.secho("Well indented", fg="green")
                else:
                    click.echo(fname + ": ", nl=False)
                    click.secho("Bad indentation", fg="red")
        except ValueError as error:
            click.echo(fname + ": ", nl=False)
            click.secho("Invalid JSON", fg="red", nl=False)
            click.echo(f" -- {error}")
            error_cnt = 1

        tot_error_cnt += error_cnt

    sys.exit(tot_error_cnt)


SPDX_TAGS = ("SPDX-FileCopyrightText:", "SPDX-License-Identifier: AGPL-3.0-or-later")
SPDX_EXTENSIONS = (
    ".cfg",
    ".conf",
    ".css",
    ".html",
    ".ini",
    ".js",
    ".md",
    ".py",
    ".scss",
    ".sh",
    ".toml",
    ".yml",
)
# `.github` templates and generated or fixture content have no license header
SPDX_EXCLUDED_PATHS = (".github/", "CHANGELOG.md", "data/wiki/", "tests/data/help/")


def needs_spdx_header(file_name):
    """Check if a file is expected to have a SPDX license header.

    Files are selected by extension. Files without extension are selected when
    they are Dockerfiles or scripts starting with a shebang.

    :param file_name: the path of the file to check.
    :returns: True if the file requires a SPDX license header.
    """
    if any(excluded in file_name for excluded in SPDX_EXCLUDED_PATHS):
        return False
    base_name = os.path.basename(file_name)
    if base_name.startswith("Dockerfile"):
        return True
    if extension := os.path.splitext(base_name)[1]:
        return extension in SPDX_EXTENSIONS
    with open(file_name, "rb") as opened_file:
        return opened_file.read(2) == b"#!"


def has_spdx_header(file_name):
    """Check if a file starts with the SPDX license header.

    The comment syntax is not checked, only the presence of both SPDX tags in
    the first lines of the file.

    :param file_name: the path of the file to check.
    :returns: True if the copyright and the license tags are both present.
    """
    with open(file_name) as opened_file:
        header = "".join(itertools.islice(opened_file, 5))
    return all(tag in header for tag in SPDX_TAGS)


@utils.command("check_license")
@click.option("-v", "--verbose", "verbose", is_flag=True, default=False)
def check_license(verbose):
    """Check SPDX license headers of the files tracked by git."""
    click.secho("Testing SPDX license headers.", fg="green")
    try:
        tracked_files = subprocess.check_output(["git", "ls-files", "-z"], text=True).split("\0")
    except (OSError, subprocess.CalledProcessError) as error:
        raise click.ClickException("git is required and must run in a git repository.") from error
    error_cnt = 0
    for file_name in tracked_files:
        if not os.path.isfile(file_name) or not needs_spdx_header(file_name):
            continue
        if has_spdx_header(file_name):
            if verbose:
                click.echo(f"{file_name}: ", nl=False)
                click.secho("License header found", fg="green")
        else:
            click.echo(f"{file_name}: ", nl=False)
            click.secho("Missing license header", fg="red")
            error_cnt += 1

    sys.exit(1 if error_cnt else 0)


@utils.command("schedules")
@with_appcontext
def schedules():
    """List harvesting schedules."""
    celery_ext = current_app.extensions.get("invenio-celery")
    for key, value in celery_ext.celery.conf.beat_schedule.items():
        click.echo(key + "\t", nl=False)
        click.echo(value)


@utils.command("validate")
@click.argument("jsonfile", type=click.File("r"))
@click.argument("type", default="doc")
@click.option("-v", "--verbose", "verbose", is_flag=True, default=False)
@click.option("-d", "--debug", "debug", is_flag=True, default=False)
@click.option("-e", "--error_file", "error_file_name", default=None, help="error file")
@click.option("-o", "--ok_file", "ok_file_name", default=None, help="ok file")
@with_appcontext
def check_validate(jsonfile, type, verbose, debug, error_file_name, ok_file_name):
    """Check record validation."""
    click.secho(f"Testing json schema for file: {jsonfile.name} type: {type}", fg="green")

    schema_path = current_jsonschemas.url_to_path(get_schema_for_resource(type))
    schema = current_jsonschemas.get_schema(path=schema_path)
    schema = _records_state.replace_refs(schema)

    datas = json.load(jsonfile)
    count = 0
    if error_file_name:
        error_file = JsonWriter(error_file_name)
    if ok_file_name:
        ok_file = JsonWriter(ok_file_name)
    for count, data in enumerate(datas, 1):
        if verbose:
            click.echo(f"\tTest record: {count}")
        if not data.get("$schema"):
            scheme = current_app.config.get("JSONSCHEMAS_URL_SCHEME")
            host = current_app.config.get("JSONSCHEMAS_HOST")
            endpoint = current_app.config.get("JSONSCHEMAS_ENDPOINT")
            url_schema = f"{scheme}://{host}{endpoint}{schema_path}"
            data["$schema"] = url_schema
        if not data.get("pid"):
            # create dummy pid in data
            data["pid"] = "dummy"
        try:
            validate(data, schema)
            if ok_file_name:
                if data["pid"] == "dummy":
                    del data["pid"]
                ok_file.write(data)
        except ValidationError:
            trace_lines = traceback.format_exc(1).split("\n")
            trace = trace_lines[5].strip()
            click.secho(f"Error validate in record: {count} {trace}", fg="red")
            if error_file_name:
                error_file.write(data)
            if debug:
                pass


@utils.command()
@click.argument("pid_file", type=click.File("r"))
@click.argument("xml_file_in", type=click.File("r"))
@click.argument("xml_file_out", type=click.File("wb"))
@click.option("-t", "--tag", "tag", default="001")
@click.option("-p", "--progress", "progress", is_flag=True, default=False)
@click.option("-v", "--verbose", "verbose", is_flag=True, default=False)
def extract_from_xml(pid_file, xml_file_in, xml_file_out, tag, progress, verbose):
    """Extracts xml records with pids."""
    click.secho("Extract pids from xml: ", fg="green")
    click.secho(f"PID file    : {pid_file.name}")
    click.secho(f"XML file in : {xml_file_in.name}")
    click.secho(f"XML file out: {xml_file_out.name}")

    found_pids = {}
    pids = {line.strip(): 0 for line in pid_file}
    count = len(pids)
    click.secho(f"Search pids count: {count}")
    xml_file_out.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
    xml_file_out.write(b'<collection xmlns="http://www.loc.gov/MARC21/slim">\n\n')
    found = 0
    for idx, xml in enumerate(read_xml_record(xml_file_in), 1):
        for child in xml:
            is_controlfield = child.tag == "controlfield"
            is_tag = child.get("tag") == tag
            if is_controlfield and is_tag:
                if progress:
                    click.secho(f"{idx:>10} {child.text!r:>20}\r", nl=False)
                if pids.get(child.text, -1) >= 0:
                    found += 1
                    pids[child.text] += 1
                    data = etree.tostring(xml, pretty_print=True, encoding="UTF-8").strip()

                    xml_file_out.write(data)
                    found_pids[child.text] = True
                    if verbose:
                        click.secho(f"Found: {child.text} on position: {idx}")
                    break
    xml_file_out.write(b"\n</collection>")
    if count != found:
        click.secho(f"Count: {count} Found: {found}", fg="red")
        for key, value in pids.items():
            if value == 0:
                click.secho(key)


@utils.command()
@click.argument("pid_file", type=click.File("r"))
@click.argument("json_file_in", type=click.File("r"))
@click.argument("json_file_out")
@click.option("-t", "--tag", "tag", default="pid")
@click.option("-p", "--progress", "progress", is_flag=True, default=False)
@click.option("-v", "--verbose", "verbose", is_flag=True, default=False)
def extract_from_json(pid_file, json_file_in, json_file_out, tag, progress, verbose):
    """Extracts json records with pids."""
    click.secho("Extract pids from json: ", fg="green")
    click.secho(f"PID file     : {pid_file.name}")
    click.secho(f"JSON file in : {json_file_in.name}")
    click.secho(f"JSON file out: {json_file_out}")

    pids = {line.strip(): 0 for line in pid_file}
    count = len(pids)
    click.secho(f"Search pids count: {count}")
    out = JsonWriter(json_file_out)
    found = 0
    for idx, data in enumerate(read_json_record(json_file_in), 1):
        pid = data.get(tag)
        if progress:
            click.secho(f"{idx:>10} {pid:>20}\r", nl=False)
        if pid in pids:
            found += 1
            pids[pid] += 1
            out.write(data)
            if verbose:
                click.secho(f"Found: {pid} on position: {idx}")
    if count != found:
        click.secho(f"Count: {count} Found: {found}", fg="red")
        for key, value in pids.items():
            if value == 0:
                click.secho(key)


@utils.command("reserve_pid_range")
@click.option("-t", "--pid_type", "pid_type", default=None, help="pid type of the resource")
@click.option(
    "-n",
    "--records_number",
    "records_number",
    default=None,
    help="Number of records to load",
)
@click.option(
    "-u",
    "--unused",
    "unused",
    is_flag=True,
    default=False,
    help="Set unused (gaps) pids status to NEW ",
)
@with_appcontext
def reserve_pid_range(pid_type, records_number, unused):
    """Reserve a range of pids for future records loading.

    reserved pids will have the status RESERVED.
    - pid_type: the pid type of the resource as configured in config.py
    - records_number: number of new records(with pids) to load.
    - unused: set that the status of unused (gaps) pids to NEW.
    """
    click.secho(f'Reserving pids for loading "{pid_type}" records', fg="green")
    try:
        records_number = int(records_number)
    except ValueError:
        raise ValueError("Parameter records_number must be integer.")

    record_class = get_record_class_from_schema_or_pid_type(pid_type=pid_type)
    if not record_class:
        raise AttributeError("Invalid pid type.")

    identifier = record_class.provider.identifier
    reserved_pids = []
    for _ in range(records_number):
        pid = identifier.next()
        reserved_pids.append(pid)
        record_class.provider.create(pid_type, pid_value=pid, status=PIDStatus.RESERVED)
        db.session.commit()
    min_pid = min(reserved_pids)
    max_pid = max(reserved_pids)
    click.secho(f"reserved_pids range, from: {min_pid} to: {max_pid}")
    if unused:
        for pid in range(1, identifier.max()):
            if not db.session.query(identifier.query.filter(identifier.recid == pid).exists()).scalar():
                record_class.provider.create(pid_type, pid_value=pid, status=PIDStatus.NEW)
                db.session.add(identifier(recid=pid))
            db.session.commit()


@utils.command("export")
@click.option("-v", "--verbose", "verbose", is_flag=True, default=False)
@click.option("-t", "--pid_type", "pid_type", default="doc")
@click.option("-o", "--outfile", "outfile_name", required=True)
@click.option("-i", "--pidfile", "pidfile", type=click.File("r"), default=None)
@click.option("-I", "--indent", "indent", type=click.INT, default=2)
@click.option("-s", "--schema", "schema", is_flag=True, default=False)
@with_appcontext
def export(verbose, pid_type, outfile_name, pidfile, indent, schema):
    """Export REROILS record.

    :param verbose: verbose
    :param pid_type: record type
    :param outfile: Json output file
    :param pidfile: files with pids to extract
    :param indent: indent for output
    :param schema: do not delete $schema
    """
    click.secho(f"Export {pid_type} records: {outfile_name}", fg="green")
    outfile = JsonWriter(outfile_name)
    record_class = get_record_class_from_schema_or_pid_type(pid_type=pid_type)

    pids = list(filter(None, [line.rstrip() for line in pidfile])) if pidfile else record_class.get_all_pids()

    agents_sources = current_app.config.get("RERO_ILS_AGENTS_SOURCES", [])
    for count, pid in enumerate(pids, 1):
        try:
            rec = record_class.get_record_by_pid(pid)
            if verbose:
                click.echo(f"{count: <8} {pid_type} export {rec.pid}:{rec.id}")
            if not schema:
                rec.pop("$schema", None)
                if isinstance(rec, RemoteEntity):
                    for agent_source in agents_sources:
                        rec.get(agent_source, {}).pop("$schema", None)
            outfile.write(rec)
        except Exception as err:
            click.echo(err)
            click.echo(f"ERROR: Cannot export pid:{pid}")


def create_personal(name, user_id, scopes=None, is_internal=False, access_token=None):
    """Create a personal access token.

    A token that is bound to a specific user and which doesn't expire, i.e.
    similar to the concept of an API key.

    :param name: Client name.
    :param user_id: User ID.
    :param scopes: The list of permitted scopes. (Default: ``None``)
    :param is_internal: If ``True`` it's a internal access token.
            (Default: ``False``)
    :param access_token: personalized access_token.
    :returns: A new access token.
    """
    with db.session.begin_nested():
        scopes = " ".join(scopes) if scopes else ""

        client = Client(
            name=name,
            user_id=user_id,
            is_internal=True,
            is_confidential=False,
            _default_scopes=scopes,
        )
        client.gen_salt()

        if not access_token:
            access_token = gen_salt(current_app.config.get("OAUTH2SERVER_TOKEN_PERSONAL_SALT_LEN"))
        token = Token(
            client_id=client.client_id,
            user_id=user_id,
            access_token=access_token,
            expires=None,
            _scopes=scopes,
            is_personal=True,
            is_internal=is_internal,
        )

        db.session.add(client)
        db.session.add(token)

    return token


@utils.command()
@click.option("-n", "--name", required=True)
@click.option("-u", "--user", required=True, callback=process_user, help="User ID or email.")
@click.option("-s", "--scope", "scopes", multiple=True, callback=process_scopes)
@click.option("-i", "--internal", is_flag=True)
@click.option(
    "-t",
    "--access_token",
    "access_token",
    required=False,
    help="personalized access_token.",
)
@with_appcontext
def token_create(name, user, scopes, internal, access_token):
    """Create a personal OAuth token."""
    if user:
        token = create_personal(
            name,
            user.id,
            scopes=scopes,
            is_internal=internal,
            access_token=access_token,
        )
        db.session.commit()
        click.secho(token.access_token, fg="blue")
    else:
        click.secho("No user found", fg="red")


@utils.command()
@click.option("-v", "--verbose", is_flag=True, default=False, help="Verbose print.")
@click.option(
    "-h",
    "--hours",
    default=1,
    help="How many houres befor now not to delete default=1.",
)
@with_appcontext
def delete_loans_created(verbose, hours):
    """Delete loans with state CREATED."""
    return task_delete_loans_created(verbose=verbose, hours=hours)
