# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

"""API for manipulating internal circulation notifications."""

from __future__ import absolute_import, print_function

import hashlib
from abc import ABC

from .circulation import CirculationNotification
from ..models import NotificationChannel


class InternalCirculationNotification(CirculationNotification, ABC):
    """Internal circulation notifications class.

    An internal notification is a message send to a library to notify that a
    circulation operation has been done by a patron. Internal notification
    should never be cancelled (except if the requested item doesn't exist
    anymore) and are always send by email to the item owning library.

    Internal notification works synchronously. This means it will be send just
    after the creation. This also means that it should never be aggregated.
    """

    def can_be_cancelled(self):
        """Check if a notification can be cancelled.

        We need to call the loan to check all notification candidates and
        check if the corresponding notification type is into candidates.

        :return a tuple with two values: a boolean to know if the notification
                can be cancelled; the reason why the notification can be
                cancelled (only present if tuple first value is True).
        """
        # Check if parent class would cancel the notification. If yes other
        # check could be skipped.
        can, reason = super().can_be_cancelled()
        if can:
            return can, reason
        # Check loan notification candidate (by unpacking tuple's notification
        # candidate)
        candidates_types = [
            n[1] for n in
            self.loan.get_notification_candidates(trigger=None)
        ]
        if self.type not in candidates_types:
            msg = "Notification type isn't into notification candidate"
            return True, msg
        # we don't find any reasons to cancel this notification
        return False, None

    @property
    def aggregation_key(self):
        """Get the aggregation key for this notification."""
        # Internal notifications must be sent to a library. No need to
        # take care of the requested patron for these notifications.
        parts = [
            self.get_template_path(),
            self.get_communication_channel(),
            self.library.pid,
        ]
        return hashlib.md5(str(parts).encode()).hexdigest()

    def get_communication_channel(self):
        """Get the communication channel to dispatch the notification."""
        return NotificationChannel.EMAIL

    def get_language_to_use(self):
        """Get the language to use when dispatching the notification."""
        return self.library.get('communication_language')

    def get_recipients_to(self):
        """Get notification recipient email addresses."""
        # Internal notification will be sent to the library, not to the
        # patron related to the loan.
        if recipient := self.library.get_email(self.type):
            return [recipient]
