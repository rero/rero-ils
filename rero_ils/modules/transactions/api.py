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

"""API for manipulating circulation transactions."""

from uuid import uuid4

from invenio_db import db
from invenio_records.api import Record

from rero_ils.modules.transactions.models import CircTransactions


class CircTransaction(Record):
    """Transaction class."""

    modelcls = CircTransactions

    @classmethod
    def create(cls, json, id=None):
        """Create a new Transaction record."""
        if not id:
            id = str(uuid4())
        record = cls(json)
        record.model = cls.modelcls(json=record, id=id)
        with db.session.begin_nested():
            db.session.add(record.model)
        return record

    @classmethod
    def get_transaction(cls, id_):
        """Retrieve the transaction record by id."""
        with db.session.no_autoflush:
            query = CircTransactions.query.filter_by(id=id_)
            obj = query.one()
            return obj.json

    # TODO: add other circulation transation types
    #       such as delete, update, ...etc
