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

"""Default configuration for rero-ils.

You overwrite and set instance-specific configuration by either:

- Configuration file: ``<virtualenv prefix>/var/instance/invenio.cfg``
- Environment variables: ``APP_<variable name>``
"""

from __future__ import absolute_import, print_function

from datetime import timedelta
from functools import partial

from celery.schedules import crontab
from flask import request
from invenio_circulation.pidstore.pids import CIRCULATION_LOAN_FETCHER, \
    CIRCULATION_LOAN_MINTER, CIRCULATION_LOAN_PID_TYPE
from invenio_circulation.search.api import LoansSearch
from invenio_circulation.transitions.transitions import CreatedToPending, \
    ItemAtDeskToItemOnLoan, ItemInTransitHouseToItemReturned, \
    ItemOnLoanToItemInTransitHouse, ItemOnLoanToItemOnLoan, \
    ItemOnLoanToItemReturned, PendingToItemAtDesk, \
    PendingToItemInTransitPickup, ToItemOnLoan
from invenio_records_rest.facets import terms_filter
from invenio_records_rest.utils import allow_all, deny_all
from invenio_search import RecordsSearch

from rero_ils.modules.api import IlsRecordIndexer

from .modules.circ_policies.api import CircPolicy
from .modules.documents.api import Document, DocumentsIndexer
from .modules.fees.api import Fee
from .modules.holdings.api import Holding, HoldingsIndexer
from .modules.item_types.api import ItemType
from .modules.items.api import Item, ItemsIndexer
from .modules.items.permissions import can_create_item_factory, \
    can_update_delete_item_factory
from .modules.libraries.api import Library
from .modules.libraries.permissions import can_create_library_factory, \
    can_delete_library_factory, can_update_library_factory
from .modules.loans.api import Loan
from .modules.loans.permissions import can_list_loan_factory, \
    can_read_loan_factory
from .modules.loans.utils import can_be_requested, get_default_loan_duration, \
    get_extension_params, is_item_available_for_checkout, \
    loan_satisfy_circ_policies
from .modules.locations.api import Location
from .modules.locations.permissions import can_create_location_factory, \
    can_update_delete_location_factory
from .modules.notifications.api import Notification
from .modules.organisations.api import Organisation
from .modules.patron_types.api import PatronType
from .modules.patrons.api import Patron
from .modules.patrons.permissions import can_delete_patron_factory, \
    can_update_patron_factory
from .modules.persons.api import Person
from .modules.vendors.api import Vendor
from .permissions import can_access_organisation_patrons_factory, \
    can_access_organisation_records_factory, \
    can_create_organisation_records_factory, \
    can_delete_organisation_records_factory, \
    can_update_organisation_records_factory, \
    librarian_delete_permission_factory, librarian_permission_factory, \
    librarian_update_permission_factory


def _(x):
    """Identity function used to trigger string extraction."""
    return x


# Rate limiting
# =============
#: Storage for ratelimiter.
RATELIMIT_STORAGE_URL = 'redis://localhost:6379/3'
RATELIMIT_DEFAULT = '5000/second'
RATELIMIT_ENABLED = False

# I18N
# ====
#: Default language
BABEL_DEFAULT_LANGUAGE = 'en'
#: Default time zone
BABEL_DEFAULT_TIMEZONE = 'Europe/Zurich'
#: Other supported languages (do not include the default language in list).
I18N_LANGUAGES = [
    ('fr', _('French')),
    ('de', _('German')),
    ('it', _('Italian')),
]

# Base templates
# ==============
#: Global base template.
BASE_TEMPLATE = 'rero_ils/page.html'
THEME_BASE_TEMPLATE = BASE_TEMPLATE
#: Cover page base template (used for e.g. login/sign-up).
COVER_TEMPLATE = 'rero_ils/page_cover.html'
THEME_COVER_TEMPLATE = COVER_TEMPLATE
#: Footer base template.
THEME_FOOTER_TEMPLATE = 'rero_ils/footer.html'
#: Header base template.
HEADER_TEMPLATE = 'rero_ils/header.html'
#: Header base template.
THEME_HEADER_TEMPLATE = HEADER_TEMPLATE
#: Settings page template used for e.g. display user settings views.
THEME_SETTINGS_TEMPLATE = 'invenio_theme/page_settings.html'
#: Template for security pages.
SECURITY_LOGIN_USER_TEMPLATE = 'rero_ils/login_user.html'
SECURITY_REGISTER_USER_TEMPLATE = 'rero_ils/register_user.html'
SECURITY_FORGOT_PASSWORD_TEMPLATE = 'rero_ils/forgot_password.html'
SECURITY_RESET_PASSWORD_TEMPLATE = 'rero_ils/reset_password.html'
#: Template for error pages.
THEME_ERROR_TEMPLATE = 'rero_ils/page_error.html'
#: Template for tombstone page.
RECORDS_UI_TOMBSTONE_TEMPLATE = "rero_ils/tombstone.html"

RERO_ILS_THEME_SEARCH_ENDPOINT = '/search/documents'

# Logings
# =======
LOGGING_SENTRY_LEVEL = "ERROR"
LOGGING_SENTRY_CELERY = True

# Theme configuration
# ===================
#: Site name
THEME_SITENAME = _('rero-ils')
#: Use default frontpage.
THEME_FRONTPAGE = False
#: Frontpage title.
THEME_FRONTPAGE_TITLE = _('rero-ils')
#: Frontpage template.
THEME_FRONTPAGE_TEMPLATE = 'rero_ils/frontpage.html'

