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

"""Utils methods for ILL requests."""

from rero_ils.modules.locations.api import Location
from rero_ils.modules.patrons.api import current_patrons


def get_pickup_location_options():
    """Get all ill pickup location for all patron accounts."""
    for ptrn_pid in [ptrn.pid for ptrn in current_patrons]:
        for pid in Location.get_pickup_location_pids(ptrn_pid,
                                                     is_ill_pickup=True):
            location = Location.get_record_by_pid(pid)
            location_name = location.get(
                'ill_pickup_name', location.get('name'))
            yield (location.pid, location_name)


def get_production_activity(doc, types=None):
    """Get document production activity.

    :param: doc: document
    :param: types: available types of production activity
    :return: generator production activity object
    """
    assert types
    for activity in doc.get('provisionActivity', []):
        if activity['type'] in types:
            yield activity


def get_production_activity_statement(production_activity, types=None):
    """Get production activity statement.

    :param: production_activity: document production activity
    :param: types: available types of statement
    :return: generator statement object
    """
    assert types
    for statement in production_activity.get('statement', []):
        if statement['type'] in types:
            yield statement


def get_document_identifiers(doc, types=None):
    """Get document identifiers.

    :param: doc: document
    :param: types: available types of identifiers
    :returns: generator of ``rero_ils.commons.Identifier`` object
    """
    assert types  # ensure a least one type is asked
    for identifier in doc.get('identifiedBy', []):
        if identifier['type'] in types:
            yield identifier
