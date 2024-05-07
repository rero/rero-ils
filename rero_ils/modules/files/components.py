# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2024 RERO
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

"""Files components."""

from invenio_records_resources.services.files.components import \
    FileServiceComponent
from invenio_records_resources.services.records.components import \
    ServiceComponent

from rero_ils.modules.documents.api import Document
from rero_ils.modules.libraries.api import Library
from rero_ils.modules.operation_logs.extensions import OperationLogFactory
from rero_ils.modules.operation_logs.logs.api import SpecificOperationLog
from rero_ils.modules.operation_logs.models import OperationLogOperation
from rero_ils.modules.utils import extracted_data_from_ref

from .operations import ReindexDoc, ReindexRecordFile


class OperationLogRecordFactory(OperationLogFactory):
    """Factory to create CURD operation logs."""

    def get_additional_informations(self, record):
        """Get some informations to add into the operation log.

        Subclasses can override this property to add some informations into
        the operation log dictionary.

        :param record: the observed record.
        :return a dict with additional informations.
        """
        data = {}
        if doc := record.get('document'):
            data.setdefault(
                'file', {})['document'] = \
                    SpecificOperationLog._get_document_data(doc)
        if recid := record.get('recid'):
            data.setdefault('file', {})['recid'] = recid
        return data


class OperationLogsComponent(ServiceComponent):
    """Component to create CRUD operation logs."""

    def _create_operation_logs(self, record, operation):
        """Create operation logs.

        :param record: obj - record instance.
        :param operation: str - CRUD operation
        """
        # as the invenio record resource record is different than ILSRecord
        # a wrapper should be created
        class Rec(dict):
            class provider:
                pid_type = 'recid'

        rec = Rec()
        rec['pid'] = record.pid.pid_value
        if library := record.get('metadata', {}).get('library'):
            rec.library_pid = extracted_data_from_ref(library)
            rec.organisation_pid = Library.get_record_by_pid(
                rec.library_pid).organisation_pid
        if document := record.get('metadata', {}).get('document'):
            rec['document'] = Document.get_record_by_pid(
                extracted_data_from_ref(document))
        OperationLogRecordFactory().create_operation_log(rec, operation)

    def create(self, identity, data, record, errors=None, **kwargs):
        """Create handler.

        :param identity: flask principal Identity
        :param data: dict - creation data
        :param record: obj - the created record
        """
        self._create_operation_logs(
            record=record, operation=OperationLogOperation.CREATE)

    def update(self, identity, data, record, **kwargs):
        """Update handler.

        :param identity: flask principal Identity
        :param data: dict - data to update the record
        :param record: obj - the updated record
        """
        self._create_operation_logs(
            record=record, operation=OperationLogOperation.UPDATE)

    def delete(self, identity, record, **kwargs):
        """Delete handler.

        :param identity: flask principal Identity
        :param record: obj - the updated record
        """
        self._create_operation_logs(
            record=record, operation=OperationLogOperation.DELETE)


class OperationLogsFileComponent(FileServiceComponent):
    """Component to create files CRUD operation logs."""

    def _create_operation_logs(
        self, record, file_key, operation, deleted_file=None
    ):
        """Create operation logs.

        :param record: obj - record instance.
        :param file_key: str - file key in the file record.
        :param operation: str - CRUD operation
        :param deleted_file: file instance - the deleted file instance.
        """
        # for deletion the file is not in the record anymore.
        if deleted_file:
            file_metadata = deleted_file.get('metadata', {})
        else:
            file_metadata = record.files.get(file_key).get('metadata', {})

        # only for main files
        if file_metadata.get('type') in ['fulltext', 'thumbnail']:
            return

        # as the invenio record resource record is different than ILSRecord
        # a wrapper should be created
        class Rec(dict):
            class provider:
                pid_type = 'file'

        rec = Rec()
        rec['pid'] = file_key
        if library := record.get('metadata', {}).get('library'):
            rec.library_pid = extracted_data_from_ref(library)
            rec.organisation_pid = Library.get_record_by_pid(
                rec.library_pid).organisation_pid
        if document := record.get('metadata', {}).get('document'):
            rec['document'] = Document.get_record_by_pid(
                extracted_data_from_ref(document))
        rec['recid'] = record['id']
        OperationLogRecordFactory().create_operation_log(
            record=rec, operation=operation)

    def commit_file(self, identity, id_, file_key, record):
        """Commit file handler.

        :param identity: flask principal Identity
        :param id_: str - record file id.
        :param file_key: str - file key in the file record.
        :param record: obj - record instance.
        """
        self._create_operation_logs(
            record, file_key, OperationLogOperation.CREATE)

    def delete_file(self, identity, id_, file_key, record, deleted_file):
        """Delete file handler.

        :param identity: flask principal Identity
        :param id_: str - record file id.
        :param file_key: str - file key in the file record.
        :param record: obj - record instance.
        :param deleted_file: file instance - the deleted file instance.
        """
        self._create_operation_logs(
            record, file_key, OperationLogOperation.DELETE,
            deleted_file=deleted_file)


class ReindexFileComponent(FileServiceComponent):
    """Component to reindex linked resources to the file record."""

    def _register(self, record):
        """Register a document reindex operation.

        :param record: obj - record instance.
        """
        doc_pid = extracted_data_from_ref(record["metadata"]["document"])
        for operation in [ReindexRecordFile(record.id), ReindexDoc(doc_pid)]:
            if operation not in self.uow._operations:
                self.uow.register(operation)

    def commit_file(self, identity, id_, file_key, record):
        """Commit file handler.

        :param identity: flask principal Identity
        :param id_: str - record file id.
        :param file_key: str - file key in the file record.
        :param record: obj - record instance.
        """
        self._register(record)

    def update_file_metadata(self, identity, id_, file_key, record, data):
        """Update file metadata handler.

        :param identity: flask principal Identity
        :param id_: str - record file id.
        :param file_key: str - file key in the file record.
        :param record: obj - record instance.
        :param deleted_file: file instance - the deleted file instance.
        :param data: dict - data to update the record
        """
        self._register(record)

    def delete_file(self, identity, id_, file_key, record, deleted_file):
        """Delete file handler.

        :param identity: flask principal Identity
        :param id_: str - record file id.
        :param file_key: str - file key in the file record.
        :param record: obj - record instance.
        :param deleted_file: file instance - the deleted file instance.
        """
        self._register(record)

    def delete_all_files(self, identity, id_, record, results):
        """Delete all files handler.

        :param identity: flask principal Identity
        :param id_: str - record file id.
        :param record: obj - record instance.
        """
        self._register(record)


class ReindexRecordComponent(FileServiceComponent):
    """Component to reindex linked resources to the file record."""

    def _register(self, record):
        """Register a document reindex operation.

        :param record: obj - record instance.
        """
        doc_pid = extracted_data_from_ref(record["metadata"]["document"])
        for operation in [ReindexDoc(doc_pid)]:
            if operation not in self.uow._operations:
                self.uow.register(operation)

    def create(self, identity, data, record, errors=None, **kwargs):
        """Create handler.

        :param identity: flask principal Identity
        :param data: dict - creation data
        :param record: obj - the created record
        """
        self._register(record)

    def update(self, identity, data, record, **kwargs):
        """Update handler.

        :param identity: flask principal Identity
        :param data: dict - data to update the record
        :param record: obj - the updated record
        """
        self._register(record)

    def delete(self, identity, record, **kwargs):
        """Delete handler.

        :param identity: flask principal Identity
        :param record: obj - the updated record
        """
        self._register(record)
