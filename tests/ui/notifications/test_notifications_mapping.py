# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Notification record mapping tests."""

from copy import deepcopy

from rero_ils.modules.notifications.api import Notification, NotificationsSearch
from tests.utils import get_mapping


def test_notification_search_mapping(dummy_notification, loan_validated_martigny):
    """Test notification search index mapping."""

    search = NotificationsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping

    notif = deepcopy(dummy_notification)
    validated_pid = loan_validated_martigny.get("pid")
    loan_ref = f"https://bib.rero.ch/api/loans/{validated_pid}"
    notif["context"]["loan"]["$ref"] = loan_ref
    Notification.create(notif, dbcommit=True, delete_pid=True, reindex=True)
    assert mapping == get_mapping(search.Meta.index)
