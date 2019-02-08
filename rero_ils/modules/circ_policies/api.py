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

from invenio_search.api import RecordsSearch

from ..api import IlsRecord
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..providers import Provider
from .models import CircPolicyIdentifier

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