#: Template for including a tracking code for web analytics.
THEME_TRACKINGCODE_TEMPLATE = 'rero_ils/trackingcode.html'
THEME_JAVASCRIPT_TEMPLATE = 'rero_ils/javascript.html'
#: Brand logo.
THEME_LOGO = 'images/logo_rero_ils.png'

SEARCH_UI_JSTEMPLATE_RESULTS = (
    'templates/rero_ils/brief_view_documents.html'
)
SEARCH_UI_SEARCH_TEMPLATE = 'rero_ils/search.html'
SEARCH_UI_JSTEMPLATE_FACETS = 'templates/rero_ils/facets.html'
SEARCH_UI_JSTEMPLATE_RANGE = 'templates/rero_ils/range.html'
SEARCH_UI_JSTEMPLATE_COUNT = 'templates/rero_ils/count.html'
SEARCH_UI_JSTEMPLATE_PAGINATION = 'templates/rero_ils/pagination.html'
SEARCH_UI_SEARCH_MIMETYPE = 'application/rero+json'

SEARCH_UI_HEADER_TEMPLATE = 'rero_ils/search_header.html'
REROILS_SEARCHBAR_TEMPLATE = 'templates/rero_ils/searchbar.html'
RERO_ILS_EDITOR_TEMPLATE = 'rero_ils/editor.html'
SECURITY_LOGIN_USER_TEMPLATE = 'rero_ils/login_user.html'

# Email configuration
# ===================
#: Email address for support.
SUPPORT_EMAIL = "software@rero.ch"
#: Disable email sending by default.
MAIL_SUPPRESS_SEND = True

# Assets
# ======
#: Static files collection method (defaults to copying files).
# COLLECT_STORAGE = 'flask_collect.storage.file'

# Accounts
# ========
#: Email address used as sender of account registration emails.
SECURITY_EMAIL_SENDER = SUPPORT_EMAIL
#: Email subject for account registration emails.
SECURITY_EMAIL_SUBJECT_REGISTER = _("Welcome to RERO-ILS!")
#: Redis session storage URL.
ACCOUNTS_SESSION_REDIS_URL = 'redis://localhost:6379/1'
# Disable User Profiles
USERPROFILES = False
# make security blueprints available to the REST API
ACCOUNTS_REGISTER_BLUEPRINT = True


# Celery configuration
# ====================

BROKER_URL = 'amqp://guest:guest@localhost:5672/'
#: URL of message broker for Celery (default is RabbitMQ).
CELERY_BROKER_URL = 'amqp://guest:guest@localhost:5672/'
#: URL of backend for result storage (default is Redis).
CELERY_RESULT_BACKEND = 'redis://localhost:6379/2'
#: Scheduled tasks configuration (aka cronjobs).
CELERY_BEAT_SCHEDULE = {
    'indexer': {
        'task': 'invenio_indexer.tasks.process_bulk_queue',
        'schedule': timedelta(minutes=5),
    },
    'accounts': {
        'task': 'invenio_accounts.tasks.clean_session_table',
        'schedule': timedelta(minutes=60),
    },
    'ebooks-harvester': {
        'task': 'invenio_oaiharvester.tasks.list_records_from_dates',
        'schedule': timedelta(minutes=60),
        'kwargs': dict(name='ebooks'),
    },
    'notification-creation': {
        'task':
            'rero_ils.modules.notifications.tasks.create_over_and_due_soon_notifications',
        'schedule': crontab(minute="*/5")
        # TODO: in production set this up once a day
    },
    # 'mef-harvester': {
    #     'task': 'rero_ils.modules.apiharvester.tasks.harvest_records',
    #     'schedule': timedelta(minutes=60),
    #     'kwargs': dict(name='mef'),
    # },

}
CELERY_BROKER_HEARTBEAT = 0
INDEXER_BULK_REQUEST_TIMEOUT = 60

# Database
# ========
#: Database URI including user and password
SQLALCHEMY_DATABASE_URI = (
    'postgresql+psycopg2://rero-ils:rero-ils@localhost/rero-ils'
)
#: Disable Versioning due to Bad Performance
DB_VERSIONING = False
#: Disable warning
SQLALCHEMY_TRACK_MODIFICATIONS = False

# JSONSchemas
# ===========
#: Hostname used in URLs for local JSONSchemas.
JSONSCHEMAS_HOST = 'ils.rero.ch'
JSONSCHEMAS_ENDPOINT = '/schema'

# Flask configuration
# ===================
# See details on
# http://flask.pocoo.org/docs/0.12/config/#builtin-configuration-values

#: Secret key - each installation (dev, production, ...) needs a separate key.
#: It should be changed before deploying.
SECRET_KEY = 'CHANGE_ME'
#: Max upload size for form data via application/mulitpart-formdata.
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MiB
#: For dev. Set to false when testing on localhost in no debug mode
APP_ENABLE_SECURE_HEADERS = True

