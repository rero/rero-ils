# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
# Copyright (C) 2022 UCLouvain
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

"""API for manipulating records."""
import re
from copy import deepcopy
from uuid import uuid4

import click
import pytz
from celery import current_app as current_celery_app
from elasticsearch import VERSION as ES_VERSION
from elasticsearch.exceptions import NotFoundError
from elasticsearch.helpers import bulk
from elasticsearch.helpers import expand_action as default_expand_action
from flask import current_app
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_indexer.signals import before_record_index
from invenio_indexer.utils import _es7_expand_action
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.api import Record
from invenio_records_rest.utils import obj_or_import_string
from invenio_search import current_search
from invenio_search.api import RecordsSearch
from jsonschema import FormatChecker
from jsonschema.compat import str_types
from jsonschema.exceptions import ValidationError
from kombu.compat import Consumer
from sqlalchemy import text
from sqlalchemy.orm.exc import NoResultFound

from .utils import extracted_data_from_ref

"""Custom ILS record JSON schema format validator."""
ils_record_format_checker = FormatChecker()


@ils_record_format_checker.checks('email')
@ils_record_format_checker.checks('idn-email')
def _strong_email_validation(instance) -> bool:
    """Allow to validate an email address (only email format, not DNS)."""
    if not isinstance(instance, str_types):
        return False
    # DEV NOTE : If this regexp changes, you also need to alter the regexp
    # into `email.validator.ts` file into @rero/ng-core. The best solution
    # should be to use a configuration setting available through an API, but
    # it should be a little overkill.
    email_regexp = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return bool(re.fullmatch(email_regexp, instance))


class IlsRecordError:
    """Base class for errors in the IlsRecordClass."""

    class Deleted(Exception):
        """IlsRecord is deleted."""

    class NotDeleted(Exception):
        """IlsRecord is not deleted."""

    class PidMissing(Exception):
        """IlsRecord pid missing."""

    class PidChange(Exception):
        """IlsRecord pid change."""

    class PidAlreadyUsed(Exception):
        """IlsRecord pid already used."""

    class PidDoesNotExist(Exception):
        """Pid does not exist."""

    class DataMissing(Exception):
        """Data missing in record."""


class IlsRecordsSearch(RecordsSearch):
    """Search Class for ils."""

    class Meta:
        """Search only on item index."""

        index = 'records'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None

    @classmethod
    def flush_and_refresh(cls):
        """Flush and refresh index."""
        current_search.flush_and_refresh(cls.Meta.index)

    def get_record_by_pid(self, pid, fields=None):
        """Get ElasticSearch hit by pid.

        :param pid: the record PID to retrieve.
        :param fields: a list of field to return. If ``None`` all fields will
            be returned.
        :returns: An ``AttrDict`` representing the ElasticSearch hit found.
        :raise NotFoundError: If the record cannot be found into ElasticSearch
        """
        if hit := next(self.get_records_by_pids([pid], fields), None):
            return hit
        raise NotFoundError(f'Record not found pid: {pid}')

    def get_records_by_pids(self, pids, fields=None):
        """Get ES hits by pids.

        :param pids: the list of record pids to retrieve.
        :param fields: a list of field to return. If ``None`` all fields will
            be returned.
        :returns: A generator of ``AttrDict`` representing ElasticSearch hits
            found.
        """
        assert type(pids) is list
        query = self.filter('terms', pid=pids)
        if fields:
            query = query.source(includes=fields)
        return query.scan()

    def get_records_by_terms(self, terms, key='pid', fields=None,
                             as_dict=False):
        """Search records by terms.

        :param terms: list of term to search
        :param key: key used for search terms
        :param fields: list of field to get
        :param as_dict: if true the search result will be converted to dict
        :return: dictionary if as_dict is true else return generator
        :rtype: dictionary or generator
        """
        fields = fields or '*'
        params = {key: terms}
        query = self.filter('terms', **params).source(includes=fields)

        if as_dict:
            return {
                result.pid: result.to_dict()
                for result in query.scan()
            }

        return query.scan()


