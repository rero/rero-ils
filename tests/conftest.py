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

"""Common pytest fixtures and plugins."""
import json
import os
import shutil
import sys
import tempfile
from os.path import dirname, join

import pytest
from dotenv import load_dotenv

pytest_plugins = (
    'celery.contrib.pytest',
    'fixtures.circulation',
    'fixtures.metadata',
    'fixtures.organisations',
    'fixtures.acquisition',
    'fixtures.sip2',
    'fixtures.basics',
    'fixtures.mef'
)


@pytest.fixture(scope='module')
def search(appctx):
    """Setup and teardown all registered Elasticsearch indices.

    Scope: module
    This fixture will create all registered indexes in Elasticsearch and remove
    once done. Fixtures that perform changes (e.g. index or remove documents),
    should used the function-scoped :py:data:`es_clear` fixture to leave the
    indexes clean for the following tests.
    """
    from invenio_search import current_search, current_search_client
    from invenio_search.errors import IndexAlreadyExistsError

    try:
        list(current_search.put_templates())
    except IndexAlreadyExistsError:
        current_search_client.indices.delete_template('*')
        list(current_search.put_templates())

    try:
        list(current_search.create())
    except IndexAlreadyExistsError:
        list(current_search.delete(ignore=[404]))
        list(current_search.create())
    current_search_client.indices.refresh()

    try:
        yield current_search_client
    finally:
        current_search_client.indices.delete(index='*')
        current_search_client.indices.delete_template('*')


@pytest.fixture(scope="module")
def data():
    """Load fixture data file."""
    with open(join(dirname(__file__), 'data/data.json')) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def role_policies_data():
    """Load fixture role policies data file."""
    path = 'data/policies/role_policies.json'
    with open(join(dirname(__file__), path)) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def system_role_policies_data():
    """Load fixture role policies data file."""
    path = 'data/policies/system_role_policies.json'
    with open(join(dirname(__file__), path)) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def acquisition():
    """Load fixture acquisition file."""
    with open(join(dirname(__file__), 'data/acquisition.json')) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def holdings():
    """Load fixture holdings file."""
    with open(join(dirname(__file__), 'data/holdings.json')) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def local_fields():
    """Load local fields file."""
    with open(join(dirname(__file__), 'data/local_fields.json')) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def mef_entities():
    """Load MEF entities file."""
    with open(join(dirname(__file__), 'data/mef.json')) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def csv_header():
    """Load json headers."""
    return [
        ('Accept', 'text/csv'),
        ('Content-Type', 'application/json')
    ]


@pytest.fixture(scope="session")
def ris_header():
    """Load json headers."""
    return [
        ('Accept', 'application/x-research-info-systems'),
        ('Content-Type', 'application/json')
    ]


@pytest.fixture(scope="session")
def json_header():
    """Load json headers."""
    return [
        ('Accept', 'application/json'),
        ('Content-Type', 'application/json')
    ]


@pytest.fixture(scope="session")
def rero_marcxml_header():
    """Load marcxml headers."""
    return [
        ('Accept', 'application/json'),
        ('Content-Type', 'application/marcxml+xml')
    ]


@pytest.fixture(scope="session")
def rero_json_header():
    """Load json headers."""
    return [
        ('Accept', 'application/rero+json'),
        ('Content-Type', 'application/json')
    ]


@pytest.fixture(scope="session")
def export_json_header():
    """Load json headers."""
    return [
        ('Accept', 'application/export+json'),
        ('Content-Type', 'application/json')
    ]


@pytest.fixture(scope="session")
def can_delete_json_header():
    """Load can_delete json headers."""
    return [
        ('Accept', 'application/can-delete+json'),
        ('Content-Type', 'application/json')
    ]


