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

"""Celery database scheduler using invenios database."""

from collections import namedtuple
from copy import deepcopy

import click
import jsonpickle
from celery import current_app as current_celery
from celery.utils.log import get_logger
from flask.cli import with_appcontext
from redisbeat.scheduler import RedisScheduler as OriginalRedisScheduler
from werkzeug.local import LocalProxy

current_scheduler = LocalProxy(lambda: RedisScheduler(
    app=current_celery,
    lazy=True
))

logger = get_logger(__name__)
schedstate = namedtuple('schedstate', ('is_due', 'next'))


class RedisScheduler(OriginalRedisScheduler):
    """RedisScheduler with stores information in REDIS.

    To start celery worker beat using this backend we have to call celery
    with following parameter:
        ``-S rero_ils.schedulers.RedisScheduler``
    Example:
        ``celery worker -A invenio_app.celery --beat
            -S rero_ils.schedulers.RedisScheduler``

    base class:
        https://github.com/liuliqiang/redisbeat
    celery BeaseSchedule:
        https://github.com/celery/celery/blob/master/celery/schedules.py

    entries: https://docs.celeryproject.org/en/latest/userguide/
        periodic-tasks.html#entries
    """

    def __init__(self, app, *args, **kwargs):
        """Redis scheduler class initializer.

        :param app: current celery
        :param lazy: Do not run setup_schedule
        :param args: see base class definitions
        :param kwargs: see base class definitions
        """
        lazy = kwargs.get('lazy', False)
        url = app.conf.get("CELERY_REDIS_SCHEDULER_URL",
                           "redis://localhost:6379")
        logger.info('Connect: {url} lazy:{lazy}'.format(
            url=url,
            lazy=lazy
        ))
        kwargs['app'] = app
        kwargs['lazy'] = lazy
        super(RedisScheduler, self).__init__(*args, **kwargs)

    def get(self, name):
        """Get schedule from REDIS DB.

        :param name: name of entry in task scheduler
        :returns: scheduled task
        """
        tasks = self.rdb.zrange(self.key, 0, -1) or []
        for idx, task in enumerate(tasks):
            entry = jsonpickle.decode(task)
            if entry.name == name:
                return entry
        else:
            return None

    def enabled_name(self, name):
        """Name for enabled value in REDIS DB.

        :param name: name of entry in task scheduler
        :returns: name of the enable key in REDIS DB
        """
        return '{key}:{name}'.format(key=self.key, name=name)

    def merge_inplace(self, tasks):
        """Merge entries from CELERY_BEAT_SCHEDULE.

        :param tasks: dictionary with CELERY_BEAT_SCHEDULE tasks
        """
        for name in tasks:
            enabled = tasks[name].pop('enabled', True)
            self.rdb[self.enabled_name(name)] = int(enabled)
        super(RedisScheduler, self).merge_inplace(tasks)

    def setup_schedule(self):
        """Init entries from CELERY_BEAT_SCHEDULE."""
        config = deepcopy(self.app.conf.CELERY_BEAT_SCHEDULE)
        self.merge_inplace(config)
        msg = 'Current schedule:\n{tasks}'.format(
            tasks='\n'.join(self.display_all(prefix='- Tasks: '))
        )
        logger.info(msg)

    def is_due(self, entry):
        """Return tuple of ``(is_due, next_time_to_check)``.

        Notes:
            - next time to check is in seconds.
            - ``(True, 20)``, means the task should be run now, and the next
                time to check is in 20 seconds.
            - ``(False, 12.3)``, means the task is not due, but that the
              scheduler should check again in 12.3 seconds.
        The next time to check is used to save energy/CPU cycles,

        We get the enabled state for the task directly from REDIS DB.

        :param entry: periodic task entry (see class commands)
        :returns: the state of the entry as schedstate
        """
        if self.get_entry_enabled(entry.name):
            state = entry.is_due()
        else:
            msg = ('Not enabled: {name} = {task} {each} {kwargs}'.format(
                name=entry.name,
                task=entry.task,
                each=repr(entry.schedule),
                kwargs=entry.kwargs,
            ))
            logger.info(msg)
            state = schedstate(is_due=False, next=entry.is_due().next)
        return state

    def set(self, entry, enable=True):
        """Sets an entry.

        :param entry: periodic task entry (see class commands)
        :returns: True if successful
        """
        # TODO: find a way to change a entry in zrange directly.
        self.remove(entry.name)
        return self.add_entry(entry, enable=enable)

    def remove(self, name):
        """Remove a scheduled task.

        :param name: name of entry in task scheduler
        :returns: True if successful
        """
        enabled_name = self.enabled_name(name)
        if self.rdb.get(enabled_name):
            del self.rdb[enabled_name]
        return super(RedisScheduler, self).remove(task_key=name)

    def add_entry(self, entry, enable=True):
        """Add an entry.

        Adds an entry to the task scheduler.

        :param entry: periodic task entry (see class commands)
        :param enable: enable or disable scheduling
        :returns: True if successful
        """
        result = self.add(**{
            'name': entry.name,
            'task': entry.task,
            'schedule': entry.schedule,
            'args': entry.args,
            'kwargs': entry.kwargs,
            'options': entry.options
        })
        if result:
            self.set_entry_enabled(name=entry.name, enable=enable)
        return result

    def display_entry(self, name, prefix='- '):
        """Display an entry.

        :param name: name of entry in task scheduler
        :param prefix: prefix to add to returned info
        :returns: entry as string representative
        """
        entry_as_text = 'Not found entry: {name}'.format(name=name)
        entry = self.get(name)
        if entry:
            entry_as_text = (
                '{txt}{name} = {task} {each} {kwargs}'
                ' {options} {enabled}'
                ).format(
                    txt=prefix,
                    name=entry.name,
                    task=entry.task,
                    each=repr(entry.schedule),
                    kwargs='{txt}{data}'.format(
                        txt='kwargs:',
                        data=entry.kwargs
                    ),
                    options='{txt}{data}'.format(
                        txt='options:',
                        data=entry.options
                    ),
                    enabled='{txt}{data}'.format(
                        txt='enabled:',
                        data=self.get_entry_enabled(name)
                    )
                )
        return entry_as_text

    def display_all(self, prefix='- '):
        """Display all entries.

        :param prefix: prefix to add to returned info
        :returns: list of entry as string representative
        """
        entries_as_text_list = []
        for entry in self.rdb.zrange(self.key, 0, -1):
            entry = jsonpickle.decode(entry)
            entries_as_text_list.append(
                self.display_entry(name=entry.name, prefix=prefix)
            )
        return entries_as_text_list

    def get_entry_enabled(self, name):
        """Get the enabled status.

        :param name: name of entry in task scheduler
        :returns: enabled status
        """
        value = self.rdb.get(self.enabled_name(name))
        if value is None or value == b'1':
            return True
        return False

    def set_entry_enabled(self, name, enable=True):
        """Set enabled of an entry.

        At the moment we will save the enabled information in ``entry.kwars``.
        We have to make sure that there is a task using this parameter
        otherwise.
        In this case we have to save this information some where else.
        Override the entry (ScheduleEntry) class or saving directly in REDIS.

        :param name: name of entry in task scheduler
        :param enable: enable or disable scheduling
        """
        if self.get(name):
            enabled_name = '{key}:{name}'.format(key=self.key, name=name)
            self.rdb[enabled_name] = int(enable)

    def set_enable_all(self, enable=True):
        """Set enabled for entries."""
        for entry in self.rdb.zrange(self.key, 0, -1):
            entry = jsonpickle.decode(entry)
            self.set_entry_enabled(name=entry.name, enable=enable)


