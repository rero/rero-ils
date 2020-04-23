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

"""API for manipulating records."""

from copy import deepcopy
from uuid import uuid4

import pytz
from elasticsearch.exceptions import NotFoundError
from flask import current_app
from invenio_db import db
from invenio_indexer import current_record_to_index
from invenio_indexer.api import RecordIndexer
from invenio_indexer.signals import before_record_index
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.api import Record
from invenio_records_rest.utils import obj_or_import_string
from invenio_search import current_search
from invenio_search.api import RecordsSearch
from sqlalchemy.orm.exc import NoResultFound

from .errors import RecordValidationError


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


class IlsRecordsSearch(RecordsSearch):
    """Search Class for ils."""

    class Meta:
        """Search only on item index."""

        index = 'records'
        doc_types = None

    @classmethod
    def flush(cls):
        """Flush index."""
        current_search.flush_and_refresh(cls.Meta.index)


class IlsRecord(Record):
    """ILS Record class."""

    minter = None
    fetcher = None
    provider = None
    object_type = 'rec'

    @classmethod
    def get_indexer_class(cls):
        """Get the indexer from config."""
        try:
            indexer = obj_or_import_string(
                current_app.config['RECORDS_REST_ENDPOINTS'][
                    cls.provider.pid_type
                ]['indexer_class']
            )
        except:
            # provide default indexer if no indexer is defined in config.
            indexer = IlsRecordsIndexer
        return indexer

    def validate(self, **kwargs):
        """Validate record against schema.

        and extended validation per record class.
        """
        super(IlsRecord, self).validate(**kwargs)
        validation_message = self.extended_validation(**kwargs)
        if validation_message is not True:
            raise RecordValidationError(validation_message)

    def extended_validation(self, **kwargs):
        """Returns reasons for validation failures, otherwise True.

        Override this function for classes that require extended validations
        """
        return True

    @classmethod
    def create(cls, data, id_=None, delete_pid=False,
               dbcommit=False, reindex=False, **kwargs):
        """Create a new ils record."""
        assert cls.minter
        if '$schema' not in data:
            type = cls.provider.pid_type
            schemas = current_app.config.get('RECORDS_JSON_SCHEMA')
            if type in schemas:
                data_schema = {
                    'base_url': current_app.config.get(
                        'RERO_ILS_APP_BASE_URL'
                    ),
                    'schema_endpoint': current_app.config.get(
                        'JSONSCHEMAS_ENDPOINT'
                    ),
                    'schema': schemas[type]
                }
                data['$schema'] = '{base_url}{schema_endpoint}{schema}'\
                    .format(**data_schema)
        if delete_pid and data.get('pid'):
            del data['pid']
        if not id_:
            id_ = uuid4()
        cls.minter(id_, data)
        record = super(IlsRecord, cls).create(data=data, id_=id_, **kwargs)
        if dbcommit:
            record.dbcommit(reindex)
        return record

    @classmethod
    def get_record_by_pid(cls, pid, with_deleted=False):
        """Get ils record by pid value."""
        assert cls.provider
        try:
            persistent_identifier = PersistentIdentifier.get(
                cls.provider.pid_type,
                pid
            )
            return super(IlsRecord, cls).get_record(
                persistent_identifier.object_uuid,
                with_deleted=with_deleted
            )
        except NoResultFound:
            return None
        except PIDDoesNotExistError:
            return None

    @classmethod
    def get_pid_by_id(cls, id):
        """Get pid by uuid."""
        persistent_identifier = cls.get_persistent_identifier(id)
        return str(persistent_identifier.pid_value)

    @classmethod
    def get_record_by_id(cls, id, with_deleted=False):
        """Get ils record by uuid."""
        return super(IlsRecord, cls).get_record(id, with_deleted=with_deleted)

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
    def get_all_pids(cls, with_deleted=False):
        """Get all records pids. Return a generator iterator."""
        query = cls._get_all(with_deleted=with_deleted)
        for identifier in query:
            yield identifier.pid_value

    @classmethod
    def get_all_ids(cls, with_deleted=False):
        """Get all records uuids. Return a generator iterator."""
        query = cls._get_all(with_deleted=with_deleted)
        for identifier in query:
            yield identifier.object_uuid

    @classmethod
    def count(cls, with_deleted=False):
        """Get record count."""
        return cls._get_all(with_deleted=with_deleted).count()

    def delete(self, force=False, dbcommit=False, delindex=False):
        """Delete record and persistent identifier."""
        if self.can_delete:
            persistent_identifier = self.get_persistent_identifier(self.id)
            persistent_identifier.delete()
            self = super(IlsRecord, self).delete(force=force)
            if dbcommit:
                self.dbcommit()
            if delindex:
                self.delete_from_index()
            return self
        else:
            raise IlsRecordError.NotDeleted()

    def update(self, data, dbcommit=False, reindex=False):
        """Update data for record."""
        pid = data.get('pid')
        if pid:
            db_record = self.get_record_by_id(self.id)
            if pid != db_record.pid:
                raise IlsRecordError.PidChange(
                    'changed pid from {old_pid} to {new_pid}'.format(
                        old_pid=self.pid,
                        new_pid=pid
                    )
                )

        super(IlsRecord, self).update(data)
        if dbcommit:
            self = super(IlsRecord, self).commit()
            self.dbcommit(reindex)
        return self

    def replace(self, data, dbcommit=False, reindex=False):
        """Replace data in record."""
        new_data = deepcopy(data)
        pid = new_data.get('pid')
        if not pid:
            raise IlsRecordError.PidMissing(
                'missing pid={pid}'.format(pid=self.pid)
            )
        self.clear()
        self = self.update(new_data, dbcommit=dbcommit, reindex=reindex)
        return self

    def revert(self, revision_id, reindex=False):
        """Revert the record to a specific revision."""
        persistent_identifier = self.get_persistent_identifier(self.id)
        if persistent_identifier.is_deleted():
            raise IlsRecordError.Deleted()
        self = super(IlsRecord, self).revert(revision_id=revision_id)
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

    def reindex(self, forceindex=False):
        """Reindex record."""
        indexer = self.get_indexer_class()
        if forceindex:
            indexer(version_type="external_gte").index(self)
        else:
            indexer().index(self)

    def delete_from_index(self):
        """Delete record from index."""
        indexer = self.get_indexer_class()
        try:
            indexer().delete(self)
        except NotFoundError:
            pass

    @property
    def pid(self):
        """Get ils record pid value."""
        return self.get('pid')

    @property
    def persistent_identifier(self):
        """Get Persistent Identifier."""
        return self.get_persistent_identifier(self.id)

    def get_links_to_me(self):
        """Record links."""
        return {}

    def reasons_not_to_delete(self):
        """Record deletion reasons."""
        return {}

    @property
    def can_delete(self):
        """Record can be deleted."""
        return len(self.reasons_not_to_delete()) == 0

    @property
    def organisation_pid(self):
        """Get organisation pid for circulation policy."""
        if self.get('organisation'):
            return self.replace_refs()['organisation']['pid']
        return None


