# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

'''patron JSON schema tests.'''

from __future__ import absolute_import, print_function

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def test_required(mef_persons_schema, mef_person_data_tmp):
    '''Test required for patron jsonschemas.'''
    validate(mef_person_data_tmp, mef_persons_schema)

    with pytest.raises(ValidationError):
        validate({}, mef_persons_schema)
        validate(mef_person_data_tmp, mef_persons_schema)

    with pytest.raises(ValidationError):
        validate({
            'pid': 'pers1',
            'viaf_pid': '56597999',
            'sources': [
                'rero',
                'gnd',
                'bnf'
            ]}, mef_persons_schema)
        validate(mef_person_data_tmp, mef_persons_schema)

    with pytest.raises(ValidationError):
        validate({
            '$schema': 'http://ils.rero.ch/schema/persons/'
                       'mef-person-v0.0.1.json',
            'viaf_pid': '56597999',
            'sources': [
                'rero',
                'gnd',
                'bnf'
            ]}, mef_persons_schema)
        validate(mef_person_data_tmp, mef_persons_schema)

    with pytest.raises(ValidationError):
        validate({
            '$schema': 'http://ils.rero.ch/schema/persons/'
                       'mef-person-v0.0.1.json',
            'pid': 'pers1',
            'sources': [
                'rero',
                'gnd',
                'bnf'
            ]}, mef_persons_schema)
        validate(mef_person_data_tmp, mef_persons_schema)

    with pytest.raises(ValidationError):
        validate({
            '$schema': 'http://ils.rero.ch/schema/persons/'
                       'mef-person-v0.0.1.json',
            'pid': 'pers1',
            'viaf_pid': '56597999'
        }, mef_persons_schema)
        validate(mef_person_data_tmp, mef_persons_schema)
