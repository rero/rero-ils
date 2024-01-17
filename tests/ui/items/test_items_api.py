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

"""Items Record tests."""

from __future__ import absolute_import, print_function

from copy import deepcopy
from datetime import datetime, timedelta

import pytest
from jsonschema.exceptions import ValidationError

from rero_ils.modules.item_types.api import ItemType
from rero_ils.modules.items.api import Item, ItemsSearch, item_id_fetcher
from rero_ils.modules.items.models import ItemIssueStatus, ItemStatus, \
    TypeOfItem
from rero_ils.modules.items.utils import item_location_retriever, \
    item_pid_to_object
from rero_ils.modules.utils import get_ref_for_pid


def test_obsolete_temporary_item_types_and_locations(
        item_lib_martigny, item_type_on_site_martigny):
    """Test obsolete temporary_item_types and temporary_locations."""
    item = item_lib_martigny
    # First test - No items has temporary_item_type
    items = Item.get_items_with_obsolete_temporary_item_type_or_location()
    assert not len(list(items))
    # Second test - add an infinite temporary_item_type to an item
    item['temporary_item_type'] = {
        '$ref': get_ref_for_pid('itty', item_type_on_site_martigny.pid)
    }
    item.update(item, dbcommit=True, reindex=True)
    items = Item.get_items_with_obsolete_temporary_item_type_or_location()
    assert not len(list(items))
    # Third test - add an expiration date in the future for the temporary
    # item_type
    over_2_days = datetime.now() + timedelta(days=2)
    item['temporary_item_type']['end_date'] = over_2_days.strftime('%Y-%m-%d')
    item.update(data=item, dbcommit=True, reindex=True)
    items = Item.get_items_with_obsolete_temporary_item_type_or_location()
    assert not len(list(items))

    # Fourth test - check obsolete with for a specified date in the future
    over_3_days = datetime.now() + timedelta(days=3)
    items = Item.get_items_with_obsolete_temporary_item_type_or_location(
        end_date=over_3_days)
    assert len(list(items)) == 1

    # reset the item to original values
    del item['temporary_item_type']
    item.update(data=item, dbcommit=True, reindex=True)


def test_item_organisation_pid(client, org_martigny, item_lib_martigny):
    """Test organisation pid has been added during the indexing."""
    search = ItemsSearch()
    item = next(search.filter('term', pid=item_lib_martigny.pid).scan())
    assert item.organisation.pid == org_martigny.pid


def test_item_item_location_retriever(item_lib_martigny, loc_public_martigny,
                                      loc_restricted_martigny):
    """Test location retriever for invenio-circulation."""
    assert item_location_retriever(item_pid_to_object(
        item_lib_martigny.pid)) == loc_public_martigny.pid


def test_item_get_items_pid_by_document_pid(document, item_lib_martigny):
    """Test get items by document pid."""
    assert len(list(Item.get_items_pid_by_document_pid(document.pid))) == 1


def test_item_create(item_lib_martigny_data_tmp, item_lib_martigny):
    """Test itemanisation creation."""
    item = Item.create(item_lib_martigny_data_tmp, delete_pid=True)
    assert item == item_lib_martigny_data_tmp
    assert item.can_delete == (True, {})

    item = Item.get_record_by_pid(item.pid)
    item_lib_martigny_data_tmp['pid'] = '1'
    assert item == item_lib_martigny_data_tmp

    fetched_pid = item_id_fetcher(item.id, item)
    assert fetched_pid.pid_value == '1'
    assert fetched_pid.pid_type == 'item'


