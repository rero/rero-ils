# -*- coding: utf-8 -*-
#
# This file is part of RERO_ILS.
# Copyright (C) 2017 RERO.
#
# RERO_ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO_ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO_ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Default configuration for rero-ils.

You overwrite and set instance-specific configuration by either:

- Configuration file: ``<virtualenv prefix>/var/instance/invenio.cfg``
- Environment variables: ``APP_<variable name>``
"""

from __future__ import absolute_import, print_function

from datetime import timedelta

from invenio_circulation.pidstore.pids import CIRCULATION_LOAN_FETCHER, \
    CIRCULATION_LOAN_MINTER, CIRCULATION_LOAN_PID_TYPE
from invenio_circulation.search.api import LoansSearch
from invenio_circulation.transitions.transitions import CreatedToPending, \
    ItemAtDeskToItemOnLoan, ItemInTransitHouseToItemReturned, \
    ItemOnLoanToItemInTransitHouse, ItemOnLoanToItemOnLoan, \
    ItemOnLoanToItemReturned, PendingToItemAtDesk, \
    PendingToItemInTransitPickup, ToItemOnLoan
from invenio_records_rest.facets import range_filter, terms_filter
from invenio_records_rest.utils import allow_all, deny_all
from invenio_search import RecordsSearch

from rero_ils.modules.api import IlsRecordIndexer
from rero_ils.modules.loans.api import Loan

from .modules.items.api import Item, ItemsIndexer
from .modules.loans.utils import get_default_extension_duration, \
    get_default_extension_max_count, get_default_loan_duration, \
    is_item_available_for_checkout, is_loan_duration_valid
from .modules.patrons.api import Patron
from .permissions import librarian_permission_factory


def _(x):
    """Identity function used to trigger string extraction."""
    return x


# Rate limiting
# =============
#: Storage for ratelimiter.
RATELIMIT_STORAGE_URL = 'redis://localhost:6379/3'

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

THEME_HEADER_LOGIN_TEMPLATE = 'rero_ils/header_login.html'
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
    'mef-harvester': {
        'task': 'rero_ils.modules.apiharvester.tasks.harvest_records',
        'schedule': timedelta(minutes=60),
        'kwargs': dict(name='mef'),
    },
}

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
APP_DEFAULT_SECURE_HEADERS = {
    'force_https': True,
    'force_https_permanent': False,
    'force_file_save': False,
    'frame_options': 'sameorigin',
    'frame_options_allow_from': None,
    'strict_transport_security': True,
    'strict_transport_security_preload': False,
    'strict_transport_security_max_age': 31556926,  # One year in seconds
    'strict_transport_security_include_subdomains': True,
    'content_security_policy': {
        'default-src': ['*']
        # 'default-src': ["'self'"],
        # 'script-src': [
        #     "'self'",
        #     "'unsafe-inline'",
        #     '*.rero.ch',
        #     'https://www.googletagmanager.com',
        #     'https://www.google-analytics.com'
        # ],
        # 'img-src': [
        #     "'self'",
        #     'https://www.google-analytics.com',
        #     'http://images.amazon.com'
        # ]
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
OAISERVER_ID_PREFIX = 'oai:ils.test.rero.ch:'

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

RECORDS_REST_DEFAULT_UPDATE_PERMISSION_FACTORY = librarian_permission_factory
"""Default update permission factory: reject any request."""

RECORDS_REST_DEFAULT_DELETE_PERMISSION_FACTORY = librarian_permission_factory
"""Default delete permission factory: reject any request."""

RECORDS_REST_ENDPOINTS = dict(
    doc=dict(
        pid_type='doc',
        pid_minter='document_id',
        pid_fetcher='document_id',
        search_class=RecordsSearch,
        search_index='documents',
        search_type=None,
        indexer_class=IlsRecordIndexer,
        record_serializers={
            'application/json': (
                'invenio_records_rest.serializers' ':json_v1_response'
            )
        },
        search_serializers={
            'application/rero+json': (
                'rero_ils.modules.documents.serializers:json_doc_search'
            ),
            'application/json': (
                'invenio_records_rest.serializers:json_v1_search'
            ),
        },
        list_route='/documents/',
        item_route='/documents/<pid(doc):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='rero_ils.query:and_search_factory',
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
                'invenio_records_rest.serializers' ':json_v1_response'
            )
        },
        search_serializers={
            'application/rero+json': (
                'rero_ils.modules.serializers' ':json_v1_search'
            ),
            'application/json': (
                'invenio_records_rest.serializers' ':json_v1_search'
            ),
        },
        list_route='/items/',
        item_route='/items/<pid(item):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='rero_ils.query:and_search_factory',
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
                'invenio_records_rest.serializers' ':json_v1_response'
            )
        },
        search_serializers={
            'application/rero+json': (
                'rero_ils.modules.serializers' ':json_v1_search'
            ),
            'application/json': (
                'invenio_records_rest.serializers' ':json_v1_search'
            ),
        },
        list_route='/item_types/',
        item_route='/item_types/<pid(itty):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='rero_ils.query:and_search_factory',
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
                'invenio_records_rest.serializers' ':json_v1_response'
            )
        },
        search_serializers={
            'application/rero+json': (
                'rero_ils.modules.serializers' ':json_v1_search'
            ),
            'application/json': (
                'invenio_records_rest.serializers' ':json_v1_search'
            ),
        },
        list_route='/patrons/',
        item_route='/patrons/<pid(ptrn):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='rero_ils.query:and_search_factory',
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
                'invenio_records_rest.serializers' ':json_v1_response'
            )
        },
        search_serializers={
            'application/rero+json': (
                'rero_ils.modules.serializers' ':json_v1_search'
            ),
            'application/json': (
                'invenio_records_rest.serializers' ':json_v1_search'
            ),
        },
        list_route='/patron_types/',
        item_route='/patron_types/<pid(ptty):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='rero_ils.query:and_search_factory',
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
            'application/rero+json': (
                'rero_ils.modules.serializers' ':json_v1_response'
            ),
            'application/json': (
                'invenio_records_rest.serializers' ':json_v1_response'
            )
        },
        search_serializers={
            'application/rero+json': (
                'rero_ils.modules.serializers' ':json_v1_search'
            ),
            'application/json': (
                'invenio_records_rest.serializers' ':json_v1_search'
            ),
        },
        list_route='/libraries/',
        item_route='/libraries/<pid(lib):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='rero_ils.query:and_search_factory',
        delete_permission_factory_imp=deny_all
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
                'invenio_records_rest.serializers' ':json_v1_response'
            )
        },
        search_serializers={
            'application/rero+json': (
                'rero_ils.modules.serializers' ':json_v1_search'
            ),
            'application/json': (
                'invenio_records_rest.serializers' ':json_v1_search'
            ),
        },
        list_route='/locations/',
        item_route='/locations/<pid(loc):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='rero_ils.query:and_search_factory',
    ),
    pers=dict(
        pid_type='pers',
        pid_minter='mef_person_id',
        pid_fetcher='mef_person_id',
        search_class=RecordsSearch,
        search_index='persons',
        search_type=None,
        record_serializers={
            'application/json': (
                'invenio_records_rest.serializers' ':json_v1_response'
            )
        },
        search_serializers={
            'application/rero+json': (
                'rero_ils.modules.serializers' ':json_v1_search'
            ),
            'application/json': (
                'invenio_records_rest.serializers' ':json_v1_search'
            ),
        },
        list_route='/persons/',
        item_route='/persons/<pid(pers):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='rero_ils.query:and_search_factory',
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
                'invenio_records_rest.serializers' ':json_v1_response'
            )
        },
        search_serializers={
            'application/rero+json': (
                'rero_ils.modules.serializers' ':json_v1_search'
            ),
            'application/json': (
                'invenio_records_rest.serializers' ':json_v1_search'
            ),
        },
        list_route='/circ_policies/',
        item_route='/circ_policies/<pid(cipo):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='rero_ils.query:and_search_factory',
    ),
)

SEARCH_UI_SEARCH_INDEX = 'documents'

RERO_ILS_APP_CONFIG_FACETS = {
    'documents': {
        'order': [
            'document_type',
            'library',
            'author',
            'language',
            'subject',
            'status',
        ],
        'expand': ['document_type'],
    },
    'patrons': {'order': ['roles'], 'expand': ['roles']},
    'persons': {'order': ['sources'], 'expand': ['sources']},
}

RECORDS_REST_FACETS = {
    'documents': dict(
        aggs=dict(
            years=dict(
                date_histogram=dict(
                    field='publicationYear', interval='year', format='yyyy'
                )
            ),
            document_type=dict(terms=dict(field='type')),
            library=dict(
                terms=dict(field='items.library_pid'),
            ),
            author=dict(terms=dict(field='facet_authors')),
            language=dict(terms=dict(field='languages.language')),
            subject=dict(terms=dict(field='subject')),
            status=dict(terms=dict(field='items.status')),
        ),
        filters={
            _('document_type'): terms_filter('type'),
            _('library'): terms_filter('items.library_pid'),
            _('author'): terms_filter('facet_authors'),
            _('language'): terms_filter('languages.language'),
            _('subject'): terms_filter('subject'),
            _('status'): terms_filter('items.status'),
        },
        post_filters={
            _('years'): range_filter(
                'publicationYear', format='yyyy', end_date_math='/y'
            )
        },
    ),
    'patrons': dict(
        aggs=dict(roles=dict(terms=dict(field='roles'))),
        filters={_('roles'): terms_filter('roles')},
    ),
    'persons': dict(
        aggs=dict(sources=dict(terms=dict(field='sources'))),
        filters={_('sources'): terms_filter('sources')},
    ),
}

# sort
RECORDS_REST_SORT_OPTIONS = {
    'documents': dict(
        bestmatch=dict(
            fields=['_score'], title='Best match', default_order='asc'
        ),
        mostrecent=dict(
            fields=['-_created'], title='Most recent', default_order='desc'
        ),
    )
}

# default sort
RECORDS_REST_DEFAULT_SORT = {
    'documents': dict(query='bestmatch', noquery='mostrecent')
}

# Detailed View Configuration
# ===========================
RECORDS_UI_ENDPOINTS = {
    'doc': dict(
        pid_type='doc',
        route='/documents/<pid_value>',
        template='rero_ils/detailed_view_documents.html',
        record_class='rero_ils.modules.documents.api:Document',
        view_imp='rero_ils.modules.documents.views.doc_item_view_method',

    ),
    'doc_export': dict(
        pid_type='doc',
        route='/documents/<pid_value>/export/<format>',
        view_imp='invenio_records_ui.views.export',
        template='rero_ils/export_documents.html',
        record_class='rero_ils.modules.documents.api:Document',
    ),
    'item': dict(
        pid_type='item',
        route='/items/<pid_value>',
        template='rero_ils/detailed_view_items.html',
        view_imp='rero_ils.modules.items.views.item_view_method',
        record_class='rero_ils.modules.items.api:Item',
        permission_factory_imp='rero_ils.permissions.'
                               'librarian_permission_factory',
    ),
    'pers': dict(
        pid_type='pers',
        route='/persons/<pid_value>',
        template='rero_ils/detailed_view_persons.html',
        record_class='rero_ils.modules.mef_persons.api:MefPerson',
    )
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

RERO_ILS_PERMALINK_RERO_URL = 'http://data.rero.ch/01-{identifier}'
RERO_ILS_PERMALINK_BNF_URL = 'http://catalogue.bnf.fr/ark:/12148/{identifier}'

#: RERO_ILS MEF specificconfigurations.
RERO_ILS_HARVESTING_MEF_URL = 'http://mef.test.rero.ch/api/mef'
RERO_ILS_MEF_RESULT_SIZE = 100


#: RERO_ILS specific configurations.
RERO_ILS_APP_IMPORT_BNF_EAN = 'http://catalogue.bnf.fr/api/SRU?'\
                              'version=1.2&operation=searchRetrieve'\
                              '&recordSchema=unimarcxchange&maximumRecords=1'\
                              '&startRecord=1&query=bib.ean%%20all%%20"%s"'

RERO_ILS_APP_HELP_PAGE = (
    'https://github.com/rero/rero-ils/wiki/Public-demo-help'
)

#: Cover service
RERO_ILS_THUMBNAIL_SERVICE_URL = 'https://services.test.rero.ch/cover'

#: Persons
RERO_ILS_PERSONS_MEF_SCHEMA = 'persons/mef_person-v0.0.1.json'
RERO_ILS_PERSONS_SOURCES = ['rero', 'bnf', 'gnd']

RERO_ILS_PERSONS_LABEL_ORDER = {
    'fallback': 'fr',
    'fr': ['rero', 'bnf', 'gnd'],
    'de': ['gnd', 'rero', 'bnf'],
}

ADMIN_PERMISSION_FACTORY = 'rero_ils.permissions.admin_permission_factory'
ADMIN_BASE_TEMPLATE = BASE_TEMPLATE

#: Invenio circulation configuration.
CIRCULATION_ITEM_EXISTS = Item.get_record_by_pid
CIRCULATION_PATRON_EXISTS = Patron.get_record_by_pid

CIRCULATION_ITEM_LOCATION_RETRIEVER = Item.item_location_retriever
CIRCULATION_DOCUMENT_RETRIEVER_FROM_ITEM = \
    Item.get_document_pid_by_item_pid
CIRCULATION_ITEMS_RETRIEVER_FROM_DOCUMENT = Item.get_items_pid_by_document_pid

# This is needed for absolute URL (url_for)
SERVER_NAME = 'localhost:5000'
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
        record_class=Loan,
        record_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_response'),
        },
        search_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        list_route='/circulation/loans/',
        item_route='/circulation/loans/<{0}:pid_value>'.format(
            _LOANID_CONVERTER),
        default_media_type='application/json',
        max_result_window=10000,
        error_handlers=dict(),
        read_permission_factory_imp=deny_all,
        list_permission_factory_imp=deny_all,
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
             transition=PendingToItemAtDesk, trigger='validate'),
        dict(dest='ITEM_IN_TRANSIT_FOR_PICKUP',
             transition=PendingToItemInTransitPickup, trigger='validate'),
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
        duration_validate=is_loan_duration_valid,
        item_available=is_item_available_for_checkout
    ),
    extension=dict(
        from_end_date=True,
        duration_default=get_default_extension_duration,
        max_count=get_default_extension_max_count
    ),
)
