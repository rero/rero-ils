# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2023 RERO
# Copyright (C) 2023 UCLouvain
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

"""Pytest fixtures for statistics configurations."""


from copy import deepcopy

import pytest
from utils import flush_index

from rero_ils.modules.stats_cfg.api import StatConfiguration, \
    StatsConfigurationSearch


@pytest.fixture(scope="module")
def stats_cfg_martigny_data_3(data):
    """Load statistics configuration of martigny organisation."""
    return deepcopy(data.get('stats_cfg3'))


@pytest.fixture(scope="module")
def stats_cfg_martigny_3(
        app,
        stats_cfg_martigny_data_3,
        system_librarian_martigny):
    """Create stats_cfg of martigny organisation."""
    stats_cfg = StatConfiguration.create(
        data=stats_cfg_martigny_data_3,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(StatsConfigurationSearch.Meta.index)
    yield stats_cfg


@pytest.fixture(scope="module")
def stats_cfg_martigny_data_4(data):
    """Load statistics configuration of martigny organisation."""
    return deepcopy(data.get('stats_cfg4'))


@pytest.fixture(scope="module")
def stats_cfg_martigny_4(
        app,
        stats_cfg_martigny_data_4,
        system_librarian_martigny):
    """Create stats_cfg of martigny organisation."""
    stats_cfg = StatConfiguration.create(
        data=stats_cfg_martigny_data_4,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(StatsConfigurationSearch.Meta.index)
    yield stats_cfg


@pytest.fixture(scope="module")
def stats_cfg_martigny_data_5(data):
    """Load statistics configuration of martigny organisation."""
    return deepcopy(data.get('stats_cfg5'))


@pytest.fixture(scope="module")
def stats_cfg_martigny_5(
        app,
        stats_cfg_martigny_data_5,
        system_librarian_martigny):
    """Create stats_cfg of martigny organisation."""
    stats_cfg = StatConfiguration.create(
        data=stats_cfg_martigny_data_5,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(StatsConfigurationSearch.Meta.index)
    yield stats_cfg


@pytest.fixture(scope="module")
def stats_cfg_martigny_data_6(data):
    """Load statistics configuration of martigny organisation."""
    return deepcopy(data.get('stats_cfg6'))


@pytest.fixture(scope="module")
def stats_cfg_martigny_6(
        app,
        stats_cfg_martigny_data_6,
        system_librarian_martigny):
    """Create stats_cfg of martigny organisation."""
    stats_cfg = StatConfiguration.create(
        data=stats_cfg_martigny_data_6,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(StatsConfigurationSearch.Meta.index)
    yield stats_cfg


@pytest.fixture(scope="module")
def stats_cfg_martigny_data_7(data):
    """Load statistics configuration of martigny organisation."""
    return deepcopy(data.get('stats_cfg7'))


@pytest.fixture(scope="module")
def stats_cfg_martigny_7(
        app,
        stats_cfg_martigny_data_7,
        system_librarian_martigny):
    """Create stats_cfg of martigny organisation."""
    stats_cfg = StatConfiguration.create(
        data=stats_cfg_martigny_data_7,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(StatsConfigurationSearch.Meta.index)
    yield stats_cfg


@pytest.fixture(scope="module")
def stats_cfg_martigny_data_8(data):
    """Load statistics configuration of martigny organisation."""
    return deepcopy(data.get('stats_cfg8'))


@pytest.fixture(scope="module")
def stats_cfg_martigny_8(
        app,
        stats_cfg_martigny_data_8,
        system_librarian_martigny):
    """Create stats_cfg of martigny organisation."""
    stats_cfg = StatConfiguration.create(
        data=stats_cfg_martigny_data_8,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(StatsConfigurationSearch.Meta.index)
    yield stats_cfg


@pytest.fixture(scope="module")
def stats_cfg_martigny_data_9(data):
    """Load statistics configuration of martigny organisation."""
    return deepcopy(data.get('stats_cfg9'))


@pytest.fixture(scope="module")
def stats_cfg_martigny_9(
        app,
        stats_cfg_martigny_data_9,
        system_librarian_martigny):
    """Create stats_cfg of martigny organisation."""
    stats_cfg = StatConfiguration.create(
        data=stats_cfg_martigny_data_9,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(StatsConfigurationSearch.Meta.index)
    yield stats_cfg


@pytest.fixture(scope="module")
def stats_cfg_martigny_data_10(data):
    """Load statistics configuration of martigny organisation."""
    return deepcopy(data.get('stats_cfg10'))


@pytest.fixture(scope="module")
def stats_cfg_martigny_10(
        app,
        stats_cfg_martigny_data_10,
        system_librarian_martigny):
    """Create stats_cfg of martigny organisation."""
    stats_cfg = StatConfiguration.create(
        data=stats_cfg_martigny_data_10,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(StatsConfigurationSearch.Meta.index)
    yield stats_cfg
