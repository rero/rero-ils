# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
# Copyright (C) 2020 UCLouvain
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

"""API for manipulating Circulation policies."""
from __future__ import absolute_import, print_function

from functools import partial

from elasticsearch_dsl import Q

from .models import CircPolicyIdentifier, CircPolicyMetadata
from ..api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from ..fetchers import id_fetcher
from ..libraries.api import Library
from ..minters import id_minter
from ..providers import Provider
from ..utils import get_patron_from_arguments

# cipo provider
CircPolicyProvider = type(
    'CircPolicyProvider',
    (Provider,),
    dict(identifier=CircPolicyIdentifier, pid_type='cipo')
)
# cipo minter
circ_policy_id_minter = partial(id_minter, provider=CircPolicyProvider)
# cipo fetcher
circ_policy_id_fetcher = partial(id_fetcher, provider=CircPolicyProvider)


class CircPoliciesSearch(IlsRecordsSearch):
    """RecordsSearch for Circulation policies."""

    class Meta:
        """Search only on Circulation policies index."""

        index = 'circ_policies'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class CircPolicy(IlsRecord):
    """Circulation policies class."""

    minter = circ_policy_id_minter
    fetcher = circ_policy_id_fetcher
    provider = CircPolicyProvider
    model_cls = CircPolicyMetadata
    pids_exist_check = {
        'required': {
            'org': 'organisation',
        },
        'not_required': {
            # TODO: this is in list of settings
            # 'lib': 'library', # list
            # 'ptty': 'patron_type', # settings list
            # 'itty': 'item_type' # setings list
        }
    }

    def extended_validation(self, **kwargs):
        """Validate record against schema.

        and extended validation to check that patron types and item types are
        part of the correct organisation.
        """
        from ..item_types.api import ItemType
        from ..patron_types.api import PatronType

        for library in self.replace_refs().get('libraries', []):
            if not Library.get_record_by_pid(library.get('pid')):
                return 'CircPolicy: no library:  {pid}'.format(
                    pid=library.get('pid')
                )
        org = self.get('organisation')
        for setting in self.replace_refs().get('settings', []):
            patron_type = PatronType.get_record_by_pid(setting.get(
                'patron_type', {}).get('pid')
            )
            item_type = ItemType.get_record_by_pid(setting.get(
                'item_type', {}).get('pid')
            )
            if patron_type.get('organisation') != org or item_type.get(
                'organisation'
            ) != org:
                return 'CircPolicy: PatronType ItemType Org diff'
        return True

    @classmethod
    def exist_name_and_organisation_pid(cls, name, organisation_pid):
        """Check if the policy name is unique on organisation."""
        result = CircPoliciesSearch()\
            .filter('term', circ_policy_name=name)\
            .filter('term', organisation__pid=organisation_pid).source().scan()
        try:
            return next(result)
        except StopIteration:
            return None

    @classmethod
    def get_circ_policy_by_LPI(
            cls, organisation_pid, library_pid, patron_type_pid,
            item_type_pid):
        """Check if there is a policy for library/location/item types."""
        result = CircPoliciesSearch().filter(
            'term',
            policy_library_level=True
        ).filter(
            'term',
            organisation__pid=organisation_pid
        ).filter(
            'term',
            libraries__pid=library_pid
        ).filter(
            'nested',
            path='settings',
            query=Q(
                'bool',
                must=[
                    Q(
                        'match',
                        settings__patron_type__pid=patron_type_pid
                    ),
                    Q(
                        'match',
                        settings__item_type__pid=item_type_pid
                    )
                ]
            )
        ).source('pid').scan()
        try:
            return CircPolicy.get_record_by_pid(next(result).pid)
        except StopIteration:
            return None

    @classmethod
    def get_circ_policy_by_OPI(
            cls, organisation_pid, patron_type_pid, item_type_pid):
        """Check if there is a circ policy for location/item types."""
        result = CircPoliciesSearch().filter(
            'term',
            policy_library_level=False
        ).filter(
            'term',
            organisation__pid=organisation_pid
        ).filter(
            'nested',
            path='settings',
            query=Q(
                'bool',
                must=[
                    Q(
                        'match',
                        settings__patron_type__pid=patron_type_pid
                    ),
                    Q(
                        'match',
                        settings__item_type__pid=item_type_pid
                    )
                ]
            )
        ).source('pid').scan()
        try:
            return CircPolicy.get_record_by_pid(next(result).pid)
        except StopIteration:
            return None

    @classmethod
    def get_default_circ_policy(cls, organisation_pid):
        """Return the default circ policy."""
        result = CircPoliciesSearch().filter(
            'term',
            organisation__pid=organisation_pid
        ).filter(
            'term',
            is_default=True
        ).source('pid').scan()
        try:
            return CircPolicy.get_record_by_pid(next(result).pid)
        except StopIteration:
            return None

    @classmethod
    def provide_circ_policy(cls, library_pid, patron_type_pid, item_type_pid):
        """Return a circ policy for library/patron/item."""
        organisation_pid = Library.get_record_by_pid(
            library_pid).get_organisation().get('pid')
        LPI_policy = CircPolicy.get_circ_policy_by_LPI(
            organisation_pid,
            library_pid,
            patron_type_pid,
            item_type_pid
        )
        if LPI_policy:
            return LPI_policy
        PI_policy = CircPolicy.get_circ_policy_by_OPI(
            organisation_pid,
            patron_type_pid,
            item_type_pid
        )
        if PI_policy:
            return PI_policy
        return CircPolicy.get_default_circ_policy(organisation_pid)

    def reasons_to_keep(self):
        """Reasons aside from record_links to keep a circ policy."""
        others = {}
        is_default = self.get('is_default')
        if is_default:
            others['is_default'] = is_default
        return others

    def get_links_to_me(self):
        """Get number of links to policy."""
        links = {}
        return links

    def reasons_not_to_delete(self):
        """Get reasons not to delete policy."""
        cannot_delete = {}
        others = self.reasons_to_keep()
        links = self.get_links_to_me()
        if others:
            cannot_delete['others'] = others
        if links:
            cannot_delete['links'] = links
        return cannot_delete

    @classmethod
    def allow_request(cls, item, **kwargs):
        """Check if the cipo corresponding to item/patron allow request.

        :param item : the item to check
        :param kwargs : To be relevant, additional arguments should contains
                        'patron' argument.
        :return a tuple with True|False and reasons to disallow if False.
        """
        patron = get_patron_from_arguments(**kwargs)
        if not patron:
            # none patron get be load from kwargs argument. This check can't
            # be relevant --> return True by default
            return True, []
        if 'patron' not in patron.get('roles', []):
            # without 'patron' role, we can't find any patron_type and so we
            # can't find any corresponding cipo --> return False
            return False, ["Patron doesn't have the correct role"]
        library_pid = kwargs['library'].pid if kwargs.get('library') \
            else item.library_pid
        cipo = cls.provide_circ_policy(
            library_pid,
            patron.patron_type_pid,
            item.item_type_pid
        )
        if not cipo.get('allow_requests', False):
            return False, ["Circulation policy disallows the operation."]
        return True, []

    @classmethod
    def allow_checkout(cls, item, **kwargs):
        """Check if the cipo corresponding to item/patron allow request.

        :param item : the item to check
        :param kwargs : To be relevant, additional arguments should contains
                        'patron' argument.
        :return a tuple with True|False and reasons to disallow if False.
        """
        patron = get_patron_from_arguments(**kwargs)
        if not patron:
            # none patron get be load from kwargs argument. This check can't
            # be relevant --> return True by default
            return True, []
        if 'patron' not in patron.get('roles', []):
            # without 'patron' role, we can't find any patron_type and so we
            # can't find any corresponding cipo --> return False
            return False, ["Patron doesn't have the correct role"]
        library_pid = kwargs['library'].pid if kwargs.get('library') \
            else item.library_pid
        cipo = cls.provide_circ_policy(
            library_pid,
            patron.patron_type_pid,
            item.item_type_pid
        )
        if not cipo.get('allow_checkout', False):
            return False, ["Circulation policy disallows the operation."]
        return True, []


class CircPoliciesIndexer(IlsRecordsIndexer):
    """Indexing documents in Elasticsearch."""

    record_cls = CircPolicy

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='cipo')
