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

"""JS/CSS bundles for theme."""

from __future__ import absolute_import, print_function

from flask_assets import Bundle
from invenio_assets import NpmBundle

from ...bundles import i18n

detailed_js = Bundle(
    i18n,
    NpmBundle(
        'js/rero_ils/translations.js',
        'js/rero_ils/thumbnail.js',
        'js/rero_ils/detailed_app.js',
        filters='requirejs',
        depends=('node_modules/d3/*'),
        npm={
            "almond": "~0.3.1",
            'angular': '~1.4.10',
            'angular-loading-bar': '~0.9.0',
            'd3': '^3.5.17'
        }
    ),
    filters='jsmin',
    output='gen/rero_ils.detailed.%(version)s.js',
)
