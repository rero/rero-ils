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

from datetime import datetime

from elasticsearch_dsl import Q


def patron_expiration_filter(expired=True):
    """Create a filter for the patron account expiration status.

    :param expired: if True, filter expired accounts (expiration_date <= now),
                    if False, filter active accounts (expiration_date > now OR no expiration_date).
    """

    def inner(values):
        if not values or values[0] != "true":
            return Q()
        if expired:
            return Q("range", patron__expiration_date={"lte": datetime.now()})
        return Q("range", patron__expiration_date={"gt": datetime.now()}) | ~Q("exists", field="patron.expiration_date")

    return inner
