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

"""Patron transaction JSON Resolver tests."""

import pytest
from invenio_records.api import Record
from jsonref import JsonRefError

from rero_ils.modules.utils import extracted_data_from_ref


def test_patron_transaction_jsonresolver(patron_transaction_overdue_martigny):
    """Test patron_transaction json resolver."""
    rec = Record.create(
        {'patron_transaction': {
            '$ref': 'https://bib.rero.ch/api/patron_transactions/1'
            }
         }
    )
    assert extracted_data_from_ref(rec.get('patron_transaction')) == '1'

    # delete attached events to patron transaction
    for patron_event in patron_transaction_overdue_martigny.events:
        patron_event.delete(dbcommit=True, delindex=True)
    # deleted record
    patron_transaction_overdue_martigny.delete()
    with pytest.raises(JsonRefError):
        type(rec)(rec.replace_refs()).dumps()

    # non existing record
    rec = Record.create(
        {'patron_transaction':
            {
                '$ref': 'https://bib.rero.ch/api/patron_transactions/n_e'}}
    )
    with pytest.raises(JsonRefError):
        type(rec)(rec.replace_refs()).dumps()
