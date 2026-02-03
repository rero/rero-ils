# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Click command-line interface for API harvester management."""

import click
import dateparser
import yaml
from flask import current_app
from flask.cli import with_appcontext
from werkzeug.local import LocalProxy

from rero_ils.modules.api_harvester.tasks import harvest_records

from .models import ApiHarvestConfig
from .utils import api_source, get_apiharvest_object

datastore = LocalProxy(lambda: current_app.extensions["security"].datastore)


@click.group()
def api_harvester():
    """Api harvester commands."""


@api_harvester.command("add-source")
@click.argument("name")
@click.option("-U", "--url", default="", help="Url")
@click.option("-n", "--classname", default="", help="Class name")
@click.option("-c", "--code", default="", help="Code")
@click.option("-u", "--update", is_flag=True, default=False, help="Update config")
@click.option(
    "-s",
    "--setting",
    "settings_overrides",
    multiple=True,
    metavar="KEY=VALUE",
    help="Patch a single settings key (repeatable). E.g. --setting location_pid=3",
)
@click.option(
    "-d",
    "--delete-setting",
    "settings_deletions",
    multiple=True,
    metavar="KEY",
    help="Remove a settings key (repeatable). E.g. --delete-setting location_pid",
)
@with_appcontext
def add_api_source_config(name, url, classname, code, update, settings_overrides, settings_deletions):
    """Add or Update ApiHarvestConfig."""
    settings = None
    if settings_overrides or settings_deletions:
        existing = ApiHarvestConfig.query.filter_by(name=name).first()
        settings = dict(existing.settings or {}) if existing else {}
        for kv in settings_overrides:
            if "=" not in kv:
                raise click.BadParameter(f"Expected KEY=VALUE, got: {kv!r}", param_hint="--setting")
            key, _, value = kv.partition("=")
            settings[key.strip()] = value.strip()
        for key in settings_deletions:
            settings.pop(key.strip(), None)
    msg = api_source(name=name, url=url, classname=classname, code=code, settings=settings, update=update)
    click.echo(f"ApiHarvestConfig {name}: {msg}")


@api_harvester.command("init-config")
@click.argument("configfile", type=click.File("rb"))
@click.option("-u", "--update", is_flag=True, default=False, help="Update config")
@with_appcontext
def init_api_harvest_config(configfile, update):
    """Add or update ApiHarvestConfigs from file."""
    if configs := yaml.load(configfile, Loader=yaml.FullLoader):
        for name, values in sorted(configs.items()):
            url = values.get("url", "")
            classname = values.get("classname", "")
            code = values.get("code", "")
            settings = values.get("settings")
            msg = api_source(name=name, url=url, classname=classname, code=code, settings=settings, update=update)
            click.echo(f"ApiHarvestConfig {name}: {msg}")

    else:
        click.secho(f"ERROR: no YML config found in: {configfile.name}", fg="red")


@api_harvester.command()
@click.option("-n", "--name", default=None, help="Name of persistent configuration to use.")
@click.option(
    "-f",
    "--from-date",
    default=None,
    help="The lower bound date for the harvesting (optional).",
)
@click.option(
    "-k",
    "--enqueue",
    is_flag=True,
    default=False,
    help="Enqueue harvesting and return immediately.",
)
@click.option(
    "-m",
    "--harvest_count",
    type=int,
    default=-1,
    help="maximum of records to harvest (optional).",
)
@click.option("-v", "--verbose", "verbose", is_flag=True, default=False)
@click.option(
    "-l",
    "--log",
    "log_path",
    type=click.Path(dir_okay=False, writable=True),
    default=None,
    help="Write verbose output to this file (line-buffered, implies --verbose).",
)
@with_appcontext
def harvest(name, from_date, enqueue, harvest_count, verbose, log_path):
    """Harvest records from an API repository."""
    if log_path:
        verbose = True
    if name:
        click.secho(f"Harvest api: {name}", fg="green")
    if from_date:
        from_date = dateparser.parse(from_date).isoformat()
    if enqueue and log_path:
        raise click.UsageError("--log is not supported with --enqueue")
    log_file = open(log_path, "a", buffering=1, encoding="utf-8") if log_path else None
    try:
        if enqueue:
            async_id = harvest_records.delay(
                name=name, from_date=from_date, harvest_count=harvest_count, verbose=verbose
            )
            if verbose:
                click.echo(f"AsyncResult {async_id}")
        else:
            harvest_records(
                name=name, from_date=from_date, harvest_count=harvest_count, verbose=verbose, log_file=log_file
            )
    finally:
        if log_file:
            log_file.close()


@api_harvester.command("info")
@with_appcontext
def info():
    """List infos for tasks."""
    apis = ApiHarvestConfig.query.order_by(ApiHarvestConfig.name.asc()).all()
    for api in apis:
        click.echo(api.name)
        click.echo(f"\tlastrun   : {api.lastrun}")
        click.echo(f"\turl       : {api.url}")
        click.echo(f"\tclassname : {api.classname}")
        click.echo(f"\tcode      : {api.code}")
        click.echo(f"\tsettings  : {api.settings}")


@api_harvester.command()
@click.argument("name")
@click.option("-d", "--date", default=None, help="Set last run (default: now).")
@with_appcontext
def set_last_run(name, date):
    """Set last run."""
    if config := get_apiharvest_object(name=name):
        new_date = config.update_lastrun(new_date=date)
        click.secho(f"Set last run {name}: {new_date}", fg="green")
    else:
        click.secho(f"No config found: {name}", fg="red")
