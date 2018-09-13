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

"""JS/CSS bundles for theme."""

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


i18n = GlobBundle(
    catalog('messages'),
    filters=AngularGettextFilter(catalog_name='reroilsAppTranslations'),
    # output='gen/translations/rero_ils.js',
)

thumbnail_js = NpmBundle(
    'js/rero_ils/thumbnail.js',
    filters='uglifyjs',
    npm={
        'jquery': '~1.9.1',
    },
    output='gen/rero_ils.thumbnail.%(version)s.js',
)

_detailed_js = NpmBundle(
    'js/rero_ils/documents_items.js',
    'js/rero_ils/detailed_app.js',
    filters='requirejs',
    depends=('node_modules/d3/*'),
    # output='gen/rero_ils.search.%(version)s.js',
    npm={
        "almond": "~0.3.1",
        'angular': '~1.4.10',
        'angular-loading-bar': '~0.9.0',
        'd3': '^3.5.17'
    },
)

detailed_js = Bundle(
    _detailed_js,
    i18n,
    thumbnail_js,
    # filters='jsmin',
    output='gen/rero_ils.detailed.%(version)s.js',
)

tab_js = Bundle(
    'node_modules/bootstrap-sass/assets/javascripts/bootstrap/tab.js',
    output='gen/rero_ils.tab.%(version)s.js'
)

_search_js = NpmBundle(
    'js/rero_ils/documents_items.js',
    'js/rero_ils/search_app.js',
    filters='requirejs',
    depends=('node_modules/invenio-search-js/dist/*.js', 'node_modules/d3/*'),
    npm={
        "almond": "~0.3.1",
        'angular': '~1.4.10',
        'angular-loading-bar': '~0.9.0',
        'd3': '^3.5.17',
        'invenio-search-js': '^1.3.1',
    },
)

search_js = Bundle(
    _search_js,
    i18n,
    thumbnail_js,
    # filters='jsmin',
    output='gen/rero_ils.search.%(version)s.js',
)

thumbnail_css = NpmBundle(
    'css/rero_ils/thumbnail.scss',
    filters='node-scss,cleancssurl',
    output='gen/thumbnail.%(version)s.css',
)