# TODO: review theses rules for security purposes
APP_DEFAULT_SECURE_HEADERS = {
    # disabled as https is not used by the application:
    # https is done by the haproxy
    'force_https': False,
    'force_https_permanent': False,
    'force_file_save': False,
    'frame_options': 'sameorigin',
    'frame_options_allow_from': None,
    'strict_transport_security': True,
    'strict_transport_security_preload': False,
    'strict_transport_security_max_age': 31556926,  # One year in seconds
    'strict_transport_security_include_subdomains': True,
    'content_security_policy': {
        'default-src': ['*'],
        'style-src': ['*', "'unsafe-inline'"],
        'script-src': [
            "'self'",
            "'unsafe-eval'",
            # '*.rero.ch',
            'https://www.googletagmanager.com',
            'https://www.google-analytics.com',
            'https://services.test.rero.ch',
            'https://services.rero.ch'
        ]
    },
    'content_security_policy_report_uri': None,
    'content_security_policy_report_only': False,
    'session_cookie_secure': True,
    'session_cookie_http_only': True,
}
#: Sets cookie with the secure flag by default
SESSION_COOKIE_SECURE = False
#: Since HAProxy and Nginx route all requests no matter the host header
#: provided, the allowed hosts variable is set to localhost. In production it
#: should be set to the correct host and it is strongly recommended to only
#: route correct hosts to the application.
APP_ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# OAI-PMH
# =======
OAISERVER_ID_PREFIX = 'oai:ils.rero.ch:'

# Debug
# =====
# Flask-DebugToolbar is by default enabled when the application is running in
# debug mode. More configuration options are available at
# https://flask-debugtoolbar.readthedocs.io/en/latest/#configuration

#: Switches off incept of redirects by Flask-DebugToolbar.
DEBUG_TB_INTERCEPT_REDIRECTS = False

# REST API Configuration
# ======================
RECORDS_REST_DEFAULT_CREATE_PERMISSION_FACTORY = librarian_permission_factory
"""Default create permission factory: reject any request."""

RECORDS_REST_DEFAULT_LIST_PERMISSION_FACTORY = librarian_permission_factory
"""Default list permission factory: allow all requests"""

RECORDS_REST_DEFAULT_READ_PERMISSION_FACTORY = librarian_permission_factory
"""Default read permission factory: check if the record exists."""

RECORDS_REST_DEFAULT_UPDATE_PERMISSION_FACTORY = librarian_update_permission_factory
"""Default update permission factory: reject any request."""

RECORDS_REST_DEFAULT_DELETE_PERMISSION_FACTORY = librarian_delete_permission_factory
"""Default delete permission factory: reject any request."""

