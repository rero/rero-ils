# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

"""API for manipulating local entities."""

from functools import partial

from rero_ils.modules.api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from rero_ils.modules.documents.api import DocumentsSearch
from rero_ils.modules.utils import sorted_pids
from rero_ils.modules.fetchers import id_fetcher
from rero_ils.modules.minters import id_minter
from rero_ils.modules.providers import Provider

from .dumpers import replace_refs_dumper
from .extensions import AuthorizedAccessPointExtension
from .models import LocalEntityIdentifier, LocalEntityMetadata

# provider
LocalEntityProvider = type(
    'LocalEntityProvider',
    (Provider,),
    dict(identifier=LocalEntityIdentifier, pid_type='locent')
)
# minter
local_entity_id_minter = partial(id_minter, provider=LocalEntityProvider)
# fetcher
local_entity_id_fetcher = partial(id_fetcher, provider=LocalEntityProvider)


class LocalEntitiesSearch(IlsRecordsSearch):
    """Local entities search."""

    class Meta:
        """Meta class."""

        index = 'local_entities'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class LocalEntity(IlsRecord):
    """Local entity class."""

    minter = local_entity_id_minter
    fetcher = local_entity_id_fetcher
    provider = LocalEntityProvider
    model_cls = LocalEntityMetadata
    # disable legacy replace refs
    enable_jsonref = False

    _extensions = [
        AuthorizedAccessPointExtension()
    ]

    def resolve(self):
        """Resolve references data.

        Uses the dumper to do the job.
        Mainly used by the `resolve=1` URL parameter.

        :returns: a fresh copy of the resolved data.
        """
        return self.dumps(replace_refs_dumper)

    def get_links_to_me(self, get_pids=False):
        """Record links.

        :param get_pids: if True list of linked pids
                         if False count of linked records
        """
        document_query = DocumentsSearch() \
            .filter('term', local_entity__pid=self.pid)
        documents = sorted_pids(document_query) if get_pids \
            else document_query.count()
        links = {
            'documents': documents
        }
        return {k: v for k, v in links.items() if v}

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        cannot_delete = {}
        if links := self.get_links_to_me():
            cannot_delete['links'] = links
        return cannot_delete


class LocalEntitiesIndexer(IlsRecordsIndexer):
    """Local entity indexing class."""

    record_cls = LocalEntity

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='locent')
