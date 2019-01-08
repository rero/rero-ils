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


admin_css = NpmBundle(
    'scss/rero_ils/admin/styles.scss',
    depends=('scss/rero_ils/admin/*.scss'),
    filters='node-scss,cleancssurl',
    output='gen/rero_ils_admin.%(version)s.css',
    npm={
        'almond': '~0.3.1',
        'bootstrap': '~4.2.1',
        'popper.js': '~1.14.6',
        'font-awesome': '~4.4.0',
        'jquery': '~1.9.1',
    }
)

main_css = NpmBundle(
    'scss/rero_ils/styles.scss',
    depends=('scss/invenio_theme/*.scss', 'scss/rero_ils/*.scss'),
    filters='node-scss,cleancssurl',
    output='gen/rero_ils_main.%(version)s.css',
    npm={
        'almond': '~0.3.1',
        'bootstrap-sass': '~3.3.5',
        'font-awesome': '~4.4.0',
        'jquery': '~1.9.1',
    }
)
"""Main CSS bundle with Bootstrap and Font-Awesome."""

i18n = GlobBundle(
    catalog('messages'),
    filters=AngularGettextFilter(catalog_name='reroilsAppTranslations'),
    # output='gen/translations/rero_ils.js',
)

js = NpmBundle(
    'node_modules/almond/almond.js',
    'js/rero_ils/rero_ils.js',
    filters='requirejs',
    npm={
        'almond': '~0.3.1',
        'angular': '~1.4.9',
        'bootstrap-autohide-navbar': '~1.0.0',
        'bootstrap-sass': '~3.3.5',
        'angular-gettext': '~2.3.8',
        'jquery': '~1.9.1',
    },
    output='gen/rero_ils.main.%(version)s.js'
)

search_js = Bundle(
    i18n,
    NpmBundle(
        'js/rero_ils/invenio_config.js',
        'js/rero_ils/translations.js',
        'js/rero_ils/documents_items.js',
        'js/rero_ils/persons.js',
        'js/rero_ils/thumbnail.js',
        'js/rero_ils/search_app.js',
        filters='requirejs',
        depends=(
            'node_modules/invenio-search-js/dist/*.js',
            'node_modules/d3/*'
        ),
        npm={
            "almond": "~0.3.1",
            'angular': '~1.4.10',
            'angular-loading-bar': '~0.9.0',
            'd3': '^3.5.17',
            'invenio-search-js': '^1.3.1',
        }),
    filters='jsmin',
    output='gen/rero_ils.search.%(version)s.js',
)

schema_form_js = NpmBundle(
    'node_modules/angular/angular.js',
    'node_modules/angular-sanitize/angular-sanitize.min.js',
    'node_modules/tv4/tv4.js',
    'node_modules/objectpath/lib/ObjectPath.js',
    'node_modules/angular-schema-form/dist/schema-form.js',
    'node_modules/angular-schema-form/dist/bootstrap-decorator.js',
    npm={
        'angular': '~1.6.9',
        'angular-sanitize': '~1.6.9',
        'tv4': '^1.3.0',
        'objectpath': '^1.2.1',
        'angular-schema-form': '0.8.13'
    }
)

admin_js = Bundle(
    'js/rero_ils/admin/runtime.js',
    'js/rero_ils/admin/polyfills.js',
    'js/rero_ils/admin/styles.js',
    'js/rero_ils/admin/scripts.js',
    'js/rero_ils/admin/main.js',
    'node_modules/bootstrap-sass/assets/javascripts/bootstrap.js',
    output='gen/rero_ils.modules.admin_ui_js.%(version)s.js'
)


editor_js = Bundle(
    schema_form_js,
    'js/rero_ils/editor.js',
    'js/rero_ils/document-editor.js',
    'js/rero_ils/library-editor.js',
    'js/rero_ils/item-editor.js',
    'js/rero_ils/item-type-editor.js',
    'js/rero_ils/patron-editor.js',
    'js/rero_ils/patron-type-editor.js',
    'js/rero_ils/circ-policy-editor.js',
    'js/rero_ils/location-editor.js',
    'js/rero_ils/editor-app.js',
    filters='jsmin',
    output='gen/rero_ils.editor_js.%(version)s.js',
)