RECORDS_REST_ENDPOINTS = dict(
    doc=dict(
        pid_type='doc',
        pid_minter='document_id',
        pid_fetcher='document_id',
        search_class=RecordsSearch,
        search_index='documents',
        search_type=None,
        indexer_class=DocumentsIndexer,
        record_serializers={
            'application/json': (
                'rero_ils.modules.serializers:json_v1_response'
            ),
            'application/rero+json': (
                'rero_ils.modules.documents.serializers:json_doc_response'
            )
        },
        search_serializers={
            'application/json': (
                'rero_ils.modules.serializers:json_v1_search'
            ),
            'application/rero+json': (
                'rero_ils.modules.documents.serializers:json_doc_search'
            ),
        },
        list_route='/documents/',
        record_class='rero_ils.modules.documents.api:Document',
        item_route='/documents/<pid(doc, record_class="rero_ils.modules.documents.api:Document"):pid_value>',
        # suggesters=dict(
        #     title={
        #         'completion': {
        #             'field': 'title_suggest',
        #             'size': 10,
        #             'skip_duplicates': True
        #         }
        #     },
        # ),
        default_media_type='application/json',
        max_result_window=5000000,
        search_factory_imp='rero_ils.query:document_search_factory',
        read_permission_factory_imp=allow_all,
        list_permission_factory_imp=allow_all
    ),
    item=dict(
        pid_type='item',
        pid_minter='item_id',
        pid_fetcher='item_id',
        search_class=RecordsSearch,
        search_index='items',
        search_type=None,
        indexer_class=ItemsIndexer,
        record_serializers={
            'application/json': (
                'rero_ils.modules.serializers:json_v1_response'
            )
        },
        search_serializers={
            'application/json': (
                'rero_ils.modules.serializers:json_v1_search'
            )
        },
        list_route='/items/',
        record_loaders={
            'application/json': lambda: Item(request.get_json()),
        },
        record_class='rero_ils.modules.items.api:Item',
        item_route='/items/<pid(item, record_class="rero_ils.modules.items.api:Item"):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='rero_ils.query:organisation_search_factory',
        read_permission_factory_imp=allow_all,
        list_permission_factory_imp=allow_all,
        create_permission_factory_imp=can_create_item_factory,
        update_permission_factory_imp=can_update_delete_item_factory,
        delete_permission_factory_imp=can_update_delete_item_factory,
    ),
    itty=dict(
        pid_type='itty',
        pid_minter='item_type_id',
        pid_fetcher='item_type_id',
        search_class=RecordsSearch,
        search_index='item_types',
        indexer_class=IlsRecordIndexer,
        search_type=None,
        record_serializers={
            'application/json': (
                'rero_ils.modules.serializers:json_v1_response'
            )
        },
        search_serializers={
            'application/json': (
                'rero_ils.modules.serializers:json_v1_search'
            )
        },
        list_route='/item_types/',
        record_loaders={
            'application/json': lambda: ItemType(request.get_json()),
        },
        record_class='rero_ils.modules.item_types.api:ItemType',
        item_route='/item_types/<pid(itty, record_class="rero_ils.modules.item_types.api:ItemType"):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='rero_ils.query:organisation_search_factory',
        read_permission_factory_imp=can_access_organisation_records_factory,
        create_permission_factory_imp=can_create_organisation_records_factory,
        update_permission_factory_imp=can_update_organisation_records_factory,
        delete_permission_factory_imp=can_delete_organisation_records_factory,
    ),
    hold=dict(
        pid_type='hold',
        pid_minter='holding_id',
        pid_fetcher='holding_id',
        search_class=RecordsSearch,
        search_index='holdings',
        indexer_class=HoldingsIndexer,
        search_type=None,
        record_serializers={
            'application/json': (
                'rero_ils.modules.serializers:json_v1_response'
            )
        },
        search_serializers={
            'application/json': (
                'rero_ils.modules.serializers:json_v1_search'
            )
        },
        list_route='/holdings/',
        record_loaders={
            'application/json': lambda: Holding(request.get_json()),
        },
        record_class='rero_ils.modules.holdings.api:Holding',
        item_route='/holdings/<pid(hold, record_class="rero_ils.modules.holdings.api:Holding"):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='rero_ils.query:organisation_search_factory',
        read_permission_factory_imp=allow_all,
        list_permission_factory_imp=allow_all,
        create_permission_factory_imp=can_create_organisation_records_factory,
        update_permission_factory_imp=can_update_organisation_records_factory,
        delete_permission_factory_imp=can_delete_organisation_records_factory,
    ),
    ptrn=dict(
        pid_type='ptrn',
        pid_minter='patron_id',
        pid_fetcher='patron_id',
        search_class=RecordsSearch,
        search_index='patrons',
        indexer_class=IlsRecordIndexer,
        search_type=None,
        record_serializers={
            'application/json': (
                'rero_ils.modules.serializers:json_v1_response'
            )
        },
        search_serializers={
            'application/json': (
                'rero_ils.modules.serializers:json_v1_search'
            )
        },
        list_route='/patrons/',
        record_loaders={
            'application/json': lambda: Patron(request.get_json()),
        },
        record_class='rero_ils.modules.patrons.api:Patron',
        item_route='/patrons/<pid(ptrn, record_class="rero_ils.modules.patrons.api:Patron"):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='rero_ils.query:organisation_search_factory',
        list_permission_factory_imp=can_access_organisation_patrons_factory,
        read_permission_factory_imp=can_access_organisation_records_factory,
        create_permission_factory_imp=can_create_organisation_records_factory,
        update_permission_factory_imp=can_update_patron_factory,
        delete_permission_factory_imp=can_delete_patron_factory,
    ),
    ptty=dict(
        pid_type='ptty',
        pid_minter='patron_type_id',
        pid_fetcher='patron_type_id',
        search_class=RecordsSearch,
        search_index='patron_types',
        search_type=None,
        indexer_class=IlsRecordIndexer,
        record_serializers={
            'application/json': (
                'rero_ils.modules.serializers:json_v1_response'
            )
        },
        search_serializers={
            'application/json': (
                'rero_ils.modules.serializers:json_v1_search'
            )
        },
        list_route='/patron_types/',
        record_loaders={
            'application/json': lambda: PatronType(request.get_json()),
        },
        record_class='rero_ils.modules.patron_types.api:PatronType',
        item_route='/patron_types/<pid(ptty, record_class="rero_ils.modules.patron_types.api:PatronType"):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='rero_ils.query:organisation_search_factory',
        read_permission_factory_imp=can_access_organisation_records_factory,
        create_permission_factory_imp=can_create_organisation_records_factory,
        update_permission_factory_imp=can_update_organisation_records_factory,
        delete_permission_factory_imp=can_create_organisation_records_factory,
    ),
    org=dict(
        pid_type='org',
        pid_minter='organisation_id',
        pid_fetcher='organisation_id',
        search_class=RecordsSearch,
        search_index='organisations',
        indexer_class=IlsRecordIndexer,
        search_type=None,
        record_serializers={
            'application/json': (
                'rero_ils.modules.serializers:json_v1_response'
            )
        },
        search_serializers={
            'application/json': (
                'rero_ils.modules.serializers:json_v1_search'
            )
        },
        list_route='/organisations/',
        record_loaders={
            'application/json': lambda: Organisation(request.get_json()),
        },
        record_class='rero_ils.modules.organisations.api:Organisation',
        item_route='/organisations/<pid(org, record_class="rero_ils.modules.organisations.api:Organisation"):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='rero_ils.query:search_factory',
        create_permission_factory_imp=deny_all,
        update_permission_factory_imp=deny_all,
        delete_permission_factory_imp=deny_all,
        read_permission_factory_imp=can_access_organisation_records_factory,
    ),
    lib=dict(
        pid_type='lib',
        pid_minter='library_id',
        pid_fetcher='library_id',
        search_class=RecordsSearch,
        search_index='libraries',
        indexer_class=IlsRecordIndexer,
        search_type=None,
        record_serializers={
            'application/json': (
                'rero_ils.modules.serializers:json_v1_response'
            )
        },
        search_serializers={
            'application/json': (
                'rero_ils.modules.serializers:json_v1_search'
            )
        },
        list_route='/libraries/',
        record_loaders={
            'application/json': lambda: Library(request.get_json()),
        },
        record_class='rero_ils.modules.libraries.api:Library',
        item_route='/libraries/<pid(lib, record_class="rero_ils.modules.libraries.api:Library"):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='rero_ils.query:organisation_search_factory',
        list_permission_factory_imp=can_access_organisation_patrons_factory,
        read_permission_factory_imp=can_access_organisation_records_factory,
        create_permission_factory_imp=can_create_library_factory,
        update_permission_factory_imp=can_update_library_factory,
        delete_permission_factory_imp=can_delete_library_factory,
    ),
    loc=dict(
        pid_type='loc',
        pid_minter='location_id',
        pid_fetcher='location_id',
        search_class=RecordsSearch,
        search_index='locations',
        indexer_class=IlsRecordIndexer,
        search_type=None,
        record_serializers={
            'application/json': (
                'rero_ils.modules.serializers:json_v1_response'
            )
        },
        search_serializers={
            'application/json': (
                'rero_ils.modules.serializers:json_v1_search'
            )
        },
        list_route='/locations/',
        record_loaders={
            'application/json': lambda: Location(request.get_json()),
        },
        record_class='rero_ils.modules.locations.api:Location',
        item_route='/locations/<pid(loc, record_class="rero_ils.modules.locations.api:Location"):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='rero_ils.query:organisation_search_factory',
        read_permission_factory_imp=can_access_organisation_records_factory,
        create_permission_factory_imp=can_create_location_factory,
        update_permission_factory_imp=can_update_delete_location_factory,
        delete_permission_factory_imp=can_update_delete_location_factory,
    ),
    pers=dict(
        pid_type='pers',
        pid_minter='person_id',
        pid_fetcher='person_id',
        search_class=RecordsSearch,
        search_index='persons',
        indexer_class=IlsRecordIndexer,
        search_type=None,
        record_serializers={
            'application/json': (
                'rero_ils.modules.serializers:json_v1_response'
            )
        },
        search_serializers={
            'application/json': (
                'rero_ils.modules.serializers:json_v1_search'
            )
        },
        list_route='/persons/',
        record_loaders={
            'application/json': lambda: Person(request.get_json()),
        },
        record_class='rero_ils.modules.persons.api:Person',
        item_route='/persons/<pid(pers, record_class="rero_ils.modules.persons.api:Person"):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='rero_ils.query:person_view_search_factory',
        read_permission_factory_imp=allow_all,
        list_permission_factory_imp=allow_all,
        create_permission_factory_imp=deny_all,
        update_permission_factory_imp=deny_all,
        delete_permission_factory_imp=deny_all
    ),
    cipo=dict(
        pid_type='cipo',
        pid_minter='circ_policy_id',
        pid_fetcher='circ_policy_id',
        search_class=RecordsSearch,
        search_index='circ_policies',
        indexer_class=IlsRecordIndexer,
        search_type=None,
        record_serializers={
            'application/json': (
                'rero_ils.modules.serializers:json_v1_response'
            )
        },
        search_serializers={
            'application/json': (
                'rero_ils.modules.serializers:json_v1_search'
            )
        },
        record_loaders={
            'application/json': lambda: CircPolicy(request.get_json()),
        },
        list_route='/circ_policies/',
        record_class='rero_ils.modules.circ_policies.api:CircPolicy',
        item_route='/circ_policies/<pid(cipo, record_class="rero_ils.modules.circ_policies.api:CircPolicy"):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='rero_ils.query:organisation_search_factory',
        read_permission_factory_imp=can_access_organisation_records_factory,
        create_permission_factory_imp=can_create_organisation_records_factory,
        update_permission_factory_imp=can_update_organisation_records_factory,
        delete_permission_factory_imp=can_delete_organisation_records_factory,
    ),
    notif=dict(
        pid_type='notif',
        pid_minter='notification_id',
        pid_fetcher='notification_id',
        search_class=RecordsSearch,
        search_index='notifications',
        indexer_class=IlsRecordIndexer,
        search_type=None,
        record_serializers={
            'application/json': (
                'rero_ils.modules.serializers:json_v1_response'
            )
        },
        search_serializers={
            'application/json': (
                'rero_ils.modules.serializers:json_v1_search'
            )
        },
        record_loaders={
            'application/json': lambda: Notification(request.get_json()),
        },
        list_route='/notifications/',
        record_class='rero_ils.modules.notifications.api:Notification',
        item_route='/notifications/<pid(notif, record_class="rero_ils.modules.notifications.api:Notification"):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='rero_ils.query:organisation_search_factory',
        read_permission_factory_imp=can_access_organisation_records_factory,
        create_permission_factory_imp=can_create_organisation_records_factory,
        update_permission_factory_imp=can_update_organisation_records_factory,
        delete_permission_factory_imp=can_delete_organisation_records_factory,
    ),
    fee=dict(
        pid_type='fee',
        pid_minter='fee_id',
        pid_fetcher='fee_id',
        search_class=RecordsSearch,
        search_index='fees',
        indexer_class=IlsRecordIndexer,
        search_type=None,
        record_serializers={
            'application/json': (
                'rero_ils.modules.serializers:json_v1_response'
            )
        },
        search_serializers={
            'application/json': (
                'rero_ils.modules.serializers:json_v1_search'
            )
        },
        record_loaders={
            'application/json': lambda: Fee(request.get_json()),
        },
        list_route='/fees/',
        record_class='rero_ils.modules.fees.api:Fee',
        item_route='/fees/<pid(fee, record_class="rero_ils.modules.fees.api:Fee"):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='rero_ils.query:organisation_search_factory',
        read_permission_factory_imp=can_access_organisation_records_factory,
        create_permission_factory_imp=can_create_organisation_records_factory,
        update_permission_factory_imp=can_update_organisation_records_factory,
        delete_permission_factory_imp=can_delete_organisation_records_factory,
    ),
    vndr=dict(
        pid_type='vndr',
        pid_minter='vendor_id',
        pid_fetcher='vendor_id',
        search_class=RecordsSearch,
        search_index='vendors',
        search_type=None,
        indexer_class=IlsRecordIndexer,
        record_serializers={
            'application/json': (
                'rero_ils.modules.serializers:json_v1_response'
            )
        },
        search_serializers={
            'application/json': (
                'rero_ils.modules.serializers:json_v1_search'
            )
        },
        record_loaders={
            'application/json': lambda: Vendor(request.get_json()),
        },
        record_class='rero_ils.modules.vendors.api:Vendor',
        list_route='/vendors/',
        item_route='/vendors/<pid(vndr, record_class="rero_ils.modules.vendors.api:Vendor"):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='rero_ils.query:organisation_search_factory',
        read_permission_factory_imp=can_access_organisation_records_factory,
        list_permission_factory_imp=can_access_organisation_patrons_factory,
        create_permission_factory_imp=can_create_organisation_records_factory,
        update_permission_factory_imp=can_update_organisation_records_factory,
        delete_permission_factory_imp=can_delete_organisation_records_factory,
    ),
)

