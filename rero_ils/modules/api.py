# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""API for manipulating records."""

from copy import deepcopy
from uuid import uuid4

from elasticsearch.exceptions import NotFoundError
from flask import current_app
from invenio_db import db
from invenio_indexer import current_record_to_index
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.api import Record
from invenio_search import current_search
from invenio_search.api import RecordsSearch
from sqlalchemy.orm.exc import NoResultFound


class IlsRecordError:
    """Base class for errors in the IlsRecordClass."""

    class Deleted(Exception):
        """IlsRecord is deleted."""

        pass

    class NotDeleted(Exception):
        """IlsRecord is not deleted."""

        pass

    class PidMissing(Exception):
        """IlsRecord pid missing."""

        pass

    class PidChange(Exception):
        """IlsRecord pid change."""

        pass


class IlsRecordsSearch(RecordsSearch):
    """Search Class for ils."""

    class Meta:
        """Search only on item index."""

        index = 'records'

    @classmethod
    def flush(cls):
        """Flush index."""
        current_search.flush_and_refresh(cls.Meta.index)


class IlsRecordIndexer(RecordIndexer):
    """Indexing class for ils."""

    def index(self, record):
        """Indexing a record."""
        return_value = super(IlsRecordIndexer, self).index(record)
        index_name, doc_type = current_record_to_index(record)
        current_search.flush_and_refresh(index_name)
        return return_value

    def delete(self, record):
        """Delete a record.

        :param record: Record instance.
        """
        return_value = super(IlsRecordIndexer, self).delete(record)
        index_name, doc_type = current_record_to_index(record)
        current_search.flush_and_refresh(index_name)
        return return_value


class IlsRecord(Record):
    """ILS Record class."""

    minter = None
    fetcher = None
    provider = None
    object_type = 'rec'
    indexer = IlsRecordIndexer

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
    def get_all_pids(cls, with_deleted=False):
        """Get all records pids."""
        query = PersistentIdentifier.query.filter_by(
            pid_type=cls.provider.pid_type
        )
        if not with_deleted:
            query = query.filter_by(status=PIDStatus.REGISTERED)
        pids = [n.pid_value for n in query]
        return pids

    @classmethod
    def get_all_ids(cls, with_deleted=False):
        """Get all records uuids."""
        query = PersistentIdentifier.query.filter_by(
            pid_type=cls.provider.pid_type
        )
        if not with_deleted:
            query = query.filter_by(status=PIDStatus.REGISTERED)
        uuids = [n.object_uuid for n in query]
        return uuids

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
        if forceindex:
            self.indexer(version_type="external_gte").index(self)
        else:
            self.indexer().index(self)

    def delete_from_index(self):
        """Delete record from index."""
        try:
            self.indexer().delete(self)
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
