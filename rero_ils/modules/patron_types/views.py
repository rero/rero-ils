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

"""Blueprint used for loading templates."""

from __future__ import absolute_import, print_function

from flask import Blueprint, jsonify

from ..decorators import check_logged_as_librarian
from ..patron_types.api import PatronType
from ..patrons.api import current_librarian

blueprint = Blueprint(
    'patron_types',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.route('/patron_types/name/validate/<name>', methods=["GET"])
@check_logged_as_librarian
def name_validate(name):
    """Patron type name validation."""
    response = {
        'name': None
    }
    if current_librarian:
        patron_type = PatronType.exist_name_and_organisation_pid(
            name,
            current_librarian.organisation.pid
        )
        if patron_type:
            response = {
                'name': patron_type.name
            }
    return jsonify(response)
