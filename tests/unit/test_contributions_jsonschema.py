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

'''patron JSON schema tests.'''

from __future__ import absolute_import, print_function

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def test_required(remote_entities_schema, entity_person_data_tmp):
    '''Test required for patron jsonschemas.'''
    validate(entity_person_data_tmp, remote_entities_schema)

    with pytest.raises(ValidationError):
        validate({}, remote_entities_schema)
        validate(entity_person_data_tmp, remote_entities_schema)

    with pytest.raises(ValidationError):
        validate({
            'pid': 'ent_pers',
            'viaf_pid': '56597999',
            'sources': [
                'rero',
                'gnd'
            ]}, remote_entities_schema)
        validate(entity_person_data_tmp, remote_entities_schema)

    with pytest.raises(ValidationError):
        validate({
            '$schema': 'https://bib.rero.ch/schemas/remote_entities/'
                       'remote_entity-v0.0.1.json',
            'viaf_pid': '56597999',
            'sources': [
                'rero',
                'gnd'
            ]}, remote_entities_schema)
        validate(entity_person_data_tmp, remote_entities_schema)

    with pytest.raises(ValidationError):
        validate({
            '$schema': 'https://bib.rero.ch/schemas/remote_entities/'
                       'remote_entity-v0.0.1.json',
            'pid': 'ent_pers',
            'viaf_pid': '56597999'
        }, remote_entities_schema)
        validate(entity_person_data_tmp, remote_entities_schema)