@pytest.fixture(scope='module')
def app_config(app_config):
    """Create temporary instance dir for each test."""
    app_config['CELERY_BROKER_URL'] = 'memory://'
    app_config['RATELIMIT_STORAGE_URL'] = 'memory://'
    app_config['CACHE_TYPE'] = 'simple'
    app_config['SEARCH_ELASTIC_HOSTS'] = None
    app_config['SQLALCHEMY_DATABASE_URI'] = \
        'postgresql+psycopg2://rero-ils:rero-ils@localhost/rero-ils'
    app_config['DB_VERSIONING'] = True
    app_config['CELERY_CACHE_BACKEND'] = "memory"
    app_config['CELERY_RESULT_BACKEND'] = "cache"
    app_config['CELERY_TASK_ALWAYS_EAGER'] = True
    app_config['CELERY_TASK_EAGER_PROPAGATES'] = True
    help_test_dir = join(dirname(__file__), 'data', 'help')
    app_config['WIKI_CONTENT_DIR'] = help_test_dir
    app_config['WIKI_UPLOAD_FOLDER'] = join(help_test_dir, 'files')
    app_config['CACHE_REDIS_URL'] = 'redis://localhost:6379/0'
    app_config['ACCOUNTS_SESSION_REDIS_URL'] = 'redis://localhost:6379/1'
    app_config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/2'
    app_config['RATELIMIT_STORAGE_URL'] = 'redis://localhost:6379/3'
    app_config['CELERY_REDIS_SCHEDULER_URL'] = 'redis://localhost:6379/4'
    app_config['RERO_IMPORT_CACHE'] = 'redis://localhost:6379/5'
    app_config['WTF_CSRF_ENABLED'] = False
    # enable operation logs validation for the tests
    app_config['RERO_ILS_ENABLE_OPERATION_LOG_VALIDATION'] = True
    app_config['RERO_ILS_MEF_CONFIG'] = {
        'agents': {
            'base_url': 'https://mef.rero.ch/api/agents',
            'sources': ['idref', 'gnd']
        },
        'concepts': {
            'base_url': 'https://mef.rero.ch/api/concepts',
            'sources': ['idref']
        },
        'concepts-genreForm': {
            'base_url': 'https://mef.rero.ch/api/concepts',
            'sources': ['idref'],
            'filters': [
                {'idref.bnf_type': 'sujet Rameau'}
            ]
        },
        'places': {
            'base_url': 'https://mef.rero.ch/api/places',
            'sources': ['idref']
        },
    }
    return app_config


@pytest.fixture(scope='module')
def instance_path():
    """Temporary instance path.

    Scope: module

    This fixture creates a temporary directory if the
    environment variable ``INVENIO_INSTANCE_PATH`` is not be set.
    This directory is then automatically removed.
    """
    # load .env, .flaskenv
    load_dotenv()
    invenio_instance_path = os.environ.get('INVENIO_INSTANCE_PATH')
    invenio_static_folder = os.environ.get('INVENIO_STATIC_FOLDER')
    path = invenio_instance_path
    # static folder
    if not invenio_static_folder:
        if invenio_instance_path:
            os.environ['INVENIO_STATIC_FOLDER'] = os.path.join(
                invenio_instance_path, 'static')
        else:
            os.environ['INVENIO_STATIC_FOLDER'] = os.path.join(
                sys.prefix, 'var/instance/static')
    # instance path
    if not path:
        path = tempfile.mkdtemp()
        os.environ['INVENIO_INSTANCE_PATH'] = path
    yield path
    # clean static folder variable
    if not invenio_static_folder:
        os.environ.pop('INVENIO_STATIC_FOLDER', None)
    # clean instance path variable and remove temp dir
    if not invenio_instance_path:
        os.environ.pop('INVENIO_INSTANCE_PATH', None)
        shutil.rmtree(path)


@pytest.fixture(scope='module')
def mef_agents_url(app):
    """Get MEF agent URL from config."""
    return app.config\
        .get('RERO_ILS_MEF_CONFIG', {})\
        .get('agents', {})\
        .get('base_url')


@pytest.fixture(scope='module')
def mef_concepts_url(app):
    """Get MEF agent URL from config."""
    return app.config\
        .get('RERO_ILS_MEF_CONFIG', {})\
        .get('concepts', {})\
        .get('base_url')


@pytest.fixture(scope="module")
def bnf_ean_any_123():
    """Load bnf ean any 123 xml file."""
    file_name = join(dirname(__file__), 'data/xml/bnf/bnf_ean_any_123.xml')
    with open(file_name, 'rb') as file:
        return file.read()


@pytest.fixture(scope="module")
def bnf_ean_any_9782070541270():
    """Load bnf ean any 9782070541270 xml file."""
    file_name = join(
        dirname(__file__), 'data/xml/bnf/bnf_ean_any_9782070541270.xml')
    with open(file_name, 'rb') as file:
        return file.read()


@pytest.fixture(scope="module")
def bnf_ean_any_9782072862014():
    """Load bnf ean any 9782072862014 xml file."""
    file_name = join(
        dirname(__file__), 'data/xml/bnf/bnf_ean_any_9782072862014.xml')
    with open(file_name, 'rb') as file:
        return file.read()


