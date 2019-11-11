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

from invenio_search.api import RecordsSearch

from ..api import ElasticsearchRecord
from ..documents.api import Document, DocumentsSearch
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..models import ElasticsearchIdentifier
from ..providers import ElasticsearchProvider

# provider
MefPersonProvider = type(
    'MefPersonProvider',
    (ElasticsearchProvider,),
    dict(identifier=ElasticsearchIdentifier, pid_type='pers')
)
# minter
mef_person_id_minter = partial(id_minter, provider=MefPersonProvider)
# fetcher
mef_person_id_fetcher = partial(id_fetcher, provider=MefPersonProvider)


class MefPersonsSearch(RecordsSearch):
    """Mef person search."""

    class Meta():
        """Meta class."""

        index = 'persons'


class MefPerson(ElasticsearchRecord):
    """MefPerson class."""

    minter = mef_person_id_minter
    fetcher = mef_person_id_fetcher
    provider = MefPersonProvider
    searcher = MefPersonsSearch

    def get_number_of_linked_documents(self, org_pid=None):
        """Get number of linked documents for person."""
        return len(self.get_linked_documents_pid(org_pid))

    def get_linked_documents(self, org_pid=None):
        """Get linked documents."""
        for document_pid in self.get_linked_documents_pid(org_pid):
            document = Document.get_record_by_pid(document_pid)
            yield document

    def get_linked_documents_pid(self, org_pid=None):
        """Get linked documents by pid."""
        search = DocumentsSearch()
        search = search.filter(
                'term',
                authors__pid=self.pid
            )
        if org_pid:
            search = search.filter(
                'term', holdings__organisation__organisation_pid=org_pid
            )

        return [result.pid for result in search.scan()]
