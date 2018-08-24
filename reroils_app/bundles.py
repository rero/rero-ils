# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 RERO.
#
# reroils-app is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""JS/CSS bundles for theme."""

from __future__ import absolute_import, print_function

import os

from flask_assets import Bundle
from invenio_assets import AngularGettextFilter, GlobBundle, NpmBundle
from pkg_resources import resource_filename


def catalog(domain):
    """Return glob matching path to tranlated messages for a given domain."""
    return os.path.join(
        resource_filename('reroils_app', 'translations'),
        '*',  # language code
        'LC_MESSAGES',
        '{0}.po'.format(domain),
    )


i18n = GlobBundle(
    catalog('messages'),
    filters=AngularGettextFilter(catalog_name='reroilsAppTranslations'),
    # output='gen/translations/reroils_app.js',
)

js = NpmBundle(
    'js/reroils_app/documents_items.js',
    'js/reroils_app/app.js',
    filters='requirejs',
    depends=('node_modules/invenio-search-js/dist/*.js', 'node_modules/d3/*'),
    # output='gen/reroils_app.search.%(version)s.js',
    npm={
        "almond": "~0.3.1",
        'angular': '~1.4.10',
        'angular-loading-bar': '~0.9.0',
        'd3': '^3.5.17',
        'invenio-search-js': '^1.3.1',
    },
)

search_js = Bundle(
    js,
    i18n,
    # filters='jsmin',
    output='gen/reroils_app.search.%(version)s.js',
)
