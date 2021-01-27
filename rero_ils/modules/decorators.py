# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
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

"""Shared module decorators."""

from functools import wraps

from rero_ils.permissions import login_and_librarian


def check_logged_as_librarian(fn):
    """Decorate to check if the current logged user is logged as librarian.

    If no user is connected: return 401 (unauthorized)
    If current logged user isn't `librarian`: return 403 (forbidden)
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        login_and_librarian()
        return fn(*args, **kwargs)
    return wrapper
