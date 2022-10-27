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

import os
import pathlib

from flask import Blueprint, current_app, jsonify

from rero_ils.modules.decorators import check_logged_as_librarian

blueprint = Blueprint(
    'notifications',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.route('/notifications/templates/list', methods=['GET'])
@check_logged_as_librarian
def list_available_template():
    """List all templates to build a notification content."""
    base_path = pathlib.Path(__file__).parent.absolute()
    template_path = os.path.join(base_path, blueprint.template_folder)

    template_directories = set()
    for glob_pattern in current_app.config.get(
      'RERO_ILS_NOTIFICATIONS_ALLOWED_TEMPLATE_FILES'):
        for path in pathlib.Path(template_path).rglob(glob_pattern):
            parent_path = str(path.parent.absolute())
            parent_path = parent_path.replace(template_path, '').lstrip('/')
            template_directories.add(parent_path)
    return jsonify({'templates': list(template_directories)})
