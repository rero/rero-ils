# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
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

"""Patron Query factories for REST API."""

from __future__ import absolute_import, print_function

from datetime import datetime

from elasticsearch_dsl import Q


def patron_expired():
    """Create a filter for the patron account is expired."""
    def inner(values):
        return Q('range', patron__expiration_date={'lte': datetime.now()}) \
            if 'true' == values[0] else Q()
    return inner
