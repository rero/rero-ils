# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2024 RERO
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

"""Celery tasks for documents."""

from datetime import datetime, timedelta

import click
from celery import shared_task
from flask import current_app

from rero_ils.modules.documents.api import Document, DocumentsSearch
from rero_ils.modules.utils import set_timestamp


@shared_task(ignore_result=True)
def reindex_document(pid):
    """Reindex a document.

    :param pid: str - pid value of the document to reindex.
    """
    Document.get_record_by_pid(pid).reindex()


@shared_task(ignore_result=True)
def delete_drafts(days=1, delete=False, verbose=False):
    """Delete drafts.

    :param days: Delete drafts older then days.
    :param delete: if True delete from DB and ES.
    :param verbose: Verbose print.
    :returns: count of deleted drafts.
    """
    days_ago = datetime.now() - timedelta(days=days)
    query = (
        DocumentsSearch()
        .filter("exists", field="_draft")
        .filter("range", _created={"lte": days_ago})
        .params(preserve_order=True)
        .sort({"_created": {"order": "asc"}})
    )
    pids = [hit.pid for hit in query.source("pid").scan()]
    count = len(pids)
    if verbose:
        click.secho(f"Delete drafts {days_ago} count: {count}", fg="yellow")
    for pid in pids:
        if doc := Document.get_record_by_pid(pid):
            if verbose:
                click.secho(f"Delete draft: {pid} {doc.created}", fg="yellow")
            if delete:
                try:
                    doc.delete(dbcommit=True, delindex=True)
                except Exception:
                    count -= 1
                    msg = f"COULD NOT DELETE DRAFT: {pid} {doc.reasons_not_to_delete()}"
                    if verbose:
                        click.secho(f"ERROR: {msg}", fg="red")
                    current_app.logger.warning(msg)

    set_timestamp("delete_drafts", msg={"deleted": count})
    return count
