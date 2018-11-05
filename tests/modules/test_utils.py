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

"""Utils tests."""


from rero_ils.modules.patrons.api import Patron
from rero_ils.modules.patrons_types.api import PatronType
from rero_ils.utils import resolve_relations


def test_resolve_locations_pids_names(app, create_minimal_resources,
                                      form_locations_pids_names):
    """Test resolve locations_pids_names."""
    result = [{
        'items':
        [{
            'key': 'location_pid',
            'titleMap':
            [{
                'name': 'MV Sion: Store Base', 'value': '1'
            }]
        }]
    }]
    resolve = resolve_relations(form_locations_pids_names)
    assert resolve == result


def test_relations_locations_pids_names(app, create_minimal_resources,
                                        form_item_types_names_descriptions):
    """Test resolve item_types_names_descriptions."""
    result = [{
        'items':
        [{
            'key': 'item_type_pid',
            'titleMap':
            [{
                'name': 'Item Type Name',
                'value': '1'
            }]
        }]
    }]
    resolve = resolve_relations(form_item_types_names_descriptions)
    assert resolve == result


def test_relations_patron_names_descriptions(app, minimal_patron_record,
                                             minimal_patron_type_record,
                                             form_patron_names_descriptions):
    """Test resolve patron_names_descriptions."""
    PatronType.create(minimal_patron_type_record, dbcommit=True, reindex=True)
    Patron.create(minimal_patron_record, dbcommit=True, reindex=True)
    result = [{
        'items':
        [{
            'key': 'patron_type_pid',
            'titleMap': [{
                'name': 'Patron Type Name',
                'value': '1'
            }]
        }]
    }]
    resolve = resolve_relations(form_patron_names_descriptions)
    assert resolve == result
