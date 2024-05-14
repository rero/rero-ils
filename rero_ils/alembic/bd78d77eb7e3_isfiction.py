# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2024 RERO
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

"""Add fiction."""

from logging import getLogger

from invenio_db import db

from rero_ils.modules.documents.api import Document, DocumentsIndexer, \
    DocumentsSearch
from rero_ils.modules.documents.models import DocumentFictionType

# revision identifiers, used by Alembic.
revision = 'bd78d77eb7e3'
down_revision = ('fc45b1b998b8', 'a941628259e1')
branch_labels = ()
depends_on = None

LOGGER = getLogger('alembic')
DEBUG = False


def dbcommit_and_bulk_index(uuids, idx):
    """DB commit and bulk index.

    :param ids: ids to bulk index.
    :param idx: index.
    :return: empty list.
    """
    if uuids:
        db.session.commit()
        indexer = DocumentsIndexer()
        indexer.bulk_index(uuids)
        count = indexer.process_bulk_queue()
        LOGGER.info(f'{count[1]} records indexed.')
    return []


def upgrade():
    """Upgrade database."""
    # fiction statement: fiction
    FICTIONS_TERMS = ['Fictions', 'Films de fiction']
    query = DocumentsSearch() \
        .filter('terms', facet_genre_form_en=FICTIONS_TERMS) \
        .exclude('exists', field='fiction_statement')
    ids = [hit.meta.id for hit in query.source().scan()]
    LOGGER.info(f'Add fiction_statement="fiction" to documents: {len(ids)}')
    uuids = []
    idx = 0
    for idx, _id in enumerate(ids, 1):
        if doc := Document.get_record(_id):
            uuids.append(_id)
            if DEBUG:
                LOGGER.info(
                    f'{idx:<10} {doc.pid:<10} '
                    'add fiction_statement="fiction"'
                )
            doc['fiction_statement'] = DocumentFictionType.Fiction.value
            doc.update(data=doc, commit=True, dbcommit=False, reindex=False)
            if len(uuids) >= 1000:
                uuids = dbcommit_and_bulk_index(uuids, idx)
    dbcommit_and_bulk_index(uuids, idx)
    # fiction statement: non-fiction
    query = DocumentsSearch() \
        .exclude('term', harvested=True) \
        .exclude('terms', facet_genre_form_en=FICTIONS_TERMS) \
        .exclude('exists', field='fiction_statement') \
        .filter('exists', field='subjects')
    ids = [hit.meta.id for hit in query.source().scan()]
    LOGGER.info(
        f'Add fiction_statement="non_fiction" to documents: {len(ids)}')
    uuids = []
    for idx, _id in enumerate(ids, 1):
        if doc := Document.get_record(_id):
            uuids.append(_id)
            if DEBUG:
                LOGGER.info(
                    f'{idx:<10} {doc.pid:<10} '
                    'add fiction_statement="non_fiction"'
                )
            doc['fiction_statement'] = DocumentFictionType.NonFiction.value
            doc.update(data=doc, commit=True, dbcommit=False, reindex=False)
            if len(uuids) >= 1000:
                uuids = dbcommit_and_bulk_index(uuids, idx)
    dbcommit_and_bulk_index(uuids, idx)
    DocumentsSearch().flush_and_refresh()
    # fiction statement: unspecified
    query = DocumentsSearch() \
        .exclude('exists', field='fiction_statement')
    ids = [hit.meta.id for hit in query.source().scan()]
    LOGGER.info(
        f'Add fiction_statement="unspecified" to documents: {len(ids)}')
    uuids = []
    for idx, _id in enumerate(ids, 1):
        if doc := Document.get_record(_id):
            uuids.append(_id)
            if DEBUG:
                LOGGER.info(
                    f'{idx:<10} {doc.pid:<10} '
                    'add fiction_statement="unspecified"'
                )
            doc['fiction_statement'] = DocumentFictionType.Unspecified.value
            doc.update(data=doc, commit=True, dbcommit=False, reindex=False)
            if len(uuids) >= 1000:
                uuids = dbcommit_and_bulk_index(uuids, idx)
    dbcommit_and_bulk_index(uuids, idx)


def downgrade():
    """Downgrade database."""
    query = DocumentsSearch() \
        .filter('exists', field='fiction_statement')
    ids = [hit.meta.id for hit in query.source().scan()]
    LOGGER.info(f'Remove fiction_statement from documents: {len(ids)}')
    uuids = []
    idx = 0
    for idx, _id in enumerate(ids, 1):
        if doc := Document.get_record(_id):
            uuids.append(_id)
            if DEBUG:
                LOGGER.info(
                    f'{idx:<10} {doc.pid:<10} '
                    'remove fiction_statement'
                )
            doc.pop('fiction_statement', None)
            doc.update(data=doc, commit=True, dbcommit=False, reindex=False)
            if len(uuids) >= 1000:
                uuids = dbcommit_and_bulk_index(uuids, idx)
    dbcommit_and_bulk_index(uuids, idx)
