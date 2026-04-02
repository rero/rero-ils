# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2026 RERO
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

"""Document-specific CLI commands."""

import logging
import multiprocessing
import os
import sys
import traceback
from copy import deepcopy
from datetime import datetime

import click
import redis as redis_module
from dojson.contrib.marc21.utils import create_record
from flask import current_app
from flask.cli import with_appcontext
from invenio_jsonschemas.proxies import current_jsonschemas
from invenio_records_rest.utils import obj_or_import_string
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from lxml import etree
from werkzeug.local import LocalProxy

from rero_ils.modules.documents.api import Document
from rero_ils.modules.documents.dojson.contrib.marc21tojson.rero import marc21
from rero_ils.modules.documents.tasks import add_cover_urls as task_add_cover_urls
from rero_ils.modules.documents.tasks import process_cover_url_queue
from rero_ils.modules.items.api import Item
from rero_ils.modules.libraries.api import Library
from rero_ils.modules.local_fields.api import LocalField
from rero_ils.modules.locations.api import Location
from rero_ils.modules.utils import (
    JsonWriter,
    cached,
    extracted_data_from_ref,
    get_schema_for_resource,
    read_json_record,
    read_xml_record,
)

_records_state = LocalProxy(lambda: current_app.extensions["invenio-records"])


@click.group()
def documents():
    """Document management commands."""


def validate_lofi(local_field, lofi_schema, count):
    """Validate local fields."""
    try:
        if not local_field.get("pid"):
            local_field["pid"] = f"dummy_{count}"
        validate(local_field, lofi_schema)
    except Exception as err:
        trace = "\n".join(traceback.format_exc(1).split("\n")[:6])
        return f"{err.args[0]} \n{trace}"


def add_org_lib_doc(item, doc_pid="dummy"):
    """Add organisation, library and document to item for validation."""
    item = deepcopy(item)
    item["pid"] = "dummy"
    if "location" not in item:
        raise ValueError("No 'location' in item")
    location_pid = extracted_data_from_ref(item.get("location"))
    location = Location.get_record_by_pid(location_pid)
    if not location:
        raise ValueError(f"Location not found: {location_pid}")
    library = Library.get_record_by_pid(location.library_pid)
    if not library:
        raise ValueError(f"Library not found: {location.library_pid}")
    item["organisation"] = library.get("organisation")
    item["library"] = location.get("library")
    if "document" not in item:
        raise ValueError("No 'document' in item")
    item["document"]["$ref"] = item["document"]["$ref"].replace("{document_pid}", doc_pid)
    return item


@cached(timeout=2 * 60 * 60, key_prefix="doc_item_lofi_schemas", query_string=False)  # 2 hour timeout
def get_doc_item_lofi_schemas():
    """Get document, item, local field schemas."""
    schema_path = current_jsonschemas.url_to_path(get_schema_for_resource("doc"))
    schema = current_jsonschemas.get_schema(path=schema_path)
    doc_schema = _records_state.replace_refs(schema)
    schema_path = current_jsonschemas.url_to_path(get_schema_for_resource("item"))
    schema = current_jsonschemas.get_schema(path=schema_path)
    item_schema = _records_state.replace_refs(schema)
    schema_path = current_jsonschemas.url_to_path(get_schema_for_resource("lofi"))
    schema = current_jsonschemas.get_schema(path=schema_path)
    lofi_schema = _records_state.replace_refs(schema)
    return doc_schema, item_schema, lofi_schema


