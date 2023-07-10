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

"""API for manipulating remote entities."""

import contextlib
from functools import partial

from elasticsearch_dsl.query import Q
from flask import current_app
from invenio_db import db
from urllib3.exceptions import HTTPError

from rero_ils.modules.api import IlsRecordsIndexer, IlsRecordsSearch
from rero_ils.modules.documents.api import DocumentsIndexer
from rero_ils.modules.fetchers import id_fetcher
from rero_ils.modules.minters import id_minter
from rero_ils.modules.providers import Provider

from .models import EntityUpdateAction, RemoteEntityIdentifier, \
    RemoteEntityMetadata
from .utils import extract_data_from_mef_uri, get_mef_data_by_type
from ..api import Entity
from ..dumpers import indexer_dumper, replace_refs_dumper
from ..models import EntityResourceType

# provider
RemoteEntityProvider = type(
    'EntityProvider',
    (Provider,),
    dict(identifier=RemoteEntityIdentifier, pid_type='rement')
)
# minter
remote_entity_id_minter = partial(id_minter, provider=RemoteEntityProvider)
# fetcher
remote_entity_id_fetcher = partial(id_fetcher, provider=RemoteEntityProvider)


class RemoteEntitiesSearch(IlsRecordsSearch):
    """Mef contribution search."""

    class Meta:
        """Meta class."""

        index = 'remote_entities'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class RemoteEntity(Entity):
    """Mef contribution class."""

    minter = remote_entity_id_minter
    fetcher = remote_entity_id_fetcher
    provider = RemoteEntityProvider
    model_cls = RemoteEntityMetadata
    enable_jsonref = False  # disable legacy replace refs

    @classmethod
    def get_entity(cls, ref_type, ref_pid):
        """Get entity based on type and id.

        In case of multiple entity, we will return the most recent created.

        :param ref_type: the type of identifier (mef, viaf, ...)
        :param ref_pid: the identifier to search.
        :returns: the corresponding `Entity` if exists.
        """
        if ref_type == 'mef':
            return cls.get_record_by_pid(ref_pid)

        es_filter = Q('term', **{f'{ref_type}.pid': ref_pid})
        if ref_type == 'viaf':
            es_filter = Q('term', viaf_pid=ref_pid)
        query = RemoteEntitiesSearch() \
            .params(preserve_order=True) \
            .sort({'_created': {'order': 'desc'}}) \
            .filter(es_filter)
        with contextlib.suppress(StopIteration):
            pid = next(query.source('pid').scan()).pid
            return cls.get_record_by_pid(pid)

    @classmethod
    def get_record_by_ref(cls, ref):
        """Get a record from DB.

        If the record dos not exist get it from MEF and create it.

        :param ref: MEF URI
        :returns: the corresponding `Entity` class instance ; if entity has
            loaded from remote server.
        :rtype: tuple(`Entity`, bool)
        """
        online = False
        entity_type, ref_type, ref_pid = extract_data_from_mef_uri(ref)
        if entity := cls.get_entity(ref_type, ref_pid):
            return entity, online

        # Corresponding entity isn't found into database.
        #   1) Get it from remote MEF server
        #   2) Create the entity from remote data
        nested = db.session.begin_nested()
        try:
            data = get_mef_data_by_type(
                entity_type=entity_type, pid_type=ref_type, pid=ref_pid)
            if not data:
                raise HTTPError('', 404, "Not found")
            # Try to get the contribution from DB maybe it was not indexed.
            if entity := RemoteEntity.get_record_by_pid(data['pid']):
                entity = entity.replace(data)
            else:
                entity = cls.create(data)
            online = True
            nested.commit()
            # TODO: reindex in the document indexing
            entity.reindex()
        except Exception as err:
            nested.rollback()
            current_app.logger.error(
                f'Get MEF record: {ref_type}:{ref_pid} >>{err}<<'
            )
            entity = None
        return entity, online

    @property
    def resource_type(self):
        """Get entity type."""
        return EntityResourceType.REMOTE

    @property
    def type(self):
        """Get entity type."""
        entity_types = current_app.config['RERO_ILS_ENTITY_TYPES']
        return entity_types.get(self['type'])

    def resolve(self):
        """Resolve references data.

        Uses the dumper to do the job.
        Mainly used by the `resolve=1` URL parameter.

        :returns: a fresh copy of the resolved data.
        """
        # DEV NOTES :: Why using `replace_refs_dumper`
        #   Not really required now (because no $ref relation exists into an
        #   entity resource) but in next development, links between entity will
        #   be implemented.
        #   The links will be stored as a `$ref` and `replace_refs_dumper`
        #   will be used.
        return self.dumps(replace_refs_dumper)

    def get_authorized_access_point(self, language):
        """Get localized authorized_access_point.

        :param language: language for authorized access point.
        :returns: authorized access point in given language.
        """
        return self._get_mef_localized_value(
            key='authorized_access_point',
            language=language
        )

    def update_online(self, dbcommit=False, reindex=False, verbose=False,
                      reindex_doc=True):
        """Update record online.

        :param reindex: reindex record by record
        :param dbcommit: commit record to database
        :param verbose: verbose print
        :param reindex_doc: is the related document should be reindex ?
        :return: updated record status and updated record
        """
        action = EntityUpdateAction.UPTODATE
        pid = self.get('pid')
        try:
            if data := get_mef_data_by_type(
                    entity_type=self.type,
                    pid_type='mef',
                    pid=pid,
                    verbose=verbose):
                data['$schema'] = self['$schema']
                if data.get('deleted'):
                    current_app.logger.warning(
                        f'UPDATE ONLINE {self.type} (pid:{pid}): was deleted')
                    action = EntityUpdateAction.ERROR
                elif not data.get('sources'):
                    current_app.logger.warning(
                        f'UPDATE ONLINE {self.type} (pid:{pid}): '
                        f'has no sources'
                    )
                    action = EntityUpdateAction.ERROR
                elif not data.get('type'):
                    current_app.logger.warning(
                        f'UPDATE ONLINE {self.type} (pid:{pid}): has no type')
                    action = EntityUpdateAction.ERROR
                elif dict(self) != data:
                    action = EntityUpdateAction.REPLACE
                    self.replace(data=data, dbcommit=dbcommit, reindex=reindex)
                    if reindex and reindex_doc:
                        indexer = DocumentsIndexer()
                        indexer.bulk_index(self.documents_ids())
                        indexer.process_bulk_queue()
        except Exception as err:
            action = EntityUpdateAction.ERROR
            current_app.logger.warning(f'UPDATE ONLINE {pid}: {err}')
        return action, self

    def source_pids(self):
        """Get agents pids."""
        sources = current_app.config.get('RERO_ILS_AGENTS_SOURCES', [])
        return {
            source: self[source]['pid']
            for source in sources
            if source in self
        }

    def _get_mef_localized_value(self, key, language):
        """Get the 1st localized value for given key among MEF source list."""
        order = current_app.config.get('RERO_ILS_AGENTS_LABEL_ORDER', [])
        source_order = order.get(language, order.get(order['fallback'], []))
        for source in source_order:
            if value := self.get(source, {}).get(key, None):
                return value
        return self.get(key, None)


class RemoteEntitiesIndexer(IlsRecordsIndexer):
    """Entity indexing class."""

    record_cls = RemoteEntity
    record_dumper = indexer_dumper

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='rement')