@pytest.fixture(scope="module")
def bnf_recordid_all_FRBNF370903960000006():
    """Load bnf recordid all FRBNF370903960000006 xml file."""
    file_name = join(
        dirname(__file__),
        'data/xml/bnf/bnf_recordid_all_FRBNF370903960000006.xml'
    )
    with open(file_name, 'rb') as file:
        return file.read()


@pytest.fixture(scope="module")
def bnf_anywhere_all_peter():
    """Load bnf anywhere all peter xml file."""
    file_name = join(
        dirname(__file__),
        'data/xml/bnf/bnf_anywhere_all_peter.xml'
    )
    with open(file_name, 'rb') as file:
        return file.read()


@pytest.fixture(scope="module")
def loc_isbn_all_123():
    """Load LoC isbn all 123 xml file."""
    file_name = join(dirname(__file__), 'data/xml/loc/loc_isbn_all_123.xml')
    with open(file_name, 'rb') as file:
        return file.read()


@pytest.fixture(scope="module")
def loc_isbn_all_9781604689808():
    """Load LoC isbn all 9781604689808 xml file."""
    file_name = join(
        dirname(__file__), 'data/xml/loc/loc_isbn_all_9781604689808.xml')
    with open(file_name, 'rb') as file:
        return file.read()


@pytest.fixture(scope="module")
def loc_isbn_all_9780821417478():
    """Load LoC isbn all 9780821417478 xml file."""
    file_name = join(
        dirname(__file__), 'data/xml/loc/loc_isbn_all_9780821417478.xml')
    with open(file_name, 'rb') as file:
        return file.read()


@pytest.fixture(scope="module")
def loc_anywhere_all_samuelson():
    """Load LoC anywhere_all samuelson xml file."""
    file_name = join(
        dirname(__file__), 'data/xml/loc/loc_anywhere_all_samuelson.xml')
    with open(file_name, 'rb') as file:
        return file.read()


@pytest.fixture(scope="module")
def loc_recordid_all_2014043016():
    """Load LoC recordid 2014043016 xml file."""
    file_name = join(
        dirname(__file__), 'data/xml/loc/loc_recordid_all_2014043016.xml')
    with open(file_name, 'rb') as file:
        return file.read()


@pytest.fixture(scope="module")
def loc_without_010():
    """Load LoC without 010."""
    file_name = join(dirname(__file__), 'data/xml/loc/loc_without_010.xml')
    with open(file_name, 'rb') as file:
        return file.read()


@pytest.fixture(scope="module")
def dnb_isbn_123():
    """Load DNB isbn 123 xml file."""
    file_name = join(dirname(__file__), 'data/xml/dnb/dnb_isbn_123.xml')
    with open(file_name, 'rb') as file:
        return file.read()


@pytest.fixture(scope="module")
def dnb_isbn_9783862729852():
    """Load DNB isbn 9783862729852 file."""
    file_name = join(
        dirname(__file__), 'data/xml/dnb/dnb_isbn_9783862729852.xml')
    with open(file_name, 'rb') as file:
        return file.read()


@pytest.fixture(scope="module")
def dnb_isbn_3858818526():
    """Load DNB isbn 3858818526 file."""
    file_name = join(dirname(__file__), 'data/xml/dnb/dnb_isbn_3858818526.xml')
    with open(file_name, 'rb') as file:
        return file.read()


@pytest.fixture(scope="module")
def dnb_samuelson():
    """Load DNB samuelson file."""
    file_name = join(dirname(__file__), 'data/xml/dnb/dnb_samuelson.xml')
    with open(file_name, 'rb') as file:
        return file.read()


@pytest.fixture(scope="module")
def dnb_recordid_1214325203():
    """Load dnb recordid 1214325203 file."""
    file_name = join(
        dirname(__file__), 'data/xml/dnb/dnb_recordid_1214325203.xml')
    with open(file_name, 'rb') as file:
        return file.read()


@pytest.fixture(scope="module")
def slsp_anywhere_123():
    """Load slsp anywhere 123 file."""
    file_name = join(dirname(__file__), 'data/xml/slsp/slsp_anywhere_123.xml')
    with open(file_name, 'rb') as file:
        return file.read()


