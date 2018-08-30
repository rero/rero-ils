# -*- coding: utf-8 -*-
#
# This file is part of REROILS.
# Copyright (C) 2017 RERO.
#
# REROILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# REROILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with REROILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Invenio digital library framework."""

import os

from setuptools import find_packages, setup
from setuptools.command.egg_info import egg_info


class EggInfoWithCompile(egg_info):
    def run(self):
        from babel.messages.frontend import compile_catalog
        compiler = compile_catalog()
        option_dict = self.distribution.get_option_dict('compile_catalog')
        if option_dict.get('domain'):
            compiler.domain = [option_dict['domain'][1]]
        else:
            compiler.domain = ['messages']
        compiler.use_fuzzy = True
        compiler.directory = option_dict['directory'][1]
        compiler.run()
        super().run()


readme = open('README.rst').read()

INVENIO_VERSION = "3.0.0"

packages = find_packages()


# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('reroils_app', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    cmdclass={
        'egg_info': EggInfoWithCompile
    },
    name='reroils-app',
    version=version,
    description=__doc__,
    long_description=readme,
    keywords='reroils-app Invenio',
    license='GPL',
    author='RERO',
    author_email='software@rero.ch',
    url='https://github.com/rero/reroils-app',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'console_scripts': [
            'reroils-app = invenio_app.cli:cli',
        ],
        'invenio_base.apps': [
            # 'flask_debugtoolbar = flask_debugtoolbar:DebugToolbarExtension',
            'reroils-app = reroils_app.modules.ext:REROILSAPP'
        ],
        'invenio_base.blueprints': [
            'reroils_app = reroils_app.views:blueprint',
            'organisations =\
                reroils_app.modules.organisations_members.views:blueprint',
            'members = reroils_app.modules.members_locations.views:blueprint',
            'locations = reroils_app.modules.locations.views:blueprint',
            'documents_items =\
                reroils_app.modules.documents_items.views:blueprint',
            'documents = reroils_app.modules.documents.views:blueprint',
            'items = reroils_app.modules.items.views:blueprint',
            'patrons = reroils_app.modules.patrons.views:blueprint',
        ],
        'invenio_config.module': [
            'reroils_app = reroils_app.config',
        ],
        'invenio_i18n.translations': [
            'messages = reroils_app',
        ],
        'invenio_assets.bundles': [
            'reroils_app_search_js = reroils_app.bundles:search_js',
            'reroils_app_item_editor_js =\
                reroils_app.modules.items.bundles:editor_js',
            'reroils_app_item_circulation_ui_js =\
                reroils_app.modules.items.bundles:circulation_ui_js',
            'reroils_app_document_editor_js =\
                reroils_app.modules.documents.bundles:editor_js',
            'reroils_app_patron_profile_css =\
                reroils_app.modules.patrons.bundles:profile_css',
            'reroils_app_patron_editor_js =\
                reroils_app.modules.patrons.bundles:editor_js',
            'reroils_app_member_editor_js =\
                reroils_app.modules.members_locations.bundles:editor_js',
            'reroils_app_location_editor_js =\
                reroils_app.modules.locations.bundles:editor_js'
        ],
        'dojson.cli': [
            'reverse = reroils_app.dojson.cli:reverse',
            'head = reroils_app.dojson.cli:head',
        ],
        'dojson.cli.dump': [
            'pjson = reroils_app.modules.dojson.dump:pretty_json_dump',
        ],
        'dojson.cli.rule': [
            'marc21tojson =\
                reroils_app.modules.documents.dojson.contrib.marc21tojson:marc21tojson',
            'marc21toebooks =\
                reroils_app.modules.ebooks.dojson.contrib.marc21:marc21',
            'unimarctojson =\
                reroils_app.modules.documents.dojson.contrib.unimarctojson:unimarctojson',
        ],
        'flask.commands': [
            'fixtures = reroils_app.modules.cli:fixtures',
            'utils = reroils_app.modules.cli:utils',
            'oaiharvester = reroils_app.modules.ebooks.cli:oaiharvester'
        ],
        'invenio_db.models': [
            'organisations = reroils_app.modules.organisations.models',
            'organisations_members =\
                reroils_app.modules.organisations_members.models',
            'members = reroils_app.modules.members.models',
            'members_locations = reroils_app.modules.members_locations.models'
            'locations = reroils_app.modules.locations.models',
            'documents = reroils_app.modules.documents.models',
            'documents_items = reroils_app.modules.documents_items.models',
            'items = reroils_app.modules.items.models',
            'patrons = reroils_app.modules.patrons.models',
            'transactions = reroils_app.modules.transactions.models',
        ],
        'invenio_pidstore.minters': [
            'organisation_id =\
                reroils_app.modules.organisations.minters:organisation_id_minter',
            'member_id =\
                reroils_app.modules.members.minters:member_id_minter',
            'location_id =\
                reroils_app.modules.locations.minters:location_id_minter',
            'document_id =\
                reroils_app.modules.documents.minters:document_id_minter',
            'item_id = reroils_app.modules.items.minters:item_id_minter',
            'patron_id = reroils_app.modules.patrons.minters:patron_id_minter',
        ],
        'invenio_pidstore.fetchers': [
            'organisation_id =\
                reroils_app.modules.organisations.fetchers:organisation_id_fetcher',
            'member_id =\
                reroils_app.modules.members.fetchers:member_id_fetcher',
            'location_id =\
                reroils_app.modules.locations.fetchers:location_id_fetcher',
            'document_id =\
                reroils_app.modules.documents.fetchers:document_id_fetcher',
            'item_id =\
                reroils_app.modules.items.fetchers:item_id_fetcher',
            'patron_id =\
                reroils_app.modules.patrons.fetchers:patron_id_fetcher',
        ],
        'invenio_jsonschemas.schemas': [
            'organisations = reroils_app.modules.organisations.jsonschemas',
            'members = reroils_app.modules.members.jsonschemas',
            'locations = reroils_app.modules.locations.jsonschemas',
            'documents = reroils_app.modules.documents.jsonschemas',
            'items = reroils_app.modules.items.jsonschemas',
            'patrons = reroils_app.modules.patrons.jsonschemas',
        ],
        'invenio_search.mappings': [
            'organisations = reroils_app.modules.organisations.mappings',
            'members = reroils_app.modules.members.mappings',
            'locations = reroils_app.modules.locations.mappings',
            'documents = reroils_app.modules.documents.mappings',
            'items = reroils_app.modules.items.mappings',
            'patrons = reroils_app.modules.patrons.mappings',
        ],
        'invenio_celery.tasks': [
            'reroils_app_oaiharvest = reroils_app.modules.ebooks.tasks',
        ]
    },
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GPL License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Development Status :: 3 - Alpha',
    ],
)
