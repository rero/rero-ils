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


def test_required(contributions_schema, contribution_person_data_tmp):
    '''Test required for patron jsonschemas.'''
    validate(contribution_person_data_tmp, contributions_schema)

    with pytest.raises(ValidationError):
        validate({}, contributions_schema)
        validate(contribution_person_data_tmp, contributions_schema)

    with pytest.raises(ValidationError):
        validate({
            'pid': 'cont_pers',
            'viaf_pid': '56597999',
            'sources': [
                'rero',
                'gnd'
            ]}, contributions_schema)
        validate(contribution_person_data_tmp, contributions_schema)

    with pytest.raises(ValidationError):
        validate({
            '$schema': 'https://bib.rero.ch/schemas/contributions/'
                       'contribution-v0.0.1.json',
            'viaf_pid': '56597999',
            'sources': [
                'rero',
                'gnd'
            ]}, contributions_schema)
        validate(contribution_person_data_tmp, contributions_schema)

    with pytest.raises(ValidationError):
        validate({
            '$schema': 'https://bib.rero.ch/schemas/contributions/'
                       'contribution-v0.0.1.json',
            'pid': 'cont_pers',
            'viaf_pid': '56597999'
        }, contributions_schema)
        validate(contribution_person_data_tmp, contributions_schema)
