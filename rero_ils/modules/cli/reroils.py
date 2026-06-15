# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Click command-line utilities."""

import click

from rero_ils.modules.acquisition.cli import acquisition
from rero_ils.modules.api_harvester.cli import api_harvester
from rero_ils.modules.cli.messages import messages
from rero_ils.modules.entities.remote_entities.cli import entity
from rero_ils.modules.migrations.cli import migrations
from rero_ils.modules.monitoring.cli import monitoring
from rero_ils.modules.notifications.cli import notifications
from rero_ils.modules.stats.cli import stats
from rero_ils.schedulers import scheduler

from .documents import documents
from .fixtures import fixtures
from .index import index
from .utils import utils


@click.group()
def reroils():
    """Reroils management commands."""


reroils.add_command(acquisition)
reroils.add_command(api_harvester)
reroils.add_command(documents)
reroils.add_command(entity)
reroils.add_command(fixtures)
reroils.add_command(index)
reroils.add_command(migrations)
reroils.add_command(messages)
reroils.add_command(monitoring)
reroils.add_command(notifications)
reroils.add_command(scheduler)
reroils.add_command(stats)
reroils.add_command(utils)
