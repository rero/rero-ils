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

"""Notification record mapping tests."""

from copy import deepcopy

from rero_ils.modules.notifications.api import Notification, NotificationsSearch
from tests.utils import get_mapping


def test_notification_es_mapping(dummy_notification, loan_validated_martigny):
    """Test notification elasticsearch mapping."""

    search = NotificationsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping

    notif = deepcopy(dummy_notification)
    validated_pid = loan_validated_martigny.get("pid")
    loan_ref = f"https://bib.rero.ch/api/loans/{validated_pid}"
    notif["context"]["loan"]["$ref"] = loan_ref
    Notification.create(notif, dbcommit=True, delete_pid=True, reindex=True)
    assert mapping == get_mapping(search.Meta.index)
