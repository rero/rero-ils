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
BASE_TEMPLATE = 'rero_ils/page.html'
#: Cover page base template (used for e.g. login/sign-up).
COVER_TEMPLATE = 'invenio_theme/page_cover.html'
#: Footer base template.
FOOTER_TEMPLATE = 'invenio_theme/footer.html'
#: Header base template.
HEADER_TEMPLATE = 'rero_ils/header.html'
#: Settings base template.
SETTINGS_TEMPLATE = 'invenio_theme/page_settings.html'

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

THEME_HEADER_TEMPLATE = HEADER_TEMPLATE
THEME_HEADER_LOGIN_TEMPLATE = 'rero_ils/header_login.html'
#: Template for including a tracking code for web analytics.
THEME_TRACKINGCODE_TEMPLATE = 'rero_ils/trackingcode.html'
THEME_FOOTER_TEMPLATE = 'rero_ils/footer.html'
THEME_LOGO = 'images/logo_rero_ils.png'

SEARCH_UI_JSTEMPLATE_RESULTS = \
    'templates/rero_ils/brief_view_documents_items.html'
SEARCH_UI_SEARCH_TEMPLATE = 'rero_ils/search.html'
SEARCH_UI_JSTEMPLATE_FACETS = 'templates/rero_ils/facets.html'
SEARCH_UI_JSTEMPLATE_RANGE = 'templates/rero_ils/range.html'
SEARCH_UI_JSTEMPLATE_COUNT = 'templates/rero_ils/count.html'
SEARCH_UI_SEARCH_MIMETYPE = 'application/rero+json'

REROILS_RECORD_EDITOR_BASE_TEMPLATE = 'rero_ils/page.html'
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
        'kwargs': dict(name='ebooks')
    },
    'mef-harvester': {
        'task': 'rero_ils.modules.apiharvester.tasks.harvest_records',
        'schedule': timedelta(minutes=60),
        'kwargs': dict(name='mef')
    },

}

# Database
# ========
#: Database URI including user and password
SQLALCHEMY_DATABASE_URI = \
    'postgresql+psycopg2://rero-ils:rero-ils@localhost/rero-ils'
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
APP_ENABLE_SECURE_HEADERS = False
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
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_response'),
        },
        search_serializers={
            'application/rero+json': ('rero_ils.modules.serializers'
                                      ':json_v1_search'),
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        list_route='/documents/',
        item_route='/documents/<pid(doc):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='rero_ils.query:and_search_factory'
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
            ),
        },
        search_serializers={
            'text/csv': (
                'rero_ils.modules.documents_items.serializers'
                ':documents_items_csv_v1_search'
            ),
        },
        list_route='/export/documents/csv/',
        item_route='/export/documents/csv/<pid(doc):pid_value>',
        default_media_type='text/csv',
        max_result_window=20000,
        search_factory_imp='rero_ils.query:and_search_factory'
    ),
    org=dict(
        pid_type='org',
        pid_minter='organisation_id',
        pid_fetcher='organisation_id',
        search_class=RecordsSearch,
        search_index='organisations',
        search_type=None,
        record_serializers={
            'application/rero+json': ('rero_ils.modules.serializers'
                                      ':json_v1_search'),
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_response'),
        },
        search_serializers={
            'application/rero+json': ('rero_ils.modules.serializers'
                                      ':json_v1_search'),
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        list_route='/organisations/',
        item_route='/organisations/<pid(org):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='rero_ils.query:and_search_factory'
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
            'application/rero+json': ('rero_ils.modules.serializers'
                                      ':json_v1_search'),
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        list_route='/items/',
        item_route='/items/<pid(org):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='rero_ils.query:and_search_factory'
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
            'application/rero+json': ('rero_ils.modules.serializers'
                                      ':json_v1_search'),
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        list_route='/patrons/',
        item_route='/patrons/<pid(ptrn):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='rero_ils.query:and_search_factory'
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
            'application/rero+json': ('rero_ils.modules.serializers'
                                      ':json_v1_search'),
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        list_route='/members/',
        item_route='/members/<pid(memb):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='rero_ils.query:and_search_factory'
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
            'application/rero+json': ('rero_ils.modules.serializers'
                                      ':json_v1_search'),
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        list_route='/locations/',
        item_route='/locations/<pid(loc):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='rero_ils.query:and_search_factory'
    ),
    pers=dict(
        pid_type='pers',
        pid_minter='mef_person_id',
        pid_fetcher='mef_person_id',
        search_class=RecordsSearch,
        search_index='persons',
        search_type=None,
        record_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_response'),
        },
        search_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        list_route='/persons/',
        item_route='/persons/<pid(loc):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        search_factory_imp='rero_ils.query:and_search_factory'
    )

)

