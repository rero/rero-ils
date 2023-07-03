# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
# Copyright (C) 2022 UCLouvain
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

"""Items Record dumper tests."""

from rero_ils.modules.entities.dumpers import document_dumper


def test_local_entities_document_dumper(local_entity_person2):
    """Test document dumper."""

    dumped_record = local_entity_person2.dumps(dumper=document_dumper)
    authorized_access_point = 'William III, King of England (1650-1702)'
    for field in [
        'authorized_access_point_de',
        'authorized_access_point_en',
        'authorized_access_point_fr',
        'authorized_access_point_it'
    ]:
        assert dumped_record[field] == authorized_access_point
