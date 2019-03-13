# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2018 RERO.
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

"""API for manipulating circ_policies."""

from __future__ import absolute_import, print_function

from functools import partial

from elasticsearch_dsl import Q
from invenio_search.api import RecordsSearch

from .models import CircPolicyIdentifier
from ..api import IlsRecord
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..providers import Provider

# provider
CircPolicyProvider = type(
    'CircPolicyProvider',
    (Provider,),
    dict(identifier=CircPolicyIdentifier, pid_type='cipo')
)
# minter
circ_policy_id_minter = partial(id_minter, provider=CircPolicyProvider)
# fetcher
circ_policy_id_fetcher = partial(id_fetcher, provider=CircPolicyProvider)


class CircPoliciesSearch(RecordsSearch):
    """RecordsSearch for borrowed documents."""

    class Meta:
        """Search only on patrons index."""

        index = 'circ_policies'


class CircPolicy(IlsRecord):
    """CircPolicy class."""

    minter = circ_policy_id_minter
    fetcher = circ_policy_id_fetcher
    provider = CircPolicyProvider

    @classmethod
    def exist_name_and_organisation_pid(cls, name, organisation_pid):
        """Check if the name is unique on organisation."""
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

    def get_circ_policy_by_LPI(
        library_pid,
        patron_type_pid,
        item_type_pid
    ):
        """Check if there is a circ poliy for library/location/item types."""
        result = CircPoliciesSearch().filter(
            'term',
            policy_library_level=True
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

    def get_circ_policy_by_OPI(
        patron_type_pid,
        item_type_pid
    ):
        """Check if there is a circ poliy for location/item types."""
        result = CircPoliciesSearch().filter(
            'term',
            policy_library_level=False
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

    def get_default_circ_policy():
        """Return the default circ policy."""
        result = CircPoliciesSearch().filter(
            'term',
            is_default=True
        ).source().scan()
        try:
            return CircPolicy.get_record_by_pid(next(result).pid)
        except StopIteration:
            return None

    def provide_circ_policy(
        library_pid,
        patron_type_pid,
        item_type_pid
    ):
        """Return a circ policy for library/patron/item."""
        LPI_policy = CircPolicy.get_circ_policy_by_LPI(
            library_pid,
            patron_type_pid,
            item_type_pid
        )
        if LPI_policy:
            return LPI_policy
        PI_policy = CircPolicy.get_circ_policy_by_OPI(
            patron_type_pid,
            item_type_pid
        )
        if PI_policy:
            return PI_policy
        return CircPolicy.get_default_circ_policy()

    def get_non_link_reasons_to_not_delete(self):
        """Get reasons other than links not to delete a record."""
        others = {}
        is_default = self.get('is_default')
        if is_default:
            others['is_default'] = is_default
        has_settings = self.get('settings')
        if has_settings:
            others['has_settings'] = has_settings
        return others

    def get_links_to_me(self):
        """Get number of links."""
        links = {}
        return links

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        cannot_delete = {}
        others = self.get_non_link_reasons_to_not_delete()
        links = self.get_links_to_me()
        if others:
            cannot_delete['others'] = others
        if links:
            cannot_delete['links'] = links
        return cannot_delete