def test_item_extended_validation(client, holding_lib_martigny_w_patterns):
    """Test item extended validation in relation with its parent holding."""
    data = {
        '$schema': 'https://bib.rero.ch/schemas/items/item-v0.0.1.json',
        'type': 'issue',
        'document': {
            '$ref': 'https://bib.rero.ch/api/documents/doc4'
        },
        'call_number': '00001',
        'location': {
            '$ref': 'https://bib.rero.ch/api/locations/loc1'
        },
        'item_type': {
            '$ref': 'https://bib.rero.ch/api/item_types/itty1'
        },
        'holding': {
            '$ref': 'https://bib.rero.ch/api/holdings/holding5'
        },
        'status': ItemStatus.ON_SHELF,
        'enumerationAndChronology': 'irregular_issue',
        'issue': {
            'status': ItemIssueStatus.RECEIVED,
            'received_date': datetime.now().strftime('%Y-%m-%d'),
            'expected_date': datetime.now().strftime('%Y-%m-%d'),
            'regular': False
        }
    }
    Item.create(data, dbcommit=True, reindex=True, delete_pid=True)

    # TODO: check why system is not raising validation error here
    # # can not have a standard item with issues on a serial holdings
    # data['type'] = 'standard'
    # with pytest.raises(ValidationError):
    #     Item.create(data, dbcommit=True, reindex=True, delete_pid=True)
    # data['type'] == 'issue'
    # data.pop('issue')
    # # can not create an issue item without issues on a serial holdings
    # with pytest.raises(ValidationError):
    #     Item.create(data, dbcommit=True, reindex=True, delete_pid=True)


def test_extended_validation_unique_barcode(item_lib_martigny, item_lib_fully,
                                            item_lib_martigny_data_tmp,
                                            lib_martigny):
    """Test that a barcode must be unique"""
    # check that own barcode doesn't fail validation on item update
    assert item_lib_martigny.update(item_lib_martigny)

    # check that an item cannot be updated with an already existing barcode
    item_lib_martigny['barcode'] = 'duplicate'
    item_lib_martigny.update(item_lib_martigny, dbcommit=True, reindex=True)
    item_lib_fully['barcode'] = 'duplicate'
    with pytest.raises(ValidationError) as err:
        item_lib_fully.update(item_lib_fully)
    assert 'already taken' in str(err)

    # check that an item with an already existing barcode cannot be created
    item_lib_martigny_data_tmp = deepcopy(item_lib_martigny_data_tmp)
    item_lib_martigny_data_tmp['barcode'] = 'duplicate'
    with pytest.raises(ValidationError) as err:
        Item.create(item_lib_martigny_data_tmp, delete_pid=True)
    assert 'already taken' in str(err)


def test_items_new_acquisition(item_lib_martigny):
    """Test acquisition date behavior."""
    item = item_lib_martigny

    # test 'is_new_acquisition' property
    #  --> not yet a new acquisition
    acq_date = datetime.now() + timedelta(days=1)
    item['acquisition_date'] = acq_date.strftime('%Y-%m-%d')
    assert not item.is_new_acquisition

    # --> Without acq_date, this will be never a new acq
    del item['acquisition_date']
    assert not item.is_new_acquisition

    # --> there is an acq_date and this date is now past
    acq_date = datetime.now() - timedelta(days=1)
    item['acquisition_date'] = acq_date.strftime('%Y-%m-%d')
    assert item.is_new_acquisition


def test_replace_refs(item_lib_martigny, item_type_on_site_martigny):
    """Test specific replace_refs for items."""
    item_lib_martigny['temporary_item_type'] = {
        '$ref': get_ref_for_pid('itty', item_type_on_site_martigny.pid),
        'end_date': '2020-12-31'
    }
    assert 'end_date' in item_lib_martigny.replace_refs().\
        get('temporary_item_type')


def test_item_type_circulation_category_pid(item_lib_martigny,
                                            item_type_on_site_martigny):
    """Test item_type circulation category pid."""
    assert item_lib_martigny.item_type_pid == \
        item_lib_martigny.item_type_circulation_category_pid

    past_2_days = datetime.now() - timedelta(days=2)
    over_2_days = datetime.now() + timedelta(days=2)

    # add an obsolete temporary item_type end_date :: In this case, the
    # circulation item_type must be the default item_type
    item_lib_martigny['temporary_item_type'] = {
        '$ref': get_ref_for_pid('itty', item_type_on_site_martigny.pid),
        'end_date': past_2_days.strftime('%Y-%m-%d')
    }
    assert item_lib_martigny.item_type_pid == \
        item_lib_martigny.item_type_circulation_category_pid

    # add a valid temporary item_type end_date :: In this case, the
    # circulation item_type must be the temporary item_type
    item_lib_martigny['temporary_item_type']['end_date'] = \
        over_2_days.strftime('%Y-%m-%d')
    assert item_type_on_site_martigny.pid == \
        item_lib_martigny.item_type_circulation_category_pid

    # removing any temporary item_type end_date :: In this case, the
    # circulation item_type must be the temporary item_type
    del item_lib_martigny['temporary_item_type']['end_date']
    assert item_type_on_site_martigny.pid == \
        item_lib_martigny.item_type_circulation_category_pid

    # reset the object with default value
    del item_lib_martigny['temporary_item_type']


