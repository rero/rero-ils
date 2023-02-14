# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
# Copyright (C) 2021 UCLouvain
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

"""Tests dumpers from RERO-ILS projects."""
from rero_ils.modules.acquisition.acq_orders.dumpers import \
    AcqOrderNotificationDumper
from rero_ils.modules.acquisition.dumpers import document_acquisition_dumper
from rero_ils.modules.documents.dumpers import document_title
from rero_ils.modules.libraries.dumpers import \
    LibraryAcquisitionNotificationDumper


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


def test_library_dumpers(lib_martigny, lib_saxon):
    """Test library dumpers."""

    dump_data = lib_martigny.dumps(
        dumper=LibraryAcquisitionNotificationDumper())
    assert dump_data['shipping_informations']
    assert dump_data['billing_informations']

    dump_data = lib_saxon.dumps(
        dumper=LibraryAcquisitionNotificationDumper())
    assert dump_data['shipping_informations']
    assert 'billing_informations' not in dump_data


def test_document_dumpers(document):
    """Test document dumpers."""
    dump_data = document.dumps(
        dumper=document_title
    )
    assert dump_data['pid']
    assert dump_data['title_text']

    dump_data = document.dumps(
        dumper=document_acquisition_dumper
    )
    assert dump_data['pid']
    assert dump_data['title_text']
    assert dump_data['identifiers']