SEARCH_UI_SEARCH_INDEX = 'documents'

# Default view code for all organisations view
# TODO: Should be taken into angular
RERO_ILS_SEARCH_GLOBAL_VIEW_CODE = 'global'

# Default number of results in facet
RERO_ILS_DEFAULT_AGGREGATION_SIZE = 30

# Number of aggregation by index name
RERO_ILS_AGGREGATION_SIZE = {
    'documents': 50
}

DOCUMENTS_AGGREGATION_SIZE = RERO_ILS_AGGREGATION_SIZE.get(
    'documents', RERO_ILS_DEFAULT_AGGREGATION_SIZE)
RECORDS_REST_FACETS = dict(
    documents=dict(
        aggs=dict(
            # The organisation or library facet is defined
            # dynamically during the query (query.py)
            document_type=dict(
                terms=dict(field='type', size=DOCUMENTS_AGGREGATION_SIZE)
            ),
            author__en=dict(
                terms=dict(field='facet_authors_en', size=DOCUMENTS_AGGREGATION_SIZE)
            ),
            author__fr=dict(
                terms=dict(field='facet_authors_fr', size=DOCUMENTS_AGGREGATION_SIZE)
            ),
            author__de=dict(
                terms=dict(field='facet_authors_de', size=DOCUMENTS_AGGREGATION_SIZE)
            ),
            author__it=dict(
                terms=dict(field='facet_authors_it', size=DOCUMENTS_AGGREGATION_SIZE)
            ),
            language=dict(
                terms=dict(field='language.value', size=DOCUMENTS_AGGREGATION_SIZE)
            ),
            subject=dict(
                terms=dict(field='facet_subjects', size=DOCUMENTS_AGGREGATION_SIZE)
            ),
            status=dict(
                terms=dict(field='holdings.items.status', size=DOCUMENTS_AGGREGATION_SIZE)
            )
        ),
        filters={
            _('document_type'): terms_filter('type'),
            _('organisation'): terms_filter(
                'holdings.organisation.organisation_pid'
            ),
            _('library'): terms_filter('holdings.organisation.library_pid'),
            _('author__en'): terms_filter('facet_authors_en'),
            _('author__fr'): terms_filter('facet_authors_fr'),
            _('author__de'): terms_filter('facet_authors_de'),
            _('author__it'): terms_filter('facet_authors_it'),
            _('language'): terms_filter('language.value'),
            _('subject'): terms_filter('facet_subjects'),
            _('status'): terms_filter('holdings.items.status'),
        }
    ),
    patrons=dict(
        aggs=dict(
            roles=dict(
                terms=dict(
                    field='roles',
                    # This does not take into account
                    # env variable or instance config file
                    size=RERO_ILS_AGGREGATION_SIZE.get(
                        'patrons', RERO_ILS_DEFAULT_AGGREGATION_SIZE)
                )
            )
        ),
        filters={
            _('roles'): terms_filter('roles')
        },
    ),
    persons=dict(
        aggs=dict(
            sources=dict(
                terms=dict(
                    field='sources',
                    # This does not take into account
                    # env variable or instance config file
                    size=RERO_ILS_AGGREGATION_SIZE.get(
                        'persons', RERO_ILS_DEFAULT_AGGREGATION_SIZE)
                )
            )
        ),
        filters={
            _('sources'): terms_filter('sources')
        }
    )
)