def test_items_availability(item_type_missing_martigny,
                            item_type_standard_martigny,
                            item_lib_martigny_data_tmp, loc_public_martigny,
                            lib_martigny, org_martigny, document):
    """Test availability for an item."""

    # Create a temporary item with correct data for the test
    item_data = deepcopy(item_lib_martigny_data_tmp)
    del item_data['pid']
    item_data['barcode'] = 'TEST_AVAILABILITY'
    item_data['temporary_item_type'] = {
        '$ref': get_ref_for_pid(ItemType, item_type_missing_martigny.pid)
    }
    item = Item.create(item_data, dbcommit=True, reindex=True)

    # test the availability and availability_text
    assert not item.is_available()
    assert len(item.availability_text) == \
        len(item_type_missing_martigny.get('displayed_status', [])) + 1

    del item['temporary_item_type']
    item = item.update(item, dbcommit=True, reindex=True)
    assert item.is_available()
    assert len(item.availability_text) == 1  # only default value

    # test availabilty by item status
    item['status'] = ItemStatus.IN_TRANSIT
    item = item.update(item, dbcommit=True, reindex=True)
    assert not item.is_available()
    assert item.availability_text[0]['label'] == ItemStatus.IN_TRANSIT

    item['status'] = ItemStatus.ON_SHELF
    item = item.update(item, dbcommit=True, reindex=True)
    assert item.is_available()
    assert len(item.availability_text) == 1  # only default value

    # test availability and availability_text for an issue
    item['type'] = TypeOfItem.ISSUE
    item['enumerationAndChronology'] = 'dummy'
    item['issue'] = {
        'regular': False,
        'status': ItemIssueStatus.RECEIVED,
        'received_date': '1970-01-01',
        'expected_date': '1970-01-01'
    }
    item = item.update(item, dbcommit=True, reindex=True)
    assert item.is_available()
    assert item.availability_text[0]['label'] == item.status

    item['issue']['status'] = ItemIssueStatus.LATE
    item = item.update(item, dbcommit=True, reindex=True)
    assert not item.is_available()
    assert item.availability_text[0]['label'] == ItemIssueStatus.LATE

    # delete the created item
    item.delete()


def test_get_links_to_me_with_fees(patron_transaction_overdue_saxon):
    """Test for number loans with fees."""
    pttr = patron_transaction_overdue_saxon
    loan = pttr.loan
    item = Item.get_record_by_pid(loan.item_pid)
    assert item.get_links_to_me() == {'fees': 1, 'loans': 1}
    assert item.get_links_to_me(get_pids=True) == {
        'fees': ['1'], 'loans': ['1']}

    pttr['status'] = 'closed'
    pttr['total_amount'] = 0
    pttr = pttr.update(pttr, reindex=True, dbcommit=True)
    assert item.get_links_to_me() == {'loans': 1}
    assert item.get_links_to_me(get_pids=True) == {'loans': ['1']}


def test_get_links_to_me_with_collection(coll_martigny_1, item_lib_martigny):
    """Test item deletion used by a collection."""
    assert item_lib_martigny.get_links_to_me() == {
        'collections': 1
    }
    assert item_lib_martigny.get_links_to_me(get_pids=True) == {
        'collections': [coll_martigny_1.pid]
    }
    can_delete, links = item_lib_martigny.can_delete
    assert not can_delete
    assert links == {'links': {'collections': 1}}


def test_items_properties(item_lib_martigny):
    """Test some properties about item class."""
    item = item_lib_martigny
    assert len(item.call_numbers) == 1
    assert item.get('call_number') in item.call_numbers

    item['second_call_number'] = 'SECOND_CALL'
    item = item.update(item, dbcommit=True, reindex=True)
    assert len(item.call_numbers) == 2
    assert item.get('call_number') in item.call_numbers
    assert item.get('second_call_number') in item.call_numbers

    del item['second_call_number']
    item.update(item, dbcommit=True, reindex=True)
