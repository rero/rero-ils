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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""API tests for non modules."""


from functools import partial

import pytest
from invenio_db import db
from invenio_pidstore.errors import PIDAlreadyExists
from invenio_pidstore.models import PIDStatus, RecordIdentifier
from invenio_pidstore.providers.base import BaseProvider
from invenio_search import current_search
from invenio_search.api import RecordsSearch
from utils import flush_index

from rero_ils.modules.api import IlsRecord, IlsRecordError
from rero_ils.modules.fetchers import id_fetcher
from rero_ils.modules.minters import id_minter


class IdentifierTest(RecordIdentifier):
    """Sequence generator for Test identifiers."""

    __tablename__ = 'test_id'
    __mapper_args__ = {'concrete': True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, 'sqlite'),
        primary_key=True, autoincrement=True,
    )


class SearchTest(RecordsSearch):
    """Test Search."""

    class Meta:
        """Search only on test index."""

        index = 'records-record-v1.0.0'


class ProviderTest(BaseProvider):
    """Test identifier provider."""

    pid_type = 'test'
    """Type of persistent identifier."""

    pid_identifier = IdentifierTest.__tablename__
    """Identifier for table name"""

    pid_provider = None
    """Provider name.

    The provider name is not recorded in the PID since the provider does not
    provide any additional features besides creation of Test ids.
    """

    default_status = PIDStatus.REGISTERED
    """Test IDs are by default registered immediately."""

    @classmethod
    def create(cls, object_type=None, object_uuid=None, **kwargs):
        """Create a new Test identifier."""
        if not kwargs.get('pid_value'):
            kwargs['pid_value'] = str(IdentifierTest.next())
        kwargs.setdefault('status', cls.default_status)
        if object_type and object_uuid:
            kwargs['status'] = PIDStatus.REGISTERED
        return super(ProviderTest, cls).create(
            object_type=object_type, object_uuid=object_uuid, **kwargs
        )


id_minter_test = partial(id_minter, provider=ProviderTest)
id_fetcher_test = partial(id_fetcher, provider=ProviderTest)


class RecordTest(IlsRecord):
    """Test record class."""

    minter = id_minter_test
    fetcher = id_fetcher_test
    provider = ProviderTest


def test_ilsrecord(app, es_default_index, ils_record, ils_record_2):
    """Test IlsRecord update."""
    current_search.delete(ignore=[404])

    # the created records will be acessible in all function of this test file
    record_1 = RecordTest.create(
        data=ils_record,
        dbcommit=True,
        reindex=True
    )
    assert record_1.pid == 'ilsrecord_pid'
    record_2 = RecordTest.create(
        data=ils_record_2,
        dbcommit=True,
        reindex=True,
    )
    assert record_2.pid == 'ilsrecord_pid_2'
    record_created_pid = RecordTest.create(
        data=ils_record,
        reindex=True,
        dbcommit=True,
        delete_pid=True
    )
    assert record_created_pid.pid == '1'
    with pytest.raises(PIDAlreadyExists):
        RecordTest.create(
            data=ils_record,
            dbcommit=True,
            reindex=True
        )
    flush_index(SearchTest.Meta.index)

    """Test IlsRecord."""
    assert sorted(RecordTest.get_all_pids()) == [
        '1', 'ilsrecord_pid', 'ilsrecord_pid_2'
    ]

    """Test IlsRecord update."""
    record = RecordTest.get_record_by_pid('ilsrecord_pid')
    record['name'] = 'name changed'
    record = record.update(record, dbcommit=True)
    assert record['name'] == 'name changed'
    with pytest.raises(IlsRecordError.PidChange):
        record['pid'] = 'pid changed'
        record.update(record, dbcommit=True)

    """Test IlsRecord replace."""
    record = RecordTest.get_record_by_pid('ilsrecord_pid')

    del record['name']
    record = record.replace(record, dbcommit=True)
    assert record.get_links_to_me() == {}
    assert not record.get('name')

    with pytest.raises(IlsRecordError.PidMissing):
        del record['pid']
        record.replace(record, dbcommit=True)

    """Test IlsRecord get pid by id."""
    record = RecordTest.get_record_by_pid('ilsrecord_pid')
    pid = RecordTest.get_pid_by_id(record.id)
    assert pid == record.pid

    """Test IlsRecord revert."""
    record = RecordTest.get_record_by_pid('ilsrecord_pid')
    record = record.revert(record.revision_id - 1)
    assert record.get('name') == 'name changed'

    record.delete()
    with pytest.raises(IlsRecordError.Deleted):
        record = record.revert(record.revision_id - 1)
    record = record.undelete()
    assert record.get('pid') == 'ilsrecord_pid'
    with pytest.raises(IlsRecordError.NotDeleted):
        record = record.undelete()

    """Test IlsRecord es search."""
    search_all = list(
        SearchTest().filter('match_all').source().scan()
    )
    assert len(search_all) == 3
    search = list(
        SearchTest()
        .filter('term', pid='ilsrecord_pid_2')
        .source(includes=['pid'])
        .scan()
    )
    assert search[0]['pid'] == 'ilsrecord_pid_2'

    """Test IlsRecord update."""
    record = RecordTest.get_record_by_pid('ilsrecord_pid')
    record.delete(delindex=True)
    assert len(RecordTest.get_all_pids()) == 2
    assert len(RecordTest.get_all_ids()) == 2
    record = RecordTest.get_record_by_pid('ilsrecord_pid_2')
    record.delete(delindex=True)
    assert len(RecordTest.get_all_pids()) == 1
    assert len(RecordTest.get_all_ids()) == 1
    record = RecordTest.get_record_by_pid('1')
    record.delete(delindex=True)
    assert len(RecordTest.get_all_pids()) == 0
    assert len(RecordTest.get_all_ids()) == 0
