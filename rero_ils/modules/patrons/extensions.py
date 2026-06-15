# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Patron record extensions."""

from invenio_records.extensions import RecordExtension

from rero_ils.modules.users.api import User


class UserDataExtension(RecordExtension):
    """Add related user data extension."""

    def pre_dump(self, record, data, dumper=None):
        """Add user data.

        :param record: the record metadata.
        :param data: The dumped data dictionary.
        :param dumper: Dumper to use when dumping the record.
        :return the future dumped data.
        """
        user = User.get_record(record.get("user_id"))
        user_info = user.dumps_metadata()
        return data.update(user_info)
