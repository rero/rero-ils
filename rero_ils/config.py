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

from invenio_circulation.transitions.transitions import CreatedToPending, \
    ItemAtDeskToItemOnLoan, ItemInTransitHouseToItemReturned, \
    ItemOnLoanToItemInTransitHouse, ItemOnLoanToItemOnLoan, \
    ItemOnLoanToItemReturned, PendingToItemAtDesk, \
    PendingToItemInTransitPickup, ToItemOnLoan
from invenio_records_rest.facets import range_filter, terms_filter
from invenio_search import RecordsSearch

from .modules.circ_policies.api import CircPolicy
from .modules.documents_items.api import DocumentsWithItems
from .modules.items.api import Item
from .modules.items_types.api import ItemType
from .modules.libraries_locations.api import LibraryWithLocations
# from .modules.loans.api import Loan
from .modules.locations.api import Location
from .modules.mef.api import MefPerson
from .modules.organisations_libraries.api import OrganisationWithLibraries
from .modules.patrons.api import Patron
from .modules.patrons_types.api import PatronType
from .permissions import cataloguer_permission_factory


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
    'templates/rero_ils/brief_view_documents_items.html'
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
JSONSCHEMAS_HOST = 'ils.test.rero.ch'
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
RECORDS_REST_ENDPOINTS = dict(
    doc=dict(
        pid_type='doc',
        pid_minter='document_id',
        pid_fetcher='document_id',
        search_class=RecordsSearch,
        search_index='documents',
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
        list_route='/documents/',
        item_route='/documents/<pid(doc):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='rero_ils.query:and_search_factory',
    ),
    doc_csv=dict(
        pid_type='doc',
        pid_minter='document_id',
        pid_fetcher='document_id',
        search_class=RecordsSearch,
        search_index='documents',
        search_type=None,
        record_serializers={
            'text/csv': (
                'rero_ils.modules.documents_items.serializers'
                ':documents_items_csv_v1_response'
            )
        },
        search_serializers={
            'text/csv': (
                'rero_ils.modules.documents_items.serializers'
                ':documents_items_csv_v1_search'
            )
        },
        list_route='/export/documents/csv/',
        item_route='/export/documents/csv/<pid(doc):pid_value>',
        default_media_type='text/csv',
        max_result_window=20000,
        search_factory_imp='rero_ils.query:and_search_factory',
    ),
    org=dict(
        pid_type='org',
        pid_minter='organisation_id',
        pid_fetcher='organisation_id',
        search_class=RecordsSearch,
        search_index='organisations',
        search_type=None,
        record_serializers={
            'application/rero+json': (
                'rero_ils.modules.serializers' ':json_v1_search'
            ),
            'application/json': (
                'invenio_records_rest.serializers' ':json_v1_response'
            ),
        },
        search_serializers={
            'application/rero+json': (
                'rero_ils.modules.serializers' ':json_v1_search'
            ),
            'application/json': (
                'invenio_records_rest.serializers' ':json_v1_search'
            ),
        },
        list_route='/organisations/',
        item_route='/organisations/<pid(org):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='rero_ils.query:and_search_factory',
    ),
    item=dict(
        pid_type='item',
        pid_minter='item_id',
        pid_fetcher='item_id',
        search_class=RecordsSearch,
        search_index='items',
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
        list_route='/items/',
        item_route='/items/<pid(item):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='rero_ils.query:and_search_factory',
    ),
    # loanid=dict(
    #     pid_type='loanid',
    #     pid_minter='loan_pid_minter',
    #     pid_fetcher='loan_pid_fetcher',
    #     search_class=RecordsSearch,
    #     search_index='loans',
    #     search_type=None,
    #     record_serializers={
    #         'application/json': (
    #             'invenio_records_rest.serializers' ':json_v1_response'
    #         )
    #     },
    #     search_serializers={
    #         'application/rero+json': (
    #             'rero_ils.modules.serializers' ':json_v1_search'
    #         ),
    #         'application/json': (
    #             'invenio_records_rest.serializers' ':json_v1_search'
    #         ),
    #     },
    #     list_route='/loans/',
    #     item_route='/loans/<pid(loanid):pid_value>',
    #     default_media_type='application/json',
    #     max_result_window=10000,
    #     search_factory_imp='rero_ils.query:and_search_factory',
    # ),
    itty=dict(
        pid_type='itty',
        pid_minter='item_type_id',
        pid_fetcher='item_type_id',
        search_class=RecordsSearch,
        search_index='items_types',
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
        list_route='/items_types/',
        item_route='/items_types/<pid(itty):pid_value>',
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
        search_index='patrons_types',
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
        list_route='/patrons_types/',
        item_route='/patrons_types/<pid(ptty):pid_value>',
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
        update_permission_factory_imp=cataloguer_permission_factory
    ),
    loc=dict(
        pid_type='loc',
        pid_minter='location_id',
        pid_fetcher='location_id',
        search_class=RecordsSearch,
        search_index='locations',
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
    ),
    cipo=dict(
        pid_type='cipo',
        pid_minter='circ_policy_id',
        pid_fetcher='circ_policy_id',
        search_class=RecordsSearch,
        search_index='circ_policies',
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
                terms=dict(field='itemslist.library_name'),
                # aggs=dict(
                #     location=dict(
                #         terms=dict(
                #             field='itemslist.location_name'
                #         )
                #     )
                # )
            ),
            author=dict(terms=dict(field='facet_authors')),
            language=dict(terms=dict(field='languages.language')),
            subject=dict(terms=dict(field='subject')),
            status=dict(terms=dict(field='itemslist.item_status')),
        ),
        # can be also post_filter
        filters={
            _('document_type'): terms_filter('type'),
            _('library'): terms_filter('itemslist.library_name'),
            _('author'): terms_filter('facet_authors'),
            _('language'): terms_filter('languages.language'),
            _('subject'): terms_filter('subject'),
            _('status'): terms_filter('itemslist.item_status'),
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
        template='rero_ils/detailed_view_documents_items.html',
        view_imp='rero_ils.modules.documents_items.views.doc_item_view_method',
        record_class='rero_ils.modules.documents_items.api:DocumentsWithItems',
    ),
    'doc_export': dict(
        pid_type='doc',
        route='/documents/<pid_value>/export/<format>',
        view_imp='invenio_records_ui.views.export',
        template='rero_ils/export_documents_items.html',
        record_class='rero_ils.modules.documents_items.api:DocumentsWithItems',
    ),
    'org': dict(
        pid_type='org',
        route='/organisations/<pid_value>',
        template='rero_ils/detailed_view_organisations_libraries.html',
        record_class='rero_ils.modules.organisations_libraries.api:OrganisationWithLibraries',
        permission_factory_imp='rero_ils.permissions.cataloguer_permission_factory',
    ),
    'lib': dict(
        pid_type='lib',
        route='/libraries/<pid_value>',
        template='rero_ils/detailed_view_libraries_locations.html',
        record_class='rero_ils.modules.libraries_locations.api:LibraryWithLocations',
        permission_factory_imp='rero_ils.permissions.cataloguer_permission_factory',
    ),
    'loc': dict(
        pid_type='loc',
        route='/locations/<pid_value>',
        template='rero_ils/detailed_view_locations.html',
        record_class='rero_ils.modules.locations.api:Location',
        permission_factory_imp='rero_ils.permissions.cataloguer_permission_factory',
    ),
    'item': dict(
        pid_type='item',
        route='/items/<pid_value>',
        template='rero_ils/detailed_view_items.html',
        view_imp='rero_ils.modules.items.views.item_view_method',
        record_class='rero_ils.modules.items.api:Item',
        permission_factory_imp='rero_ils.permissions.cataloguer_permission_factory',
    ),
    # 'loanid': dict(
    #     pid_type='loanid',
    #     route='/loans/<pid_value>',
    #     record_class='rero_ils.modules.loans.api:Loan',
    # ),
    'itty': dict(
        pid_type='itty',
        route='/items_types/<pid_value>',
        template='rero_ils/detailed_view_items_types.html',
        record_class='rero_ils.modules.items_types.api:ItemType',
        permission_factory_imp='rero_ils.permissions.cataloguer_permission_factory',
    ),
    'ptrn': dict(
        pid_type='ptrn',
        route='/patrons/<pid_value>',
        template='rero_ils/detailed_view_patrons.html',
        record_class='rero_ils.modules.patrons.api:Patron',
        permission_factory_imp='rero_ils.permissions.cataloguer_permission_factory',
    ),
    'ptty': dict(
        pid_type='ptty',
        route='/patrons_types/<pid_value>',
        template='rero_ils/detailed_view_patrons_types.html',
        record_class='rero_ils.modules.patrons_types.api:PatronType',
        permission_factory_imp='rero_ils.permissions.cataloguer_permission_factory',
    ),
    'pers': dict(
        pid_type='pers',
        route='/persons/<pid_value>',
        template='rero_ils/detailed_view_persons.html',
        record_class='rero_ils.modules.mef.api:MefPerson',
    ),
    'cipo': dict(
        pid_type='cipo',
        route='/circ_policies/<pid_value>',
        template='rero_ils/detailed_view_circ_policies.html',
        record_class='rero_ils.modules.circ_policies.api:CircPolicy',
        permission_factory_imp='rero_ils.permissions.cataloguer_permission_factory',
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

# Editor Configuration
# =====================

RERO_ILS_RESOURCES_ADMIN_OPTIONS = {
    _('doc'): dict(
        api='/api/documents/',
        results_template='templates/rero_ils/brief_view_documents_items.html',
        editor_template='rero_ils/document_editor.html',
        schema='documents/document-v0.0.1.json',
        form_options=(
            'rero_ils.modules.documents.form_options',
            'documents/document-v0.0.1.json',
        ),
        record_class=DocumentsWithItems,
        form_options_create_exclude=['pid'],
    ),
    _('item'): dict(
        # api='/api/items/',
        editor_template='rero_ils/item_editor.html',
        schema='items/item-v0.0.1.json',
        form_options=(
            'rero_ils.modules.items.form_options',
            'items/item-v0.0.1.json',
        ),
        save_record='rero_ils.modules.documents_items.utils:save_item',
        delete_record='rero_ils.modules.documents_items.utils:delete_item',
        record_class=Item,
        form_options_create_exclude=['pid'],
    ),
    # _('loanid'): dict(
    #     api='/api/circulation/loans/',
    #     schema='loans/loan-v0.0.1.json',
    #     record_class=Loan
    # ),
    _('itty'): dict(
        api='/api/items_types/',
        schema='items_types/item_type-v0.0.1.json',
        form_options=(
            'rero_ils.modules.items_types.form_options',
            'items_types/item_type-v0.0.1.json',
        ),
        save_record='rero_ils.modules.items_types.utils:save_item_type',
        editor_template='rero_ils/item_type_editor.html',
        results_template='templates/rero_ils/brief_view_items_types.html',
        record_class=ItemType,
        form_options_create_exclude=['pid', 'organisation_pid'],
    ),
    _('ptrn'): dict(
        api='/api/patrons/',
        schema='patrons/patron-v0.0.1.json',
        form_options=(
            'rero_ils.modules.patrons.form_options',
            'patrons/patron-v0.0.1.json',
        ),
        save_record='rero_ils.modules.patrons.utils:save_patron',
        editor_template='rero_ils/patron_editor.html',
        results_template='templates/rero_ils/brief_view_patrons.html',
        record_class=Patron,
    ),
    _('ptty'): dict(
        api='/api/patrons_types/',
        schema='patrons_types/patron_type-v0.0.1.json',
        form_options=(
            'rero_ils.modules.patrons_types.form_options',
            'patrons_types/patron_type-v0.0.1.json',
        ),
        save_record='rero_ils.modules.patrons_types.utils:save_patron_type',
        editor_template='rero_ils/patron_type_editor.html',
        results_template='templates/rero_ils/brief_view_patrons_types.html',
        record_class=PatronType,
        form_options_create_exclude=['pid', 'organisation_pid'],
    ),
    _('org'): dict(
        schema='organisations/organisation-v0.0.1.json',
        form_options=(
            'rero_ils.modules.organisations.form_options',
            'organisations/organisation-v0.0.1.json',
        ),
        record_class=OrganisationWithLibraries,
        form_options_create_exclude=['pid'],
    ),
    _('lib'): dict(
        api='/api/libraries/',
        results_template='templates/rero_ils/brief_view_libraries_locations.html',
        editor_template='rero_ils/library_editor.html',
        schema='libraries/library-v0.0.1.json',
        form_options=(
            'rero_ils.modules.libraries.form_options',
            'libraries/library-v0.0.1.json',
        ),
        save_record='rero_ils.modules.organisations_libraries.utils:save_library',
        delete_record='rero_ils.modules.organisations_libraries.utils:delete_library',
        record_class=LibraryWithLocations,
        form_options_create_exclude=['pid'],
    ),
    _('loc'): dict(
        editor_template='rero_ils/location_editor.html',
        schema='locations/location-v0.0.1.json',
        form_options=(
            'rero_ils.modules.locations.form_options',
            'locations/location-v0.0.1.json',
        ),
        save_record='rero_ils.modules.libraries_locations.utils:save_location',
        delete_record='rero_ils.modules.libraries_locations.utils:delete_location',
        record_class=Location,
        form_options_create_exclude=['pid'],
    ),
    _('pers'): dict(
        api='/api/persons/',
        results_template='templates/rero_ils/brief_view_mef_persons.html',
        editor_template='rero_ils/document_editor.html',
        schema='persons/mef-person-v0.0.1.json',
        form_options=(
            'rero_ils.modules.documents.form_options',
            'persons/mef-person-v0.0.1.json',
        ),
        record_class=MefPerson,
        can_create=lambda: False,
    ),
    _('cipo'): dict(
        api='/api/circ_policies/',
        schema='circ_policies/circ_policy-v0.0.1.json',
        form_options=(
            'rero_ils.modules.circ_policies.form_options',
            'circ_policies/circ_policy-v0.0.1.json',
        ),
        save_record='rero_ils.modules.circ_policies.utils:save_circ_policy',
        editor_template='rero_ils/circ_policy_editor.html',
        results_template='templates/rero_ils/brief_view_circ_policies.html',
        record_class=CircPolicy,
        form_options_create_exclude=['pid', 'organisation_pid'],
    ),
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
INDEXER_REPLACE_REFS = False

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
RERO_ILS_APP_IMPORT_BNF_EAN = 'http://catalogue.bnf.fr/api/SRU?' 'version=1.2&operation=searchRetrieve' '&recordSchema=unimarcxchange&maximumRecords=1' '&startRecord=1&query=bib.ean%%20all%%20"%s"'

RERO_ILS_APP_HELP_PAGE = (
    'https://github.com/rero/rero-ils/wiki/Public-demo-help'
)

#: Cover service
RERO_ILS_THUMBNAIL_SERVICE_URL = 'https://services.test.rero.ch/cover'

#: Persons
RERO_ILS_PERSONS_MEF_SCHEMA = 'persons/mef-person-v0.0.1.json'
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
    DocumentsWithItems.document_retriever
CIRCULATION_ITEMS_RETRIEVER_FROM_DOCUMENT = DocumentsWithItems.items_retriever

# This is needed for absolute URL
SERVER_NAME = 'localhost:5000'

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
        dict(dest='ITEM_ON_LOAN', transition=ItemAtDeskToItemOnLoan, trigger='checkout'),
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
