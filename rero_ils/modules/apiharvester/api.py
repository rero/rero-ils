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

"""Define relation between records and buckets."""

from datetime import datetime

import click
from dateutil import parser
from flask.globals import current_app
from invenio_db import db
from six.moves.urllib.parse import parse_qs, urlencode, urlparse

from .extensions import ApiHarvesterExtensionAgentMef
from .models import ApiHarvestConfig
from ..utils import requests_retry_session


class ApiHarvester(dict):
    """Base class for Record and RecordRevision to share common features."""

    model_cls = ApiHarvestConfig
    """SQLAlchemy model class defining which table stores the records."""

    _extensions = [ApiHarvesterExtensionAgentMef()]
    """Record extensions registry.
    Allows extensions (like system fields) to be registered on the record.
    """

    def __init__(self, name=None):
        """Initialize instance with data from DB.

        :param name: Name of config.
        """
        self.model = None
        if name:
            with db.session.begin_nested():
                query = self.model_cls.query.filter_by(name=name)
                self.model = query.first()
        if self.model:
            super().__init__(self.dumps())

    @property
    def id(self):
        """Get model identifier."""
        return self.model.id if self.model else None

    @id.setter
    def id(self, id):
        """Set model identifier."""
        self.model.id = id
        self.commit()

    @property
    def name(self):
        """Get model name."""
        return self.model.name if self.model else None

    @name.setter
    def name(self, name):
        """Set model name."""
        self.model.name = name
        self.commit()

    @property
    def size(self):
        """Get model size."""
        return self.model.size if self.model else None

    @size.setter
    def size(self, size):
        """Set model size."""
        self.model.size = size
        self.commit()

    @property
    def url(self):
        """Get model url."""
        return self.model.url if self.model else None

    @url.setter
    def url(self, url):
        """Set model url."""
        self.model.url = url
        self.commit()

    @property
    def lastrun(self):
        """Get model last run."""
        return self.model.lastrun if self.model else None

    @lastrun.setter
    def lastrun(self, lastrun):
        """Set model last run."""
        self.model.lastrun = lastrun
        self.commit()

    # TODO: implement correct dict to DB setitem
    # def __setitem__(self, key, value):
    #     if key in self:
    #         self[key] = value

    def dumps(self):
        """Make a dump of the record (defaults to a deep copy of the dict).

        :returns: A ``dict``.
        """
        data = {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'lastrun': self.lastrun
        }
        return data

    @classmethod
    def get_config(cls, name):
        """Retrieve config by name."""
        return cls(name=name)

    @classmethod
    def create(cls, name, url, size=100):
        """Create config in DB.

        :param name: Name for config.
        :param url: Url for API harvesting.
        :param size: Record size for harvesting.
        """
        with db.session.begin_nested():
            config = ApiHarvestConfig(name=name, url=url, size=size)
            db.session.merge(config)
        db.session.commit()
        return cls(name=name)

    def commit(self):
        """Commit changes to DB."""
        with db.session.begin_nested():
            db.session.merge(self.model)
        db.session.commit()
        self = self.dumps()

    def delete(self):
        """Delete API config."""
        with db.session.begin_nested():
            db.session.delete(self.model)
        db.session.commit()

    def update_lastrun(self, new_date=None):
        """Update the 'lastrun' attribute of object to now."""
        with db.session.begin_nested():
            # TODO: Date validation
            self.model.lastrun = new_date or datetime.utcnow()
            db.session.merge(self.model)
        db.session.commit()

    def update(self, name=None, url=None, size=None, lastrun=None):
        """Update config data if not None."""
        if name is not None:
            self.model.name = name
        if url is not None:
            self.model.url = url
        if size is not None:
            if isinstance(size, int):
                self.model.size = size
            else:
                raise ValueError('Size not int!')
        if lastrun is not None:
            # TODO: Date validation
            self.model.lastrun = lastrun
        with db.session.begin_nested():
            db.session.merge(self.model)
        db.session.commit()

    @classmethod
    def count(cls):
        """Get API harvest count."""
        return cls.model_cls.query.count()

    @classmethod
    def get_all_configs(cls):
        """Get all API harvest configs."""
        for config in cls.model_cls.query.order_by('id'):
            yield cls(config.name)

    def extract_records(self, data):
        """Extract records from REST data.

        :param api_harvester: Api harvester instance.
        :param data: REST data.
        :returns: list of records.
        """
        records = []
        hits = data.get('hits', {}).get('hits', {})
        for hit in hits:
            # pid = data.get('id', '')
            # updated = data.get('updated', '')
            # links = data.get('links', {}).get('self', '')
            record = hit.get('metadata', '')
            if record:
                records.append(record)
            else:
                current_app.logger.warning(
                    f'No metadata found for {self.name}: {hit}')
        return records

    def get_url(self, from_date=None):
        """Makes the URL."""
        parsed = urlparse(self.url)
        queries = parse_qs(parsed.query)
        if from_date:
            if isinstance(from_date, str):
                from_date = parser.parse(from_date)
        else:
            from_date = self.lastrun
            self.update_lastrun()
        queries['size'] = self.size

        search = queries.pop('q', [])
        from_date = from_date.isoformat()
        # we have to urlencode the time with \:
        from_date = from_date.replace(':', '%5C:')
        search.append(f'_updated:>{from_date}')
        parsed = parsed._replace(query=urlencode(queries))
        return f'{parsed.geturl()}&q={" AND ".join(search)}'

    def get_records(self, from_date=None, max=0, verbose=False):
        """Harvest multiple records from invenio api."""
        url = self.get_url(from_date=from_date)
        if verbose:
            current_app.logger.info(f'Get records from {url}')

        count = 0
        process_count = {}
        try:
            # get first data page
            request = requests_retry_session().get(url)
            data = request.json()

            if verbose:
                total = data.get('hits', {}).get('total', 'NO TOTAL')
                click.echo(f'API records found: {total}')
            # If we have no next url set it to true to process the data on
            # the first data page
            while url and (count < max or max == 0):
                records = self.extract_records(data)
                if count + self.size - max > 0 and max != 0:
                    records = records[:max - count]
                count += len(records)
                if verbose:
                    click.echo(f'{count:<10} URL: {url}')
                for extension in self._extensions:
                    extension_count, records = extension.process_records(
                        self, records, verbose)
                    process_count.setdefault(extension.name, 0)
                    process_count[extension.name] += extension_count
                url = data.get('links', {}).get('next', False)
                if url:
                    # get next data page
                    request = requests_retry_session().get(url)
                    data = request.json()
        except Exception as error:
            msg = f'Harvesting API Error: {error}'
            if verbose:
                click.secho(msg, fg='red')
            else:
                current_app.logger.error(msg)
            # import traceback
            # traceback.print_exc()
        return count, process_count
