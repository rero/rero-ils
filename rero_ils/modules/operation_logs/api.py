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

"""API for manipulating operation_logs."""

from elasticsearch.exceptions import NotFoundError
from elasticsearch.helpers import bulk
from elasticsearch_dsl import Document
from flask import current_app
from invenio_jsonschemas.proxies import current_jsonschemas
from invenio_records.api import RecordBase
from invenio_search import RecordsSearch, current_search_client

from .extensions import DatesExtension, IDExtension, ResolveRefsExtension
from ..api import IlsRecordsSearch
from ..fetchers import FetchedPID


class OperationLogsSearch(IlsRecordsSearch):
    """RecordsSearch for OperationLogs."""

    class Meta:
        """Search only on Notifications index."""

        index = 'operation_logs'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None

    def get_logs_by_notification_pid(self, notif_pid):
        """Get operation logs records by notification pid.

        :param notif_pid: The notification pid.
        :returns a generator of ElasticSearch hit.
        :rtype generator<dict>.
        """
        query = self.filter('term', notification__pid=notif_pid)
        for hit in query.scan():
            yield hit.to_dict()

    def get_logs_by_record_pid(self, pid):
        """Get all logs for a given record PID.

        :param str pid: record PID.
        :returns: List of logs.
        """
        return list(
            self.filter(
                'bool', must={
                    'exists': {
                        'field': 'loan'
                    }
                }).filter('term', record__value=pid).scan())


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

    _extensions = [
        ResolveRefsExtension(),
        DatesExtension(),
        IDExtension()
    ]

    @classmethod
    def create(cls, data, id_=None, index_refresh='false', **kwargs):
        """Create a new record instance and store it in elasticsearch.

        :param data: Dict with the record metadata.
        :param id_: Specify a UUID to use for the new record, instead of
                    automatically generated.
        :param index_refresh: If `true` then refresh the affected shards to
            make this operation visible to search, if `wait_for` then wait for
            a refresh to make this operation visible to search, if `false`
            (the default) then do nothing with refreshes.
            Valid choices: 'true', 'false', 'wait_for'
        :returns: A new :class:`Record` instance.
        """
        if id_:
            data['pid'] = id_

        record = cls(data, model=None, **kwargs)

        # Run pre create extensions
        for e in cls._extensions:
            e.pre_create(record)

        if current_app.config.get('RERO_ILS_ENABLE_OPERATION_LOG_VALIDATION'):
            # Validate also encodes the data
            # For backward compatibility we pop them here.
            format_checker = kwargs.pop('format_checker', None)
            validator = kwargs.pop('validator', None)
            if '$schema' not in record:
                record['$schema'] = current_jsonschemas.path_to_url(
                    cls._schema)
            record._validate(
                format_checker=format_checker,
                validator=validator,
                use_model=False
            )

        current_search_client.index(
            index=cls.get_index(record),
            body=record.dumps(),
            id=record['pid'],
            refresh=index_refresh
        )

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
            oplg = d.dumps()
            if oplg.get('record', {}).get('pid'):
                oplg['record']['value'] = oplg['record'].pop('pid', None)
            # Run pre create extensions
            for e in cls._extensions:
                e.pre_create(oplg)

            action = {
                '_op_type': 'index',
                '_index': cls.get_index(oplg),
                '_source': oplg,
                '_id': oplg['pid']
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

    @classmethod
    def update(cls, _id, date, data):
        """Update all data for a record.

        :param str _id: Elasticsearch document ID.
        :param str date: Log date, useful for getting the right index.
        :param dict data: New record data.
        """
        index = cls.get_index({'date': date})

        document = Document.get(_id, index=index, using=current_search_client)

        # Assign each properties to the document
        for key, item in data.items():
            document[key] = item

        result = document.save(
            index=index,
            using=current_search_client,
            refresh=True,
        )

        if result != 'updated':
            raise Exception('Operation log cannot be updated.')

    @property
    def id(self):
        """Get model identifier."""
        return self.get('pid')

    @classmethod
    def count(cls, with_deleted=False):
        """Get record count."""
        count = 0
        try:
            count = OperationLogsSearch().filter('match_all').count()
        except NotFoundError:
            current_app.logger.warning('Operation logs index not found.')
        return count
