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

"""Tests `LocalEntity` authorized access point."""


def test_local_entities_authorized_access_point(local_entity_person,
                                                local_entity_person2,
                                                local_entity_org,
                                                local_entity_org2):
    """Test authorized access point calculation."""
    dumped_record = local_entity_person.dumps()
    assert dumped_record['authorized_access_point'] == 'Loy, Georg (1881-1968)'
    dumped_record = local_entity_person2.dumps()
    assert dumped_record['authorized_access_point'] == \
           'William III, King of England (1650-1702)'

    dumped_record = local_entity_org.dumps()
    assert dumped_record['authorized_access_point'] == \
           'Convegno internazionale di Italianistica'
    #
    dumped_record = local_entity_org2.dumps()
    assert dumped_record['authorized_access_point'] == \
           'Catholic Church. Concilium Plenarium Americae ' \
           'Latinae (5th ; 1899 ; Rome, Italy)'
