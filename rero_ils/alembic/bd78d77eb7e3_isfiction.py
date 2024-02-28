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

from rero_ils.modules.documents.api import Document, DocumentsSearch

# revision identifiers, used by Alembic.
revision = 'bd78d77eb7e3'
down_revision = ('fc45b1b998b8', 'a941628259e1')
branch_labels = ()
depends_on = None

LOGGER = getLogger('alembic')


def upgrade():
    """Upgrade database."""
    FICTIONS_TERMS = ['Fictions', 'Films de fiction']
    query = DocumentsSearch() \
        .filter('terms', facet_genre_form_en=FICTIONS_TERMS)
    ids = [hit.meta.id for hit in query.source().scan()]
    LOGGER.info(f'Add fiction=true to documents: {len(ids)}')
    for idx, _id in enumerate(ids, 1):
        if (doc := Document.get_record(_id)):
            if not doc.get('fiction'):
                LOGGER.info(f'{idx:<10} {doc.pid:<10} add fiction=true')
                doc['fiction'] = True
                doc.update(data=doc, dbcommit=True, reindex=True)
    query = DocumentsSearch() \
        .exclude('term', harvested=True) \
        .exclude('terms', facet_genre_form_en=FICTIONS_TERMS) \
        .filter('exists', field='subjects')
    ids = [hit.meta.id for hit in query.source().scan()]
    LOGGER.info(f'Add fiction=False to documents: {len(ids)}')
    for idx, _id in enumerate(ids, 1):
        if doc := Document.get_record(_id):
            if not doc.get('fiction'):
                LOGGER.info(f'{idx:<10} {doc.pid:<10} add fiction=false')
                doc['fiction'] = False
                doc.update(data=doc, dbcommit=True, reindex=True)


def downgrade():
    """Downgrade database."""
    query = DocumentsSearch() \
        .filter('exists', field='fiction')
    ids = [hit.meta.id for hit in query.source().scan()]
    LOGGER.info(f'Remove fiction from documents: {len(ids)}')
    for idx, _id in enumerate(ids, 1):
        if doc := Document.get_record(_id):
            LOGGER.info(f'{idx:<10} {doc.pid:<10} pop fiction')
            doc.pop('fiction', None)
            doc.update(data=doc, dbcommit=True, reindex=True)
