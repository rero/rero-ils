# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2018 RERO.
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

"""Utilities functions for circ_policies."""


from __future__ import absolute_import, print_function


def clean_circ_policy_fields(data):
    """Clean circ policy fields."""
    if data.get('allow_checkout') is False:
        if 'checkout_duration' in data:
            del(data['checkout_duration'])
        if 'number_renewals' in data:
            del(data['number_renewals'])
        if 'renewal_duration' in data:
            del(data['renewal_duration'])
    if data.get('number_renewals') == 0:
        if 'renewal_duration' in data:
            del(data['renewal_duration'])
    return data