def validate_documents_with_items_lofis(data, count=0, clean_pid=False, debug=False):
    """Validate REROILS record with items and local fields.

    :param data: document data.
    :param count: count of document.
    :param debug: get traceback.
    :returns: document, items, local fields error messages and total error count.
    """
    data = deepcopy(data)
    doc_schema, item_schema, lofi_schema = get_doc_item_lofi_schemas()
    items = data.pop("items", [])
    local_field_docs = data.pop("local_fields", [])
    errors = {"documents": [], "items": [], "local_fields": []}

    if clean_pid or not data.get("pid"):
        data["pid"] = f"dummy_{count}"
    try:
        validate(data, doc_schema)
    except ValidationError as err:
        errors["documents"].append(f"{err.args[0]}")
        if debug:
            errors["documents"][-1] = f"{errors['documents'][-1]}\n{traceback.format_exc(1)}"
    for idx, item in enumerate(items, 1):
        local_field_items = item.pop("local_fields", [])
        try:
            validate(add_org_lib_doc(item=item), item_schema)
        except Exception as err:
            errors["items"].append(f"{idx} {err.args[0]}")
            if debug:
                errors["items"][-1] = f"{errors['items'][-1]}\n{traceback.format_exc(1)}"
        for lofi_idx, local_field in enumerate(local_field_items, 1):
            try:
                if not local_field.get("pid"):
                    local_field["pid"] = f"dummy_{count}"
                validate(local_field, lofi_schema)
            except Exception as err:
                errors["local_fields"].append(f"item: {idx} lofi: {lofi_idx} {err.args[0]}")
                if debug:
                    errors["local_fields"][-1] = f"{errors['local_fields'][-1]}\n{traceback.format_exc(1)}"

    for idx, local_field in enumerate(local_field_docs, 1):
        try:
            if not local_field.get("pid"):
                local_field["pid"] = f"dummy_{count}"
            validate(local_field, lofi_schema)
        except Exception as err:
            errors["local_fields"].append(f"doc lofi: {idx} {err.args[0]}")
            if debug:
                errors["local_fields"][-1] = f"{errors['local_fields'][-1]}\n{traceback.format_exc(1)}"
    return errors, len(errors["documents"]) + len(errors["items"]) + len(errors["local_fields"])


@documents.command("validate-documents-with-items-lofis")
@click.argument("infile", type=click.File("r"), default=sys.stdin)
@click.option("-v", "--verbose", "verbose", is_flag=True, default=False)
@click.option("-d", "--debug", "debug", is_flag=True, default=False)
@click.option("-c", "--clean_pid", "clean_pid", is_flag=True, default=False)
@with_appcontext
def validate_documents_with_items_lofis_cli(infile, verbose, debug, clean_pid):
    """Validate REROILS records with items.

    :param infile: Json file.
    :param verbose: verbose print.
    :param debug: get traceback.
    :param clean_pid: clean pids.
    """
    click.secho(f"Validate documents items lofis from {infile.name}.", fg="green")
    all_errors_count = 0
    for count, record in enumerate(read_json_record(infile), 1):
        pid = f"dummy_{count}" if clean_pid else record.get("pid", f"dummy_{count}")
        errors, errors_count = validate_documents_with_items_lofis(
            data=record, count=count, clean_pid=clean_pid, debug=debug
        )
        if errors_count:
            all_errors_count += errors_count
            click.echo(f"{count:<10} document: {pid} errors: {errors_count}")
            for error_name in ["documents", "items", "local_fields"]:
                for error in errors[error_name]:
                    click.secho(f"    {error_name}: {error}", fg="red")
        elif verbose:
            click.secho(f"{count:<10} document: {pid} OK", fg="green")
    click.secho(f"Errors: {all_errors_count}", fg="red")


