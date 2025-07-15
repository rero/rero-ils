# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2024 RERO
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

"""API for cantook records."""

import click

from rero_ils.modules.api_harvester.models import ApiHarvestConfig
from rero_ils.modules.locations.api import Location
from rero_ils.modules.organisations.api import Organisation


class ApiHarvest:
    """ApiHarvest class."""

    def __init__(
        self, name, file_name=None, process=False, harvest_count=-1, verbose=False
    ):
        """Class init.

        :param name: name of API config
        :param file_name: to save records to file
        :param process: create harvested records
        :param harvest_count: how many records to harvest
        :param verbose: print verbose messages
        """
        config = self.get_config(name)
        if not config:
            raise NameError(f"API Config not found: {name}")
        self.config = config
        self.file = file_name
        self.process = process
        self.harvest_count = harvest_count
        self.verbose = verbose
        self._vendor = None
        self._url = self.config.url
        self._code = self.config.code
        self._count = 0
        self._count_new = 0
        self._count_upd = 0
        self._count_del = 0
        info = {}
        for organisation in Organisation.get_records_by_online_harvested_source(
            self._code
        ):
            locations = {}
            for location_pid in organisation.get_online_locations():
                locations[location_pid] = None
                location = Location.get_record_by_pid(location_pid)
                library = location.get_library()
                if url := library.get_online_harvested_source_url(source=self._code):
                    locations[location_pid] = url
            info[organisation.pid] = {
                "item_type_pid": organisation.online_circulation_category(),
                "locations": locations,
            }
        self._info = info

    @classmethod
    def get_config(cls, name):
        """Get config.

        :param name: name of config
        :returns: API config
        """
        return ApiHarvestConfig.query.filter_by(name=name).first()

    def get_request_url(self, start_date="1990-01-01", page=1):
        """Get request URL.

        :param start_date: date from where records has to be harvested
        :param page: page from where records have to be harvested
        """
        raise NotImplementedError()

    def create_update_record(self, record):
        """Create new record or update record.

        :param record: record to create or update
        """
        raise NotImplementedError()

    def save_record(self, record):
        """Save record to file.

        :param record: record to write to file
        """
        if self.file:
            self.file.write(record)

    def msg_text(self, pid, msg):
        """Logging message text.

        :param pid: pid for message text
        :param msg: msg text for message
        :returns: string message
        """
        return f"{self._count}: {self._vendor}:{self._code} {pid} = {msg}"

    def process_records(self, records):
        """Process records.

        :param records: records to process
        """
        for record in records:
            if self.harvest_count >= 0 and self._count >= self.harvest_count:
                break
            self._count += 1
            self.save_record(record)
            if self.process:
                pid, status = self.create_update_record(record)
                self.verbose_print(self.msg_text(pid=pid, msg=status.value))

    def verbose_print(self, msg):
        """Print verbose message.

        :param msg: message to print if verbose
        """
        if self.verbose:
            click.echo(msg)

    def harvest_records(self, from_date):
        """Harvest records from servers.

        :param from_date: records changed after this date to harvest
        :returns: count and count of records processed
        """
        records = []
        self.process_records(records=records)
        return self._count, len(records)

    @property
    def count(self):
        """Get count."""
        return self._count

    @property
    def count_new(self):
        """Get new count."""
        return self._count_new

    @property
    def count_upd(self):
        """Get updated count."""
        return self._count_upd

    @property
    def count_del(self):
        """Get deleted count."""
        return self._count_del
