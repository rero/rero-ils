# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Circulation policies tests."""

from copy import deepcopy

import pytest
from jsonschema.exceptions import ValidationError

from rero_ils.modules.circ_policies.api import (
    DUE_SOON_REMINDER_TYPE,
    OVERDUE_REMINDER_TYPE,
    CircPolicy,
    circ_policy_id_fetcher,
)


def test_no_default_policy(app):
    """Test when no default circulation policy configured."""
    cipo = CircPolicy.get_default_circ_policy("org1")
    assert not cipo


def test_circ_policy_create(
    circ_policy_martigny_data_tmp,
    circ_policy_short_martigny_data,
    org_martigny,
    lib_martigny,
    lib_saxon,
    patron_type_children_martigny,
    item_type_standard_martigny,
    patron_type_adults_martigny,
    item_type_specific_martigny,
    item_type_regular_sion,
    patron_type_youngsters_sion,
):
    """Test circulation policy creation."""
    cipo = CircPolicy.create(circ_policy_martigny_data_tmp, delete_pid=True)
    assert cipo == circ_policy_martigny_data_tmp
    assert cipo.get("pid") == "1"

    cipo = CircPolicy.get_record_by_pid("1")
    assert cipo == circ_policy_martigny_data_tmp

    fetched_pid = circ_policy_id_fetcher(cipo.id, cipo)
    assert fetched_pid.pid_value == "1"
    assert fetched_pid.pid_type == "cipo"

    circ_policy_data = deepcopy(circ_policy_short_martigny_data)
    del circ_policy_data["$schema"]
    cipo = CircPolicy.create(circ_policy_data, delete_pid=True)
    assert cipo.get("$schema")
    assert cipo.get("pid") == "2"

    cipo_data = {
        "$schema": "https://bib.rero.ch/schemas/circ_policies/circ_policy-v0.0.1.json",
        "pid": "cipo_test",
        "name": "test",
        "organisation": {"$ref": "https://bib.rero.ch/api/organisations/org1"},
        "is_default": False,
        "allow_requests": True,
        "policy_library_level": False,
        "settings": [
            {
                "patron_type": {"$ref": "https://bib.rero.ch/api/patron_types/ptty3"},
                "item_type": {"$ref": "https://bib.rero.ch/api/item_types/itty1"},
            },
            {
                "patron_type": {"$ref": "https://bib.rero.ch/api/patron_types/ptty2"},
                "item_type": {"$ref": "https://bib.rero.ch/api/item_types/itty4"},
            },
        ],
    }
    with pytest.raises(ValidationError):
        cipo = CircPolicy.create(cipo_data, delete_pid=False)

    # TEST #2 : create a second defaut policy
    #   The first created policy (pid=1) is the default policy.
    #   Creation of a second default policy should raise a ValidationError
    default_cipo = CircPolicy.get_record_by_pid("1")
    assert default_cipo.get("is_default")
    with pytest.raises(ValidationError) as excinfo:
        CircPolicy.create(circ_policy_martigny_data_tmp, delete_pid=True)
    assert "CircPolicy: already a default policy for this org" in str(excinfo.value)


def test_circ_policy_exist_name_and_organisation_pid(circ_policy_short_martigny):
    """Test policy name existence."""
    cipo = circ_policy_short_martigny.replace_refs()
    assert CircPolicy.exist_name_and_organisation_pid(cipo.get("name"), cipo.get("organisation", {}).get("pid"))
    assert not CircPolicy.exist_name_and_organisation_pid("not exists yet", cipo.get("organisation", {}).get("pid"))


def test_circ_policy_can_not_delete(circ_policy_short_martigny):
    """Test cannot delete a policy."""
    org_pid = circ_policy_short_martigny.organisation_pid
    defaut_cipo = CircPolicy.get_default_circ_policy(org_pid)
    can, reasons = defaut_cipo.can_delete
    assert not can
    assert reasons["others"]["is_default"]

    can, reasons = circ_policy_short_martigny.can_delete
    assert can
    assert reasons == {}


def test_circ_policy_can_delete(app, circ_policy_martigny_data_tmp):
    """Test can delete a policy."""
    circ_policy_martigny_data_tmp["is_default"] = False
    cipo = CircPolicy.create(circ_policy_martigny_data_tmp, delete_pid=True)

    can, reasons = cipo.can_delete
    assert can
    assert reasons == {}


def test_circ_policy_extended_validation(
    app,
    circ_policy_short_martigny,
    circ_policy_short_martigny_data,
    circ_policy_default_sion_data,
):
    """Test extended validation for circ policy"""
    cipo_data = deepcopy(circ_policy_short_martigny_data)
    cipo_data["allow_requests"] = False
    cipo_data["pickup_hold_duration"] = 10
    del cipo_data["pid"]

    cipo = CircPolicy.create(cipo_data)
    assert cipo
    assert "pickup_hold_duration" not in cipo

    cipo.delete()

    # Check that I cannot save a CiPo without a renewal duration if
    # renewals are enabled.
    cipo_sion_data = deepcopy(circ_policy_default_sion_data)
    assert cipo_sion_data["number_renewals"] > 0

    cipo_sion_data.pop("renewal_duration")

    with pytest.raises(ValidationError) as err:
        CircPolicy.create(cipo_sion_data, delete_pid=True)
    assert "renewal duration is required" in str(err.value)


def test_circ_policy_get_reminders(circ_policy_short_martigny):
    """Check that the reminders of a circulation policy are correctly ordered when returned."""
    original_reminders = deepcopy(circ_policy_short_martigny["reminders"])
    circ_policy_short_martigny["reminders"] = [
        {
            "communication_channel": "mail",
            "days_delay": 2,
            "template": "email/due_soon",
            "type": "due_soon",
        },
        {"communication_channel": "mail", "days_delay": 49, "template": "email/overdue", "type": "overdue"},
        {"communication_channel": "mail", "days_delay": 25, "template": "email/overdue", "type": "overdue"},
        {
            "communication_channel": "patron_setting",
            "days_delay": 1,
            "template": "email/overdue",
            "type": "overdue",
        },
    ]

    due_soon_reminders = circ_policy_short_martigny.get_reminders(DUE_SOON_REMINDER_TYPE)
    overdue_reminders = circ_policy_short_martigny.get_reminders(OVERDUE_REMINDER_TYPE)
    overdue_reminders_limit = circ_policy_short_martigny.get_reminders(OVERDUE_REMINDER_TYPE, limit=30)

    assert len(due_soon_reminders) == 1
    assert due_soon_reminders[0]["days_delay"] == 2
    assert due_soon_reminders[0]["communication_channel"] == "mail"

    assert len(overdue_reminders) == 3
    assert overdue_reminders[0]["days_delay"] == 1
    assert overdue_reminders[0]["communication_channel"] == "patron_setting"
    assert overdue_reminders[-1]["days_delay"] == 49
    assert overdue_reminders[-1]["communication_channel"] == "mail"

    assert len(overdue_reminders_limit) == 2
    assert overdue_reminders_limit[-1]["days_delay"] == 25
    assert overdue_reminders_limit[-1]["communication_channel"] == "mail"

    circ_policy_short_martigny["reminders"] = original_reminders
