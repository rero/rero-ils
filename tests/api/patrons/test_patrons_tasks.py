# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2024-2026 RERO
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

"""Tests for the inactive patron cleanup task."""

from copy import deepcopy
from datetime import datetime, timedelta

from invenio_db import db

from rero_ils.modules.patrons.api import Patron, PatronsSearch
from rero_ils.modules.patrons.tasks import (
    _delete_inactive_patrons_for_org,
    task_delete_inactive_patrons,
)
from rero_ils.modules.patrons.utils import create_user_from_data


def _set_patron_cleanup_config(org, config):
    """Set patron_cleanup config on an organisation."""
    org["patron_cleanup"] = config
    org.update(org, dbcommit=True, reindex=True)


def _clear_patron_cleanup_config(org):
    """Remove patron_cleanup config from an organisation."""
    org.pop("patron_cleanup", None)
    org.update(org, dbcommit=True, reindex=True)


def _make_patron_expired(patron, years_ago=5):
    """Set patron expiration_date to years_ago in the past."""
    past_date = datetime.now() - timedelta(days=365 * years_ago)
    patron["patron"]["expiration_date"] = past_date.strftime("%Y-%m-%d")
    patron.update(patron, dbcommit=True, reindex=True)
    PatronsSearch.flush_and_refresh()


def _restore_patron_expiration(patron):
    """Restore patron expiration_date to 1 year in the future."""
    future_date = datetime.now() + timedelta(days=365)
    patron["patron"]["expiration_date"] = future_date.strftime("%Y-%m-%d")
    patron.update(patron, dbcommit=True, reindex=True)
    PatronsSearch.flush_and_refresh()


def _make_user_inactive(user, years_ago=5):
    """Set user last login to years_ago in the past."""
    past = datetime.now() - timedelta(days=365 * years_ago)
    user.current_login_at = past
    user.last_login_at = past
    db.session.merge(user)
    db.session.commit()


def _make_user_recently_active(user):
    """Set user last login to now."""
    now = datetime.now()
    user.current_login_at = now
    user.last_login_at = now
    db.session.merge(user)
    db.session.commit()


def _clear_user_login(user):
    """Clear user login dates to simulate never-logged-in."""
    user.current_login_at = None
    user.last_login_at = None
    db.session.merge(user)
    db.session.commit()


def _create_throwaway_patron(app, data_tmp, suffix="1"):
    """Create a throwaway patron for deletion tests.

    :param suffix: unique suffix for email/username/barcode.
    :returns: tuple (patron, user_id)
    """
    data = deepcopy(data_tmp)
    data["email"] = f"throwaway_cleanup{suffix}@test.ch"
    data["username"] = f"throwaway_cleanup{suffix}"
    data["patron"]["barcode"] = [f"999999990{suffix}"]
    del data["pid"]
    data = create_user_from_data(data)
    patron = Patron.create(data=data, delete_pid=False, dbcommit=True, reindex=True)
    PatronsSearch.flush_and_refresh()
    return patron, data["user_id"]


def test_org_without_config_is_skipped(app, org_martigny, patron_martigny):
    """Test that organisations without patron_cleanup config are skipped."""
    _clear_patron_cleanup_config(org_martigny)
    _make_patron_expired(patron_martigny)
    _make_user_inactive(patron_martigny.user)

    task_delete_inactive_patrons(dry_run=True)

    assert Patron.get_record_by_pid(patron_martigny.pid) is not None

    _restore_patron_expiration(patron_martigny)
    _make_user_recently_active(patron_martigny.user)


def test_dry_run_does_not_delete(app, org_martigny, patron_martigny):
    """Test that dry_run mode logs candidates without deleting."""
    config = {"expiration_years": 3, "inactivity_years": 3}
    _set_patron_cleanup_config(org_martigny, config)
    _make_patron_expired(patron_martigny)
    _make_user_inactive(patron_martigny.user)

    deleted, skipped = _delete_inactive_patrons_for_org(org_martigny.pid, config, dry_run=True)

    assert Patron.get_record_by_pid(patron_martigny.pid) is not None

    _clear_patron_cleanup_config(org_martigny)
    _restore_patron_expiration(patron_martigny)
    _make_user_recently_active(patron_martigny.user)


