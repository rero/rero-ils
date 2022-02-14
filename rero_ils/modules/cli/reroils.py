# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
# Copyright (C) 2020 UCLouvain
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

from .fixtures import fixtures
from .index import index
from .users import users
from .utils import utils
from ..apiharvester.cli import apiharvester
from ..contributions.cli import contribution
from ..ebooks.cli import oaiharvester
from ..monitoring.cli import monitoring
from ..notifications.cli import notifications
from ..stats.cli import stats
from ...schedulers import scheduler


@click.group()
def reroils():
    """Reroils management commands."""


reroils.add_command(apiharvester)
reroils.add_command(contribution)
reroils.add_command(fixtures)
reroils.add_command(index)
reroils.add_command(monitoring)
reroils.add_command(notifications)
reroils.add_command(oaiharvester)
reroils.add_command(scheduler)
reroils.add_command(stats)
reroils.add_command(users)
reroils.add_command(utils)