# Elasticsearch fields boosting by index
RERO_ILS_QUERY_BOOSTING = {
    'documents': {
        'title.*': 3,
        'titlesProper.*': 3,
        'authors.name': 2,
        'authors.name_*': 2,
        'publicationYearText': 2,
        'freeFormedPublicationDate': 2,
        'subjects.*': 2
    }
}

# sort options
indexes = [
    'documents',
    'items',
    'item_types',
    'patrons',
    'patron_types',
    'organisations',
    'libraries',
    'locations',
    'persons',
    'circ_policies',
    'loans'
]

RECORDS_REST_SORT_OPTIONS = dict()
RECORDS_REST_DEFAULT_SORT = dict()
for index in indexes:
    RECORDS_REST_SORT_OPTIONS[index] = dict(
        bestmatch=dict(
            fields=['-_score'], title='Best match', default_order='asc',
            order=1
        ),
        mostrecent=dict(
            fields=['-_created'], title='Most recent', default_order='desc',
            order=2
        ),
        lastupdated=dict(
            fields=['-_updated'], title='Last updated', default_order='desc',
            order=3
        ),
    )
    RECORDS_REST_DEFAULT_SORT[index] = dict(
        query='bestmatch', noquery='mostrecent')

RECORDS_REST_SORT_OPTIONS['loans'] = dict(
    transactiondate=dict(
        fields=['-transaction_date'], title='Transaction date',
        default_order='asc'
    )
)