class IlsRecord(Record):
    """ILS Record class."""

    minter = None
    fetcher = None
    provider = None
    object_type = 'rec'
    pids_exist_check = None
    pid_check = True

    format_checker = ils_record_format_checker

    @classmethod
    def get_indexer_class(cls):
        """Get the indexer from config."""
        endpoints = current_app.config['RECORDS_REST_ENDPOINTS']
        endpoints.update(current_app.config['CIRCULATION_REST_ENDPOINTS'])
        try:
            indexer = obj_or_import_string(
                endpoints[cls.provider.pid_type]['indexer_class']
            )
        except Exception:
            # provide default indexer if no indexer is defined in config.
            indexer = IlsRecordsIndexer
        return indexer

    def _validate(self, **kwargs):
        """Validate record against schema.

        extended validation per record class
        and test of pid existence.
        """
        if self.get('_draft'):
            # No validation is needed for draft records
            return self

        json = super()._validate(**kwargs)
        validation_message = self.extended_validation(**kwargs)
        # We only like to run pids_exist_check if validation_message is True
        # and not a string with error from extended_validation
        if validation_message is True and self.pid_check and \
                self.pids_exist_check:
            from .utils import pids_exists_in_data
            validation_message = pids_exists_in_data(
                info=f'{self.provider.pid_type} ({self.pid})',
                data=self,
                required=self.pids_exist_check.get('required', {}),
                not_required=self.pids_exist_check.get('not_required', {})
            ) or True
        if validation_message is not True:
            if not isinstance(validation_message, list):
                validation_message = [validation_message]
            raise ValidationError(';'.join(validation_message))
        return json

    def extended_validation(self, **kwargs):
        """Returns reasons for validation failures, otherwise True.

        Override this function for classes that require extended validations
        """
        return True

    @classmethod
    def create(cls, data, id_=None, delete_pid=False,
               dbcommit=False, reindex=False, pidcheck=True, **kwargs):
        """Create a new ils record."""
        assert cls.minter
        assert cls.provider
        if '$schema' not in data:
            pid_type = cls.provider.pid_type
            schemas = current_app.config.get('RERO_ILS_DEFAULT_JSON_SCHEMA')
            if pid_type in schemas:
                from .utils import get_schema_for_resource
                data['$schema'] = get_schema_for_resource(pid_type)
        pid = data.get('pid')
        if delete_pid and pid:
            del data['pid']
        elif pid:
            if test_rec := cls.get_record_by_pid(pid):
                raise IlsRecordError.PidAlreadyUsed(
                    'PidAlreadyUsed {pid_type} {pid} {uuid}'.format(
                        pid_type=cls.provider.pid_type,
                        pid=test_rec.pid,
                        uuid=test_rec.id
                    )
                )
        if not id_:
            id_ = uuid4()
        persistent_identifier = cls.minter(id_, data)
        cls.pid_check = pidcheck
        try:
            record = super().create(data=data, id_=id_, **kwargs)
            if record and dbcommit:
                record.dbcommit(reindex)
        # TODO: remove validation error once the angular editor
        #       validation is complete
        except Exception as err:
            current_app.logger.error(
                f'{cls.__name__} err:{err} data:{data}')
            raise
        return record

    @classmethod
    def get_record_by_pid(cls, pid, with_deleted=False, verbose=False):
        """Get ILS record by pid value."""
        if verbose:
            click.echo(f'\t\tget_record_by_pid: {cls.__name__} {pid}')
        if pid:
            assert cls.provider
            try:
                persistent_identifier = PersistentIdentifier.get(
                    cls.provider.pid_type,
                    pid
                )
                return super().get_record(
                    persistent_identifier.object_uuid,
                    with_deleted=with_deleted
                )
            # TODO: is it better to raise a error or to return None?
            except (NoResultFound, PIDDoesNotExistError):
                return None

    @classmethod
    def get_records_by_pids(cls, pids):
        """Get ILS records by pid values.

        :param pids: Object pid list to retrieve.
        :return: Generator of ILS resource.
        """
        assert type(pids) is list
        for pid in pids:
            if resource := cls.get_record_by_pid(pid):
                yield resource

    @classmethod
    def record_pid_exists(cls, pid):
        """Check if a persistent identifier exists.

        :param pid: The PID value.
        :returns: `True` if the PID exists.
        """
        assert cls.provider
        try:
            PersistentIdentifier.get(
                cls.provider.pid_type,
                pid
            )
            return True

        except (NoResultFound, PIDDoesNotExistError):
            return False

    @classmethod
    def get_pid_by_id(cls, id):
        """Get pid by uuid."""
        persistent_identifier = cls.get_persistent_identifier(id)
        return str(persistent_identifier.pid_value)

    @classmethod
    def get_id_by_pid(cls, pid):
        """Get uuid by pid."""
        assert cls.provider
        try:
            persistent_identifier = PersistentIdentifier.get(
                cls.provider.pid_type,
                pid
            )
            return persistent_identifier.object_uuid
        except Exception:
            return None

    @classmethod
    def get_record_by_id(cls, id, with_deleted=False):
        """Get ils record by uuid."""
        return super().get_record(id, with_deleted=with_deleted)

    @classmethod
    def get_persistent_identifier(cls, id):
        """Get Persistent Identifier."""
        return PersistentIdentifier.get_by_object(
            cls.provider.pid_type,
            cls.object_type,
            id
        )

    @classmethod
    def _get_all(cls, with_deleted=False):
        """Get all persistent identifier records."""
        query = PersistentIdentifier.query.filter_by(
            pid_type=cls.provider.pid_type
        )
        if not with_deleted:
            query = query.filter_by(status=PIDStatus.REGISTERED)
        return query

    @classmethod
    def get_all_pids(cls, with_deleted=False, limit=100000):
        """Get all records pids. Return a generator iterator."""
        query = cls._get_all(with_deleted=with_deleted)
        if limit:
            count = query.count()
            # slower, less memory
            query = query.order_by(text('pid_value')).limit(limit)
            offset = 0
            while offset < count:
                for identifier in query.offset(offset):
                    yield identifier.pid_value
                offset += limit
        else:
            # faster, more memory
            for identifier in query:
                yield identifier.pid_value

    @classmethod
    def get_all_ids(cls, with_deleted=False, limit=100000):
        """Get all records uuids. Return a generator iterator."""
        query = cls._get_all(with_deleted=with_deleted)
        if limit:
            # slower, less memory
            query = query.order_by(text('pid_value')).limit(limit)
            offset = 0
            count = cls.count(with_deleted=with_deleted)
            while offset < count:
                for identifier in query.limit(limit).offset(offset):
                    yield identifier.object_uuid
                offset += limit
        else:
            # faster, more memory
            for identifier in query:
                yield identifier.object_uuid

    @classmethod
    def count(cls, with_deleted=False):
        """Get record count."""
        return cls._get_all(with_deleted=with_deleted).count()

    def delete(self, force=False, dbcommit=False, delindex=False):
        """Delete record and persistent identifier."""
        can, _ = self.can_delete
        if can or force:
            if delindex:
                self.delete_from_index()
            persistent_identifier = self.get_persistent_identifier(self.id)
            persistent_identifier.delete()
            if force:
                db.session.delete(persistent_identifier)
            self = super().delete(force=force)
            if dbcommit:
                db.session.commit()
            return self
        else:
            raise IlsRecordError.NotDeleted()

    def update(self, data, commit=False, dbcommit=False, reindex=False):
        """Update data for record.

        :param data: a dict data to update the record.
        :param commit: if True push the db transaction.
        :param dbcommit: if True call dbcommit, make the change effective
                         in db.
        :param redindex: reindex the record.
        :returns: the modified record
        """
        if pid := data.get('pid'):
            db_record = self.get_record_by_id(self.id)
            if pid != db_record.pid:
                raise IlsRecordError.PidChange(
                    f'{self.__class__.__name__} changed pid from '
                    f'{db_record.pid} to {pid}')
        record = self

        # TODO: find a way to make extended validations.
        # Add schema if missing.
        schema = data.get('$schema')
        if not schema:
            pid_type = self.provider.pid_type
            schemas = current_app.config.get('RERO_ILS_DEFAULT_JSON_SCHEMA')
            if pid_type in schemas:
                from .utils import get_schema_for_resource
                data['$schema'] = get_schema_for_resource(pid_type)

        super().update(data)
        if commit or dbcommit:
            self.commit()
        if dbcommit:
            record = self.dbcommit(reindex)
            record = self.get_record_by_id(self.id)
        return record

    def replace(self, data, commit=True, dbcommit=False, reindex=False):
        """Replace data in record."""
        new_data = deepcopy(data)
        pid = new_data.get('pid')
        if not pid:
            raise IlsRecordError.PidMissing(f'missing pid={self.pid}')
        self.clear()
        return self.update(
            new_data, commit=commit, dbcommit=dbcommit, reindex=reindex)

    def revert(self, revision_id, reindex=False):
        """Revert the record to a specific revision."""
        persistent_identifier = self.get_persistent_identifier(self.id)
        if persistent_identifier.is_deleted():
            raise IlsRecordError.Deleted()
        self = super().revert(revision_id=revision_id)
        if reindex:
            self.reindex(forceindex=False)
        return self

    def undelete(self, reindex=False):
        """Undelete the record."""
        persistent_identifier = self.get_persistent_identifier(self.id)
        if persistent_identifier.is_deleted():
            with db.session.begin_nested():
                persistent_identifier.status = PIDStatus.REGISTERED
                db.session.add(persistent_identifier)
        else:
            raise IlsRecordError.NotDeleted()

        self = self.revert(self.revision_id - 2, reindex=reindex)
        return self

    def dbcommit(self, reindex=False, forceindex=False):
        """Commit changes to db."""
        db.session.commit()
        if reindex:
            self.reindex(forceindex=forceindex)
        return self

    def reindex(self, forceindex=False):
        """Reindex record."""
        indexer = self.get_indexer_class()
        if forceindex:
            return indexer(version_type="external_gte").index(self)
        else:
            return indexer().index(self)

    def delete_from_index(self):
        """Delete record from index."""
        indexer = self.get_indexer_class()
        try:
            indexer().delete(self)
        except NotFoundError:
            current_app.logger.warning(
                f'Can not delete from index {self.__class__.__name__}'
                f': {self.pid}')

    @property
    def pid(self):
        """Get ils record pid value."""
        return self.get('pid')

    @property
    def persistent_identifier(self):
        """Get Persistent Identifier."""
        return self.get_persistent_identifier(self.id)

    def get_links_to_me(self, get_pids=False):
        """Record links.

        :param get_pids: if True list of linked pids
                         if False count of linked records
        """
        return {}

    def reasons_not_to_delete(self):
        """Record deletion reasons."""
        return {}

    @property
    def can_delete(self):
        """Record can be deleted.

        :return a tuple with True|False and reasons not to delete if False.
        """
        reasons = self.reasons_not_to_delete()
        return len(reasons) == 0, reasons

    @property
    def organisation_pid(self):
        """Get organisation pid for circulation policy."""
        return extracted_data_from_ref(self.get('organisation'))

    @classmethod
    def get_metadata_identifier_names(cls):
        """Get metadata and identifier table names."""
        metadata = cls.model_cls.__tablename__
        identifier = cls.provider.identifier
        return metadata, identifier