SEARCH_UI_SEARCH_INDEX = 'documents'

RERO_ILS_APP_CONFIG_FACETS = {
    'documents': {
        'order': ['document_type', 'member', 'author', 'language', 'subject',
                  'status'],
        'expand': ['document_type']
    },
    'patrons': {
        'order': ['roles'],
        'expand': ['roles']
    }
}

RECORDS_REST_FACETS = {
    'documents': dict(
        aggs=dict(
            years=dict(
                date_histogram=dict(
                    field='publicationYear',
                    interval='year',
                    format='yyyy',
                )
            ),
            document_type=dict(
                terms=dict(
                    field='type',
                )
            ),
            member=dict(
                terms=dict(
                    field='itemslist.member_name',
                ),
                # aggs=dict(
                #     location=dict(
                #         terms=dict(
                #             field='itemslist.location_name'
                #         )
                #     )
                # )
            ),
            author=dict(
                terms=dict(
                    field='facet_authors',
                )
            ),
            language=dict(
                terms=dict(
                    field='languages.language',
                )
            ),
            subject=dict(
                terms=dict(
                    field='subject',
                )
            ),
            status=dict(
                terms=dict(
                    field='itemslist._circulation.status',
                )
            ),
        ),
        # can be also post_filter
        filters={
            _('document_type'): terms_filter('type'),
            _('member'): terms_filter('itemslist.member_name'),
            _('author'): terms_filter('facet_authors'),
            _('language'): terms_filter('languages.language'),
            _('subject'): terms_filter('subject'),
            _('status'): terms_filter('itemslist._circulation.status')
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

# Detailed View Configuration
# ===========================
RECORDS_UI_ENDPOINTS = {
    "doc": {
        "pid_type": "doc",
        "route": "/documents/<pid_value>",
        "template": "rero_ils/detailed_view_documents_items.html",
        "view_imp": "rero_ils.modules.documents_items.views.doc_item_view_method",
        "record_class": "rero_ils.modules.documents_items.api:DocumentsWithItems"
    },
    "doc_export": {
        "pid_type": "doc",
        "route": "/documents/<pid_value>/export/<format>",
        "view_imp": "invenio_records_ui.views.export",
        "template": "rero_ils/export_documents_items.html",
        "record_class": 'rero_ils.modules.documents_items.api:DocumentsWithItems',
    },
    "org": {
        "pid_type": "org",
        "route": "/organisations/<pid_value>",
        "template": "rero_ils/detailed_view_organisations_members.html",
        "record_class":
            "rero_ils.modules.organisations_members.api:OrganisationWithMembers",
        "permission_factory_imp":
            "reroils_record_editor.permissions.cataloguer_permission_factory"
    },
    "memb": {
        "pid_type": "memb",
        "route": "/members/<pid_value>",
        "template": "rero_ils/detailed_view_members_locations.html",
        "record_class":
            "rero_ils.modules.members_locations.api:MemberWithLocations",
        "permission_factory_imp":
            "reroils_record_editor.permissions.cataloguer_permission_factory"
    },
    "loc": {
        "pid_type": "loc",
        "route": "/locations/<pid_value>",
        "template": "rero_ils/detailed_view_locations.html",
        "record_class": 'rero_ils.modules.locations.api:Location',
        "permission_factory_imp":
            "reroils_record_editor.permissions.cataloguer_permission_factory"
    },
    "item": {
        "pid_type": "item",
        "route": "/items/<pid_value>",
        "template": "rero_ils/detailed_view_items.html",
        "view_imp": "rero_ils.modules.items.views.item_view_method",
        "record_class": 'rero_ils.modules.items.api:Item',
        "permission_factory_imp":
            "reroils_record_editor.permissions.cataloguer_permission_factory"
    },
    "ptrn": {
        "pid_type": "ptrn",
        "route": "/patrons/<pid_value>",
        "template": "rero_ils/detailed_view_patrons.html",
        "record_class": 'rero_ils.modules.patrons.api:Patron',
        "permission_factory_imp":
            "reroils_record_editor.permissions.cataloguer_permission_factory"

    },
    "pers": {
        "pid_type": "pers",
        "route": "/persons/<pid_value>",
        "template": "rero_ils/detailed_view_persons.html",
        "record_class": 'rero_ils.modules.mef.api:MefPerson',
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

# Editor Configuration
# =====================
REROILS_RECORD_EDITOR_OPTIONS = {
    _('doc'): dict(
        api='/api/documents/',
        search_template='reroils_record_editor/search.html',
        results_template='templates/rero_ils/brief_view_documents_items.html',
        editor_template='rero_ils/document_editor.html',
        schema='documents/document-v0.0.1.json',
        form_options=('rero_ils.modules.documents.form_options',
                      'documents/document-v0.0.1.json'),
        record_class=DocumentsWithItems,
        form_options_create_exclude=['pid']
    ),
    _('item'): dict(
        editor_template='rero_ils/item_editor.html',
        schema='items/item-v0.0.1.json',
        form_options=('rero_ils.modules.items.form_options',
                      'items/item-v0.0.1.json'),
        save_record='rero_ils.modules.documents_items.utils:save_item',
        delete_record='rero_ils.modules.documents_items.utils:delete_item',
        record_class=Item,
        form_options_create_exclude=['pid']
    ),
    _('ptrn'): dict(
        api='/api/patrons/',
        schema='patrons/patron-v0.0.1.json',
        form_options=('rero_ils.modules.patrons.form_options',
                      'patrons/patron-v0.0.1.json'),
        save_record='rero_ils.modules.patrons.utils:save_patron',
        editor_template='rero_ils/patron_editor.html',
        search_template='reroils_record_editor/search.html',
        results_template='templates/rero_ils/brief_view_patrons.html',
        record_class=Patron,
    ),
    _('org'): dict(
        schema='organisations/organisation-v0.0.1.json',
        form_options=('rero_ils.modules.organisations.form_options',
                      'organisations/organisation-v0.0.1.json'),
        record_class=OrganisationWithMembers,
        form_options_create_exclude=['pid']
    ),
    _('memb'): dict(
        api='/api/members/',
        search_template='reroils_record_editor/search.html',
        results_template='templates/rero_ils/brief_view_members_locations.html',
        editor_template='rero_ils/member_editor.html',
        schema='members/member-v0.0.1.json',
        form_options=('rero_ils.modules.members.form_options',
                      'members/member-v0.0.1.json'),
        save_record='rero_ils.modules.organisations_members.utils:save_member',
        delete_record='rero_ils.modules.organisations_members.utils:delete_member',
        record_class=MemberWithLocations,
        form_options_create_exclude=['pid']
    ),
    _('loc'): dict(
        editor_template='rero_ils/location_editor.html',
        schema='locations/location-v0.0.1.json',
        form_options=('rero_ils.modules.locations.form_options',
                      'locations/location-v0.0.1.json'),
        save_record='rero_ils.modules.members_locations.utils:save_location',
        delete_record='rero_ils.modules.members_locations.utils:delete_location',
        record_class=Location,
        form_options_create_exclude=['pid']
    ),
    _('pers'): dict(
        api='/api/persons/',
        results_template='templates/rero_ils/brief_view_mef_persons.html',
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
REROILS_RECORD_EDITOR_TRANSLATE_JSON_KEYS = [
    'title', 'description', 'placeholder',
    'validationMessage', 'name', 'add', '403'
]

RERO_ILS_PERMALINK_RERO_URL = 'http://data.rero.ch/'
RERO_ILS_PERMALINK_BNF_URL = 'http://catalogue.bnf.fr/ark:/12148/'

#: RERO_ILS MEF specificconfigurations.
RERO_ILS_HARVESTING_MEF_URL = 'http://mef.test.rero.ch/api/mef'
RERO_ILS_MEF_RESULT_SIZE = 100


#: RERO_ILS specific configurations.
RERO_ILS_APP_IMPORT_BNF_EAN = 'http://catalogue.bnf.fr/api/SRU?'\
    'version=1.2&operation=searchRetrieve'\
    '&recordSchema=unimarcxchange&maximumRecords=1'\
    '&startRecord=1&query=bib.ean%%20all%%20"%s"'

RERO_ILS_APP_HELP_PAGE = 'https://github.com/rero/rero-ils/wiki/Public-demo-help'

#: Cover service
RERO_ILS_THUMBNAIL_SERVICE_URL = 'https://services.test.rero.ch/cover'

#: Persons
RERO_ILS_PERSONS_MEF_SCHEMA = 'persons/mef-person-v0.0.1.json'
RERO_ILS_PERSONS_SOURCES = ['rero', 'bnf', 'gnd']
RERO_ILS_PERSONS_PERMALINK = {
    'bnf': 'https://catalogue.bnf.fr/ark:/12148/{pid}',
    'gnd': 'http://d-nb.info/gnd/{pid}',
    'rero': 'http://data.rero.ch/02-{pid}'
}

RERO_ILS_PERSONS_LABEL_ORDER = {
    'fallback': 'fr',
    'fr': ['rero', 'bnf', 'gnd'],
    'de': ['gnd', 'rero', 'bnf']
}
