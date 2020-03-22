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

"""API for manipulating Circulation policies."""

from __future__ import absolute_import, print_function

from functools import partial

from elasticsearch_dsl import Q

from .models import CircPolicyIdentifier
from ..api import IlsRecord, IlsRecordIndexer, IlsRecordsSearch
from ..fetchers import id_fetcher
from ..libraries.api import Library
from ..minters import id_minter
from ..providers import Provider

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


class CircPolicy(IlsRecord):
    """Circulation policies class."""

    minter = circ_policy_id_minter
    fetcher = circ_policy_id_fetcher
    provider = CircPolicyProvider

    def extended_validation(self, **kwargs):
        """Validate record against schema.

        and extended validation to check that patron types and item types are
        part of the correct organisation.
        """
        from ..patron_types.api import PatronType
        from ..item_types.api import ItemType

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
                return False
        return True

    @classmethod
    def exist_name_and_organisation_pid(cls, name, organisation_pid):
        """Check if the policy name is unique on organisation."""
        result = CircPoliciesSearch().filter(
            'term',
            circ_policy_name=name
        ).filter(
            'term',
            organisation__pid=organisation_pid
        ).source().scan()
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
        ).source().scan()
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
        ).source().scan()
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
        ).source().scan()
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


class CircPoliciesIndexer(IlsRecordIndexer):
    """Indexing circulation policy in Elasticsearch."""

    record_cls = CircPolicy
