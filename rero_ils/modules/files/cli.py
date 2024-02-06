# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
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

"""Click command-line interface for item record management."""

from io import BytesIO
from random import choice, randrange, shuffle

import click
from flask import current_app
from flask.cli import with_appcontext
from invenio_access.permissions import system_identity
from invenio_db import db
from invenio_search import current_search
from rero_invenio_files.pdf import PDFGenerator

from rero_ils.modules.documents.api import Document
from rero_ils.modules.documents.dojson.contrib.jsontodc import dublincore
from rero_ils.modules.libraries.api import Library


def create_pdf_file(document):
    """Create a pdf file from a document record.

    :param doc: Document - a given bibliographic document
    :returns: a byte stream of the pdf content
    """
    # get the dublin core format of the given document
    dc = dublincore.do(document, "english")
    data = dict(header=f"Document ({document.pid})")
    if titles := dc.get("titles"):
        data["title"] = "\n".join(titles)
    if contributors := dc.get("contributors"):
        data["authors"] = contributors
    # Some fields are not well converted
    # TODO: remove this when the dc conversion will be fixed
    try:
        if descriptions := dc.get("descriptions"):
            data["summary"] = "\n".join(descriptions)
    except Exception:
        pass
    generator = PDFGenerator(data)
    generator.render()
    return generator.output()


def create_pdf_record_files(document, metadata, flush=False):
    """Creates and attach a pdf file to a given document.

    :param document: Document - the document record.
    :param metadata: dict - file metadata.
    """
    # add document link
    metadata.setdefault("links", [f"doc_{document.pid}"])
    ext = current_app.extensions["rero-invenio-files"]
    # get services
    record_service = ext.records_service
    file_service = ext.records_files_service
    # generate the PDF file
    stream = BytesIO(create_pdf_file(document))
    # create the record file
    record = record_service.record_cls.create(data={"metadata": metadata})
    record.commit()
    recid = record["id"]
    # index the file record
    record_service.indexer.index_by_id(record.id)
    if flush:
        current_search.flush_and_refresh(record_service.record_cls.index._name)
    # attach the file record to the document
    file_name = f"doc_{document.pid}.pdf"
    file_service.init_files(system_identity, recid, [{"key": file_name}])
    file_service.set_file_content(system_identity, recid, file_name, stream)
    file_service.commit_file(system_identity, recid, file_name)
    db.session.commit()


@click.command()
@click.argument("number", type=int)
@with_appcontext
def create_files(number):
    """Create attached files.

    :param number: integer - number of the files to generate
    """
    collections = ["col1", "col2", "col3"]
    doc_pids = list(Document.get_all_pids())
    lib_pids = list(Library.get_all_pids())
    shuffle(doc_pids)

    for _ in range(0, number):
        pid = choice(doc_pids)
        doc = Document.get_record_by_pid(pid)
        while doc.get('harvested'):
            pid = choice(doc_pids)
            doc = Document.get_record_by_pid(pid)
        click.echo(f"Create file for {pid}")
        lib_pid = choice(lib_pids)
        metadata = dict(
            collections=[choice(collections)],
            owners=[f"lib_{lib_pid}"]
        )
        for _ in range(randrange(10)):
            create_pdf_record_files(document=doc, metadata=metadata)