RECORDS_REST_SORT_OPTIONS['libraries'] = dict(
    name=dict(
        fields=['name_sort'], title='Library name',
        default_order='asc'
    )
)


# Detailed View Configuration
# ===========================
RECORDS_UI_ENDPOINTS = {
    'doc': dict(
        pid_type='doc',
        route='/<string:viewcode>/documents/<pid_value>',
        template='rero_ils/detailed_view_documents.html',
        record_class='rero_ils.modules.documents.api:Document',
        view_imp='rero_ils.modules.documents.views.doc_item_view_method',

    ),
    'doc_export': dict(
        pid_type='doc',
        route='/<string:viewcode>/documents/<pid_value>/export/<format>',
        view_imp='invenio_records_ui.views.export',
        template='rero_ils/export_documents.html',
        record_class='rero_ils.modules.documents.api:Document',
    ),
    'item': dict(
        pid_type='item',
        route='/<string:viewcode>/items/<pid_value>',
        template='rero_ils/detailed_view_items.html',
        view_imp='rero_ils.modules.items.views.item_view_method',
        record_class='rero_ils.modules.items.api:Item',
        permission_factory_imp='rero_ils.permissions.'
                               'librarian_permission_factory',
    ),
    'hold': dict(
        pid_type='hold',
        route='/<string:viewcode>/holdings/<pid_value>',
        template='rero_ils/detailed_view_holdings.html',
        view_imp='rero_ils.modules.holdings.views.holding_view_method',
        record_class='rero_ils.modules.holdings.api:Holding',
        permission_factory_imp='rero_ils.permissions.'
                               'librarian_permission_factory',
    ),
    'pers': dict(
        pid_type='pers',
        route='/<string:viewcode>/persons/<pid_value>',
        template='rero_ils/detailed_view_persons.html',
        record_class='rero_ils.modules.persons.api:Person',
        view_imp='rero_ils.modules.persons.views.person_view_method'
    ),
}

RECORDS_UI_EXPORT_FORMATS = {
    'doc': {
        'json': dict(
            title='JSON',
            serializer='invenio_records_rest.serializers' ':json_v1',
            order=1,
        )
    }
}

RECORDS_JSON_SCHEMA = {
    'cipo': '/circ_policies/circ_policy-v0.0.1.json',
    'doc': '/documents/document-v0.0.1.json',
    'item': '/items/item-v0.0.1.json',
    'itty': '/item_types/item_type-v0.0.1.json',
    'lib': '/libraries/library-v0.0.1.json',
    'loc': '/locations/location-v0.0.1.json',
    'org': '/organisations/organisation-v0.0.1.json',
    'ptrn': '/patrons/patron-v0.0.1.json',
    'ptty': '/patron_types/patron_type-v0.0.1.json',
    'notif': '/notifications/notification-v0.0.1.json',
    'hold': '/holdings/holding-v0.0.1.json',
    'fee': '/fees/fee-v0.0.1.json',
    'pers': '/persons/person-v0.0.1.json',
    'vndr': '/vendors/vendor-v0.0.1.json',
}

# Login Configuration
# ===================
#: Allow password change by users.
SECURITY_CHANGEABLE = False

#: Allow user to confirm their email address.
SECURITY_CONFIRMABLE = True

#: Allow password recovery by users.
SECURITY_RECOVERABLE = True

#: Allow users to register.
SECURITY_REGISTERABLE = True

#: Allow sending registration email.
SECURITY_SEND_REGISTER_EMAIL = True

#: Allow users to login without first confirming their email address.
SECURITY_LOGIN_WITHOUT_CONFIRMATION = False

# Misc
INDEXER_REPLACE_REFS = True
INDEXER_RECORD_TO_INDEX = 'rero_ils.modules.indexer_utils.record_to_index'

SEARCH_UI_SEARCH_API = '/api/documents/'

# RERO Specific Configuration
# ===========================
RERO_ILS_BABEL_TRANSLATE_JSON_KEYS = [
    'title',
    'description',
    'placeholder',
    'validationMessage',
    'name',
    'add',
    '403',
]

RERO_ILS_APP_BASE_URL = 'https://ils.rero.ch'

RERO_ILS_PERMALINK_RERO_URL = 'http://data.rero.ch/01-{identifier}'
RERO_ILS_PERMALINK_BNF_URL = 'http://catalogue.bnf.fr/ark:/12148/{identifier}'

#: Git commit hash. If set, a link to github commit page
#: is displayed on RERO-ILS frontpage.
RERO_ILS_APP_GIT_HASH = None
#: rero-ils-ui Git commit hash. If set, a link to github commit
#: page is displayed on RERO-ILS frontpage.
RERO_ILS_UI_GIT_HASH = None

#: RERO_ILS MEF specific configurations.
RERO_ILS_MEF_URL = 'https://{host}/api/mef/'.format(host='mef.rero.ch')
RERO_ILS_MEF_RESULT_SIZE = 100


#: RERO_ILS specific configurations.
RERO_ILS_APP_IMPORT_BNF_EAN = 'http://catalogue.bnf.fr/api/SRU?'\
                              'version=1.2&operation=searchRetrieve'\
                              '&recordSchema=unimarcxchange&maximumRecords=1'\
                              '&startRecord=1&query=bib.ean all "{}"'

RERO_ILS_APP_HELP_PAGE = (
    'https://github.com/rero/rero-ils/wiki/Public-demo-help'
)

#: Cover service
RERO_ILS_THUMBNAIL_SERVICE_URL = 'https://services.test.rero.ch/cover'

