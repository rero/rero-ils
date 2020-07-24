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

"""Common pytest fixtures and plugins."""


from copy import deepcopy
from os.path import dirname, join

import mock
import pytest
from utils import flush_index, mock_response

from rero_ils.modules.documents.api import Document, DocumentsSearch
from rero_ils.modules.holdings.api import Holding, HoldingsSearch
from rero_ils.modules.items.api import Item, ItemsSearch
from rero_ils.modules.persons.api import Person, PersonsSearch


@pytest.fixture(scope="module")
def ebook_1_data(data):
    """Load ebook 1 data."""
    return deepcopy(data.get('ebook1'))


@pytest.fixture(scope="module")
def ebook_1(app, ebook_1_data):
    """Load ebook 1 record."""
    del ebook_1_data['electronicLocator']
    doc = Document.create(
        data=ebook_1_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(DocumentsSearch.Meta.index)
    return doc


@pytest.fixture(scope="module")
def ebook_2_data(data):
    """Load ebook 2 data."""
    return deepcopy(data.get('ebook2'))


@pytest.fixture(scope="module")
def ebook_2(app, ebook_2_data):
    """Load ebook 2 record."""
    del ebook_2_data['electronicLocator']
    doc = Document.create(
        data=ebook_2_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(DocumentsSearch.Meta.index)
    return doc


@pytest.fixture(scope="module")
def ebook_3_data(data):
    """Load ebook 3 data."""
    return deepcopy(data.get('ebook3'))


@pytest.fixture(scope="module")
def ebook_3(app, ebook_3_data):
    """Load ebook 3 record."""
    del ebook_3_data['electronicLocator']
    doc = Document.create(
        data=ebook_3_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(DocumentsSearch.Meta.index)
    return doc


@pytest.fixture(scope="module")
def ebook_4_data(data):
    """Load ebook 4 data."""
    return deepcopy(data.get('ebook4'))


@pytest.fixture(scope="module")
def ebook_4(app, ebook_4_data):
    """Load ebook 4 record."""
    del ebook_4_data['electronicLocator']
    doc = Document.create(
        data=ebook_4_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(DocumentsSearch.Meta.index)
    return doc


@pytest.fixture(scope="module")
def document_data(data):
    """Load document data."""
    return deepcopy(data.get('doc1'))


@pytest.fixture(scope="module")
def document_chinese_data(data):
    """Load chinese document data."""
    return deepcopy(data.get('doc4'))


@pytest.fixture(scope="function")
def document_data_tmp(data):
    """Load document data scope function."""
    return deepcopy(data.get('doc1'))


@pytest.fixture(scope="module")
def document(app, document_data):
    """Load document record."""
    doc = Document.create(
        data=document_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(DocumentsSearch.Meta.index)
    return doc


@pytest.fixture(scope="module")
def document_with_issn(app, journal_data_with_issn):
    """Load document record."""
    doc = Document.create(
        data=journal_data_with_issn,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(DocumentsSearch.Meta.index)
    return doc


@pytest.fixture(scope="module")
def document_data_ref(data):
    """Load document ref data."""
    return deepcopy(data.get('doc2'))


@pytest.fixture(scope="module")
def journal_data_with_issn(data):
    """Load journal document with issn data."""
    return deepcopy(data.get('doc5'))


@pytest.fixture(scope="module")
def journal_data(holdings):
    """Load journal data."""
    return deepcopy(holdings.get('doc4'))


@pytest.fixture(scope="module")
def journal(app, journal_data):
    """Load journal record."""
    doc = Document.create(
        data=journal_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(DocumentsSearch.Meta.index)
    return doc


@pytest.fixture(scope="module")
def person_data(data):
    """Load mef person data."""
    return deepcopy(data.get('pers1'))


@pytest.fixture(scope="function")
def person_data_tmp(data):
    """Load mef person data scope function."""
    return deepcopy(data.get('pers1'))


@pytest.fixture(scope="module")
def person_response_data(person_data):
    """Load mef person response data."""
    json_data = {
        'hits': {
            'hits': [
                {
                    'id': person_data['pid'],
                    'metadata': person_data
                }
            ]
        }
    }
    return json_data


@pytest.fixture(scope="module")
def person(app, person_data):
    """Create mef person record."""
    pers = Person.create(
        data=person_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PersonsSearch.Meta.index)
    return pers


@pytest.fixture(scope="module")
@mock.patch('rero_ils.modules.persons.api.requests_get')
def document_ref(mock_persons_mef_get,
                 app, document_data_ref, person_response_data):
    """Load document with mef records reference."""
    mock_persons_mef_get.return_value = mock_response(
        json_data=person_response_data
    )
    doc = Document.create(
        data=document_data_ref,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(DocumentsSearch.Meta.index)
    return doc


@pytest.fixture(scope="module")
def document_sion_items_data(data):
    """Load document data for sion items."""
    return deepcopy(data.get('doc3'))


@pytest.fixture(scope="function")
def document_sion_items_data_tmp(data):
    """Load document data for sion items scope function."""
    return deepcopy(data.get('doc3'))


@pytest.fixture(scope="module")
def document_sion_items(app, document_sion_items_data):
    """Create document data for sion items."""
    doc = Document.create(
        data=document_sion_items_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(DocumentsSearch.Meta.index)
    return doc


@pytest.fixture(scope="module")
def item_lib_martigny_data(data):
    """Load item of martigny library."""
    return deepcopy(data.get('item1'))


@pytest.fixture(scope="function")
def item_lib_martigny_data_tmp(data):
    """Load item of martigny library scope function."""
    return deepcopy(data.get('item1'))


@pytest.fixture(scope="module")
def item_lib_martigny(
        app,
        document,
        item_lib_martigny_data,
        loc_public_martigny,
        item_type_standard_martigny):
    """Create item of martigny library."""
    item = Item.create(
        data=item_lib_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(ItemsSearch.Meta.index)
    return item


@pytest.fixture(scope="module")
def item2_lib_martigny_data(data):
    """Load item of martigny library."""
    return deepcopy(data.get('item5'))


@pytest.fixture(scope="function")
def item2_lib_martigny_data_tmp(data):
    """Load item of martigny library scope function."""
    return deepcopy(data.get('item5'))


@pytest.fixture(scope="module")
def item2_lib_martigny(
        app,
        document,
        item2_lib_martigny_data,
        loc_public_martigny,
        item_type_standard_martigny):
    """Create item2 of martigny library."""
    item = Item.create(
        data=item2_lib_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(ItemsSearch.Meta.index)
    return item


@pytest.fixture(scope="module")
def item3_lib_martigny_data(data):
    """Load item of martigny library."""
    return deepcopy(data.get('item7'))


@pytest.fixture(scope="function")
def item3_lib_martigny_data_tmp(data):
    """Load item of martigny library scope function."""
    return deepcopy(data.get('item7'))


@pytest.fixture(scope="module")
def item3_lib_martigny(
        app,
        document,
        item3_lib_martigny_data,
        loc_public_martigny,
        item_type_standard_martigny):
    """Create item3 of martigny library."""
    item = Item.create(
        data=item3_lib_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(ItemsSearch.Meta.index)
    return item


@pytest.fixture(scope="module")
def item4_lib_martigny_data(data):
    """Load item of martigny library."""
    return deepcopy(data.get('item8'))


@pytest.fixture(scope="function")
def item4_lib_martigny_data_tmp(data):
    """Load item of martigny library scope function."""
    return deepcopy(data.get('item8'))


@pytest.fixture(scope="module")
def item4_lib_martigny(
        app,
        document,
        item4_lib_martigny_data,
        loc_public_martigny,
        item_type_standard_martigny):
    """Create item of martigny library."""
    item = Item.create(
        data=item4_lib_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(ItemsSearch.Meta.index)
    return item


@pytest.fixture(scope="module")
def item_lib_saxon_data(data):
    """Load item of saxon library."""
    return deepcopy(data.get('item2'))


@pytest.fixture(scope="module")
def item_lib_saxon(
        app,
        document,
        item_lib_saxon_data,
        loc_public_saxon,
        item_type_standard_martigny):
    """Create item of saxon library."""
    item = Item.create(
        data=item_lib_saxon_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(ItemsSearch.Meta.index)
    return item


@pytest.fixture(scope="module")
def item_lib_fully_data(data):
    """Load item of fully library."""
    return deepcopy(data.get('item3'))


@pytest.fixture(scope="module")
def item_lib_fully(
        app,
        document,
        item_lib_fully_data,
        loc_public_fully,
        item_type_standard_martigny):
    """Create item of fully library."""
    item = Item.create(
        data=item_lib_fully_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(ItemsSearch.Meta.index)
    return item


@pytest.fixture(scope="module")
def item_lib_sion_data(data):
    """Load item of sion library."""
    return deepcopy(data.get('item4'))


@pytest.fixture(scope="module")
def item_lib_sion(
        app,
        document_sion_items,
        item_lib_sion_data,
        loc_public_sion,
        item_type_regular_sion):
    """Create item of sion library."""
    item = Item.create(
        data=item_lib_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(ItemsSearch.Meta.index)
    return item


@pytest.fixture(scope="module")
def item2_lib_sion_data(data):
    """Load item of sion library."""
    return deepcopy(data.get('item6'))


@pytest.fixture(scope="module")
def item2_lib_sion(
        app,
        document,
        item2_lib_sion_data,
        loc_restricted_sion,
        item_type_regular_sion):
    """Create item of sion library."""
    item = Item.create(
        data=item2_lib_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(ItemsSearch.Meta.index)
    return item


@pytest.fixture(scope="module")
def item2_lib_saxon_data(data):
    """Load item of saxon library."""
    return deepcopy(data.get('item9'))


@pytest.fixture(scope="module")
def item2_lib_saxon(
        app,
        document,
        item2_lib_saxon_data,
        loc_public_saxon,
        item_type_standard_martigny):
    """Create item of saxon library."""
    item = Item.create(
        data=item2_lib_saxon_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(ItemsSearch.Meta.index)
    return item


# --------- Holdings records -----------


@pytest.fixture(scope="module")
def holding_lib_martigny_data(holdings):
    """Load holding of martigny library."""
    return deepcopy(holdings.get('holding1'))


@pytest.fixture(scope="function")
def holding_lib_martigny_data_tmp(holdings):
    """Load holding of martigny library scope function."""
    return deepcopy(holdings.get('holding1'))


@pytest.fixture(scope="module")
def holding_lib_martigny(app, loc_public_martigny, item_type_standard_martigny,
                         document, holding_lib_martigny_data):
    """Create holding of martigny library."""
    holding = Holding.create(
        data=holding_lib_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(HoldingsSearch.Meta.index)
    return holding


@pytest.fixture(scope="module")
def holding_lib_saxon_data(holdings):
    """Load holding of saxon library."""
    return deepcopy(holdings.get('holding2'))


@pytest.fixture(scope="module")
def holding_lib_saxon(app, document, holding_lib_saxon_data,
                      loc_public_saxon, item_type_standard_martigny):
    """Create holding of saxon library."""
    holding = Holding.create(
        data=holding_lib_saxon_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(HoldingsSearch.Meta.index)
    return holding


@pytest.fixture(scope="module")
def holding_lib_fully_data(holdings):
    """Load holding of fully library."""
    return deepcopy(holdings.get('holding3'))


@pytest.fixture(scope="module")
def holding_lib_fully(app, document, holding_lib_fully_data,
                      loc_public_fully, item_type_standard_martigny):
    """Create holding of fully library."""
    holding = Holding.create(
        data=holding_lib_fully_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(HoldingsSearch.Meta.index)
    return holding


@pytest.fixture(scope="module")
def holding_lib_sion_data(holdings):
    """Load holding of sion library."""
    return deepcopy(holdings.get('holding4'))


@pytest.fixture(scope="module")
def holding_lib_sion(app, document, holding_lib_sion_data,
                     loc_public_sion, item_type_internal_sion):
    """Create holding of sion library."""
    holding = Holding.create(
        data=holding_lib_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(HoldingsSearch.Meta.index)
    return holding


# --------- Holdings with patterns records -----------

@pytest.fixture(scope="module")
def holding_lib_martigny_w_patterns_data(holdings):
    """Load holding of martigny library."""
    return deepcopy(holdings.get('holding5'))


@pytest.fixture(scope="module")
def holding_lib_martigny_w_patterns(
    app, journal, holding_lib_martigny_w_patterns_data,
        loc_public_martigny, item_type_standard_martigny):
    """Create holding of martigny library with patterns."""
    holding = Holding.create(
        data=holding_lib_martigny_w_patterns_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(HoldingsSearch.Meta.index)
    return holding


@pytest.fixture(scope="module")
def holding_lib_sion_w_patterns_data(holdings):
    """Load holding of sion library."""
    return deepcopy(holdings.get('holding4'))


@pytest.fixture(scope="module")
def holding_lib_sion_w_patterns(
    app, journal, holding_lib_sion_w_patterns_data,
        loc_public_sion, item_type_internal_sion):
    """Create holding of sion library with patterns."""
    holding = Holding.create(
        data=holding_lib_sion_w_patterns_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(HoldingsSearch.Meta.index)
    return holding

# --------- Pattern records -----------


@pytest.fixture(scope="module")
def pattern_quarterly_one_level_data(holdings):
    """Load holding with patterns of martigny library scope function."""
    del holdings['pattern1']['template_name']
    return deepcopy(holdings.get('pattern1'))


@pytest.fixture(scope="module")
def pattern_yearly_one_level_data(holdings):
    """Load patterns of martigny library scope function."""
    del holdings['pattern2']['template_name']
    return deepcopy(holdings.get('pattern2'))


@pytest.fixture(scope="module")
def pattern_yearly_one_level_with_label_data(holdings):
    """Load patterns of martigny library scope function."""
    del holdings['pattern3']['template_name']
    return deepcopy(holdings.get('pattern3'))


@pytest.fixture(scope="module")
def pattern_yearly_two_times_data(holdings):
    """Load patterns of martigny library scope function."""
    del holdings['pattern4']['template_name']
    return deepcopy(holdings.get('pattern4'))


@pytest.fixture(scope="module")
def pattern_quarterly_two_levels_data(holdings):
    """Load patterns of martigny library scope function."""
    del holdings['pattern5']['template_name']
    return deepcopy(holdings.get('pattern5'))


@pytest.fixture(scope="module")
def pattern_quarterly_two_levels_with_season_data(holdings):
    """Load patterns of martigny library scope function."""
    del holdings['pattern6']['template_name']
    return deepcopy(holdings.get('pattern6'))


@pytest.fixture(scope="module")
def pattern_half_yearly_one_level_data(holdings):
    """Load patterns of martigny library scope function."""
    del holdings['pattern7']['template_name']
    return deepcopy(holdings.get('pattern7'))


@pytest.fixture(scope="module")
def pattern_bimonthly_every_two_months_one_level_data(holdings):
    """Load patterns of martigny library scope function."""
    del holdings['pattern8']['template_name']
    return deepcopy(holdings.get('pattern8'))


@pytest.fixture(scope="module")
def pattern_half_yearly_two_levels_data(holdings):
    """Load patterns of martigny library scope function."""
    del holdings['pattern9']['template_name']
    return deepcopy(holdings.get('pattern9'))


@pytest.fixture(scope="module")
def pattern_bimonthly_every_two_months_two_levels_data(holdings):
    """Load patterns of martigny library scope function."""
    del holdings['pattern10']['template_name']
    return deepcopy(holdings.get('pattern10'))


@pytest.fixture(scope='module')
def ebooks_1_xml():
    """Load ebook1 xml file."""
    with open(join(dirname(__file__), '..', 'data', 'ebook1.xml')) as fh:
        return fh.read()


@pytest.fixture(scope='module')
def ebooks_2_xml():
    """Load ebook2 xml file."""
    with open(join(dirname(__file__), '..', 'data', 'ebook2.xml')) as fh:
        return fh.read()


@pytest.fixture(scope='module')
def babel_filehandle():
    """Load ebook2 xml file."""
    return open(
        join(dirname(__file__), '..', 'data', 'babel_extraction.json'),
        'rb'
    )
