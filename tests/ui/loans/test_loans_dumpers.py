# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

"""Loans Record dumper tests."""

from rero_ils.modules.loans.dumpers import CirculationDumper


def test_loan_circulation_dumper(loan_pending_martigny):
    """Test loan circulation action dumper."""
    data = loan_pending_martigny.dumps(CirculationDumper())
    assert data['state']
    assert data['creation_date']
    assert 'name' in data['patron']
    assert 'barcode' in data['patron']
    assert 'name' in data['pickup_location']
    assert 'library_name' in data['pickup_location']
