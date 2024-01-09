# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

"""Click command-line utilities."""

from __future__ import absolute_import, print_function

import click

from rero_ils.modules.acquisition.cli import acquisition
from rero_ils.modules.apiharvester.cli import apiharvester
from rero_ils.modules.ebooks.cli import oaiharvester
from rero_ils.modules.entities.remote_entities.cli import entity
from rero_ils.modules.monitoring.cli import monitoring
from rero_ils.modules.notifications.cli import notifications
from rero_ils.modules.stats.cli import stats
from rero_ils.schedulers import scheduler

from .fixtures import fixtures
from .index import index
from .utils import utils


@click.group()
def reroils():
    """Reroils management commands."""


reroils.add_command(acquisition)
reroils.add_command(apiharvester)
reroils.add_command(entity)
reroils.add_command(fixtures)
reroils.add_command(index)
reroils.add_command(monitoring)
reroils.add_command(notifications)
reroils.add_command(oaiharvester)
reroils.add_command(scheduler)
reroils.add_command(stats)
reroils.add_command(utils)
