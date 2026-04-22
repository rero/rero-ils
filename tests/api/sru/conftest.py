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

"""SRU test fixtures."""

import pytest


@pytest.fixture()
def sru_result_set_client(client):
    """Yield a client with RERO_ILS_SRU_RESULT_SET_TTL set to 60 seconds."""
    client.application.config["RERO_ILS_SRU_RESULT_SET_TTL"] = 60
    yield client
    client.application.config.pop("RERO_ILS_SRU_RESULT_SET_TTL", None)