def test_patron_with_recent_expiration_not_deleted(app, org_martigny, patron_martigny):
    """Test that a patron with recent expiration date is not deleted."""
    config = {"expiration_years": 3, "inactivity_years": 3}
    _set_patron_cleanup_config(org_martigny, config)
    # patron_martigny has expiration_date +1 year (set by patch_expiration_date)
    _make_user_inactive(patron_martigny.user)

    deleted, skipped = _delete_inactive_patrons_for_org(org_martigny.pid, config)

    assert Patron.get_record_by_pid(patron_martigny.pid) is not None
    assert deleted == 0

    _clear_patron_cleanup_config(org_martigny)
    _make_user_recently_active(patron_martigny.user)


def test_patron_with_recent_login_not_deleted(app, org_martigny, patron_martigny):
    """Test that a patron with recent login is not deleted."""
    config = {"expiration_years": 3, "inactivity_years": 3}
    _set_patron_cleanup_config(org_martigny, config)
    _make_patron_expired(patron_martigny)
    _make_user_recently_active(patron_martigny.user)

    deleted, skipped = _delete_inactive_patrons_for_org(org_martigny.pid, config)

    assert Patron.get_record_by_pid(patron_martigny.pid) is not None
    assert deleted == 0

    _clear_patron_cleanup_config(org_martigny)
    _restore_patron_expiration(patron_martigny)


def test_blocked_patron_not_deleted(app, org_martigny, patron_martigny):
    """Test that a blocked patron is not deleted."""
    config = {"expiration_years": 3, "inactivity_years": 3}
    _set_patron_cleanup_config(org_martigny, config)
    _make_patron_expired(patron_martigny)
    _make_user_inactive(patron_martigny.user)

    patron_martigny["patron"]["blocked"] = True
    patron_martigny["patron"]["blocked_note"] = "Test block"
    patron_martigny.update(patron_martigny, dbcommit=True, reindex=True)
    PatronsSearch.flush_and_refresh()

    deleted, skipped = _delete_inactive_patrons_for_org(org_martigny.pid, config)

    assert Patron.get_record_by_pid(patron_martigny.pid) is not None
    assert deleted == 0

    patron_martigny["patron"]["blocked"] = False
    del patron_martigny["patron"]["blocked_note"]
    patron_martigny.update(patron_martigny, dbcommit=True, reindex=True)
    PatronsSearch.flush_and_refresh()
    _clear_patron_cleanup_config(org_martigny)
    _restore_patron_expiration(patron_martigny)
    _make_user_recently_active(patron_martigny.user)


def test_excluded_patron_type_not_deleted(app, org_martigny, patron_martigny, patron_type_children_martigny):
    """Test that patron with excluded patron type is not deleted."""
    config = {
        "expiration_years": 3,
        "inactivity_years": 3,
        "excluded_patron_types": [patron_type_children_martigny.pid],
    }
    _set_patron_cleanup_config(org_martigny, config)
    _make_patron_expired(patron_martigny)
    _make_user_inactive(patron_martigny.user)

    deleted, skipped = _delete_inactive_patrons_for_org(org_martigny.pid, config)

    assert Patron.get_record_by_pid(patron_martigny.pid) is not None
    assert deleted == 0

    _clear_patron_cleanup_config(org_martigny)
    _restore_patron_expiration(patron_martigny)
    _make_user_recently_active(patron_martigny.user)


def test_professional_patron_not_deleted(app, org_martigny, librarian_martigny):
    """Test that a patron with professional roles is not deleted."""
    config = {"expiration_years": 3, "inactivity_years": 3}
    _set_patron_cleanup_config(org_martigny, config)

    deleted, skipped = _delete_inactive_patrons_for_org(org_martigny.pid, config)

    assert Patron.get_record_by_pid(librarian_martigny.pid) is not None

    _clear_patron_cleanup_config(org_martigny)


