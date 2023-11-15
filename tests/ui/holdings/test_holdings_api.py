# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

"""Holding Record tests."""

from __future__ import absolute_import, print_function

import mock
import pytest
from jsonschema.exceptions import ValidationError

from rero_ils.modules.documents.api import Document
from rero_ils.modules.holdings.api import Holding, HoldingsSearch
from rero_ils.modules.holdings.api import holding_id_fetcher as fetcher
from rero_ils.modules.holdings.models import HoldingTypes
from rero_ils.modules.holdings.tasks import \
    delete_standard_holdings_having_no_items


def test_holding_create(db, search, document, org_martigny,
                        loc_public_martigny, item_type_standard_martigny,
                        holding_lib_martigny_data):
    """Test holding creation."""
    next_pid = Holding.provider.identifier.next()
    holding = Holding.create(holding_lib_martigny_data, dbcommit=True,
                             reindex=True, delete_pid=True)
    next_pid += 1
    assert holding == holding_lib_martigny_data
    assert holding.get('pid') == str(next_pid)

    holding = Holding.get_record_by_pid(str(next_pid))
    assert holding == holding_lib_martigny_data

    fetched_pid = fetcher(holding.id, holding)
    assert fetched_pid.pid_value == str(next_pid)
    assert fetched_pid.pid_type == 'hold'

    search = HoldingsSearch()
    es_hit = next(search.filter('term', pid=holding.pid).source('pid').scan())
    holding_record = Holding.get_record_by_pid(es_hit.pid)
    assert holding_record.organisation_pid == org_martigny.get('pid')
    # holdings does not exist
    assert not Holding.get_holdings_type_by_holding_pid('toto')

    # clean created data
    holding.delete(force=True, dbcommit=True, delindex=True)


def test_holding_holding_type(holding_lib_martigny_w_patterns,
                              holding_lib_sion_electronic):
    """Test holdings type."""
    assert holding_lib_martigny_w_patterns.is_serial
    assert holding_lib_sion_electronic.is_electronic


def test_holding_availability(holding_lib_sion_electronic,
                              holding_lib_martigny, item_lib_martigny):
    """Test holding availability."""
    # An electronic holding is always available despite if no item are linked
    assert holding_lib_sion_electronic.is_available()
    # The availability of other holdings type depends on children availability
    assert holding_lib_martigny.is_available() == \
        item_lib_martigny.is_available()


def test_holding_extended_validation(
    client, journal, ebook_5, loc_public_sion, loc_public_martigny,
    item_type_standard_martigny, item_type_online_sion,
    holding_lib_martigny_w_patterns_data, holding_lib_sion_electronic_data
):
    """Test holding extended validation."""
    serial_holding_data = holding_lib_martigny_w_patterns_data

    # TESTING SERIAL HOLDINGS
    #   1. validate correct holding
    #   2. testing next expected date for regular frequencies
    #   3. test multiple note with same type
    #   4. test for unknown document
    #   5. test not allowed field.
    record = Holding.create(serial_holding_data, delete_pid=True)

    record.validate()

    expected_date = record['patterns']['next_expected_date']
    del record['patterns']['next_expected_date']
    with pytest.raises(ValidationError):
        record.validate()
    # reset data with original value
    record['patterns']['next_expected_date'] = expected_date

    record.get('notes').append({'type': 'general_note', 'content': 'note'})
    with pytest.raises(ValidationError) as err:
        record.validate()
    assert 'Can not have multiple notes of the same type' in str(err)
    del record['notes']

    with mock.patch.object(Document, 'get_record_by_pid',
                           mock.MagicMock(return_value=None)), \
         pytest.raises(ValidationError) as err:
        record.validate()
    assert 'Document does not exist' in str(err)

    record['holdings_type'] = HoldingTypes.STANDARD
    assert record['enumerationAndChronology']
    with pytest.raises(ValidationError) as err:
        record.validate()
    assert 'is allowed only for serial holdings' in str(err)

    # TESTING ELECTRONIC HOLDING
    #   1. instantiate electronic holding
    #   2. test electronic holding with enumeration and chronology
    electronic_holding_data = holding_lib_sion_electronic_data
    record = Holding.create(electronic_holding_data, delete_pid=True)
    record.validate()

    record['enumerationAndChronology'] = 'enumerationAndChronology'
    record.validate()


def test_holding_tasks(
        client, holding_lib_martigny, item_lib_martigny, document,
        loc_public_saxon):
    """Test delete standard holdings with no items attached."""
    # move item to a new holdings record by changing its location
    item_lib_martigny['location'] = \
        {'$ref': 'https://bib.rero.ch/api/locations/loc3'}
    item = item_lib_martigny.update(
        item_lib_martigny, dbcommit=True, reindex=True)
    holdings_pid = holding_lib_martigny.pid
    # parent holding has no items and it is not automatically deleted.
    hold = Holding.get_record_by_pid(holdings_pid)
    assert hold
    # execute job to delete standard holdings with no attached items.
    delete_standard_holdings_having_no_items()
    hold = Holding.get_record_by_pid(holdings_pid)
    # holdings no longer exist.
    assert not hold


def test_holdings_properties(holding_lib_martigny_w_patterns, vendor_martigny):
    """Test holding properties."""
    holding = holding_lib_martigny_w_patterns
    assert holding.vendor == vendor_martigny
    assert holding.vendor_pid == vendor_martigny.pid

    assert holding.max_number_of_claims == 2
    assert holding.days_before_first_claim == 7
    assert holding.days_before_next_claim == 7

    holding['_masked'] = True
    assert not holding.is_available()