def create_document_with_items_lofis(
    data,
    dont_stop_on_error,
    file_document,
    error_file_doc,
    file_item,
    error_file_item,
    file_lofi,
    error_file_lofi,
    commit,
    debug,
):
    """Load REROILS record with items and lofi.

    :param data: record to load.
    :param dont_stop_on_error: don't stop on error
    :param file_document: file to write document records.
    :param error_file_doc: file to write document error records.
    :param file_item: file to write item records.
    :param error_file_item: file to write item error records.
    :param file_lofi: file to write local field records.
    :param error_file_lofi: file to write local field error records.
    :param commit: commit to database every count records
    :param debug: print traceback
    """

    def create_lofi(
        local_field,
        parent_pid,
        file_lofi,
        error_file_lofi,
        dont_stop_on_error,
        commit,
        debug,
        pids,
        errors,
    ):
        """Create local field."""
        try:
            local_field.setdefault("parent", {})["$ref"] = (
                local_field.get("parent", {}).get("$ref", "").format(parent_pid=parent_pid)
            )
            local_field_rec = LocalField.create(data=local_field, dbcommit=commit, reindex=commit)
            pids.setdefault("lofis", []).append(local_field_rec.pid)
            file_lofi.write(local_field_rec)
        except Exception as err:
            errors["local_fields"].append(f"{err.args[0]}")
            if debug:
                errors["local_fields"][-1] = f"{errors['local_fields'][-1]}\n{traceback.format_exc(1)}"
            if error_file_lofi:
                error_file_lofi.write(local_field_rec)
            if not dont_stop_on_error:
                click.secho(errors["local_fields"][-1], fg="red")
                sys.exit(1)
        return pids, errors

    schema_path = current_jsonschemas.url_to_path(get_schema_for_resource("item"))
    schema = current_jsonschemas.get_schema(path=schema_path)
    item_schema = _records_state.replace_refs(schema)

    items = data.pop("items", [])
    doc_local_fields = data.pop("local_fields", [])
    errors = {"documents": [], "items": [], "local_fields": []}
    pids = {}
    try:
        doc_rec = Document.create(data=data, dbcommit=commit, reindex=commit, delete_pid=True)
        pids["doc"] = doc_rec.pid
        file_document.write(doc_rec)

        for item in items:
            try:
                item_local_fields = item.pop("local_fields", [])
                item = add_org_lib_doc(item=item, doc_pid=doc_rec.pid)
                validate(item, item_schema)
                item_rec = Item.create(data=item, delete_pid=True, dbcommit=commit, reindex=commit)
                pids.setdefault("items", []).append(item_rec.pid)
                file_item.write(item_rec)
                for local_field in item_local_fields:
                    pids, errors = create_lofi(
                        local_field=local_field,
                        parent_pid=item_rec.pid,
                        file_lofi=file_lofi,
                        error_file_lofi=error_file_lofi,
                        dont_stop_on_error=dont_stop_on_error,
                        commit=commit,
                        debug=debug,
                        pids=pids,
                        errors=errors,
                    )
            except Exception as err:
                errors["items"].append(f"{err.args[0]}")
                if debug:
                    errors["items"][-1] = f"{errors['items'][-1]}\n{traceback.format_exc(1)}"
                if error_file_item:
                    if item_local_fields:
                        item_rec["local_fields"] = item_local_fields
                    error_file_item.write(item_rec)
                if not dont_stop_on_error:
                    click.secho(errors["items"][-1], fg="red")
                    sys.exit(1)

        for local_field in doc_local_fields:
            pids, errors = create_lofi(
                local_field=local_field,
                parent_pid=doc_rec.pid,
                file_lofi=file_lofi,
                error_file_lofi=error_file_lofi,
                dont_stop_on_error=dont_stop_on_error,
                commit=commit,
                debug=debug,
                pids=pids,
                errors=errors,
            )
    except Exception as err:
        errors["documents"].append(f"{err.args[0]}")
        if debug:
            errors["documents"][-1] = f"{errors['documents'][-1]}\n{traceback.format_exc(1)}"
        if items:
            data["items"] = items
        if doc_local_fields:
            data["local_fields"] = doc_local_fields
        if error_file_doc:
            error_file_doc.write(data)
        if not dont_stop_on_error:
            click.echo(errors["documents"][-1], fg="red")
            sys.exit(1)
    return pids, errors


