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

"""Test library dumpers."""
from rero_ils.modules.acquisition.acq_orders.dumpers import \
    AcqOrderNotificationDumper


def test_acquisition_dumpers(
    acq_order_fiction_martigny,
    acq_order_line_fiction_martigny,
    acq_order_line2_fiction_martigny
):
    """Test acquisition dumpers."""

    # Test AcqOrderNotificationDumper. This will also test the
    #  * AcqOrderLineNotificationDumper
    #  * LibraryAcquisitionNotificationDumper
    acor = acq_order_fiction_martigny
    dump_data = acor.dumps(dumper=AcqOrderNotificationDumper())
    assert len(dump_data['order_lines']) == 2
    assert dump_data['library']['shipping_informations']
    assert dump_data['library']['billing_informations']
    assert dump_data['vendor']
