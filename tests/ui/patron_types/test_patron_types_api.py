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

"""CircPolicy Record tests."""

from __future__ import absolute_import, print_function

from rero_ils.modules.patron_types.api import PatronType, patron_type_id_fetcher
from rero_ils.modules.utils import extracted_data_from_ref


def test_patron_type_create(db, org_martigny, patron_type_children_martigny_data):
    """Test pttyanisation creation."""
    ptty = PatronType.create(patron_type_children_martigny_data, delete_pid=True)
    assert ptty == patron_type_children_martigny_data
    assert ptty.get("pid") == "1"

    ptty = PatronType.get_record_by_pid("1")
    assert ptty == patron_type_children_martigny_data

    fetched_pid = patron_type_id_fetcher(ptty.id, ptty)
    assert fetched_pid.pid_value == "1"
    assert fetched_pid.pid_type == "ptty"


def test_patron_type_exist_name_and_organisation_pid(patron_type_children_martigny):
    """Test patron type name uniquness."""
    org_pid = extracted_data_from_ref(patron_type_children_martigny.get("organisation"))
    assert PatronType.exist_name_and_organisation_pid(
        patron_type_children_martigny.get("name"), org_pid
    )
    assert not PatronType.exist_name_and_organisation_pid("not exists yet", org_pid)


def test_patron_type_can_delete(patron_type_children_martigny):
    """Test can delete a patron type."""
    can, reasons = patron_type_children_martigny.can_delete
    assert can
    assert reasons == {}
