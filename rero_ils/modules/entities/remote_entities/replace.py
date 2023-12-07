# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

"""Replace identifiedBy with $ref from MEF."""

import contextlib
from copy import deepcopy
from datetime import datetime, timezone

import requests
from flask import current_app
from sqlalchemy.orm.exc import NoResultFound

from rero_ils.modules.documents.api import Document, DocumentsSearch
from rero_ils.modules.utils import get_mef_url, get_timestamp, \
    requests_retry_session
from rero_ils.modules.utils import set_timestamp as utils_set_timestamp

from .api import RemoteEntity
from ..logger import create_logger


class ReplaceIdentifiedBy(object):
    """Entity replace identifiedBy with $ref.

    Usage example:
    replace_identified_by = ReplaceIdentifiedBy(
        field='contribution',
        dry_run=True,
        verbose=True
    )
    changed, not_found rero_only = replace_identified_by.run()
    # changed: count of changed identifiedBy
    # not_found: count of not found identifiedBy
    # rero_only: count of identifiedBy with RERO reference
    #            (therefore not changed).
    """

    fields = ('contribution', 'subjects', 'genreForm')
    timestamp_name = 'replace_identified_by'

    def __init__(self, field, dry_run=False, verbose=False,
                 log_dir=None):
        """Constructor.

        :param field: field type [contribution, subjects, genreForm]
        :param dry_run: bool - if true the data are not modified
        :param verbose: bool or integer - verbose level
        """
        self.field = field
        self.dry_run = dry_run
        self.verbose = verbose
        self.entity_types = current_app.config['RERO_ILS_ENTITY_TYPES']
        self.logger = create_logger(
            name='ReplaceIdentifiedBy',
            file_name='replace_identifiedby.log',
            log_dir=log_dir,
            verbose=verbose
        )
        self.changed = 0
        self.rero_only = {}
        self.not_found = {}

    def _get_base_url(self, entity_type):
        """Get MEF base URL."""
        if base_url := get_mef_url(entity_type):
            return base_url
        raise KeyError(f'Unable to find MEF base url for {entity_type}')

    def _get_latest(self, entity_type, source, pid):
        """Query the MEF server to retrieve the last MEF for a given entity id.

        :param source: (string) the entity source such as `idref`, `gnd`
        :param pid: (string) the entity identifier.
        :returns: dictionary representing the MEF record.
        :rtype: dictionary.
        """
        url = f'{self._get_base_url(entity_type)}/mef/latest/{source}:{pid}'
        res = requests_retry_session().get(url)
        if res.status_code == requests.codes.ok:
            return res.json()
        self.logger.warning(f'Problem get {url}: {res.status_code}')
        return {}

    def _find_other_source(self, source, mef_data):
        """Find other soure.

        If source is 'rero' try to find other source in mef_data.
        :params source: source type
        :params mef_data: mef data to find other source
        :returns: found source and source pid
        """
        if source in ('idref', 'gnd'):
            return source, mef_data[source]['pid']
        elif source == 'rero':
            for new_source in ('idref', 'gnd'):
                if source_data := mef_data.get(new_source):
                    return new_source, source_data['pid']
        return None, None

    @property
    def query(self):
        """ES query for documents with identifiedBy and entity types."""
        entity_types = list(current_app.config['RERO_ILS_ENTITY_TYPES'].keys())
        return DocumentsSearch() \
            .filter('exists', field=f'{self.field}.entity.identifiedBy') \
            .filter({'terms': {f'{self.field}.entity.type': entity_types}})

    def count(self):
        """Get count of Documents with identifiedBy."""
        return self.query.count()

    def _create_entity(self, mef_type, mef_data):
        """Create entity if not exists.

        :param mef_type: MEF type (agent, concept)
        :param mef_data: MEF data for entity.
        """
        if not RemoteEntity.get_record_by_pid(mef_data['pid']):
            if not self.dry_run:
                new_mef_data = deepcopy(mef_data)
                fields_to_remove = ['$schema', '_created', '_updated']
                for field in fields_to_remove:
                    new_mef_data.pop(field, None)
                # TODO: try to optimize with parent commit and reindex
                #       bulk operation
                RemoteEntity.create(
                    data=new_mef_data,
                    dbcommit=True,
                    reindex=True
                )
            self.logger.info(
                f'Create a new MEF {mef_type} '
                f'record(pid: {mef_data["pid"]})'
            )

    def _do_entity(self, entity, doc_pid):
        """Do entity.

        :param entity: entity to chnage.
        :param doc_pid: document pid.
        :returns: changed
        """
        changed = False
        doc_entity_type = entity['entity']['type']
        self.not_found.setdefault(doc_entity_type, {})
        self.rero_only.setdefault(doc_entity_type, {})
        if mef_type := self.entity_types.get(doc_entity_type):
            source_pid = entity['entity']['identifiedBy']['value']
            source = entity['entity']['identifiedBy']['type'].lower()
            identifier = f'{source}:{source_pid}'
            if (
                identifier in self.not_found[doc_entity_type] or
                identifier in self.rero_only[doc_entity_type]
            ):
                # MEF was not found previously. Do not try it again.
                return None
            if mef_data := self._get_latest(mef_type, source, source_pid):
                new_source, new_source_pid = self._find_other_source(
                    source=source,
                    mef_data=mef_data
                )
                if new_source:
                    mef_entity_type = mef_data.get('type')
                    # verify local and MEF type are the same
                    if mef_entity_type == doc_entity_type:
                        self._create_entity(mef_type, mef_data)
                        authorized_access_point = entity[
                            "entity"]["authorized_access_point"]
                        mef_authorized_access_point = mef_data[
                            new_source]["authorized_access_point"]
                        self.logger.info(
                            f'Replace document:{doc_pid} '
                            f'{self.field} "{authorized_access_point}" - '
                            f'({mef_type}:{mef_data["pid"]}) '
                            f'{new_source}:{new_source_pid} '
                            f'"{mef_authorized_access_point}"'
                        )
                        entity['entity'] = {
                            '$ref': (
                                f'{self._get_base_url(mef_type)}'
                                f'/{new_source}/{new_source_pid}'
                            ),
                            'pid': mef_data['pid']
                        }
                        changed = True
                    else:
                        authorized_access_point = mef_data.get(
                            source, {}).get('authorized_access_point')
                        info = (
                            f'{doc_entity_type} != {mef_entity_type} '
                            f': "{authorized_access_point}"'
                        )
                        self.rero_only[doc_entity_type][identifier] = info
                        self.logger.warning(
                            f'Type differ:{doc_pid} '
                            f'{self.field} - ({mef_type}) {identifier} {info}'
                        )
                else:
                    authorized_access_point = mef_data.get(
                        source, {}).get('authorized_access_point')
                    info = f'{authorized_access_point}'
                    self.rero_only[doc_entity_type][identifier] = info
                    self.logger.info(
                        f'No other source found for document:{doc_pid} '
                        f'{self.field} - ({mef_type}|{doc_entity_type}) '
                        f'{identifier} "{info}"'
                    )
            else:
                authorized_access_point = entity[
                    'entity']['authorized_access_point']
                info = f'{authorized_access_point}'
                self.not_found[doc_entity_type][identifier] = info
                self.logger.info(
                    f'No MEF found for document:{doc_pid} '
                    f' - ({mef_type}) {identifier} "{info}"'
                )
        self.not_found = {k: v for k, v in self.not_found.items() if v}
        self.rero_only = {k: v for k, v in self.rero_only.items() if v}
        return changed

    def _replace_entities_in_document(self, doc_id):
        """Replace identifiedBy with $ref.

        :param doc_id: (string) document id
        """
        changed = False
        with contextlib.suppress(NoResultFound):
            doc = Document.get_record(doc_id)
            entities_to_update = filter(
                lambda c: c.get('entity', {}).get('identifiedBy'),
                doc.get(self.field, {})
            )
            for entity in entities_to_update:
                try:
                    changed = self._do_entity(entity, doc.pid) or changed
                except Exception as err:
                    self.logger.error(
                        f'Error document:{doc.pid} {entity} {err}"'
                    )
            if changed:
                return doc

    def _error_count(self, counter_dict):
        """Summ of error count."""
        return sum(len(values) for values in counter_dict.values())

    def run(self):
        """Replace identifiedBy with $ref."""
        self.changed = 0
        self.not_found = {}
        self.rero_only = {}
        self.logger.info(
                f'Found {self.field} identifiedBy: {self.count()}')
        query = self.query \
                    .params(preserve_order=True) \
                    .sort({'_created': {'order': 'asc'}}) \
                    .source(['pid', self.field])
        for hit in list(query.scan()):
            if doc := self._replace_entities_in_document(hit.meta.id):
                self.changed += 1
                if not self.dry_run:
                    doc.update(data=doc, dbcommit=True, reindex=True)
        self.set_timestamp()
        return self.changed, self._error_count(self.not_found), \
            self._error_count(self.rero_only)

    def get_timestamp(self):
        """Get time stamp."""
        if data := get_timestamp('replace_identified_by'):
            data.pop('name', None)
        return data or {}

    def set_timestamp(self):
        """Set time stamp.

        Dictionary with entity type and count of changed, not found and
        `rero` only records.
        * not found: no entity was found.
        * rero only: entity was found but has only `rero` as source.
        """
        data = self.get_timestamp()
        # Count of changed, not found and rero only records.
        # not found: no entity was found.
        # rero only: entity was found but has only `rero` as source.
        data[self.field] = {
            'changed': self.changed,
            'not found': self._error_count(self.not_found),
            'rero only': self._error_count(self.rero_only),
            'time': datetime.now(timezone.utc),
        }
        utils_set_timestamp(self.timestamp_name, **data)