@documents.command("create-documents-with-items-lofis")
@click.argument("infile", type=click.File("r"), default=sys.stdin)
@click.option("-o", "--dont-stop", "dont_stop_on_error", is_flag=True, default=False)
@click.option("-e", "--save_errors", "save_errors", is_flag=True, default=False)
@click.option("-c", "--commit", "commit", is_flag=True, default=False)
@click.option("-v", "--verbose", "verbose", is_flag=True, default=False)
@click.option("-d", "--debug", "debug", is_flag=True, default=False)
@with_appcontext
def create_documents_with_items_lofis_cli(infile, dont_stop_on_error, save_errors, commit, verbose, debug):
    """Load REROILS record with items and lofi.

    :param infile: Json file
    :param dont_stop_on_error: don't stop on error
    :param save_errors: save error records to file
    :param commit: commit to database every count records
    :param verbose: verbose print
    :param debug: print traceback
    """
    click.secho(f"Loading documents items lofis from {infile.name}.", fg="green")
    name, ext = os.path.splitext(infile.name)
    file_document = JsonWriter(f"{name}_documents{ext}")
    file_item = JsonWriter(f"{name}_items{ext}")
    file_lofi = JsonWriter(f"{name}_lofis{ext}")
    error_file_doc = None
    error_file_item = None
    error_file_lofi = None
    if save_errors:
        error_file_doc = JsonWriter(f"{name}_documents_errors{ext}")
        error_file_item = JsonWriter(f"{name}_items_errors{ext}")
        error_file_lofi = JsonWriter(f"{name}_lofis_errors{ext}")

    count = 0
    counts = {
        "documents": {"ok": 0, "error": 0},
        "items": {"ok": 0, "error": 0},
        "local_fields": {"ok": 0, "error": 0},
    }
    for count, record in enumerate(read_json_record(infile), 1):
        pids, errors = create_document_with_items_lofis(
            data=record,
            dont_stop_on_error=dont_stop_on_error,
            file_document=file_document,
            error_file_doc=error_file_doc,
            file_item=file_item,
            error_file_item=error_file_item,
            file_lofi=file_lofi,
            error_file_lofi=error_file_lofi,
            commit=commit,
            debug=debug,
        )
        if doc_pid := pids.get("doc"):
            counts["documents"]["ok"] += 1
            pid_msg = f"doc: {doc_pid}"
        else:
            pid_msg = "doc: ???"
        if item_pids := ", ".join(pids.get("items", [])):
            counts["items"]["ok"] += len(item_pids)
            pid_msg = f"{pid_msg} items: {item_pids}"
        if lofi_pids := ", ".join(pids.get("lofis", [])):
            counts["local_fields"]["ok"] += len(lofi_pids)
            pid_msg = f"{pid_msg} lofis: {lofi_pids}"
        if verbose:
            click.echo(f"{count:<10} {pid_msg}")
        for error_name, error_data in errors.items():
            if not verbose:
                click.echo(f"{count:<10} {pid_msg}")
            for error in error_data:
                counts[error_name]["error"] += 1
                click.secho(f"    {error_name}: {error}", fg="red")

    click.secho(f"Document count: {count}", fg="green")
    for count_type, count in counts.items():
        click.secho(f"{count_type}", fg="green")
        click.secho(f"    ok    : {count['ok']}", fg="green")
        click.secho(f"    errors: {count['error']}", fg="red")


def error_record(pid, record, notes):
    """Error record."""
    error_rec = {
        "adminMetadata": {"encodingLevel": "Full level", "note": notes},
        "issuance": {"main_type": "rdami:1001", "subtype": "materialUnit"},
        "language": [{"type": "bf:Language", "value": "und"}],
        "pid": pid,
        "provisionActivity": [{"startDate": int(datetime.now().year), "type": "bf:Publication"}],
        "title": [{"mainTitle": [{"value": f"ERROR DOCUMENT {pid}"}], "type": "bf:Title"}],
        "type": [{"main_type": "docmaintype_other"}],
        "_masked": True,
    }
    if record:
        schema = record.get("$schema")
        if schema and schema != "dummy":
            error_rec["$schema"] = schema
        if identified_by := record.get("identifiedBy"):
            error_rec["identifiedBy"] = identified_by
    return error_rec


def do_worker(marc21records, results, pid_required, debug, dojson, schema=None):
    """Worker for marc21 to json transformation."""
    if dojson:
        dojson = obj_or_import_string(f"rero_ils.modules.documents.dojson.contrib.marc21tojson.{dojson}:marc21")
    else:
        dojson = marc21
    for data in marc21records:
        data_json = data["json"]
        pid = data_json.get("001", "???")
        record = {}
        try:
            record = dojson.do(data_json)
            if not record.get("$schema"):
                record["$schema"] = "dummy"
            if not pid_required and not record.get("pid"):
                record["pid"] = "dummy"
            if schema:
                items = record.pop("items", None)
                local_fields = record.pop("local_fields", None)
                validate(record, schema)
                if items:
                    record["items"] = items
                if local_fields:
                    record["local_fields"] = local_fields
            if record["$schema"] == "dummy":
                del record["$schema"]
            if not pid_required and record["pid"] == "dummy":
                del record["pid"]
            results.append({"status": True, "record": record})
        except ValidationError as err:
            if debug:
                pass
            trace_lines = traceback.format_exc(1).split("\n")
            trace = trace_lines[5].strip()
            field_035 = data_json.get("035__", {})
            if isinstance(field_035, tuple):
                field_035 = field_035[0]
            rero_pid = (field_035.get("a", "UNKNOWN"),)
            msg = f"ERROR:\t{pid}\t{rero_pid}\t{err.args[0]}\t-\t{trace}"
            click.secho(msg, fg="red")
            results.append(
                {
                    "pid": pid,
                    "status": False,
                    "data": data["xml"],
                    "record": error_record(pid, record, [f"{err.args[0]}", f"{trace}"]),
                }
            )
        except Exception as err:
            field_035 = data_json.get("035__", {})
            if isinstance(field_035, tuple):
                field_035 = field_035[0]
            rero_pid = (field_035.get("a", "UNKNOWN"),)
            msg = f"ERROR:\t{pid}\t{rero_pid}\t{err.args[0]}"
            click.secho(msg, fg="red")
            if debug:
                traceback.print_exc()
            results.append(
                {
                    "pid": pid,
                    "status": False,
                    "data": data["xml"],
                    "record": error_record(pid, record, [f"{err.args[0]}"]),
                }
            )


