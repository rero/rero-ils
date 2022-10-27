# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
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

"""Utilities functions for patrons."""


from flask_login import current_user


def user_has_patron(user=current_user):
    """Test if user has a patron."""
    from .api import Patron
    patrons = Patron.get_patrons_by_user(user=user)
    return bool(patrons)  # true if `patrons` list isn't empty; false otherwise


def get_patron_pid_by_email(email):
    """Get patron pid by email.

    :param email: email to search.
    :return: the first patron pid found corresponding to this email.
    """
    from .api import PatronsSearch
    query = PatronsSearch().filter('term', email=email).source(['pid'])
    if hit := next(query.scan(), None):
        return hit.pid


def clean_record_data(data=None):
    """Clean patron data.

    :param data: data representing patron as dictionary.
    :return: cleaned data
    """
    if data and data.get('barcode'):
        data['barcode'] = [d.strip() for d in data.get('barcode')]
    if data and data.get('patron', {}).get('barcode'):
        data['patron']['barcode'] = [
            d.strip() for d in data['patron']['barcode']]
    return data
