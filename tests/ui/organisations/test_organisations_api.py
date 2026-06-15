# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Organisation Record tests."""

from rero_ils.modules.organisations.api import Organisation
from rero_ils.modules.organisations.api import organisation_id_fetcher as fetcher
from rero_ils.modules.providers import append_fixtures_new_identifiers


def test_organisation_libraries(org_martigny, lib_martigny):
    """Test libraries retrival."""
    assert list(org_martigny.get_libraries()) == [lib_martigny]


def test_organisation_vendors(org_martigny, vendor_martigny):
    """Test vendors retrival."""
    assert list(org_martigny.get_vendors()) == [vendor_martigny]


def test_organisation_organisation_pid(org_martigny):
    """Test organisation_pid property."""
    assert org_martigny.organisation_pid == "org1"


def test_organisation_create(app, db, org_martigny_data, org_sion_data):
    """Test organisation creation."""
    org_martigny_data["pid"] = "1"
    org = Organisation.create(org_martigny_data, dbcommit=True, reindex=True)
    assert org == org_martigny_data
    assert org.get("pid") == "1"

    can, reasons = org.can_delete
    assert can
    assert reasons == {}

    org = Organisation.get_record_by_pid("1")
    assert org == org_martigny_data

    fetched_pid = fetcher(org.id, org)
    assert fetched_pid.pid_value == "1"
    assert fetched_pid.pid_type == "org"

    org_sion_data["pid"] = "2"
    org = Organisation.create(org_sion_data, dbcommit=True, reindex=True)
    assert org.get("pid") == "2"

    identifier = Organisation.provider.identifier
    count, err = append_fixtures_new_identifiers(identifier, ["3", "4"])
    assert count == 2
    assert err == ""
    assert identifier.max() == 4
    assert identifier.next() == 5
