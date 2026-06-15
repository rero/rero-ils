# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Loans logs API."""

from datetime import UTC, datetime

from rero_ils.modules.operation_logs.api import OperationLog, OperationLogsSearch
from rero_ils.modules.operation_logs.logs.api import SpecificOperationLog

from ...patrons.api import Patron, current_librarian


class LoanOperationLogsSearch(OperationLogsSearch):
    """RecordsSearch for LoanOperationLogs."""

    def get_logs_by_trigger(self, triggers, date_range=None):
        """Get the operation logs base es search.

        :param triggers: list[str] - loan triggers value to filter
        :return: a search index dsl search query
        """
        query = self.filter("term", record__type="loan").filter("terms", loan__trigger=triggers)
        if date_range:
            query = query.filter("range", date=date_range)
        return query


class LoanOperationLog(OperationLog, SpecificOperationLog):
    """Operation log for loans."""

    @classmethod
    def create(cls, data, id_=None, index_refresh="false", **kwargs):
        """Create a new record instance and store it in search index.

        :param loan_data: Dict with the loan metadata.
        :param id_: Specify a UUID to use for the new record, instead of
                    automatically generated.
        :param refresh: If `true` then refresh the affected shards to make
            this operation visible to search, if `wait_for` then wait for a
            refresh to make this operation visible to search, if `false`
            (the default) then do nothing with refreshes.
            Valid choices: true, false, wait_for
        :returns: A new :class:`Record` instance.
        """
        from ...items.api import Item

        log = {
            "record": {"value": data.get("pid"), "type": "loan"},
            "operation": "create",
            "date": data["transaction_date"],
            "loan": {
                "pid": data["pid"],
                "trigger": data["trigger"],
                "override_flag": False,
                "auto_extend": data.get("auto_extend", False),
                "transaction_channel": ("sip2" if data.get("selfcheck_terminal_id") else "system"),
                "transaction_location": {
                    "pid": data["transaction_location_pid"],
                    "name": cls._get_location_name(data["transaction_location_pid"]),
                },
                "pickup_location": {
                    "pid": data["pickup_location_pid"],
                    "name": cls._get_location_name(data["pickup_location_pid"]),
                },
                "patron": cls._get_patron_data(Patron.get_record_by_pid(data["patron_pid"])),
                "item": cls._get_item_data(Item.get_record_by_pid(data["item_pid"]["value"])),
            },
        }
        if request_start_date := data.get("request_start_date"):
            log["loan"]["request_start_date"] = request_start_date
        if request_expire_date := data.get("request_expire_date"):
            log["loan"]["request_expire_date"] = request_expire_date
        if current_librarian:
            log["user"] = {"type": "ptrn", "value": current_librarian.pid}
            log["user_name"] = current_librarian.formatted_name
            log["organisation"] = {
                "value": current_librarian.organisation_pid,
                "type": "org",
            }
            log["library"] = {"value": current_librarian.library_pid, "type": "lib"}
        else:
            log["user_name"] = "system"
        # Store transaction user name if not done by SIP2
        if log["loan"]["transaction_channel"] != "sip2":
            transaction_user = Patron.get_record_by_pid(data["transaction_user_pid"])
            log["loan"]["transaction_user"] = {
                "pid": data["transaction_user_pid"],
                "name": transaction_user.formatted_name,
            }
        return super().create(data=log, index_refresh=index_refresh)

    @classmethod
    def anonymize_logs(cls, loan_pid):
        """Anonymize all logs corresponding to the given loan.

        :param loan_pid: Loan PID.
        """
        for log in OperationLogsSearch().get_logs_by_record_pid(loan_pid):
            record = log.to_dict()
            record["loan"]["patron"]["name"] = "anonymized"
            record["loan"]["patron"]["pid"] = "anonymized"
            if record["record"]["type"] == "notif":
                record["notification"]["recipients"] = ["anonymized"]
            cls.update(log.meta.id, log["date"], record)


class NoCirculationOperationLog(OperationLog, SpecificOperationLog):
    """Operation log for no circulation."""

    @classmethod
    def create(cls, scan, id_=None, index_refresh="false", **kwargs):
        """Create a new record instance and store it in search index.
        :param item_data: Dict with the item metadata.
        :param loan: Dict with the loan metadata.
        :param message: Message for item category.
        :param id_: Specify a UUID to use for the new record, instead of
                    automatically generated.
        :param refresh: If `true` then refresh the affected shards to make
            this operation visible to search, if `wait_for` then wait for a
            refresh to make this operation visible to search, if `false`
            (the default) then do nothing with refreshes.
            Valid choices: true, false, wait_for
        :returns: A new :class:`Record` instance.
        """
        item_pid = scan["item"]["pid"]
        item_data = cls._get_item_data(scan["item"])
        scan["item"] = item_data
        transaction_location_pid = scan.pop("transaction_location_pid")
        scan["transaction_location"] = {
            "pid": transaction_location_pid,
            "name": cls._get_location_name(transaction_location_pid),
        }
        if pickup_location_pid := scan.pop("pickup_location_pid", None):
            scan["pickup_location"] = {
                "pid": pickup_location_pid,
                "name": cls._get_location_name(pickup_location_pid),
            }
        log = {
            "record": {"value": item_pid, "type": "scan_item"},
            "operation": "create",
            "date": datetime.now(UTC).isoformat(),
            "scan": scan,
        }

        if current_librarian:
            log["user"] = {"type": "ptrn", "value": current_librarian.pid}
            log["user_name"] = current_librarian.formatted_name
            log["organisation"] = {
                "value": current_librarian.organisation_pid,
                "type": "org",
            }
            log["library"] = {"value": current_librarian.library_pid, "type": "lib"}
        else:
            log["user_name"] = "system"

        return super().create(data=log, index_refresh=index_refresh)
