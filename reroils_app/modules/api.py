# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 RERO.
#
# reroils-app is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""API for manipulating records."""

from uuid import uuid4

from elasticsearch.exceptions import NotFoundError
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.models import PersistentIdentifier
from invenio_pidstore.resolver import Resolver
from invenio_records.api import Record
from invenio_records.errors import MissingModelError
from invenio_records.models import RecordMetadata


class IlsRecord(Record):
    """ILS Record class."""

    minter = None
    fetcher = None
    provider = None
    object_type = 'rec'

    @classmethod
    def create(cls, data, id_=None, delete_pid=True,
               dbcommit=False, reindex=False, **kwargs):
        """Create a new ils record."""
        assert cls.minter
        if delete_pid and data.get('pid'):
            del(data['pid'])
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
        resolver = Resolver(pid_type=cls.provider.pid_type,
                            object_type=cls.object_type,
                            getter=cls.get_record)
        persistent_identifier, record = resolver.resolve(str(pid))
        return super(IlsRecord, cls).get_record(
            persistent_identifier.object_uuid,
            with_deleted=with_deleted
        )

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
    def get_all_pids(cls):
        """Get all records pids."""
        pids = [n.pid_value for n in PersistentIdentifier.query.filter_by(
            pid_type=cls.provider.pid_type
        )]
        return pids

    @classmethod
    def get_all_ids(cls):
        """Get all records uuids."""
        uuids = [n.object_uuid for n in PersistentIdentifier.query.filter_by(
            pid_type=cls.provider.pid_type
        )]
        return uuids

    def delete(self, force=False, delindex=False):
        """Delete record and persistent identifier."""
        persistent_identifier = self.get_persistent_identifier(self.id)
        persistent_identifier.delete()
        result = super(IlsRecord, self).delete(force=force)
        if delindex:
            self.delete_from_index()
        return result

    def update(self, data, dbcommit=False, reindex=False):
        """Update data for record."""
        super(IlsRecord, self).update(data)
        super(IlsRecord, self).commit()
        if dbcommit:
            self.dbcommit(reindex)
        return self

    def dbcommit(self, reindex=False, forceindex=False):
        """Commit changes to db."""
        db.session.commit()
        if reindex:
            self.reindex(forceindex=forceindex)

    def reindex(self, forceindex=False):
        """Reindex record."""
        if forceindex:
            RecordIndexer(version_type="external_gte").index(self)
        else:
            RecordIndexer().index(self)

    def delete_from_index(self):
        """Delete record from index."""
        try:
            RecordIndexer().delete(self)
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


class RecordWithElements(IlsRecord):
    """Define API for ILSREcords with elements."""

    record = None
    element = None
    elements_list_name = 'elements'
    metadata = None
    model = None

    def dumps(self, **kwargs):
        """Return pure Python dictionary with record metadata."""
        data = super(RecordWithElements, self).dumps(**kwargs)
        data[self.elements_list_name] = \
            [element.dumps() for element in self.elements]
        return data

    def delete(self, force=False, delindex=False):
        """Delete record and all the related elements."""
        assert self.element
        assert self.record
        for element in self.elements:
            self.remove_element(
                element,
                force=force,
                delindex=delindex
            )
        super(RecordWithElements, self).delete(
            force=force,
            delindex=delindex
        )

    def add_element(self, element, dbcommit=False, reindex=False):
        """Add an element."""
        assert self.metadata
        assert self.element
        self.metadata.create(self.model, element.model)
        if dbcommit:
            self.dbcommit()
            if reindex:
                self.reindex(forceindex=True)

    def remove_element(self, element, force=False, delindex=False):
        """Remove an element."""
        assert self.record
        assert self.element
        # TODO nested db operation
        # delete from joining table
        element_id = self.element.provider.pid_identifier
        record_id = self.record.provider.pid_identifier
        sql_model = self.metadata.query.filter_by(
            **{element_id: element.id, record_id: self.id}
        ).first()
        db.session.delete(sql_model)
        db.session.commit()
        # delete element
        to_return = element.delete(force=force, delindex=delindex)
        # reindex record
        self.reindex(forceindex=True)
        return to_return

    @property
    def elements(self):
        """Return an array of elements."""
        if self.model is None:
            raise MissingModelError()

        # retrive all elements in the relation table
        # sorted by elements creation date
        record_id = self.record.provider.pid_identifier
        child = self.metadata.get_child()
        record_elements = self.metadata.query\
            .filter_by(**{record_id: self.id})\
            .join(child)\
            .order_by(RecordMetadata.created)
        to_return = []
        for rec_elem in record_elements:
            element = self.element.get_record_by_id(rec_elem.child_id)
            to_return.append(element)
        return to_return

    @classmethod
    def get_record_by_elementid(cls, id_, with_deleted=False):
        """Retrieve the record by element uuid.

        Raise a database exception if the record does not exist.

        :param id_: record ID.
        :param with_deleted: If `True` then it includes deleted records.
        :returns: The :class:`Record` instance.
        """
        assert cls.element
        element_id = cls.element.provider.pid_identifier
        record_element = cls.metadata.query.filter_by(
            **{element_id: id_}
        ).one()
        return super(RecordWithElements, cls).get_record(
            record_element.parent_id
        )
