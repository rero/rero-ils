# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

"""API for manipulating item types."""

from __future__ import absolute_import, print_function

from functools import partial

from elasticsearch_dsl import Q
from flask_babel import gettext as _

from .models import ItemTypeIdentifier, ItemTypeMetadata
from ..api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from ..circ_policies.api import CircPoliciesSearch
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..providers import Provider
from ..utils import extracted_data_from_ref, sorted_pids

# provider
ItemTypeProvider = type(
    'ItemTypeProvider',
    (Provider,),
    dict(identifier=ItemTypeIdentifier, pid_type='itty')
)
# minter
item_type_id_minter = partial(id_minter, provider=ItemTypeProvider)
# fetcher
item_type_id_fetcher = partial(id_fetcher, provider=ItemTypeProvider)


class ItemTypesSearch(IlsRecordsSearch):
    """ItemTypeSearch."""

    class Meta:
        """Search only on item_types index."""

        index = 'item_types'
        doc_types = None
        fields = ('*',)
        facets = {}

        default_filter = None


class ItemType(IlsRecord):
    """ItemType class."""

    minter = item_type_id_minter
    fetcher = item_type_id_fetcher
    provider = ItemTypeProvider
    model_cls = ItemTypeMetadata

    def extended_validation(self, **kwargs):
        """Validate record against schema.

        and extended validation to allow only one item type of type online
        per organisation.
        """
        online_type_pid = self.get_organisation().online_circulation_category()
        if self.get('type') == 'online' and online_type_pid and \
           self.pid != online_type_pid:
            return _('Another online item type exists in this organisation')
        return True

    def get_organisation(self):
        """Get organisation."""
        from ..organisations.api import Organisation
        org_pid = extracted_data_from_ref(self.get('organisation'))
        return Organisation.get_record_by_pid(org_pid)

    @classmethod
    def get_pid_by_name(cls, name):
        """Get pid by name."""
        pid = None
        try:
            pids = [
                n.pid
                for n in ItemTypesSearch()
                .filter('term', item_type_name=name)
                .source(includes=['pid'])
                .scan()
            ]
            if len(pids) > 0:
                pid = pids[0]
        except Exception:
            pass
            # needs app_context to work, but is called before
        return pid

    @classmethod
    def exist_name_and_organisation_pid(cls, name, organisation_pid):
        """Check if the name is unique in organisation.

        :param name: the circulation category name to check.
        :param organisation_pid: the organisation pid to check.
        :return: A ES hit if a circulation category already use thi name in
                 the organisation; otherwise, return None.
        """
        item_type = ItemTypesSearch() \
            .filter('term', item_type_name=name) \
            .filter('term', organisation__pid=organisation_pid)\
            .source().scan()
        try:
            return next(item_type)
        except StopIteration:
            return None

    def get_links_to_me(self, get_pids=False):
        """Record links.

        :param get_pids: if True list of linked pids
                         if False count of linked records
        """
        from ..items.api import ItemsSearch
        links = {}
        items_query = ItemsSearch().filter('bool', should=[
            Q('term', item_type__pid=self.pid),
            Q('term', temporary_item_type__pid=self.pid)
        ])
        cipo_query = CircPoliciesSearch() \
            .filter(
                'nested',
                path='settings',
                query=Q(
                    'bool', must=[
                        Q('match', settings__item_type__pid=self.pid)
                    ]
                )
            )
        if get_pids:
            items = sorted_pids(items_query)
            circ_policies = sorted_pids(cipo_query)
        else:
            items = items_query.count()
            circ_policies = cipo_query.count()
        if items:
            links['items'] = items
        if circ_policies:
            links['circ_policies'] = circ_policies
        return links

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        cannot_delete = {}
        links = self.get_links_to_me()
        if links:
            cannot_delete['links'] = links
        return cannot_delete

    def get_label(self, language=None):
        """Get the best name possible related to the current language.

        :param language: the language ISO code expected label.
        :return: the best possible label. If none label found for the language,
                 return the item_type name.
        """
        if language:
            labels = self.get('displayed_status', []) \
                if self.get('negative_availability', False) \
                else self.get('circulation_information', [])
            label = [
                entry['label'] for entry in labels
                if entry['language'] == language
            ]
            if label and label[0]:
                return label[0]
        return self.get('name')


class ItemTypesIndexer(IlsRecordsIndexer):
    """Indexing documents in Elasticsearch."""

    record_cls = ItemType

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='itty')
