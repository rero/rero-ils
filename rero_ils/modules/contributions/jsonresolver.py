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

"""Contributions resolver."""


import jsonresolver
from requests import get as requests_get  # noqa

from .api import Contribution


@jsonresolver.route('/api/<agency>/<pid>', host='mef.rero.ch')
def contribution_resolver(agency, pid):
    """MEF contribution resolver."""
    contribution = Contribution.get_contribution(agency, pid)
    return contribution


@jsonresolver.route('/api/agents/<agency>/<pid>', host='mef.rero.ch')
def contribution_agent_resolver(agency, pid):
    """MEF contribution resolver."""
    contribution = Contribution.get_contribution(agency, pid)
    return contribution