def test_patron_with_active_loans_not_deleted(app, org_martigny, patron_martigny, loan_validated_martigny):
    """Test that patron with active loans is not deleted."""
    config = {"expiration_years": 3, "inactivity_years": 3}
    _set_patron_cleanup_config(org_martigny, config)
    _make_patron_expired(patron_martigny)
    _make_user_inactive(patron_martigny.user)

    deleted, skipped = _delete_inactive_patrons_for_org(org_martigny.pid, config)

    assert Patron.get_record_by_pid(patron_martigny.pid) is not None
    assert deleted == 0

    _clear_patron_cleanup_config(org_martigny)
    _restore_patron_expiration(patron_martigny)
    _make_user_recently_active(patron_martigny.user)


def test_patron_with_ill_requests_not_deleted(app, org_martigny, patron_martigny, ill_request_martigny):
    """Test that patron with linked ILL requests is not deleted."""
    config = {"expiration_years": 3, "inactivity_years": 3}
    _set_patron_cleanup_config(org_martigny, config)
    _make_patron_expired(patron_martigny)
    _make_user_inactive(patron_martigny.user)

    deleted, skipped = _delete_inactive_patrons_for_org(org_martigny.pid, config)

    assert Patron.get_record_by_pid(patron_martigny.pid) is not None
    assert deleted == 0

    _clear_patron_cleanup_config(org_martigny)
    _restore_patron_expiration(patron_martigny)
    _make_user_recently_active(patron_martigny.user)


def test_patron_meeting_all_criteria_is_deleted(
    app, org_martigny, roles, lib_martigny, patron_type_children_martigny, patron_martigny_data_tmp
):
    """Test that a patron meeting all deletion criteria is actually deleted."""
    patron, user_id = _create_throwaway_patron(app, patron_martigny_data_tmp)
    pid = patron.pid
    config = {"expiration_years": 3, "inactivity_years": 3}
    _set_patron_cleanup_config(org_martigny, config)

    _make_patron_expired(patron)
    _make_user_inactive(patron.user)

    deleted, skipped = _delete_inactive_patrons_for_org(org_martigny.pid, config)

    assert deleted >= 1
    assert Patron.get_record_by_pid(pid) is None

    _clear_patron_cleanup_config(org_martigny)


def test_patron_with_never_logged_in_user_is_deleted(
    app, org_martigny, roles, lib_martigny, patron_type_children_martigny, patron_martigny_data_tmp
):
    """Test that patron with never-logged-in user is deleted (None login)."""
    patron, user_id = _create_throwaway_patron(app, patron_martigny_data_tmp, suffix="2")
    pid = patron.pid
    config = {"expiration_years": 3, "inactivity_years": 3}
    _set_patron_cleanup_config(org_martigny, config)

    _make_patron_expired(patron)
    _clear_user_login(patron.user)

    deleted, skipped = _delete_inactive_patrons_for_org(org_martigny.pid, config)

    assert deleted >= 1
    assert Patron.get_record_by_pid(pid) is None

    _clear_patron_cleanup_config(org_martigny)


def test_full_task_end_to_end(
    app, org_martigny, roles, lib_martigny, patron_type_children_martigny, patron_martigny_data_tmp
):
    """Test the full task_delete_inactive_patrons end-to-end."""
    patron, user_id = _create_throwaway_patron(app, patron_martigny_data_tmp, suffix="3")
    pid = patron.pid
    config = {"expiration_years": 3, "inactivity_years": 3}
    _set_patron_cleanup_config(org_martigny, config)

    _make_patron_expired(patron)
    _make_user_inactive(patron.user)

    task_delete_inactive_patrons()
    PatronsSearch.flush_and_refresh()

    assert Patron.get_record_by_pid(pid) is None

    _clear_patron_cleanup_config(org_martigny)
