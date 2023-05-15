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

"""Jinja filters."""


def issue_client_reference(issue_data):
    """Build the best possible client reference for an issue.

    :param issue_data: the dict containing holding client reference.
    :returns: the string representing the client reference.
    :rtype: str
    """
    if holding_data := issue_data.get('holdings'):
        parts = list(filter(None, [
            holding_data.get('client_id'),
            holding_data.get('order_reference')
        ]))
        return f'({"/".join(parts)})' if parts else ''
