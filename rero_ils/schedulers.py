# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
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


import contextlib

import click
from celery import current_app as current_celery
from celery.utils.log import get_logger
from flask.cli import with_appcontext
from sqlalchemy_celery_beat import DatabaseScheduler as OriginalDatabaseScheduler
from sqlalchemy_celery_beat.models import PeriodicTask
from sqlalchemy_celery_beat.schedulers import ModelEntry as ScheduleEntry
from sqlalchemy_celery_beat.session import session_cleanup
from werkzeug.local import LocalProxy

current_scheduler = LocalProxy(lambda: DatabaseScheduler(app=current_celery, lazy=True))

logger = get_logger(__name__)


class ModelEntry(ScheduleEntry):
    """Scheduler entry taken from database row."""

    @classmethod
    def from_entry(cls, name, Session, app=None, **entry):
        """Creates ModelEntry from entry.

        **entry sample:

        {
            'task': 'celery.backend_cleanup',
            'schedule': schedules.crontab('0', '4', '*'),
            'options': {'expires': 43200}
        }

        """
        session = Session()
        with session_cleanup(session):
            periodic_task = session.query(PeriodicTask).filter_by(name=name).first()
            temp = cls._unpack_fields(session, **entry)
            enabled = temp.pop("enabled", False)
            if not periodic_task:
                periodic_task = PeriodicTask(name=name, **temp)
            else:
                # Get enabled and do not update the periodic task
                enabled = periodic_task.enabled
                # periodic_task.update(**temp)
            session.add(periodic_task)
            session.commit()
            res = cls(periodic_task, app=app, Session=Session)
            res.model.enabled = res.enabled = enabled
            session.commit()
            return res


class DatabaseScheduler(OriginalDatabaseScheduler):
    """DatabaseScheduler with stores information in DB.

    To start celery worker beat using this backend we have to call celery
    with following parameter:
        ``-S rero_ils.schedulers.DatabaseScheduler``
    Example:
        ``celery worker -A invenio_app.celery --beat
            -S rero_ils.schedulers.DatabaseScheduler``

    base class:
        https://github.com/farahats9/sqlalchemy-celery-beat
    celery BeaseSchedule:
        hhttps://github.com/farahats9/sqlalchemy-celery-beat/blob/master/sqlalchemy_celery_beat/schedulers.py

    entries: https://docs.celeryproject.org/en/latest/userguide/
        periodic-tasks.html#entries
    """

    Entry = ModelEntry

    def __init__(self, *args, **kwargs):
        """Database scheduler class initializer.

        :param app: current celery
        :param lazy: Do not run setup_schedule
        :param args: see base class definitions
        :param kwargs: see base class definitions
        """
        app = kwargs["app"]
        if dburi := app.conf.get("CELERY_BEAT_DBURI"):
            app.conf["beat_dburi"] = dburi
            logger.info(f"Scheduler connect db: {dburi}")
        if engine_options := app.conf.get("CELERY_BEAT_ENGINE_OPTIONS"):
            app.conf["beat_engine_options"] = engine_options
            logger.info(f"Scheduler engine options: {engine_options}")
        if schedules := app.conf.get("CELERY_BEAT_SCHEDULE"):
            app.conf["beat_schedule"] = schedules
            logger.info(f"Schedules: {schedules}")
        app.conf["result_expires"] = False

        super().__init__(*args, **kwargs)

    def get(self, name):
        """Get schedule from DB.

        :param name: name of entry in task scheduler
        :return: scheduled task
        """
        with contextlib.suppress(KeyError):
            return self.schedule[name]

    def remove(self, name):
        """Remove a scheduled task.

        :param name: name of entry in task scheduler
        :return: True if successful
        """
        with contextlib.suppress(KeyError):
            entry = self.schedule[name]
            session = self.Session()
            with session_cleanup(session):
                session.delete(entry.model)
                session.commit()
                return True
        return False

    def reset(self):
        """Reset all scheduled tasks."""
        session = self.Session()
        with session_cleanup(session):
            for _, entry in self.all_as_schedule().items():
                session.delete(entry.model)
            session.commit()

    def all_as_schedule(self):
        """Get all schedules."""
        session = self.Session()
        with session_cleanup(session):
            # get all enabled PeriodicTask
            models = session.query(self.Model).all()
            schedules = {}
            for model in models:
                with contextlib.suppress(ValueError):
                    schedules[model.name] = self.Entry(
                        model, app=self.app, Session=self.Session
                    )
            return schedules

    def display_entry(self, entry, prefix="- "):
        """Display an entry.

        :param name: name of entry in task scheduler
        :param prefix: prefix to add to returned info
        :return: entry as string representative
        """
        # return f"{prefix}{name} = {data} "
        return (
            f"{prefix}{entry.name} = {entry.task} | {repr(entry.schedule)} | "
            f"kwargs:{entry.kwargs} | "
            # f"options:{entry.options} "
            f"enabled:{entry.model.enabled}"
        )

    def display_all(self, prefix="- "):
        """Display all entries.

        :return: list of entry as string representative
        """
        entries_as_text_list = []
        entries_as_text_list.extend(
            self.display_entry(entry=entry, prefix=prefix)
            for _, entry in sorted(self.all_as_schedule().items())
        )
        return entries_as_text_list

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
        with contextlib.suppress(KeyError):
            entry = self.schedule[name]
            entry.model.enabled = entry.enabled = enable
            session = self.Session()
            with session_cleanup(session):
                session.add(entry.model)
                session.commit()
                session.refresh(entry.model)

    def set_enable_all(self, enable=True):
        """Set enabled for entries."""
        session = self.Session()
        with session_cleanup(session):
            for entry in self.all_as_schedule().values():
                entry.model.enabled = entry.enabled = enable
                session.add(entry.model)
                session.commit()
                session.refresh(entry.model)


