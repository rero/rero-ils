# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Extensions for `Location` resource."""

from invenio_records.extensions import RecordExtension

from .tasks import remove_location_from_restriction


class IsPickupToExtension(RecordExtension):
    """Manage `restrict_pickup_to` fields extension."""

    def pre_commit(self, record):
        """Called before a record is committed.

        :param record: the record metadata.
        """
        # Remove the possible `pickup_name` if the location isn't (yet)
        # defined as a pickup location.
        if not record.get("is_pickup", False):
            record.pop("pickup_name", None)

    def post_commit(self, record):
        """Called after a record is committed.

        If the `Location` record isn't define as a pickup location, we need to
        ensure than no other locations use it into `restrict_pickup_to` field.
        To not block user, we do this check/update into an asynchronous task.

        :param record: the record metadata.
        """
        remove_location_from_restriction.apply_async((record,), countdown=0)
