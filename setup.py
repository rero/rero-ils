# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 RERO.
#
# reroils-app is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""reroils-app Invenio instance."""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()

DATABASE = "postgresql"
ELASTICSEARCH = "elasticsearch6"
INVENIO_VERSION = "3.0.0"

tests_require = [
    'check-manifest>=0.35',
    'coverage>=4.4.1',
    'isort>=4.3',
    'mock>=2.0.0',
    'pydocstyle>=2.0.0',
    'pytest-cov>=2.5.1',
    'pytest-invenio>=1.0.2,<1.1.0',
    'pytest-mock>=1.6.0',
    'pytest-pep8>=1.0.6',
    'pytest-random-order>=0.5.4',
    'pytest>=3.3.1',
    'selenium>=3.4.3',
]

invenio_search_version = '1.0.1'

extras_require = {
    'docs': [
        'Sphinx>=1.5.1',
    ],
    'translations': [
        'transifex-client>=0.12.5'
    ],
    'tests': tests_require,
}

extras_require['all'] = []
for name, reqs in extras_require.items():
    extras_require['all'].extend(reqs)

setup_requires = [
    'Babel>=2.4.0',
    'pytest-runner>=3.0.0,<5',
]

install_requires = [
    'dateparser>=0.7.0',
    'dojson>=1.3.2',
    'elasticsearch-dsl<6.2.0,>=6.0.0',
    'Flask>=0.11.1',
    'Flask-BabelEx>=0.9.3',
    'Flask-Debugtoolbar>=0.10.1',
    'invenio[{db},{es},base,auth,metadata]~={version}'.format(
        db=DATABASE, es=ELASTICSEARCH, version=INVENIO_VERSION),
    'invenio-accounts>=1.0.0',
    'invenio-app>=1.0.0',
    'invenio-assets>=1.0.0',
    'invenio-base>=1.0.0',
    'invenio-config>=1.0.0',
    'invenio-db[postgresql]>=1.0.0',
    'invenio-indexer>=1.0.0',
    'invenio-jsonschemas>=1.0.0',
    'invenio-oaiharvester>=v1.0.0a4',
    'invenio-oaiserver>=1.0.0',
    'invenio-pidstore>=1.0.0',
    'invenio-records-rest<1.2.0,>=1.1.0',
    'invenio-records-ui>=1.0.0',
    'invenio-search>=1.0.0',
    'invenio-search-ui>=1.0.0',
    'invenio-theme>=1.0.0',
    'invenio-celery>=1.0.0',
    'invenio-admin>=1.0.0',
    'invenio-oauth2server>=v1.0.0',
    'invenio-mail>=1.0.0',
    'isbnlib>=3.9.1',
    'jsonschema>=2.5.1',
    'PyYAML>=3.13',
    'SQLAlchemy-Continuum>=1.3,<1.3.5',
]


packages = find_packages()


# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('reroils_app', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='reroils-app',
    version=version,
    description=__doc__,
    long_description=readme,
    keywords='reroils-app Invenio',
    license='MIT',
    author='RERO',
    author_email='software@rero.ch',
    url='https://github.com/rero/reroils-app',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'invenio_base.apps': [
            'reroils_app = reroils_app.modules.ext:REROILSAPP'
        ],
        'console_scripts': [
            'reroils-app = invenio_app.cli:cli',
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
            'reroils_app_item_editor_js = reroils_app.modules.items.bundles:editor_js',
            'reroils_app_item_circulation_ui_js = reroils_app.modules.items.bundles:circulation_ui_js',
            'reroils_app_document_editor_js = reroils_app.modules.documents.bundles:editor_js',
            'reroils_app_patron_profile_css = reroils_app.modules.patrons.bundles:profile_css',
            'reroils_app_patron_editor_js = reroils_app.modules.patrons.bundles:editor_js',
            'reroils_app_member_editor_js = reroils_app.modules.members_locations.bundles:editor_js',
            'reroils_app_location_editor_js = reroils_app.modules.locations.bundles:editor_js'
        ],
        'dojson.cli': [
            'reverse = reroils_app.dojson.cli:reverse',
            'head = reroils_app.dojson.cli:head',
        ],
        'dojson.cli.dump': [
            'pjson = reroils_app.modules.dojson.dump:pretty_json_dump',
        ],
        'dojson.cli.rule': [
            'marc21tojson = reroils_app.modules.documents.dojson.contrib.marc21tojson:marc21tojson',
            'marc21toebooks = reroils_app.modules.ebooks.dojson.contrib.marc21:marc21',
            'unimarctojson = reroils_app.modules.documents.dojson.contrib.unimarctojson:unimarctojson',
        ],
        'flask.commands': [
            'fixtures = reroils_app.modules.cli:fixtures',
            'utils = reroils_app.modules.cli:utils',
            'oaiharvester = reroils_app.modules.ebooks.cli:oaiharvester'
        ],
        'invenio_db.models': [
            'organisations = reroils_app.modules.organisations.models',
            'organisations_members = reroils_app.modules.organisations_members.models',
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
            'organisation_id = reroils_app.modules.organisations.minters:organisation_id_minter',
            'member_id = reroils_app.modules.members.minters:member_id_minter',
            'location_id = reroils_app.modules.locations.minters:location_id_minter',
            'document_id = reroils_app.modules.documents.minters:document_id_minter',
            'item_id = reroils_app.modules.items.minters:item_id_minter',
            'patron_id = reroils_app.modules.patrons.minters:patron_id_minter',
        ],
        'invenio_pidstore.fetchers': [
            'organisation_id = reroils_app.modules.organisations.fetchers:organisation_id_fetcher',
            'member_id = reroils_app.modules.members.fetchers:member_id_fetcher',
            'location_id = reroils_app.modules.locations.fetchers:location_id_fetcher',
            'document_id = reroils_app.modules.documents.fetchers:document_id_fetcher',
            'item_id = reroils_app.modules.items.fetchers:item_id_fetcher',
            'patron_id = reroils_app.modules.patrons.fetchers:patron_id_fetcher',
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
    extras_require=extras_require,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Development Status :: 3 - Alpha',
    ],

)