# cli: command line code for scheduler ---------------------------------------
# TODO: put cli code into separate File
@click.group()
def scheduler():
    """Scheduler management commands."""


@scheduler.command("info")
@with_appcontext
def info():
    """Displays infos about all periodic tasks."""
    click.secho("Scheduled tasks:", fg="green")
    click.echo("\n".join(current_scheduler.display_all()))


@scheduler.command("")
@click.option("-r", "--reset", "reset", is_flag=True, default=False)
@click.option("-v", "--verbose", "verbose", is_flag=True, default=False)
@with_appcontext
def init(reset, verbose):
    """Initialize scheduler.

    :param reset: remove DB before initializing the tasks
    :param verbose: verbose output
    """
    if reset:
        click.secho("Reset DB scheduler!", fg="red", bold=True)
        current_scheduler.reset()
    else:
        click.secho("Initalize DB scheduler!", fg="yellow")
    current_scheduler.setup_schedule()
    if verbose:
        click.echo("\n".join(current_scheduler.display_all()))


@scheduler.command("")
@click.option("-a", "--all", "all_", is_flag=True, default=False)
@click.option("-n", "--name", "names", multiple=True, default=None)
@click.option("-d", "--disable", "disable", is_flag=True, default=False)
@click.option("-v", "--verbose", "verbose", is_flag=True, default=False)
@with_appcontext
def enable_tasks(all_, names, disable, verbose):
    """Enable or disable a periodic tasks.

    :param all: change all tasks
    :param name: name of task to change (multiple names are possible)
    :param disable: disables the task(s)
    :param verbose: verbose output
    """
    if verbose:
        click.secho("Scheduler tasks enabled:", fg="green")
    if all_:
        current_scheduler.set_enable_all(not disable)
        if verbose:
            click.echo("\n".join(current_scheduler.display_all()))
    else:
        names = names or []
        for name in names:
            name = name.strip()
            current_scheduler.set_entry_enabled(name=name, enable=not disable)
            if verbose:
                if entry := current_scheduler.get(name=name):
                    click.echo(current_scheduler.display_entry(entry=entry))
                else:
                    click.secho(f"Not found entry: {name}", fg="red")
