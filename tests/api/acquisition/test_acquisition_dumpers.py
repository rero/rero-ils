# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test library dumpers."""

from rero_ils.modules.acquisition.acq_orders.dumpers import AcqOrderNotificationDumper


def test_acquisition_dumpers(
    acq_order_fiction_martigny,
    acq_order_line_fiction_martigny,
    acq_order_line2_fiction_martigny,
):
    """Test acquisition dumpers."""

    # Test AcqOrderNotificationDumper. This will also test the
    #  * AcqOrderLineNotificationDumper
    #  * LibraryAcquisitionNotificationDumper
    acor = acq_order_fiction_martigny
    dump_data = acor.dumps(dumper=AcqOrderNotificationDumper())
    assert len(dump_data["order_lines"]) == 2
    assert dump_data["library"]["shipping_informations"]
    assert dump_data["library"]["billing_informations"]
    assert dump_data["vendor"]
