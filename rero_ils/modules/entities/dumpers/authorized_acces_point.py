# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""LocalizedAuthorizedAccessPoint dumper."""

from invenio_records.dumpers import Dumper

from rero_ils.utils import get_i18n_supported_languages


class LocalizedAuthorizedAccessPointDumper(Dumper):
    """Localized entity authorized access point dumper."""

    def dump(self, record, data):
        """Dump a local entity by adding localized authorized access point.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        """
        for language in get_i18n_supported_languages():
            data[f"authorized_access_point_{language}"] = record.get_authorized_access_point(language)
        return data