class IlsRecordsIndexer(RecordIndexer):
    """Indexing class for ils."""

    record_cls = IlsRecord

    def index(self, record):
        """Indexing a record."""
        return super().index(record, arguments=dict(refresh='true'))

    def delete(self, record):
        """Delete a record.

        :param record: Record instance.
        """
        return super().delete(record, refresh='true')

    def bulk_index(self, record_id_iterator, doc_type=None, index=None):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        self._bulk_op(
            record_id_iterator, op_type='index', doc_type=doc_type,
            index=index)

    def process_bulk_queue(self, es_bulk_kwargs=None, stats_only=True):
        """Process bulk indexing queue.

        :param dict es_bulk_kwargs: Passed to
            :func:`elasticsearch:elasticsearch.helpers.bulk`.
        :param boolean stats_only: if `True` only report number of
            successful/failed operations instead of just number of
            successful and a list of error responses
        """
        with current_celery_app.pool.acquire(block=True) as conn:
            consumer = Consumer(
                connection=conn,
                queue=self.mq_queue.name,
                exchange=self.mq_exchange.name,
                routing_key=self.mq_routing_key,
            )
            req_timeout = current_app.config['INDEXER_BULK_REQUEST_TIMEOUT']

            es_bulk_kwargs = es_bulk_kwargs or {}
            count = bulk(
                self.client,
                self._actionsiter(consumer.iterqueue()),
                stats_only=stats_only,
                request_timeout=req_timeout,
                expand_action_callback=(
                    _es7_expand_action if ES_VERSION[0] >= 7
                    else default_expand_action
                ),
                **es_bulk_kwargs
            )

            consumer.close()

        return self.mq_queue.name, count

    def _get_record_class(self, payload):
        """Get the record class from payload."""
        from .utils import get_record_class_from_schema_or_pid_type

        # take the first defined doc type for finding the class
        pid_type = payload.get('doc_type', 'rec')
        return get_record_class_from_schema_or_pid_type(pid_type=pid_type)

    def _actionsiter(self, message_iterator):
        """Iterate bulk actions.

        :param message_iterator: Iterator yielding messages from a queue.
        """
        for message in message_iterator:
            payload = message.decode()
            try:
                indexer = self._get_record_class(payload).get_indexer_class()
                if payload['op'] == 'delete':
                    yield indexer()._delete_action(payload=payload)
                else:
                    yield indexer()._index_action(payload=payload)
                message.ack()
            except NoResultFound:
                message.reject()
            except Exception:
                message.reject()
                current_app.logger.error(
                    f"Failed to index record {payload.get('id')}",
                    exc_info=True)

    def _index_action(self, payload):
        """Bulk index action.

        :param payload: Decoded message body.
        :return: Dictionary defining an Elasticsearch bulk 'index' action.
        """
        with db.session.begin_nested():
            record = self.record_cls.get_record(payload['id'])
        index, doc_type = self.record_to_index(record)

        arguments = {}
        index = payload.get('index') or index
        body = self._prepare_record(record, index, doc_type, arguments)
        action = {
            '_op_type': 'index',
            '_index': index,
            '_type': doc_type,
            '_id': str(record.id),
            '_version': record.revision_id,
            '_version_type': self._version_type,
            '_source': body
        }
        action.update(arguments)

        return action

    @staticmethod
    def _prepare_record(record, index, doc_type, arguments=None, **kwargs):
        """Prepare record data for indexing.

        :param record: The record to prepare.
        :param index: The Elasticsearch index.
        :param doc_type: The Elasticsearch document type.
        :param arguments: The arguments to send to Elasticsearch upon indexing.
        :param **kwargs: Extra parameters.
        :return: The record metadata.
        """
        if current_app.config['INDEXER_REPLACE_REFS']:
            data = record.replace_refs().dumps()
        else:
            data = record.dumps()

        data['_created'] = pytz.utc.localize(record.created).isoformat() \
            if record.created else None
        data['_updated'] = pytz.utc.localize(record.updated).isoformat() \
            if record.updated else None

        # Allow modification of data prior to sending to Elasticsearch.
        before_record_index.send(
            current_app._get_current_object(),
            json=data,
            record=record,
            index=index,
            doc_type=doc_type,
            arguments={} if arguments is None else arguments,
            **kwargs
        )
        return data
