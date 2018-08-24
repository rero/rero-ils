# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 RERO.
#
# reroils-app is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Default configuration for reroils-app.

You overwrite and set instance-specific configuration by either:

- Configuration file: ``<virtualenv prefix>/var/instance/invenio.cfg``
- Environment variables: ``APP_<variable name>``
"""

from __future__ import absolute_import, print_function

from datetime import timedelta

from invenio_records_rest.facets import range_filter, terms_filter
from invenio_search import RecordsSearch

from .modules.documents_items.api import DocumentsWithItems
from .modules.items.api import Item
from .modules.locations.api import Location
from .modules.members_locations.api import MemberWithLocations
from .modules.organisations_members.api import OrganisationWithMembers
from .modules.patrons.api import Patron


def _(x):
    """Identity function used to trigger string extraction."""
    return x


# Rate limiting
# =============
#: Storage for ratelimiter.
RATELIMIT_STORAGE_URL = 'redis://localhost:6379/3'
#: no needs for redis
CACHE_TYPE = 'redis'
USER_EMAIL = 'software@rero.ch'
USER_PASS = 'uspass123'

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
    ('it', _('Italian'))
]

# Base templates
# ==============
#: Global base template.
BASE_TEMPLATE = 'reroils_app/page.html'
#: Cover page base template (used for e.g. login/sign-up).
COVER_TEMPLATE = 'invenio_theme/page_cover.html'
#: Footer base template.
FOOTER_TEMPLATE = 'invenio_theme/footer.html'
#: Header base template.
HEADER_TEMPLATE = 'reroils_app/header.html'
#: Settings base template.
SETTINGS_TEMPLATE = 'invenio_theme/page_settings.html'

# Theme configuration
# ===================
#: Site name
THEME_SITENAME = _('reroils-app')
#: Use default frontpage.
THEME_FRONTPAGE = False
#: Frontpage title.
THEME_FRONTPAGE_TITLE = _('reroils-app')
#: Frontpage template.
THEME_FRONTPAGE_TEMPLATE = 'reroils_app/frontpage.html'

THEME_HEADER_TEMPLATE = HEADER_TEMPLATE
THEME_HEADER_LOGIN_TEMPLATE = 'reroils_app/header_login.html'
#: Template for including a tracking code for web analytics.
THEME_TRACKINGCODE_TEMPLATE = 'reroils_app/trackingcode.html'
THEME_FOOTER_TEMPLATE = 'reroils_app/footer.html'
THEME_LOGO = 'images/logo_rero_ils.png'

SEARCH_UI_JSTEMPLATE_RESULTS = \
    'templates/reroils_app/brief_view_documents_items.html'
SEARCH_UI_SEARCH_TEMPLATE = 'reroils_app/search.html'
SEARCH_UI_JSTEMPLATE_FACETS = 'templates/reroils_app/facets.html'
SEARCH_UI_JSTEMPLATE_RANGE = 'templates/reroils_app/range.html'
SEARCH_UI_JSTEMPLATE_COUNT = 'templates/reroils_app/count.html'

REROILS_RECORD_EDITOR_BASE_TEMPLATE = 'reroils_app/page.html'
SECURITY_LOGIN_USER_TEMPLATE = 'reroils_app/login_user.html'

# Email configuration
# ===================
#: Email address for support.
SUPPORT_EMAIL = "software@rero.ch"
#: Disable email sending by default.
MAIL_SUPPRESS_SEND = True

# Assets
# ======
#: Static files collection method (defaults to copying files).
COLLECT_STORAGE = 'flask_collect.storage.file'

# Accounts
# ========
#: Email address used as sender of account registration emails.
SECURITY_EMAIL_SENDER = SUPPORT_EMAIL
#: Email subject for account registration emails.
SECURITY_EMAIL_SUBJECT_REGISTER = _(
    "Welcome to RERO-ILS!")
#: Redis session storage URL.
ACCOUNTS_SESSION_REDIS_URL = 'redis://localhost:6379/1'

# Celery configuration
# ====================

BROKER_URL = 'amqp://guest:guest@localhost:5672/'
#: URL of message broker for Celery (default is RabbitMQ).
CELERY_BROKER_URL = 'amqp://guest:guest@localhost:5672/'
#: URL of backend for result storage (default is Redis).
CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'
#: Scheduled tasks configuration (aka cronjobs).
CELERY_BEAT_SCHEDULE = {
    'indexer': {
        'task': 'invenio_indexer.tasks.process_bulk_queue',
        'schedule': timedelta(minutes=5),
    },
    'session-cleaner': {
        'task': 'invenio_accounts.tasks.clean_session_table',
        'schedule': timedelta(minutes=60),
    },
    'ebooks-harvester': {
        'task': 'invenio_oaiharvester.tasks.list_records_from_dates',
        'schedule': timedelta(minutes=60),
        'kwargs': dict(name='ebooks')
    },
}

# Database
# ========
#: Database URI including user and password
SQLALCHEMY_DATABASE_URI = \
    'postgresql+psycopg2://reroils:dbpass123@localhost:5432/reroils'
DB_VERSIONING = False

# JSONSchemas
# ===========
#: Hostname used in URLs for local JSONSchemas.
JSONSCHEMAS_HOST = 'ils.test.rero.ch'
JSONSCHEMAS_ENDPOINT = '/schema'
"""Default schema endpoint."""

# Flask configuration
# ===================
# See details on
# http://flask.pocoo.org/docs/0.12/config/#builtin-configuration-values

#: For dev. Set to false when testing on localhost in no debug mode
APP_ENABLE_SECURE_HEADERS = False

#: Secret key - each installation (dev, production, ...) needs a separate key.
#: It should be changed before deploying.
SECRET_KEY = 'vdJLhU0z3elI6NyfB0y8ZSJwabuJ4B3mgjXtVxBKUGaqKxfoirLUrVjJAMQx3zKCzPqo6YwT0cprOsamTEI2vVMWdmOTp7Xn0GjzcIFs1n3baDQlicLhbI5dzyWqGBrKZS6rOpipZMdnwP1yMBtmu5dTBVfVjLd5yaTCx1iUKHjLNYMdY6k4XWUWDSIdNMfM5GF63Ar1qfRcCtzivQtYMX4UujM03rC5Ciu6osoxDMsxEwfwaMXhkUn1Py6WtttM'
#: Max upload size for form data via application/mulitpart-formdata.
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MiB
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

RECORDS_REST_ENDPOINTS = dict(
    doc=dict(
        pid_type='doc',
        pid_minter='document_id',
        pid_fetcher='document_id',
        search_class=RecordsSearch,
        search_index='documents',
        search_type=None,
        record_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_response'),
        },
        search_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        list_route='/documents/',
        item_route='/documents/<pid(doc):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='reroils_app.query:and_search_factory'
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
                'reroils_app.modules.documents_items.serializers'
                ':documents_items_csv_v1_response'
            ),
        },
        search_serializers={
            'text/csv': (
                'reroils_app.modules.documents_items.serializers'
                ':documents_items_csv_v1_search'
            ),
        },
        list_route='/export/documents/csv/',
        item_route='/export/documents/csv/<pid(doc):pid_value>',
        default_media_type='text/csv',
        max_result_window=20000,
        search_factory_imp='reroils_app.query:and_search_factory'
    ),
    org=dict(
        pid_type='org',
        pid_minter='organisation_id',
        pid_fetcher='organisation_id',
        search_class=RecordsSearch,
        search_index='organisations',
        search_type=None,
        record_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_response'),
        },
        search_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        list_route='/organisations/',
        item_route='/organisations/<pid(org):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='reroils_app.query:and_search_factory'
    ),
    item=dict(
        pid_type='item',
        pid_minter='item_id',
        pid_fetcher='item_id',
        search_class=RecordsSearch,
        search_index='items',
        search_type=None,
        record_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_response'),
        },
        search_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        list_route='/items/',
        item_route='/items/<pid(org):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='reroils_app.query:and_search_factory'
    ),
    ptrn=dict(
        pid_type='ptrn',
        pid_minter='patron_id',
        pid_fetcher='patron_id',
        search_class=RecordsSearch,
        search_index='patrons',
        search_type=None,
        record_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_response'),
        },
        search_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        list_route='/patrons/',
        item_route='/patrons/<pid(ptrn):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='reroils_app.query:and_search_factory'
    ),
    memb=dict(
        pid_type='memb',
        pid_minter='member_id',
        pid_fetcher='member_id',
        search_class=RecordsSearch,
        search_index='members',
        search_type=None,
        record_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_response'),
        },
        search_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        list_route='/members/',
        item_route='/members/<pid(memb):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='reroils_app.query:and_search_factory'
    ),
    loc=dict(
        pid_type='loc',
        pid_minter='location_id',
        pid_fetcher='location_id',
        search_class=RecordsSearch,
        search_index='locations',
        search_type=None,
        record_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_response'),
        },
        search_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        list_route='/locations/',
        item_route='/locations/<pid(loc):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='reroils_app.query:and_search_factory'
    )
)

RECORDS_UI_ENDPOINTS = {
    "doc": {
        "pid_type": "doc",
        "route": "/documents/<pid_value>",
        "template": "reroils_app/detailed_view_documents_items.html",
        "view_imp": "reroils_app.modules.documents_items.views.doc_item_view_method",
        "record_class": "reroils_app.modules.documents_items.api:DocumentsWithItems"
    },
    "doc_export": {
        "pid_type": "doc",
        "route": "/documents/<pid_value>/export/<format>",
        "view_imp": "invenio_records_ui.views.export",
        "template": "reroils_app/export_documents_items.html",
        "record_class": 'reroils_app.modules.documents_items.api:DocumentsWithItems',
    },
    "org": {
        "pid_type": "org",
        "route": "/organisations/<pid_value>",
        "template": "reroils_app/detailed_view_organisations_members.html",
        "record_class":
            "reroils_app.modules.organisations_members.api:OrganisationWithMembers",
        "permission_factory_imp":
            "reroils_record_editor.permissions.cataloguer_permission_factory"
    },
    "memb": {
        "pid_type": "memb",
        "route": "/members/<pid_value>",
        "template": "reroils_app/detailed_view_members_locations.html",
        "record_class":
            "reroils_app.modules.members_locations.api:MemberWithLocations",
        "permission_factory_imp":
            "reroils_record_editor.permissions.cataloguer_permission_factory"
    },
    "loc": {
        "pid_type": "loc",
        "route": "/locations/<pid_value>",
        "template": "reroils_app/detailed_view_locations.html",
        "record_class": 'reroils_app.modules.locations.api:Location',
        "permission_factory_imp":
            "reroils_record_editor.permissions.cataloguer_permission_factory"
    },
    "item": {
        "pid_type": "item",
        "route": "/items/<pid_value>",
        "template": "reroils_app/detailed_view_items.html",
        "view_imp": "reroils_app.modules.items.views.item_view_method",
        "record_class": 'reroils_app.modules.items.api:Item',
        "permission_factory_imp":
            "reroils_record_editor.permissions.cataloguer_permission_factory"
    },
    "ptrn": {
        "pid_type": "ptrn",
        "route": "/patrons/<pid_value>",
        "template": "reroils_app/detailed_view_patrons.html",
        "record_class": 'reroils_app.modules.patrons.api:Patron',
        "permission_factory_imp":
            "reroils_record_editor.permissions.cataloguer_permission_factory"

    }
}

RECORDS_UI_EXPORT_FORMATS = {
    'doc': {
        'json': dict(
            title='JSON',
            serializer='invenio_records_rest.serializers'
                       ':json_v1',
            order=1,
        )
    }
}

REROILS_APP_SORT_FACETS = {
    'documents': 'language,author,location,status',
    'patrons': 'roles'
}

# SEARCH_UI_SEARCH_INDEX = 'records-record-v0.0.1'

RECORDS_REST_FACETS = {
    'documents': dict(
        aggs=dict(
            status=dict(
                terms=dict(
                    field='itemslist._circulation.status',
                    size=100
                )
            ),
            location=dict(
                terms=dict(
                    field='itemslist.location_name',
                    size=100000
                )
            ),
            language=dict(
                terms=dict(
                    field='languages.language',
                    size=10000
                )
            ),
            document_type=dict(
                terms=dict(
                    field='type',
                    size=1000
                )
            ),
            author=dict(
                terms=dict(
                    field='facet_authors',
                    size=5
                )
            ),
            years=dict(
                date_histogram=dict(
                    field='publicationYear',
                    interval='year',
                    format='yyyy'
                )
            ),
        ),
        # can be also post_filter
        filters={
            _('status'): terms_filter('itemslist._circulation.status'),
            _('location'): terms_filter('itemslist.location_name'),
            _('language'): terms_filter('languages.language'),
            _('document_type'): terms_filter('type'),
            _('author'): terms_filter('facet_authors')
        },
        post_filters={
            _('years'): range_filter(
                'publicationYear',
                format='yyyy',
                end_date_math='/y'
            )
        }
    ),
    'patrons': dict(
        aggs=dict(
            roles=dict(
                terms=dict(
                    field='roles',
                    size=100
                )
            )
        ),
        filters={
            _('roles'): terms_filter('roles')
        }
    )
}


# sort
RECORDS_REST_SORT_OPTIONS = {
    'documents': dict(
        bestmatch=dict(
            fields=['_score'],
            title='Best match',
            default_order='asc'
        ),
        mostrecent=dict(
            fields=['-_created'],
            title='Most recent',
            default_order='desc'
        ),
    )
}

# default sort
RECORDS_REST_DEFAULT_SORT = {
    'documents': dict(query='bestmatch', noquery='mostrecent'),
}


INDEXER_REPLACE_REFS = False

REROILS_RECORD_EDITOR_OPTIONS = {
    _('doc'): dict(
        api='/api/documents/',
        search_template='reroils_record_editor/search.html',
        results_template='templates/reroils_app/brief_view_documents_items.html',
        editor_template='reroils_app/document_editor.html',
        schema='documents/document-v0.0.1.json',
        form_options=('reroils_app.modules.documents.form_options',
                      'documents/document-v0.0.1.json'),
        record_class=DocumentsWithItems,
        form_options_create_exclude=['pid']
    ),
    _('item'): dict(
        editor_template='reroils_app/item_editor.html',
        schema='items/item-v0.0.1.json',
        form_options=('reroils_app.modules.items.form_options',
                      'items/item-v0.0.1.json'),
        save_record='reroils_app.modules.documents_items.utils:save_item',
        delete_record='reroils_app.modules.documents_items.utils:delete_item',
        record_class=Item,
        form_options_create_exclude=['pid']
    ),
    _('ptrn'): dict(
        api='/api/patrons/',
        schema='patrons/patron-v0.0.1.json',
        form_options=('reroils_app.modules.patrons.form_options',
                      'patrons/patron-v0.0.1.json'),
        save_record='reroils_app.modules.patrons.utils:save_patron',
        editor_template='reroils_app/patron_editor.html',
        search_template='reroils_record_editor/search.html',
        results_template='templates/reroils_app/brief_view_patrons.html',
        record_class=Patron,
    ),
    _('org'): dict(
        schema='organisations/organisation-v0.0.1.json',
        form_options=('reroils_app.modules.organisations.form_options',
                      'organisations/organisation-v0.0.1.json'),
        record_class=OrganisationWithMembers,
        form_options_create_exclude=['pid']
    ),
    _('memb'): dict(
        api='/api/members/',
        search_template='reroils_record_editor/search.html',
        results_template='templates/reroils_app/brief_view_members_locations.html',
        editor_template='reroils_app/member_editor.html',
        schema='members/member-v0.0.1.json',
        form_options=('reroils_app.modules.members.form_options',
                      'members/member-v0.0.1.json'),
        save_record='reroils_app.modules.organisations_members.utils:save_member',
        delete_record='reroils_app.modules.organisations_members.utils:delete_member',
        record_class=MemberWithLocations,
        form_options_create_exclude=['pid']
    ),
    _('loc'): dict(
        editor_template='reroils_app/location_editor.html',
        schema='locations/location-v0.0.1.json',
        form_options=('reroils_app.modules.locations.form_options',
                      'locations/location-v0.0.1.json'),
        save_record='reroils_app.modules.members_locations.utils:save_location',
        delete_record='reroils_app.modules.members_locations.utils:delete_location',
        record_class=Location,
        form_options_create_exclude=['pid']
    ),
}

REROILS_RECORD_EDITOR_TRANSLATE_JSON_KEYS = [
    'title', 'description', 'placeholder',
    'validationMessage', 'name', 'add', '403'
]
SEARCH_UI_SEARCH_API = '/api/documents/'
# REROILS_RECORD_EDITOR_JSONSCHEMA = 'records/record-v0.0.1.json'
REROILS_RECORD_EDITOR_PERMALINK_RERO_URL = 'http://data.rero.ch/'
REROILS_RECORD_EDITOR_PERMALINK_BNF_URL = 'http://catalogue.bnf.fr/ark:/12148/'

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

#: REROILS specific configurations.
REROILS_APP_IMPORT_BNF_EAN = 'http://catalogue.bnf.fr/api/SRU?'\
    'version=1.2&operation=searchRetrieve'\
    '&recordSchema=unimarcxchange&maximumRecords=1'\
    '&startRecord=1&query=bib.ean%%20all%%20"%s"'

REROILS_APP_HELP_PAGE = 'https://github.com/rero/reroils-app/wiki/Public-demo-help'
