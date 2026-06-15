# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Document record extension to add the MEF pid in the database."""

from invenio_db import db
from invenio_records.extensions import RecordExtension


class AddMEFPidExtension(RecordExtension):
    """Adds the MEF pid for contributions and subjects."""

    def __init__(self, *args):
        """Initialization.

        :param args: the list of fields where to find entity and add the
            local Entity.pid corresponding to $ref.
        :param args: tuple<str>.
        """
        self.field_names = list(args) or []

    def add_mef_pid(self, record):
        """Injects the MEF pid in the contribution.

        :params record: dict - a document record.
        """
        from rero_ils.modules.entities.remote_entities.api import RemoteEntity

        remote_entities = []

        # Search about all entities present in the document through fields
        # defined for this extension
        for field_name in self.field_names:
            fields = record.get(field_name, [])
            if not isinstance(fields, list):
                fields = [fields]
            remote_entities.extend([field["entity"] for field in fields if "entity" in field])

        # For each found entity, add its PID into the entity data.
        for entity_data in remote_entities:
            if ref := entity_data.get("$ref"):
                entity, _ = RemoteEntity.get_record_by_ref(ref)
                if entity:
                    # inject mef pid
                    entity_data["pid"] = entity["pid"]

    def post_create(self, record):
        """Called after a record is initialized.

        :param record: dict - the record to be modified.
        """
        self.add_mef_pid(record)
        if record.model:
            with db.session.begin_nested():
                record.model.data = record
                db.session.add(record.model)

    def post_commit(self, record):
        """Called before a record is committed.

        :param record: dict - the record to be modified.
        """
        self.add_mef_pid(record)
        if record.model:
            with db.session.begin_nested():
                record.model.data = record
                # Note: session merge is not required as it is done by the
                #       record.commit
