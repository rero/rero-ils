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

"""Blueprint used for loading templates."""

from __future__ import absolute_import, print_function

from functools import wraps

from flask import Blueprint, jsonify

from ..item_types.api import ItemType
from ..patrons.api import current_patron
from ...permissions import login_and_librarian

blueprint = Blueprint(
    'item_types',
    __name__,
    template_folder='templates',
    static_folder='static',
)


def check_permission(fn):
    """Decorate to check permission access."""
    @wraps(fn)
    def decorated_view(*args, **kwargs):
        """Decorated view."""
        login_and_librarian()
        return fn(*args, **kwargs)
    return decorated_view


@blueprint.route('/item_types/name/validate/<name>', methods=["GET"])
@check_permission
def name_validate(name):
    """Item type name validation."""
    response = {
        'name': None
    }
    if current_patron:
        patron_type = ItemType.exist_name_and_organisation_pid(
            name,
            current_patron.organisation.pid
        )
        if patron_type:
            response = {
                'name': patron_type.name
            }
    return jsonify(response)
