# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""CircPolicy Record tests."""

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
    assert PatronType.exist_name_and_organisation_pid(patron_type_children_martigny.get("name"), org_pid)
    assert not PatronType.exist_name_and_organisation_pid("not exists yet", org_pid)


def test_patron_type_can_delete(patron_type_children_martigny):
    """Test can delete a patron type."""
    can, reasons = patron_type_children_martigny.can_delete
    assert can
    assert reasons == {}