#: Persons
RERO_ILS_PERSONS_MEF_SCHEMA = 'persons/person-v0.0.1.json'
RERO_ILS_PERSONS_SOURCES = ['rero', 'bnf', 'gnd']

RERO_ILS_PERSONS_LABEL_ORDER = {
    'fallback': 'fr',
    'fr': ['rero', 'bnf', 'gnd'],
    'de': ['gnd', 'rero', 'bnf'],
}

ADMIN_BASE_TEMPLATE = BASE_TEMPLATE

#: Invenio circulation configuration.
CIRCULATION_ITEM_EXISTS = Item.get_record_by_pid
CIRCULATION_PATRON_EXISTS = Patron.get_record_by_pid

CIRCULATION_ITEM_LOCATION_RETRIEVER = Item.item_location_retriever
CIRCULATION_DOCUMENT_RETRIEVER_FROM_ITEM = \
    Item.get_document_pid_by_item_pid
CIRCULATION_ITEMS_RETRIEVER_FROM_DOCUMENT = Item.get_items_pid_by_document_pid

CIRCULATION_DOCUMENT_EXISTS = Document.get_record_by_pid
CIRCULATION_ITEM_REF_BUILDER = Loan.loan_build_item_ref

# This is needed for absolute URL (url_for)
# SERVER_NAME = 'localhost:5000'
# CIRCULATION_REST_ENDPOINTS = {}
"""Default circulation policies when performing an action on a Loan."""

_LOANID_CONVERTER = 'pid(loanid,record_class="invenio_circulation.api:Loan")'
"""Loan PID url converter."""

CIRCULATION_REST_ENDPOINTS = dict(
    loanid=dict(
        pid_type=CIRCULATION_LOAN_PID_TYPE,
        pid_minter=CIRCULATION_LOAN_MINTER,
        pid_fetcher=CIRCULATION_LOAN_FETCHER,
        search_class=LoansSearch,
        search_type=None,
        record_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_response'),
        },
        search_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        record_loaders={
            'application/json': lambda: Loan(request.get_json()),
        },
        record_class='rero_ils.modules.loans.api:Loan',
        search_factory_imp='rero_ils.query:loans_search_factory',
        list_route='/loans/',
        item_route='/loans/<{0}:pid_value>'.format(
            _LOANID_CONVERTER),
        default_media_type='application/json',
        max_result_window=10000,
        error_handlers=dict(),
        read_permission_factory_imp=can_read_loan_factory,
        list_permission_factory_imp=can_list_loan_factory,
        create_permission_factory_imp=deny_all,
        update_permission_factory_imp=deny_all,
        delete_permission_factory_imp=deny_all
    )
)
"""Disable Circulation REST API."""

CIRCULATION_LOAN_TRANSITIONS = {
    'CREATED': [
        dict(dest='PENDING', trigger='request', transition=CreatedToPending),
        dict(
            dest='ITEM_ON_LOAN',
            trigger='checkout',
            transition=ToItemOnLoan,
        ),
    ],
    'PENDING': [
        dict(dest='ITEM_AT_DESK',
             transition=PendingToItemAtDesk, trigger='validate_request'),
        dict(dest='ITEM_IN_TRANSIT_FOR_PICKUP',
             transition=PendingToItemInTransitPickup,
             trigger='validate_request'),
        dict(dest='ITEM_ON_LOAN', transition=ToItemOnLoan, trigger='checkout'),
        dict(dest='CANCELLED', trigger='cancel')
    ],
    'ITEM_AT_DESK': [
        dict(
            dest='ITEM_ON_LOAN',
            transition=ItemAtDeskToItemOnLoan,
            trigger='checkout'
        ),
        dict(dest='CANCELLED', trigger='cancel')
    ],
    'ITEM_IN_TRANSIT_FOR_PICKUP': [
        dict(dest='ITEM_AT_DESK', trigger='receive'),
        dict(dest='CANCELLED', trigger='cancel')
    ],
    'ITEM_ON_LOAN': [
        dict(dest='ITEM_RETURNED',
             transition=ItemOnLoanToItemReturned, trigger='checkin'),
        dict(dest='ITEM_IN_TRANSIT_TO_HOUSE',
             transition=ItemOnLoanToItemInTransitHouse, trigger='checkin'),
        dict(dest='ITEM_ON_LOAN', transition=ItemOnLoanToItemOnLoan,
             trigger='extend'),
        dict(dest='CANCELLED', trigger='cancel')
    ],
    'ITEM_IN_TRANSIT_TO_HOUSE': [
        dict(dest='ITEM_RETURNED',
             transition=ItemInTransitHouseToItemReturned, trigger='receive'),
        dict(dest='CANCELLED', trigger='cancel')
    ],
    'ITEM_RETURNED': [],
    'CANCELLED': [],
}


CIRCULATION_POLICIES = dict(
    checkout=dict(
        duration_default=get_default_loan_duration,
        duration_validate=loan_satisfy_circ_policies,
        item_can_circulate=is_item_available_for_checkout
    ),
    extension=dict(
        from_end_date=False,
        duration_default=partial(
            get_extension_params, parameter_name='duration_default'),
        max_count=partial(
            get_extension_params, parameter_name='max_count'),
    ),
    request=dict(
        can_be_requested=can_be_requested
    )
)

# Define the default system currency in used. Each organisation can override
# this parameter using the 'default_currency' field
RERO_ILS_DEFAULT_CURRENCY = 'CHF'

WEBPACKEXT_PROJECT = 'rero_ils.webpack:project'