# cli: command line code for scheduler ---------------------------------------
# TODO: put cli code into separate File
@click.group()
def scheduler():
    """Scheduler management commands."""


@scheduler.command('info')
@with_appcontext
def info():
    """Displays infos about all periodic tasks."""
    click.secho('Scheduled tasks:', fg='green')
    click.echo('\n'.join(current_scheduler.display_all()))


@scheduler.command('init')
@click.option('-r', '--reset', 'reset', is_flag=True, default=False)
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@with_appcontext
def init(reset, verbose):
    """Initialize scheduler.

    :param reset: remove DB before initializing the tasks
    :param verbose: verbose output
    """
    if reset:
        click.secho('Reset REDIS scheduler!', fg='red', bold=True)
        current_scheduler._remove_db()
    else:
        click.secho('Initalize REDIS scheduler!', fg='yellow')
    current_scheduler.setup_schedule()
    if verbose:
        click.echo('\n'.join(current_scheduler.display_all()))


@scheduler.command('enable_tasks')
@click.option('-a', '--all', 'all', is_flag=True, default=False)
@click.option('-n', '--name', 'names', multiple=True, default=[])
@click.option('-d', '--disable', 'disable', is_flag=True, default=False)
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@with_appcontext
def enable_tasks(all, names, disable, verbose):
    """Enable or disable a periodic tasks.

    :param all: change all tasks
    :param name: name of task to change (multiple names are possible)
    :param disable: disables the task(s)
    :param verbose: verbose output
    """
    if verbose:
        click.secho('Scheduler tasks enabled:', fg='green')
    if all:
        current_scheduler.set_enable_all(not disable)
        if verbose:
            click.echo('\n'.join(current_scheduler.display_all()))
    else:
        for name in names:
            name = name.strip()
            current_scheduler.set_entry_enabled(name=name, enable=not disable)
            if verbose:
                click.echo(current_scheduler.display_entry(name=name))
