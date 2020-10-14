# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""API for manipulating the item issue."""

from ...api import IlsRecord


class ItemIssue(IlsRecord):
    """Item issue class."""

    @property
    def expected_date(self):
        """Shortcut for issue expected date."""
        return self.get('issue', {}).get('expected_date')

    @property
    def received_date(self):
        """Shortcut for issue received date."""
        return self.get('issue', {}).get('received_date')

    @property
    def issue_status(self):
        """Shortcut for issue status."""
        return self.get('issue', {}).get('status')

    @property
    def issue_is_regular(self):
        """Shortcut for issue is regular."""
        return self.get('issue', {}).get('regular', True)
