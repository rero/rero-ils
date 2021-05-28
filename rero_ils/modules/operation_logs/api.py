# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
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

"""API for manipulating operation_logs."""

from elasticsearch.helpers import bulk
from invenio_records.api import RecordBase
from invenio_search import RecordsSearch, current_search_client

from .extensions import DatesExension, IDExtension, ResolveRefsExension
from ..fetchers import FetchedPID


def operation_log_id_fetcher(record_uuid, data):
    """Fetch an Organisation record's identifier.

    :param record_uuid: The record UUID.
    :param data: The record metadata.
    :return: A :data:`rero_ils.modules.fetchers.FetchedPID` instance.
    """
    return FetchedPID(provider=None, pid_type='oplg', pid_value=record_uuid)


class OperationLog(RecordBase):
    """OperationLog class."""

    index_name = 'operation_logs'

    _schema = 'operation_logs/operation_log-v0.0.1.json'

    _extensions = [ResolveRefsExension(), DatesExension(), IDExtension()]

    @classmethod
    def create(cls, data, id_=None, index_refresh='false', **kwargs):
        r"""Create a new record instance and store it in elasticsearch.

        :param data: Dict with the record metadata.
        :param id_: Specify a UUID to use for the new record, instead of
                    automatically generated.
        :param refresh: If `true` then refresh the affected shards to make
            this operation visible to search, if `wait_for` then wait for a
            refresh to make this operation visible to search, if `false`
            (the default) then do nothing with refreshes.
            Valid choices: true, false, wait_for
        :returns: A new :class:`Record` instance.
        """
        if id_:
            data['pid'] = id_

        record = cls(data, model=None, **kwargs)

        # Run pre create extensions
        for e in cls._extensions:
            e.pre_create(record)

        current_search_client.index(index=cls.get_index(record),
                                    body=record.dumps(),
                                    id=record['pid'],
                                    refresh=index_refresh)

        # Run post create extensions
        for e in cls._extensions:
            e.post_create(record)
        return record

    @classmethod
    def get_index(cls, data):
        """Get the index name given the data.

        One index per year is created based on the data date field.

        :param data: Dict with the record metadata.
        :returns: str, the corresponding index name.
        """
        suffix = '-'.join(data.get('date', '').split('-')[0:1])
        return f'{cls.index_name}-{suffix}'

    @classmethod
    def bulk_index(cls, data):
        """Bulk indexing.

        :params data: list of dicts with the record metadata.
        """
        actions = []
        for d in data:
            d = OperationLog(d)
            # Run pre create extensions
            for e in cls._extensions:
                e.pre_create(d)

            action = {
                '_op_type': 'index',
                '_index': cls.get_index(d),
                '_source': d.dumps(),
                '_id': d['pid']
            }
            actions.append(action)
        n_succeed, errors = bulk(current_search_client, actions)
        if n_succeed != len(data):
            raise Exception(f'Elasticsearch Indexing Errors: {errors}')

    @classmethod
    def get_record(cls, _id):
        """Retrieve the record by ID.

        Raise a database exception if the record does not exist.
        :param id_: record ID.
        :returns: The :class:`Record` instance.
        """
        # here the elasticsearch get API cannot be used with an index alias
        return cls(
            next(
                RecordsSearch(index=cls.index_name).filter(
                    'term', _id=_id).scan()).to_dict())

    @classmethod
    def get_indices(cls):
        """Get all index names present in the elasticsearch server."""
        return set([
            v['index'] for v in current_search_client.cat.indices(
                index=f'{cls.index_name}*', format='json')
        ])

    @classmethod
    def delete_indices(cls):
        """Remove all index names present in the elasticsearch server."""
        current_search_client.indices.delete(f'{cls.index_name}*')
        return True

    @property
    def id(self):
        """Get model identifier."""
        return self.get('pid')
