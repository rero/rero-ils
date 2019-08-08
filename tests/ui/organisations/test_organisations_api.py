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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Organisation Record tests."""

from __future__ import absolute_import, print_function

from rero_ils.modules.organisations.api import Organisation
from rero_ils.modules.organisations.api import \
    organisation_id_fetcher as fetcher


def test_organisation_libararies(org_martigny, lib_martigny):
    """Test libraries retrival."""
    assert list(org_martigny.get_libraries()) == [lib_martigny]


def test_organisation_create(app, db, org_martigny_data):
    """Test organisation creation."""
    org = Organisation.create(org_martigny_data, delete_pid=True)
    assert org == org_martigny_data
    assert org.get('pid') == '1'

    assert org.get_links_to_me() == {}
    assert org.can_delete

    org = Organisation.get_record_by_pid('1')
    assert org == org_martigny_data

    fetched_pid = fetcher(org.id, org)
    assert fetched_pid.pid_value == '1'
    assert fetched_pid.pid_type == 'org'