class Marc21toJson:
    """Class for Marc21 recorts to Json transformation."""

    __slots__ = [
        "active_buffer",
        "buffer",
        "chunk",
        "count",
        "count_ko",
        "count_ok",
        "ctx",
        "debug",
        "dojson",
        "error_records",
        "json_file_ok",
        "parallel",
        "pid_mapping",
        "pid_required",
        "pids",
        "results",
        "schema",
        "verbose",
        "xml_file",
        "xml_file_error",
    ]

    def __init__(
        self,
        xml_file,
        json_file_ok,
        xml_file_error,
        parallel=8,
        chunk=10000,
        dojson=None,
        verbose=False,
        debug=False,
        pid_required=False,
        schema=None,
        pid_mapping=None,
        error_records=False,
    ):
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
        self.schema = schema
        self.dojson = dojson
        if verbose:
            click.echo(f"Main process pid: {multiprocessing.current_process().pid}")
        self.debug = debug
        if debug:
            multiprocessing.log_to_stderr(logging.DEBUG)
        self.error_records = error_records
        self.pid_required = pid_required
        self.pids = {}
        if pid_mapping:
            click.echo(f"Read pid mapping: {pid_mapping.name}")
            datas = read_json_record(pid_mapping)
            self.pids = {data["bib_id"]: data["document_pid"] for data in datas}
            click.echo(f"  Found pids: {len(self.pids)}")
        self.ctx = multiprocessing.get_context("spawn")
        manager = self.ctx.Manager()
        self.results = manager.list()
        self.active_buffer = 0
        self.buffer = []
        for _ in range(parallel):
            self.buffer.append({"process": None, "records": []})
        self.start()

    def counts(self):
        """Get the counters."""
        return self.count, self.count_ok, self.count_ko

    def write_results(self):
        """Write results from multiprocess to file."""
        while self.results:
            value = self.results.pop(0)
            status = value.get("status")
            data = value.get("data")
            record = value.get("record")
            if status:
                self.count_ok += 1
            else:
                self.count_ko += 1
                self.xml_file_error.write(data)
            if status or self.error_records:
                self.json_file_ok.write(record)

    def wait_free_process(self):
        """Wait for next process to finish."""
        index = (self.active_buffer + 1) % self.parallel
        if process := self.buffer[index]["process"]:
            process.join()
        for index in range(self.parallel):
            process = self.buffer[index].get("process")
            if process and process.exitcode is not None:
                del self.buffer[index]["process"]
                self.buffer[index].clear()
                self.buffer[index] = {"process": None, "records": []}

    def next_active_buffer(self):
        """Set the next active buffer index."""
        self.active_buffer = (self.active_buffer + 1) % self.parallel

    def wait_all_free_process(self):
        """Wait for all processes to finish."""
        for _ in range(self.parallel):
            self.wait_free_process()
            self.next_active_buffer()

    def start_new_process(self):
        """Start a new process in context."""
        new_process = self.ctx.Process(
            target=do_worker,
            args=(
                self.active_records,
                self.results,
                self.pid_required,
                self.debug,
                self.dojson,
                self.schema,
            ),
        )
        self.wait_free_process()
        new_process.start()
        self.active_process = new_process
        if self.verbose:
            start = 1 if self.count < self.chunk else self.count - len(self.active_records) + 1
            pid = new_process.pid
            click.echo(f"Start process: {pid} records: {start}..{self.count}")
        self.next_active_buffer()

    def write_start(self):
        """Write initial lines to files."""
        self.xml_file_error.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        self.xml_file_error.write(b'<collection xmlns="http://www.loc.gov/MARC21/slim">\n\n')

    def write_stop(self):
        """Write finishing lines to files."""
        self.xml_file_error.write(b"\n</collection>")

    def start(self):
        """Start the transformation."""
        click.echo("Start processing ...")
        self.write_start()
        for marc21xml in read_xml_record(self.xml_file):
            if self.pids:
                for child in marc21xml:
                    if child.attrib.get("tag") == "001":
                        old_pid = child.text
                        if pid := self.pids.get(old_pid):
                            new_pid = f"REROILS:{pid}"
                            child.text = new_pid
                        else:
                            click.echo(f"ERROR: No pid mapping for {old_pid}")
                        break
            marc21json_record = create_record(marc21xml)
            self.active_records.append(
                {
                    "json": marc21json_record,
                    "xml": etree.tostring(marc21xml, pretty_print=True, encoding="UTF-8").strip(),
                }
            )
            self.count += 1
            if len(self.active_records) % self.chunk == 0:
                self.write_results()
                self.start_new_process()

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
        return self.buffer[self.active_buffer]["process"]

    @active_process.setter
    def active_process(self, process):
        """Set the active process."""
        self.buffer[self.active_buffer]["process"] = process

    @property
    def active_records(self):
        """Get the active records."""
        return self.buffer[self.active_buffer]["records"]


