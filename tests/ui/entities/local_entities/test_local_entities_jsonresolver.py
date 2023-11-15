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

"""Item JSON Resolver tests."""

import pytest
from invenio_records.api import Record
from jsonref import JsonRefError


def test_local_entities_jsonresolver(local_entity_person2):
    """Test local entity json resolver."""
    rec = Record.create({
        'local_entity': {
            '$ref': 'https://bib.rero.ch/api/local_entities/locent_pers2'
        }
    })
    assert rec.replace_refs().get('local_entity') == {
        'pid': 'locent_pers2',
        'type': 'locent'
    }

    # deleted record
    local_entity_person2.delete()
    with pytest.raises(JsonRefError):
        type(rec)(rec.replace_refs()).dumps()

    # non existing record
    rec = Record.create({
        'local_entity': {'$ref': 'https://bib.rero.ch/api/local_entities/n_e'}
    })
    with pytest.raises(JsonRefError):
        type(rec)(rec.replace_refs()).dumps()
