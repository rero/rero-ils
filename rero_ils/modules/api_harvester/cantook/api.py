# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2024 RERO
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

"""API for cantook records."""

from __future__ import absolute_import, print_function

from invenio_db import db
from requests import codes as requests_codes

from rero_ils.modules.documents.api import Document, DocumentsSearch
from rero_ils.modules.holdings.api import Holding, HoldingsSearch, create_holding
from rero_ils.modules.utils import JsonWriter, requests_retry_session

from ..api import ApiHarvest
from ..models import HarvestActionType
from .dojson.json import cantook_json


class ApiCantook(ApiHarvest):
    """ApiCantook class.

    Class for harvesting ebooks from cantook API resources.
    """

    def __init__(
        self, name, file_name=None, process=False, harvest_count=-1, verbose=False
    ):
        """Class init."""
        super().__init__(
            name=name,
            process=process,
            harvest_count=harvest_count,
            verbose=verbose,
        )
        if file_name:
            self.file = JsonWriter(file_name)
        self._vendor = "CANTOOK"

    def get_request_url(self, start_date="1990-01-01", page=1):
        """Get request URL.

        :param start_date: date from where records has to be harvested
        :param page: page from where records have to be harvested
        :resturns: request url
        """
        params = f"start_at={start_date}&page={page}"
        return f"{self._url}/v1/resources.json?{params}"

    def delete_holdings(self, document_pid):
        """
        Delete holdings.

        :param document_pid: document pid
        """
        for hold_pid in list(Holding.get_holdings_pid_by_document_pid(document_pid)):
            if holding := Holding.get_record_by_pid(hold_pid):
                for electronic_location in holding["electronic_location"]:
                    if electronic_location["source"] == self._code:
                        holding.delete(dbcommit=True, delindex=True)
                        break

    def create_holdings(self, document_pid, link):
        """
        Create holdings.

        :param document_pid: document pid
        :param link: link to cantook document
        """
        holdings = []
        for _, info in self._info.items():
            item_type_pid = info["item_type_pid"]
            for location_pid, url in info["locations"].items():
                if url:
                    uri_split = link.split("/")[3:]
                    uri_split.insert(0, url.rstrip("/"))
                    link = "/".join(uri_split)
                # See if the holding already exist
                query = (
                    HoldingsSearch()
                    .filter("term", document__pid=document_pid)
                    .filter("term", location__pid=location_pid)
                    .filter("term", holdings_type="electronic")
                    .filter("term", electronic_location__source=self._code)
                )
                if query.count() == 0:
                    holding = create_holding(
                        document_pid=document_pid,
                        location_pid=location_pid,
                        item_type_pid=item_type_pid,
                        electronic_location={"source": self._code, "uri": link},
                        holdings_type="electronic",
                    )
                    holdings.append(holding)
        db.session.commit()
        for holding in holdings:
            holding.reindex()

    def create_update_record(self, data):
        """Create, update or delete record.

        :param data: date for record operation
        :returns: harvested id and status
        """
        status = HarvestActionType.NOTSET
        record = None
        record_data = cantook_json.do(data)
        if record_data.pop("deleted", None):
            status = HarvestActionType.DELETED
        link = record_data.pop("link", None)
        # See if we have this document already
        harvested_id = record_data.pop("pid")
        query = (
            DocumentsSearch()
            .filter("term", identifiedBy__value__raw=harvested_id)
            .source(includes=["pid"])
        )
        try:
            pid = next(query.scan()).pid
        except StopIteration:
            pid = None
        if pid:
            if doc := Document.get_record_by_pid(pid):
                if status == HarvestActionType.DELETED:
                    self._count_del += 1
                    self.delete_holdings(document_pid=doc.pid)
                    # Try to delete document (we have to delete `harvested` for this)
                    doc.pop("harvested", None)
                    if not doc.reasons_not_to_delete():
                        doc.delete(dbcommit=True, delindex=True)
                else:
                    self._count_upd += 1
                    status = HarvestActionType.UPDATED
                    record_data["pid"] = doc.pid
                    record = doc.replace(data=record_data, dbcommit=True, reindex=True)
                    self.create_holdings(document_pid=record.pid, link=link)
        elif status == HarvestActionType.NOTSET:
            self._count_new += 1
            status = HarvestActionType.CREATED
            record = Document.create(data=record_data, dbcommit=True, reindex=True)
            self.create_holdings(document_pid=record.pid, link=link)
        return harvested_id, status

    def harvest_records(self, from_date):
        """Harvest CANTOOK records.

        :param from_date: record changed after this date to get
        :returns: count and total items
        """
        self._count = 0
        url = self.get_request_url(start_date=from_date, page=1)
        request = requests_retry_session().get(url)
        total_pages = int(request.headers.get("X-Total-Pages", 0))
        total_items = int(request.headers.get("X-Total-Items", 0))
        current_page = int(request.headers.get("X-Current-Page", 0))
        while (
            request.status_code == requests_codes.ok
            and current_page <= total_pages
            and (self.harvest_count < 0 or self._count < self.harvest_count)
        ):
            self.verbose_print(f"API page: {current_page} url: {url}")
            self.process_records(request.json().get("resources", []))
            # get next page and update current_page
            url = self.get_request_url(start_date=from_date, page=current_page + 1)
            request = requests_retry_session().get(url)
            current_page = int(request.headers.get("X-Current-Page", 0))

        return self._count, total_items
