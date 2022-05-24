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


"""Change subjects bf:Organization to bf:Organisation."""

from logging import getLogger

from elasticsearch_dsl.query import Q

from rero_ils.modules.documents.api import Document, DocumentsSearch

LOGGER = getLogger('alembic')

# revision identifiers, used by Alembic.
revision = '0387b753585f'
down_revision = 'ce4923ba5286'
branch_labels = ()
depends_on = None


def upgrade():
    """Change subjects bf:Organization to bf:Organisation."""
    query = DocumentsSearch().filter('bool', should=[
        Q('term', subjects__type='bf:Organization'),
        Q('term', subjects_imported__type='bf:Organization')
    ])

    LOGGER.info(f'Upgrade to {revision}')
    LOGGER.info(f'Documents to change: {query.count()}')
    pids = [hit.pid for hit in query.source('pid').scan()]
    errors = 0
    idx = 0
    for idx, pid in enumerate(pids, 1):
        LOGGER.info(f'{idx} * Change document: {pid}')
        doc = Document.get_record_by_pid(pid)
        for subject in doc.get('subjects', []):
            if subject['type'] == 'bf:Organization':
                subject['type'] = 'bf:Organisation'
        for subjects_imported in doc.get('subjects_imported', []):
            if subjects_imported['type'] == 'bf:Organization':
                subjects_imported['type'] = 'bf:Organisation'
        try:
            doc.update(data=doc, dbcommit=True, reindex=True)
        except Exception as err:
            LOGGER.error(f'\tError: {err}')
            errors += 1
    LOGGER.info(f'Updated: {idx} Errors: {errors}')


def downgrade():
    """Change subjects bf:Organisation to bf:Organization."""
    query = DocumentsSearch().filter('bool', should=[
        Q('bool', must=[
            Q('term', subjects__type='bf:Organisation'),
            Q('exists', field='subjects.preferred_name')
        ]),
        Q('bool', must=[
            Q('term', subjects_imported__type='bf:Organisation'),
            Q('exists', field='subjects_imported.preferred_name')
        ])
    ])
    LOGGER.info(f'Downgrade to {down_revision}')
    LOGGER.info(f'Documents to change: {query.count()}')
    pids = [hit.pid for hit in query.source('pid').scan()]
    errors = 0
    idx = 0
    for idx, pid in enumerate(pids, 1):
        LOGGER.info(f'{idx} * Change document: {pid}')
        doc = Document.get_record_by_pid(pid)
        for subject in doc.get('subjects', []):
            if subject['type'] == 'bf:Organisation':
                subject['type'] = 'bf:Organization'
        for subjects_imported in doc.get('subjects_imported', []):
            if subjects_imported['type'] == 'bf:Organisation':
                subjects_imported['type'] = 'bf:Organization'
        try:
            doc.update(data=doc, dbcommit=True, reindex=True)
        except Exception as err:
            LOGGER.error(f'\tError: {err}')
            errors += 1
    LOGGER.info(f'Updated: {idx} Errors: {errors}')
