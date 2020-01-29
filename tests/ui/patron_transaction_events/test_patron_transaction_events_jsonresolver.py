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

"""Patron transaction event JSON Resolver tests."""

import pytest
from invenio_records.api import Record
from jsonref import JsonRefError


def test_patron_transaction_event_jsonresolver(
        patron_transaction_overdue_event_saxon):
    """Test patron transaction event json resolver."""
    rec = Record.create(
        {'patron_transaction_event': {
            '$ref': 'https://ils.rero.ch/api/patron_transaction_events/1'
            }
         }
    )
    assert rec.replace_refs().get('patron_transaction_event') == {'pid': '1'}

    # deleted record
    patron_transaction_overdue_event_saxon.delete()
    with pytest.raises(JsonRefError):
        rec.replace_refs().dumps()

    # non existing record
    rec = Record.create(
        {'patron_transaction':
            {
                '$ref':
                    'https://ils.rero.ch/api/patron_transaction_events/n_e'}}
    )
    with pytest.raises(JsonRefError):
        rec.replace_refs().dumps()
