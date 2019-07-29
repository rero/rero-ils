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

INVENIO_VERSION = "3.1.1"

packages = find_packages()


# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('rero_ils', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    cmdclass={
        'egg_info': EggInfoWithCompile
    },
    name='rero-ils',
    version=version,
    description=__doc__,
    long_description=readme,
    keywords='rero-ils Invenio',
    license='GPL',
    author='RERO',
    author_email='software@rero.ch',
    url='https://github.com/rero/rero-ils',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'console_scripts': [
            'rero-ils = invenio_app.cli:cli',
        ],
        'babel.extractors': [
            'json = rero_ils.modules.babel_extractors:extract_json',
            # TODO: remove once the thumbnail are done in angular
            'angular_gettext = angular_gettext_babel.extract:extract_angular'
        ],
        'invenio_base.apps': [
            # 'flask_debugtoolbar = flask_debugtoolbar:DebugToolbarExtension',
            'rero-ils = rero_ils.modules.ext:REROILSAPP'
        ],
        'invenio_base.api_apps': [
            'rero-ils = rero_ils.modules.ext:REROILSAPP'
        ],
        'invenio_base.blueprints': [
            'rero_ils = rero_ils.views:blueprint',
            'libraries = rero_ils.modules.libraries.views:blueprint',
            'patrons = rero_ils.modules.patrons.views:blueprint',
            'mef_persons = rero_ils.modules.mef_persons.views:blueprint',
            'documents = rero_ils.modules.documents.views:blueprint',
            'items = rero_ils.modules.items.views:blueprint',
            'notifications = rero_ils.modules.notifications.views:blueprint',
        ],
        'invenio_base.api_blueprints': [
            'circ_policies = rero_ils.modules.circ_policies.views:blueprint',
            'item_types = rero_ils.modules.item_types.views:blueprint',
            'patron_types = rero_ils.modules.patron_types.views:blueprint',
            'notifications = rero_ils.modules.notifications.views:blueprint',
            'patrons = rero_ils.modules.patrons.views:api_blueprint',
            'api_documents = rero_ils.modules.documents.views:api_blueprint',
            'items = rero_ils.modules.items.api_views:api_blueprint',
            'mef_persons = rero_ils.modules.mef_persons.views:api_blueprint',
        ],
        'invenio_config.module': [
            'rero_ils = rero_ils.config',
        ],
        'invenio_i18n.translations': [
            'messages = rero_ils',
        ],
        # TODO: remove this dirty hack when the following PR
        # (https://github.com/flask-admin/flask-admin/pull/1798)
        # will be integrated
        'invenio_admin.views': [
            '100_rero_ils_admin_circulation = \
                rero_ils.modules.admin:circulation',
            'rero_ils_admin_library = \
                rero_ils.modules.admin:library',
            '303_rero_ils_admin_my_library = \
                rero_ils.modules.admin:my_library',
            '301_rero_ils_admin_item_types = \
                rero_ils.modules.admin:item_types',
            '302_rero_ils_admin_patron_types = \
                rero_ils.modules.admin:patron_types',
            '101_rero_ils_admin_patrons = \
                rero_ils.modules.admin:patrons',
            '300_rero_ils_admin_circ_policies = \
                rero_ils.modules.admin:circ_policies',
            'rero_ils_admin_locations = \
                rero_ils.modules.admin:locations',
            '304_rero_ils_admin_libraries = \
                rero_ils.modules.admin:libraries',
            'rero_ils_admin_items = \
                rero_ils.modules.admin:items',
            '200_rero_ils_admin_documents = \
                rero_ils.modules.admin:documents',
            '201_rero_ils_admin_documents_create = \
                rero_ils.modules.admin:documents_create',
            '299_rero_ils_admin_persons = \
                rero_ils.modules.admin:persons'
        ],
        'invenio_assets.bundles': [
            'rero_ils_main_css = rero_ils.bundles:main_css',
            'rero_ils_main_js = rero_ils.bundles:js',
            'rero_ils_ui_js = rero_ils.bundles:ui_js',
            'rero_ils_documents_detailed_js = \
                rero_ils.modules.documents.bundles:detailed_js'
        ],
        'dojson.cli': [
            'reverse = rero_ils.dojson.cli:reverse',
            'head = rero_ils.dojson.cli:head',
        ],
        'dojson.cli.dump': [
            'pjson = rero_ils.dojson.cli:pretty_json_dump',
        ],
        'dojson.cli.rule': [
            'marc21tojson = rero_ils.modules.documents.dojson'
            '.contrib.marc21tojson:marc21tojson',
            'marc21toebooks = \
                rero_ils.modules.ebooks.dojson.contrib.marc21:marc21',
            'unimarctojson = '
            'rero_ils.modules.documents.dojson'
            '.contrib.unimarctojson:unimarctojson',
        ],
        'flask.commands': [
            'fixtures = rero_ils.modules.cli:fixtures',
            'utils = rero_ils.modules.cli:utils',
            'oaiharvester = rero_ils.modules.ebooks.cli:oaiharvester',
            'apiharvester = rero_ils.modules.apiharvester.cli:apiharvester'
        ],
        'invenio_db.models': [
            'organisations = rero_ils.modules.organisations.models',
            'libraries = rero_ils.modules.libraries.models',
            'locations = rero_ils.modules.locations.models',
            'documents = rero_ils.modules.documents.models',
            'items = rero_ils.modules.items.models',
            'item_types = rero_ils.modules.item_types.models',
            'patrons = rero_ils.modules.patrons.models',
            'patron_types = rero_ils.modules.patron_types.models',
            'transactions = rero_ils.modules.transactions.models',
            'mef = rero_ils.modules.mef_persons.models',
            'apiharvester = rero_ils.modules.apiharvester.models',
            'circ_policies = rero_ils.modules.circ_policies.models',
            'notifications = rero_ils.modules.notifications.models',
        ],
        'invenio_pidstore.minters': [
            'organisation_id = \
                rero_ils.modules.organisations.api:organisation_id_minter',
            'library_id = \
                rero_ils.modules.libraries.api:library_id_minter',
            'location_id = \
                rero_ils.modules.locations.api:location_id_minter',
            'document_id = \
                rero_ils.modules.documents.api:document_id_minter',
            'item_id = rero_ils.modules.items.api:item_id_minter',
            'item_type_id = \
                rero_ils.modules.item_types.api:item_type_id_minter',
            'patron_id = rero_ils.modules.patrons.api:patron_id_minter',
            'patron_type_id = \
                rero_ils.modules.patron_types.api:patron_type_id_minter',
            'mef_person_id = rero_ils.modules.mef_persons.api'
            ':mef_person_id_minter',
            'circ_policy_id = rero_ils.modules.circ_policies.api'
            ':circ_policy_id_minter',
            'notification_id = rero_ils.modules.notifications.api'
            ':notification_id_minter',
        ],
        'invenio_pidstore.fetchers': [
            'organisation_id = rero_ils.modules.organisations'
            '.api:organisation_id_fetcher',
            'library_id = \
                rero_ils.modules.libraries.api:library_id_fetcher',
            'location_id = \
                rero_ils.modules.locations.api:location_id_fetcher',
            'document_id = \
                rero_ils.modules.documents.api:document_id_fetcher',
            'item_id = \
                rero_ils.modules.items.api:item_id_fetcher',
            'item_type_id = \
                rero_ils.modules.item_types.api:item_type_id_fetcher',
            'patron_id = \
                rero_ils.modules.patrons.api:patron_id_fetcher',
            'patron_type_id = \
                rero_ils.modules.patron_types.api:patron_type_id_fetcher',
            'mef_person_id = \
                rero_ils.modules.mef_persons.api:mef_person_id_fetcher',
            'circ_policy_id = rero_ils.modules.circ_policies.api'
            ':circ_policy_id_fetcher',
            'notification_id = rero_ils.modules.notifications.api'
            ':notification_id_fetcher',
        ],
        'invenio_jsonschemas.schemas': [
            'organisations = rero_ils.modules.organisations.jsonschemas',
            'libraries = rero_ils.modules.libraries.jsonschemas',
            'locations = rero_ils.modules.locations.jsonschemas',
            'documents = rero_ils.modules.documents.jsonschemas',
            'items = rero_ils.modules.items.jsonschemas',
            'item_types = rero_ils.modules.item_types.jsonschemas',
            'patrons = rero_ils.modules.patrons.jsonschemas',
            'patron_types = rero_ils.modules.patron_types.jsonschemas',
            'persons = rero_ils.modules.mef_persons.jsonschemas',
            'circ_policies = rero_ils.modules.circ_policies.jsonschemas',
            'loans = rero_ils.modules.loans.jsonschemas',
            'notifications = rero_ils.modules.notifications.jsonschemas'
        ],
        'invenio_search.mappings': [
            'organisations = rero_ils.modules.organisations.mappings',
            'libraries = rero_ils.modules.libraries.mappings',
            'locations = rero_ils.modules.locations.mappings',
            'documents = rero_ils.modules.documents.mappings',
            'items = rero_ils.modules.items.mappings',
            'item_types = rero_ils.modules.item_types.mappings',
            'patrons = rero_ils.modules.patrons.mappings',
            'patron_types = rero_ils.modules.patron_types.mappings',
            'persons = rero_ils.modules.mef_persons.mappings',
            'circ_policies = rero_ils.modules.circ_policies.mappings',
            'loans = rero_ils.modules.loans.mappings',
            'notifications = rero_ils.modules.notifications.mappings',
        ],
        'invenio_search.templates': [
            'base-record = rero_ils.es_templates:list_es_templates'
        ],
        'invenio_celery.tasks': [
            'rero_ils_oaiharvest = rero_ils.modules.ebooks.tasks',
            'rero_ils_mefharvest = rero_ils.modules.apiharvester.tasks',
            'rero_ils_notifications = rero_ils.modules.notifications.tasks',
        ],
        'invenio_records.jsonresolver': [
            'organisations = rero_ils.modules.organisations.jsonresolver',
            'locations = rero_ils.modules.locations.jsonresolver',
            'items = rero_ils.modules.items.jsonresolver',
            'patrons = rero_ils.modules.patrons.jsonresolver',
            'libraries = rero_ils.modules.libraries.jsonresolver',
            'patron_types = rero_ils.modules.patron_types.jsonresolver',
            'item_types = rero_ils.modules.item_types.jsonresolver',
            'documents = rero_ils.modules.documents.jsonresolver',
            'loans = rero_ils.modules.loans.jsonresolver',
            'documents_mef_person = \
                rero_ils.modules.documents.jsonresolver_mef_person'
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