@documents.command("marc21tojson")
@click.argument("xml_file", type=click.File("r"))
@click.argument("json_file_ok")
@click.argument("xml_file_error", type=click.File("wb"))
@click.option("-p", "--parallel", "parallel", default=8)
@click.option("-c", "--chunk", "chunk", default=10000)
@click.option("-v", "--verbose", "verbose", is_flag=True, default=False)
@click.option("-d", "--debug", "debug", is_flag=True, default=False)
@click.option("-r", "--pid_required", "pid_required", is_flag=True, default=False)
@click.option("-t", "--transformation", "transformation", default=None)
@click.option("-P", "--pid_mapping", "pid_mapping", type=click.File("r"), default=None)
@click.option("-e", "--error_records", "error_records", is_flag=True, default=False)
@with_appcontext
def marc21json(
    xml_file,
    json_file_ok,
    xml_file_error,
    parallel,
    chunk,
    verbose,
    debug,
    pid_required,
    transformation,
    pid_mapping,
    error_records,
):
    """Convert xml file to json with dojson."""
    click.secho("Marc21 to Json transform: ", fg="green", nl=False)
    if pid_required and verbose:
        click.secho(" (validation tests pid) ", nl=False)
    click.secho(xml_file.name)
    json_file_ok = JsonWriter(json_file_ok)

    path = current_jsonschemas.url_to_path(get_schema_for_resource("doc"))
    schema = current_jsonschemas.get_schema(path=path)
    schema = _records_state.replace_refs(schema)
    transform = Marc21toJson(
        xml_file,
        json_file_ok,
        xml_file_error,
        parallel,
        chunk,
        transformation,
        verbose,
        debug,
        pid_required,
        schema,
        pid_mapping,
        error_records,
    )

    count, count_ok, count_ko = transform.counts()

    click.secho("Total records: ", fg="green", nl=False)
    click.secho(str(count), nl=False)
    click.secho("-", nl=False)
    click.secho(str(count_ok + count_ko))

    click.secho("Records transformed: ", fg="green", nl=False)
    click.secho(str(count_ok))
    if count_ko:
        click.secho("Records with errors: ", fg="red", nl=False)
        click.secho(str(count_ko))


