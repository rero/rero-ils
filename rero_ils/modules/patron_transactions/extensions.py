# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Patron transactions record extensions."""

from flask_babel import gettext as _
from invenio_records.extensions import RecordExtension

from rero_ils.modules.patron_transaction_events.api import PatronTransactionEvent
from rero_ils.modules.utils import get_ref_for_pid


class PatronTransactionExtension(RecordExtension):
    """Patron transactions extension."""

    @staticmethod
    def _base_data_patron_event(record, steps=None):
        """Create a initial data for Patron Transaction Event."""
        data = {
            "creation_date": record.get("creation_date"),
            "type": "fee",
            "subtype": "other",
            "amount": record.get("total_amount"),
            "parent": {"$ref": get_ref_for_pid("pttr", record.pid)},
            "note": _("Initial charge"),
        }
        if library := record.get("library"):
            data["library"] = {"$ref": library.get("$ref")}
        if steps:
            data["steps"] = steps
        return data

    @staticmethod
    def _data_operator_event(data, event=None):
        """Add event on Patron Transaction Event.

        If the library is defined at the event level,
        it overrides the library of the patron transaction.
        """
        if event:
            if operator := event.get("operator"):
                data["operator"] = {"$ref": operator.get("$ref")}
            if library := event.get("library"):
                data["library"] = {"$ref": library.get("$ref")}
        return data

    @staticmethod
    def _data_overdue(data, record):
        """Add overdue informations on Patron Transaction Event."""
        if record.get("type") == "overdue":
            data["subtype"] = "overdue"
            library_pid = record.loan.library_pid if record.loan_pid else record.notification_transaction_library_pid
            if library_pid:
                data["library"] = {"$ref": get_ref_for_pid("lib", library_pid)}
        return data

    def pre_create(self, record):
        """Called before a patron transaction event record is created."""
        # Extract steps and event if exists.
        steps = record.pop("steps", None)
        event = record.pop("event", None)
        # Update the model with the new data of the record.
        record.model.data = dict(record)
        # Creation of data for the event
        data = PatronTransactionExtension._base_data_patron_event(record, steps)
        data = PatronTransactionExtension._data_operator_event(data, event)
        data = PatronTransactionExtension._data_overdue(data, record)
        rec = PatronTransactionEvent.create(data, update_parent=False)
        # Add the event pid for indexing
        record.event_pids.append(rec.pid)