class IlsRecordsIndexer(RecordIndexer):
    """Indexing class for ils."""

    record_cls = IlsRecord

    def index(self, record):
        """Indexing a record."""
        return_value = super(IlsRecordsIndexer, self).index(record)
        index_name, doc_type = current_record_to_index(record)
        # TODO: Do we need to flush everytime the ES index?
        # Tests depends on this at the moment.
        current_search.flush_and_refresh(index_name)
        return return_value

    def delete(self, record):
        """Delete a record.

        :param record: Record instance.
        """
        return_value = super(IlsRecordsIndexer, self).delete(record)
        index_name, doc_type = current_record_to_index(record)
        current_search.flush_and_refresh(index_name)
        return return_value

    def bulk_index(self, record_id_iterator, doc_type=None):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        self._bulk_op(record_id_iterator, op_type='index', doc_type=doc_type)

    def _get_record_class(self, payload):
        """Get the record class from payload."""
        # take the first defined doc type for finding the class
        pid_type = payload.get('doc_type', 'rec')
        record_class = obj_or_import_string(
            current_app.config.get('RECORDS_REST_ENDPOINTS').get(
                pid_type
            ).get('record_class', Record)
        )
        return record_class

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
                    "Failed to index record {id}".format(id=payload.get('id')),
                    exc_info=True)

    def _index_action(self, payload):
        """Bulk index action.

        :param payload: Decoded message body.
        :returns: Dictionary defining an Elasticsearch bulk 'index' action.
        """
        record = self.record_cls.get_record(payload['id'])
        index, doc_type = self.record_to_index(record)

        arguments = {}
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
        :returns: The record metadata.
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
