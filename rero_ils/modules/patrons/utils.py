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

"""Utilities functions for patrons."""


from flask_login import current_user


def user_has_patron(user=current_user):
    """Test if user has a patron."""
    from .api import Patron
    patron = Patron.get_patron_by_user(user=user)
    if patron and 'patron' in patron.get('roles'):
        return True
    return False


def get_patron_from_arguments(**kwargs):
    """Try to load a patron from potential arguments."""
    from .api import Patron
    required_arguments = ['patron', 'patron_barcode', 'patron_pid', 'loan']
    if not any(k in required_arguments for k in kwargs):
        return None
    return kwargs.get('patron') \
        or Patron.get_patron_by_barcode(kwargs.get('patron_barcode')) \
        or Patron.get_record_by_pid(kwargs.get('patron_pid')) \
        or Patron.get_record_by_pid(kwargs.get('loan').get('patron_pid'))
