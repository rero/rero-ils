# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Files services."""

from invenio_records.dumpers import SearchDumper
from invenio_records.dumpers.indexedat import IndexedAtDumperExt
from rero_invenio_files.records.services import FileServiceConfig, RecordServiceConfig

from .api import RecordWithFile
from .components import (
    OperationLogsComponent,
    OperationLogsFileComponent,
    ReindexFileComponent,
    ReindexRecordComponent,
)
from .dumpers import FileInformationDumperExt
from .permissions import FilePermissionPolicy
from .results import MainFileList
from .schemas import RecordSchema


class RecordServiceConfig(RecordServiceConfig):
    """File record service."""

    # Record class
    record_cls = RecordWithFile

    # Common configuration
    permission_policy_cls = FilePermissionPolicy

    # Service components
    components = [*RecordServiceConfig.components, OperationLogsComponent, ReindexRecordComponent]

    # Dumper for the indexer
    index_dumper = SearchDumper(extensions=[IndexedAtDumperExt(), FileInformationDumperExt()])

    # Marshmalow schema
    schema = RecordSchema


class RecordFileServiceConfig(FileServiceConfig):
    """Files service configuration."""

    # Record class
    record_cls = RecordWithFile

    file_result_list_cls = MainFileList

    # Common configuration
    permission_policy_cls = FilePermissionPolicy

    class _MaxFilesCount:
        """Descriptor for max_files_count that works on both class and instance access."""

        def __get__(self, obj, objtype=None):
            from flask import current_app

            max_ui_files = current_app.config.get("RERO_ILS_FILES_UI_MAX", 600)
            return max_ui_files * 3 + 100

    max_files_count = _MaxFilesCount()

    # Service components
    components = [*FileServiceConfig.components, ReindexFileComponent, OperationLogsFileComponent]
