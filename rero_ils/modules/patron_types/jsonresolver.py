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

"""Organisation resolver."""

import jsonresolver
from invenio_pidstore.models import PersistentIdentifier, PIDStatus

from .api import PatronType


@jsonresolver.route('/api/patron_types/<pid>', host='ils.rero.ch')
def patron_type_resolver(pid):
    """Resolve patron type."""
    persistent_id = PersistentIdentifier.get('ptty', pid)
    if persistent_id.status == PIDStatus.REGISTERED:
        patron_type = PatronType.get_record_by_pid(persistent_id.pid_value)
        patron_type = patron_type.dumps()
        return dict(
            pid=patron_type['pid'],
            name=patron_type['name']
        )
    raise Exception('unable to resolve')
