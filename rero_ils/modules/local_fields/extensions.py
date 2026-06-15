# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""`LocalField` record extensions."""

from invenio_records.extensions import RecordExtension


class DeleteRelatedLocalFieldExtension(RecordExtension):
    """Extension managing LocalFields deletion when parent resource is deleted.

    `LocalFields` should not be a reason to block suppression of related
    resource. But if the parent resource is deleted, then the related
    `LocalFields` must be deleted too to avoid LocalField orphan.
    """

    def pre_delete(self, record, force=False):
        """Called before a record is deleted.

        :param record: the parent related record.
        :param force: is the suppression must be forced.
        """
        from .api import LocalField

        for local_field in LocalField.get_local_fields(record):
            local_field.delete(force=force, delindex=True)
