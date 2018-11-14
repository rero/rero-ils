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

"""API for manipulating patrons_types."""

from __future__ import absolute_import, print_function

from invenio_search.api import RecordsSearch

from ..api import IlsRecord
from .fetchers import patron_type_id_fetcher
from .minters import patron_type_id_minter
from .providers import PatronTypeProvider


class PatronTypeSearch(RecordsSearch):
    """PatronTypeSearch."""

    class Meta:
        """Search only on patrons index."""

        index = 'patrons_types'


class PatronType(IlsRecord):
    """PatronType class."""

    minter = patron_type_id_minter
    fetcher = patron_type_id_fetcher
    provider = PatronTypeProvider

    @property
    def can_delete(self):
        """Record can be deleted."""
        from ..patrons.api import PatronsSearch

        count = len(
            list(
                PatronsSearch()
                .filter('term', **{'patron_type_pid': self.pid})
                .source()
                .scan()
            )
        )
        return count == 0

    @classmethod
    def exist_name_and_organisation_pid(cls, name, organisation_pid):
        """Check if the name is unique on organisation."""
        patron_type = (
            PatronTypeSearch()
            .filter('term', **{'patron_type_name': name})
            .filter('term', **{'organisation_pid': organisation_pid})
            .source()
            .scan()
        )
        result = list(patron_type)
        if len(result) > 0:
            return result.pop(0)
        else:
            return None
