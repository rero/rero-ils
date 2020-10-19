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

"""JS/CSS bundles for RERO ILS theme."""

from __future__ import absolute_import, print_function

import os

from invenio_assets import AngularGettextFilter, GlobBundle, NpmBundle
from pkg_resources import resource_filename

RERO_ILS_UI_VERSION = '0.6.0'


def catalog(domain):
    """Return glob matching path to tranlated messages for a given domain."""
    return os.path.join(
        os.path.abspath(resource_filename('rero_ils', 'translations')),
        '*',  # language code
        'LC_MESSAGES',
        '{0}.po'.format(domain),
    )


main_css = NpmBundle(
    'scss/rero_ils/styles.scss',
    depends=('scss/rero_ils/*.scss'),
    filters='node-scss,cleancssurl',
    output='gen/rero_ils_main.%(version)s.css',
    npm={
        'almond': '~0.3.3',
        'bootstrap': '~4.2.1',
        'font-awesome': '~4.7.0',
        'jquery': '~1.9.1',
    }
)
"""Main CSS bundle with Bootstrap and Font-Awesome."""

i18n = GlobBundle(
    catalog('messages'),
    filters=AngularGettextFilter(catalog_name='reroilsAppTranslations'),
)

js = NpmBundle(
    'node_modules/almond/almond.js',
    'js/rero_ils/rero_ils.js',
    'js/rero_ils/rero_keep_tab.js',
    filters='requirejs',
    npm={
        'almond': '~0.3.3',
        'angular': '~1.6.9',
        'bootstrap': '~4.2.1',
        'angular-gettext': '~2.3.8',
        'jquery': '~1.9.1',
    },
    output='gen/rero_ils.main.%(version)s.js'
)

admin_ui_js = NpmBundle(
    'node_modules/@rero/rero-ils-ui/dist/admin/runtime.*.js',
    'node_modules/@rero/rero-ils-ui/dist/admin/polyfills.*.js',
    'node_modules/@rero/rero-ils-ui/dist/admin/styles.*.js',
    'node_modules/@rero/rero-ils-ui/dist/admin/scripts.*.js',
    'node_modules/@rero/rero-ils-ui/dist/admin/main.*.js',
    output='gen/rero_ils_admin_ui.%(version)s.js',
    npm={
        '@rero/rero-ils-ui': '~{version}'.format(version=RERO_ILS_UI_VERSION)
    }
)

public_search_ui_js = NpmBundle(
    'node_modules/@rero/rero-ils-ui/dist/public-search/runtime.*.js',
    'node_modules/@rero/rero-ils-ui/dist/public-search/polyfills.*.js',
    'node_modules/@rero/rero-ils-ui/dist/public-search/styles.*.js',
    'node_modules/@rero/rero-ils-ui/dist/public-search/scripts.*.js',
    'node_modules/@rero/rero-ils-ui/dist/public-search/main.*.js',
    output='gen/rero_ils_public-search_ui.%(version)s.js',
    npm={
        '@rero/rero-ils-ui': '~{version}'.format(version=RERO_ILS_UI_VERSION)
    }
)

search_bar_ui_js = NpmBundle(
    'node_modules/@rero/rero-ils-ui/dist/search-bar/polyfills.*.js',
    'node_modules/@rero/rero-ils-ui/dist/search-bar/main.*.js',
    output='gen/rero_ils_search-bar_ui.%(version)s.js',
    npm={
        '@rero/rero-ils-ui': '~{version}'.format(version=RERO_ILS_UI_VERSION)
    }
)
