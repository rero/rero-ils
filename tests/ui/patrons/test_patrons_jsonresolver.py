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

"""Patron JSON Resolver tests."""

import pytest
from invenio_records.api import Record
from jsonref import JsonRefError


def test_patrons_jsonresolver(system_librarian_martigny_no_email):
    """Test patron json resolver."""
    rec = Record.create({
        'patron': {'$ref': 'https://ils.rero.ch/api/patrons/ptrn1'}
    })
    assert rec.replace_refs().get('patron') == {'pid': 'ptrn1'}

    # deleted record
    system_librarian_martigny_no_email.delete()
    with pytest.raises(JsonRefError):
        rec.replace_refs().dumps()

    # non existing record
    rec = Record.create({
        'patron': {'$ref': 'https://ils.rero.ch/api/patrons/n_e'}
    })
    with pytest.raises(JsonRefError):
        rec.replace_refs().dumps()
