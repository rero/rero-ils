# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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
            data[f'authorized_access_point_{language}'] = \
                record.get_authorized_access_point(language)
        return data
