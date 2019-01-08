# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""JS/CSS bundles for RERO ILS theme."""

from __future__ import absolute_import, print_function

import os

from flask_assets import Bundle
from invenio_assets import AngularGettextFilter, GlobBundle, NpmBundle
from pkg_resources import resource_filename


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


search_js = Bundle(
    i18n,
    NpmBundle(
        'node_modules/almond/almond.js',
        'js/rero_ils/documents.js',
        'js/rero_ils/mef_persons.js',
        'js/rero_ils/invenio_config.js',
        'js/rero_ils/translations.js',
        'js/rero_ils/thumbnail.js',
        'js/rero_ils/search_app.js',
        filters='requirejs',
        depends=(
            'node_modules/invenio-search-js/dist/*.js',
            'node_modules/d3/*'
        ),
        npm={
            'almond': '~0.3.1',
            'angular': '~1.4.10',
            'angular-loading-bar': '~0.9.0',
            'd3': '^3.5.17',
            'invenio-search-js': '^1.5.4',
        }),
    filters='jsmin',
    output='gen/rero_ils.search.%(version)s.js',
)

admin_js = Bundle(
    'node_modules/jquery/jquery.js',
    'js/rero_ils/admin/runtime.js',
    'js/rero_ils/admin/polyfills.js',
    'js/rero_ils/admin/styles.js',
    'js/rero_ils/admin/scripts.js',
    'js/rero_ils/admin/main.js',
    'node_modules/bootstrap/dist/js/bootstrap.bundle.js',
    output='gen/rero_ils.modules.admin_ui_js.%(version)s.js'
)
