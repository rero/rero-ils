# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""API for manipulating documents."""

from functools import partial

from invenio_search.api import RecordsSearch

from .models import MefPersonIdentifier
from ..api import IlsRecord
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..providers import Provider

# provider
MefPersonProvider = type(
    'MefPersonProvider',
    (Provider,),
    dict(identifier=MefPersonIdentifier, pid_type='pers')
)
# minter
mef_person_id_minter = partial(id_minter, provider=MefPersonProvider)
# fetcher
mef_person_id_fetcher = partial(id_fetcher, provider=MefPersonProvider)


class MefPersonsSearch(RecordsSearch):
    """Mef person search."""

    class Meta():
        """Meta class."""

        index = 'persons'


class MefPerson(IlsRecord):
    """MefPerson class."""

    minter = mef_person_id_minter
    fetcher = mef_person_id_fetcher
    provider = MefPersonProvider

    @classmethod
    def create_or_update(
        cls,
        data,
        id_=None,
        dbcommit=False,
        reindex=False,
        delete_pid=False,
        **kwargs
    ):
        """Create or update mef person record."""
        pid = data.get('pid')
        record = cls.get_record_by_pid(pid, with_deleted=False)
        if record:
            record.update(data, dbcommit=dbcommit, reindex=reindex)
            return record, 'updated'
        else:
            created_record = cls.create(
                data,
                delete_pid=delete_pid,
                dbcommit=dbcommit,
                reindex=reindex,
            )
            return created_record, 'created'
