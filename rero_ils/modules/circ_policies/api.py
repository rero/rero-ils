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

from invenio_search.api import RecordsSearch

from ..api import IlsRecord
from ..errors import OrganisationDoesNotExist, PolicyNameAlreadyExists
from ..organisations.api import Organisation
from .fetchers import circ_policy_id_fetcher
from .minters import circ_policy_id_minter
from .providers import CircPolicyProvider


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
    def get_pid_by_name(cls, name, organisation_pid):
        """Get circulation policy by name."""
        search = CircPoliciesSearch()
        result = (
            search.filter('term', name=name).filter(
                'term', organisation_pid=organisation_pid
            )
            .source(includes=['pid'])
            .scan()
        )
        try:
            return next(result).pid
        except StopIteration:
            return None

    @classmethod
    def create(cls, data, id_=None, delete_pid=True, **kwargs):
        """Create a new circulation policy record."""
        name = data.get('name')
        organisation_pid = data.get('organisation_pid')
        if Organisation.get_record_by_pid(organisation_pid):
            if not cls.get_pid_by_name(name, organisation_pid):
                record = super(CircPolicy, cls).create(
                    data, id_=id_, delete_pid=delete_pid, **kwargs
                )
            else:
                raise PolicyNameAlreadyExists
        else:
            raise OrganisationDoesNotExist
        return record

    @property
    def can_delete(self):
        """Record can be deleted."""
        return True

    @classmethod
    def exist_name_and_organisation_pid(cls, name, organisation_pid):
        """Check if the name is unique on organisation."""
        circ_policy = CircPoliciesSearch().filter(
            'term',
            **{"name": name}
        ).filter(
            'term',
            **{"organisation_pid": organisation_pid}
        ).source().scan()
        result = list(circ_policy)
        if len(result) > 0:
            return result.pop(0)
        else:
            return None