@documents.command()
@click.option("-c", "--commit", is_flag=True, default=False, help="Commit changes to the database.")
@click.option("-v", "--verbose", is_flag=True, default=False, help="Print progress output.")
@click.option("-C", "--cached", is_flag=True, default=True, help="Use cached thumbnails from the provider.")
@click.option("-d", "--delay", default=0, type=float, help="Seconds to sleep between requests.")
@click.option("-k", "--enqueue", is_flag=True, default=False, help="Run as Celery async task (enqueue)")
@with_appcontext
def add_cover_urls(commit, verbose, cached, delay, enqueue):
    """Add cover URLs to all documents with ISBNs and no cover URL."""
    if enqueue:
        task = task_add_cover_urls.delay(commit=commit, verbose=verbose, cached=cached, delay=delay)
        click.secho(f"Add cover URLs task enqueued (Celery) {task}", fg="yellow")
        return
    count = task_add_cover_urls(commit=commit, verbose=verbose, cached=cached, delay=delay)
    click.secho(f"\nDone. Updated {count.get('all', 0)} documents.", fg="green")
    for provider, n in sorted(count.items()):
        if provider != "all":
            click.secho(f"  {provider}: {n}", fg="green")


@documents.command("cover-url-queue-status")
@with_appcontext
def cover_url_queue_status_cli():
    """Show the current status of the cover image queue."""
    r = redis_module.StrictRedis.from_url(current_app.config["CACHE_REDIS_URL"])
    queue_key = current_app.config.get("RERO_ILS_COVER_URL_QUEUE_KEY", "rero_ils:cover_url_queue")
    worker_key = current_app.config.get("RERO_ILS_COVER_URL_WORKER_KEY", "rero_ils:cover_url_worker")
    paused_key = current_app.config.get("RERO_ILS_COVER_URL_PAUSED_KEY", "rero_ils:cover_url_paused")

    queue_size = r.scard(queue_key)
    paused = r.exists(paused_key)
    worker_running = r.exists(worker_key)
    worker_ttl = r.ttl(worker_key)

    click.secho(f"Queued documents : {queue_size}", fg="yellow")
    if paused:
        click.secho("Status           : paused (PIDs accumulate, no worker starts)", fg="red")
    elif worker_running:
        click.secho(f"Status           : running (lock TTL: {worker_ttl}s)", fg="green")
    else:
        click.secho("Status           : idle", fg="white")


@documents.command("cover-url-queue-worker")
@click.argument("action", type=click.Choice(["pause", "resume"]))
@with_appcontext
def cover_url_queue_worker_cli(action):
    """Pause or resume the cover image queue worker.

    pause  -- PIDs still accumulate but no worker starts.
    resume -- clears the pause flag and starts the worker if PIDs are pending.
    """
    r = redis_module.StrictRedis.from_url(current_app.config["CACHE_REDIS_URL"])
    queue_key = current_app.config.get("RERO_ILS_COVER_URL_QUEUE_KEY", "rero_ils:cover_url_queue")
    worker_key = current_app.config.get("RERO_ILS_COVER_URL_WORKER_KEY", "rero_ils:cover_url_worker")
    paused_key = current_app.config.get("RERO_ILS_COVER_URL_PAUSED_KEY", "rero_ils:cover_url_paused")
    delay = current_app.config.get("RERO_ILS_COVER_URL_TASK_DELAY", 10)

    if action == "pause":
        r.set(paused_key, 1)
        click.secho("Cover URL queue paused.", fg="yellow")
    else:
        r.delete(paused_key)
        queue_size = r.scard(queue_key)
        if queue_size > 0 and r.set(worker_key, 1, nx=True, ex=3600):
            process_cover_url_queue.apply_async(kwargs={"cached": True}, countdown=delay)
            click.secho(f"Cover URL queue resumed — worker started for {queue_size} document(s).", fg="green")
        else:
            click.secho(f"Cover URL queue resumed — {queue_size} document(s) pending.", fg="green")


@documents.command("cover-url-queue-clear")
@click.option("--yes-i-know", is_flag=True, default=False, help="Skip confirmation prompt.")
@with_appcontext
def cover_url_queue_clear_cli(yes_i_know):
    """Remove all pending PIDs from the cover image queue."""
    if not yes_i_know:
        click.confirm("Do you really want to clear the cover URL queue?", abort=True)
    r = redis_module.StrictRedis.from_url(current_app.config["CACHE_REDIS_URL"])
    queue_key = current_app.config.get("RERO_ILS_COVER_URL_QUEUE_KEY", "rero_ils:cover_url_queue")
    worker_key = current_app.config.get("RERO_ILS_COVER_URL_WORKER_KEY", "rero_ils:cover_url_worker")

    queue_size = r.scard(queue_key)
    r.delete(queue_key)
    r.delete(worker_key)
    click.secho(f"Cleared {queue_size} document(s) from the queue.", fg="green")
