# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2024 RERO
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

"""Files results classes."""

from invenio_records_resources.services.files.results import FileList


class MainFileList(FileList):
    """List of file items result."""

    @property
    def entries(self):
        """Iterator over the hits."""
        for entry in self._results:
            # keep only the main files
            if entry.metadata.get('type') in ['fulltext', 'thumbnail']:
                continue
            projection = self._service.file_schema.dump(
                entry,
                context=dict(
                    identity=self._identity,
                ),
            )
            if self._links_item_tpl:
                projection["links"] = self._links_item_tpl.expand(
                    self._identity, entry)

            yield projection
