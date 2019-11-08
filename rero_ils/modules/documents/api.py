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

"""API for manipulating documents."""


from functools import partial

from flask import current_app
from invenio_circulation.search.api import search_by_pid
from invenio_search.api import RecordsSearch

from .models import DocumentIdentifier
from .utils import publication_statement_text, series_format_text
from ..api import IlsRecord
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..organisations.api import Organisation
from ..providers import Provider

# provider
DocumentProvider = type(
    'DocumentProvider',
    (Provider,),
    dict(identifier=DocumentIdentifier, pid_type='doc')
)
# minter
document_id_minter = partial(id_minter, provider=DocumentProvider)
# fetcher
document_id_fetcher = partial(id_fetcher, provider=DocumentProvider)


class DocumentsSearch(RecordsSearch):
    """DocumentsSearch."""

    class Meta:
        """Search only on documents index."""

        index = 'documents'


class Document(IlsRecord):
    """Document class."""

    minter = document_id_minter
    fetcher = document_id_fetcher
    provider = DocumentProvider

    def is_available(self, view_code):
        """Get availability for document."""
        from ..holdings.api import Holding
        if view_code != current_app.config.get(
                'RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'):
            view_id = Organisation.get_record_by_viewcode(view_code)['pid']
            for holding_pid in Holding.get_holdings_pid_by_document_pid_by_org(
                    self.pid, view_id):
                holding = Holding.get_record_by_pid(holding_pid)
                if holding.available:
                    return True
        else:
            for holding_pid in Holding.get_holdings_pid_by_document_pid(
                    self.pid):
                holding = Holding.get_record_by_pid(holding_pid)
                if holding.available:
                    return True
        return False

    @property
    def harvested(self):
        """Is this record harvested from an external service."""
        return self.get('harvested')

    @property
    def can_edit(self):
        """Return a boolean for can_edit resource."""
        # TODO: Make this condition on data
        return not self.harvested

    def get_number_of_items(self):
        """Get number of items for document."""
        from ..items.api import ItemsSearch
        results = ItemsSearch().filter(
            'term', document__pid=self.pid).source().count()
        return results

    def get_number_of_loans(self):
        """Get number of document loans."""
        search = search_by_pid(
            document_pid=self.pid,
            exclude_states=[
                'CANCELLED',
                'ITEM_RETURNED',
            ]
        )
        results = search.source().count()
        return results

    def get_links_to_me(self):
        """Get number of links."""
        links = {}
        items = self.get_number_of_items()
        if items:
            links['items'] = items
        loans = self.get_number_of_loans()
        if loans:
            links['loans'] = loans
        return links

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        cannot_delete = {}
        links = self.get_links_to_me()
        if links:
            cannot_delete['links'] = links
        if self.harvested:
            cannot_delete['others'] = dict(harvested=True)
        return cannot_delete

    def dumps(self, **kwargs):
        """Return pure Python dictionary with record metadata."""
        dump = super(Document, self).dumps(**kwargs)
        provision_activities = dump.get('provisionActivity', [])
        for provision_activity in provision_activities:
            provision_activity["_text"] = \
                publication_statement_text(provision_activity)
        series = dump.get('series', [])
        for series_element in series:
            series_element["_text"] = series_format_text(series_element)
        return dump
