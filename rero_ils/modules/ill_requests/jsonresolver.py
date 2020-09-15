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

"""ILLRequest resolver."""

import jsonresolver

from rero_ils.modules.jsonresolver import resolve_json_refs


@jsonresolver.route('/api/ill_requests/<pid>', host='ils.rero.ch')
def ill_request_resolver(pid):
    """Resolver for ill_request record."""
    return resolve_json_refs('illr', pid)
