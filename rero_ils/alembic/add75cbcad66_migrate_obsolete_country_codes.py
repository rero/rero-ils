# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2023 RERO
# Copyright (C) 2023 UCLouvain
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

"""Migrate obsolete old_country codes."""

from logging import getLogger

from invenio_db import db

from rero_ils.dojson.utils import _OBSOLETE_COUNTRIES_MAPPING
from rero_ils.modules.documents.api import Document, DocumentsSearch
from rero_ils.modules.patrons.api import Patron, PatronsSearch

# TODO: Flask2
# from invenio_userprofiles.models import UserProfile


# revision identifiers, used by Alembic.
revision = 'add75cbcad66'
down_revision = 'e3eb396b39bb'
branch_labels = ()
depends_on = None

LOGGER = getLogger('alembic')


def upgrade():
    """Replace obsolete country codes in resources.

    Change obsolete country codes to valid ones in documents,
    patrons and users.
    """

    def fix_documents(pids, old_country, new_country):
        for pid in pids:
            doc = Document.get_record_by_pid(pid)
            for provision in doc.get('provisionActivity'):
                for place in provision.get('place'):
                    if place.get('country') == old_country:
                        place['country'] = new_country
                        LOGGER.info(
                            f'Doc {pid}: replacing {old_country} by'
                            f' {new_country}')
            doc.replace(doc, commit=True, dbcommit=True, reindex=True)

    def fix_patrons(pids, old_country, new_country):
        for pid in pids:
            ptrn = Patron.get_record_by_pid(pid)
            if address := ptrn.get('second_address', {}):
                if address.get('country') == old_country:
                    address['country'] = new_country
                    LOGGER.info(
                        f'Patron {pid}: replacing {old_country} by'
                        f' {new_country}')
            ptrn.replace(ptrn, commit=True, dbcommit=True, reindex=True)

    def fix_users(query, old_country, new_country):
        for profile in query.all():
            profile.country = new_country
            db.session.merge(profile)
            LOGGER.info(
                f'User {profile.last_name}, {profile.first_name}'
                f': replacing {old_country} by {new_country}')
        db.session.commit()

    for old_country, new_country in _OBSOLETE_COUNTRIES_MAPPING.items():
        LOGGER.info(f'Processing {old_country}')

        if doc_pids := [
            hit.pid for hit in DocumentsSearch()
            .filter('term', provisionActivity__place__country=old_country)
            .source('pid').scan()
        ]:
            LOGGER.info(f'Found {len(doc_pids)} documents with {old_country}.')
            fix_documents(doc_pids, old_country, new_country)

        if ptrn_pids := [
            hit.pid for hit in PatronsSearch()
            .filter('term', second_address__country=old_country)
            .source('pid').scan()
        ]:
            LOGGER.info(f'Found {len(ptrn_pids)} patrons with {old_country}.')
            fix_patrons(ptrn_pids, old_country, new_country)

        # query = UserProfile.query.filter_by(country=old_country)
        # if query.count() > 0:
        #     LOGGER.info(f'Found {query.count()} users with {old_country}.')
        #     fix_users(query, old_country, new_country)


def downgrade():
    """Downgrade database."""
    # Nothing to do, valid country codes are still valid in previous versions.
