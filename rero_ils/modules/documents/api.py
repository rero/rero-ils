# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""API for manipulating documents."""


from functools import partial

from invenio_circulation.search.api import search_by_pid
from invenio_search.api import RecordsSearch

from .models import DocumentIdentifier
from ..api import IlsRecord
from ..fetchers import id_fetcher
from ..minters import id_minter
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

    @property
    def harvested(self):
        """Is this record harvested from an external service."""
        return bool(self.get('identifiers', {}).get('harvestedID'))

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
