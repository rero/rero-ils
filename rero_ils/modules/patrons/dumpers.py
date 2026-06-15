# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Patron dumpers."""

import contextlib

from invenio_records.dumpers import Dumper as InvenioRecordsDumper


class PatronPropertiesDumper(InvenioRecordsDumper):
    """Patron dumper class adding `formatted_name`."""

    def __init__(self, properties=None):
        """Init method.

        :param properties: all property names to add into the dump.
        """
        self._properties = properties or []

    def dump(self, record, data, **kwargs):
        """Dump a patron instance adding requested properties.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        :return a dict with dumped data.
        """
        data = record.dumps()  # use the default dumps() to get basic data.
        for property_name in self._properties:
            with contextlib.suppress(AttributeError):
                data[property_name] = getattr(record, property_name)
        return {k: v for k, v in data.items() if v}


class PatronNotificationDumper(InvenioRecordsDumper):
    """Patron dumper class for notification."""

    def dump(self, record, data, **kwargs):
        """Dump a patron instance for notification.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        :return a dict with dumped data.
        """
        data = {
            "pid": record.pid,
            "last_name": data.get("last_name"),
            "first_name": data.get("first_name"),
            "profile_url": record.profile_url,
            "address": {
                "street": data.get("street"),
                "postal_code": data.get("postal_code"),
                "city": data.get("city"),
                "country": data.get("country"),
            },
            "barcode": record.get("patron", {}).get("barcode"),
        }
        data["address"] = {k: v for k, v in data["address"].items() if v}
        return {k: v for k, v in data.items() if v}
