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

"""Test cli."""

from click.testing import CliRunner

from rero_ils.modules.cli.index import delete_queue, init_queue, purge_queue, \
    reindex, reindex_missing, run
from rero_ils.modules.organisations.api import Organisation


def test_cli_reindex_missing(app, script_info, org_sion_data):
    """Test reindex missing cli."""
    org = Organisation.create(
        data=org_sion_data,
        delete_pid=False,
        dbcommit=True,
    )

    runner = CliRunner()
    res = runner.invoke(
        reindex_missing,
        ['-t', 'xxx', '-t', 'org', '-v'],
        obj=script_info
    )
    assert res.output.strip().split('\n') == [
        'Indexing missing xxx: ERROR pid type does not exist!',
        'Indexing missing org: 1',
        '1\torg\torg2'
    ]

    # test reindex with integreted queue
    # - we have to initialize the default indexer queue
    runner = CliRunner()
    res = runner.invoke(
        init_queue,
        [],
        obj=script_info
    )
    assert res.output.strip().split('\n') == [
        'Queue has been initialized: indexer'
    ]

    runner = CliRunner()
    res = runner.invoke(
        reindex,
        ['-t', 'org', '--yes-i-know'],
        obj=script_info
    )
    assert res.output.strip().split('\n') == [
        'Sending org to indexing queue (indexer): 1',
        'Execute "invenio reroils index run" command to process the queue!'
    ]

    runner = CliRunner()
    res = runner.invoke(
        run,
        [],
        obj=script_info
    )
    assert res.output.strip().split('\n') == [
        'Indexing records ...',
        '"indexer" indexed: 1 error: 0'
    ]
    # - test direct indexing:
    runner = CliRunner()
    res = runner.invoke(
        reindex,
        ['-t', 'org', '--yes-i-know', '-d'],
        obj=script_info
    )
    assert res.output.strip().split('\n') == [
        'Indexing org: 1',
        f'1\t{org.id}\t{org.pid}'
    ]

    # test reindex with dynamicly created queue `test_queue`
    # - initialize a new indexer queue
    queue_name = 'test_queue'
    runner = CliRunner()
    res = runner.invoke(
        init_queue,
        ['-n', queue_name],
        obj=script_info
    )
    assert res.output.strip().split('\n') == [
        'Queue has been initialized: test_queue'
    ]

    runner = CliRunner()
    res = runner.invoke(
        reindex,
        ['-t', 'org', '-q', queue_name, '--yes-i-know'],
        obj=script_info
    )
    assert res.output.strip().split('\n') == [
        'Sending org to indexing queue (test_queue): 1',
        f'Execute "invenio reroils index run -q {queue_name}" '
        'command to process the queue!'
    ]

    runner = CliRunner()
    res = runner.invoke(
        run,
        ['-q', queue_name],
        obj=script_info
    )
    assert res.output.strip().split('\n') == [
        f'Indexing records ({queue_name})...',
        f'"{queue_name}" indexed: 1 error: 0'
    ]

    # - purge the new indexer queue
    queue_name = 'test_queue'
    runner = CliRunner()
    res = runner.invoke(
        purge_queue,
        ['-n', queue_name],
        obj=script_info
    )
    assert res.output.strip().split('\n') == [
        f'Queue has been purged: {queue_name} 0'
    ]
    # - delete the new indexer queue
    queue_name = 'test_queue'
    runner = CliRunner()
    res = runner.invoke(
        delete_queue,
        ['-n', queue_name],
        obj=script_info
    )
    assert res.output.strip().split('\n') == [
        f'Queue has been deleted: {queue_name}'
    ]