@pytest.fixture(scope="module")
def slsp_isbn_9782296076648():
    """Load slsp isbn 9782296076648 file."""
    file_name = join(
        dirname(__file__), 'data/xml/slsp/slsp_isbn_9782296076648.xml')
    with open(file_name, 'rb') as file:
        return file.read()


@pytest.fixture(scope="module")
def slsp_isbn_3908497272():
    """Load slsp isbn 3908497272 file."""
    file_name = join(
        dirname(__file__), 'data/xml/slsp/slsp_isbn_3908497272.xml')
    with open(file_name, 'rb') as file:
        return file.read()


@pytest.fixture(scope="module")
def slsp_samuelson():
    """Load slsp samuelson file."""
    file_name = join(dirname(__file__), 'data/xml/slsp/slsp_samuelson.xml')
    with open(file_name, 'rb') as file:
        return file.read()


@pytest.fixture(scope="module")
def slsp_recordid_9910137():
    """Load slsp recordid 991013724759705501 file."""
    file_name = join(
        dirname(__file__), 'data/xml/slsp/slsp_recordid_9910137.xml')
    with open(file_name, 'rb') as file:
        return file.read()


@pytest.fixture(scope="module")
def ugent_anywhere_123():
    """Load ugent anywhere 123 file."""
    file_name = join(
        dirname(__file__), 'data/xml/ugent/ugent_anywhere_123.xml')
    with open(file_name, 'rb') as file:
        return file.read()


@pytest.fixture(scope="module")
def ugent_isbn_9781108422925():
    """Load ugent isbn 9781108422925 file."""
    file_name = join(
        dirname(__file__), 'data/xml/ugent/ugent_isbn_9781108422925.xml')
    with open(file_name, 'rb') as file:
        return file.read()


@pytest.fixture(scope="module")
def ugent_isbn_9780415773867():
    """Load ugent isbn 9780415773867 file."""
    file_name = join(
        dirname(__file__), 'data/xml/ugent/ugent_isbn_9780415773867.xml')
    with open(file_name, 'rb') as file:
        return file.read()


@pytest.fixture(scope="module")
def ugent_samuelson():
    """Load ugent samuelson file."""
    file_name = join(
        dirname(__file__), 'data/xml/ugent/ugent_samuelson.xml')
    with open(file_name, 'rb') as file:
        return file.read()


@pytest.fixture(scope="module")
def ugent_recordid_001247835():
    """Load ugent recordid 001247835 file."""
    file_name = join(
        dirname(__file__), 'data/xml/ugent/ugent_recordid_001247835.xml')
    with open(file_name, 'rb') as file:
        return file.read()


@pytest.fixture(scope="module")
def ugent_book_without_26X():
    """Load ugent book without 26X file."""
    file_name = join(
        dirname(__file__), 'data/xml/ugent/ugent_book_without_26X.xml')
    with open(file_name, 'rb') as file:
        return file.read()


@pytest.fixture(scope="module")
def kul_anywhere_123():
    """Load kul anywhere 123 file."""
    file_name = join(dirname(__file__), 'data/xml/kul/kul_anywhere_123.xml')
    with open(file_name, 'rb') as file:
        return file.read()


@pytest.fixture(scope="module")
def kul_isbn_9782265089419():
    """Load kul isbn 9782265089419 file."""
    file_name = join(
        dirname(__file__), 'data/xml/kul/kul_isbn_9782265089419.xml')
    with open(file_name, 'rb') as file:
        return file.read()


@pytest.fixture(scope="module")
def kul_isbn_2804600068():
    """Load kul isbn 2804600068 file."""
    file_name = join(dirname(__file__), 'data/xml/kul/kul_isbn_2804600068.xml')
    with open(file_name, 'rb') as file:
        return file.read()


@pytest.fixture(scope="module")
def kul_samuelson():
    """Load kul samuelson file."""
    file_name = join(dirname(__file__), 'data/xml/kul/kul_samuelson.xml')
    with open(file_name, 'rb') as file:
        return file.read()


@pytest.fixture(scope="module")
def kul_recordid_9992876296301471():
    """Load kul recordid 9992876296301471 file."""
    file_name = join(
        dirname(__file__), 'data/xml/kul/kul_recordid_99928762.xml')
    with open(file_name, 'rb') as file:
        return file.read()


@pytest.fixture(scope="module")
def kul_book_without_26X():
    """Load kul book without 26X file."""
    file_name = join(
        dirname(__file__), 'data/xml/kul/kul_book_without_26X.xml')
    with open(file_name, 'rb') as file:
        return file.read()
