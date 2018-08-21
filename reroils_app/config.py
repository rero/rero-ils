# -*- coding: utf-8 -*-

"""reroils-app base Invenio configuration."""

from __future__ import absolute_import, print_function

from datetime import timedelta

from invenio_records_rest.facets import range_filter, terms_filter
from invenio_search import RecordsSearch
from reroils_data.documents_items.api import DocumentsWithItems
from reroils_data.items.api import Item
from reroils_data.locations.api import Location
from reroils_data.members_locations.api import MemberWithLocations
from reroils_data.organisations_members.api import OrganisationWithMembers
from reroils_data.patrons.api import Patron


# Identity function for string extraction
def _(x):
    return x


# Default language and timezone
BABEL_DEFAULT_LANGUAGE = 'en'
BABEL_DEFAULT_TIMEZONE = 'Europe/Zurich'
I18N_LANGUAGES = [
    ('fr', _('French')),
    ('de', _('German')),
    ('it', _('Italian'))
]

HEADER_TEMPLATE = 'reroils_app/header.html'
THEME_HEADER_TEMPLATE = HEADER_TEMPLATE
THEME_HEADER_LOGIN_TEMPLATE = 'reroils_app/header_login.html'
SECURITY_LOGIN_USER_TEMPLATE = 'reroils_app/login_user.html'
BASE_TEMPLATE = 'reroils_app/page.html'
REROILS_RECORD_EDITOR_BASE_TEMPLATE = 'reroils_app/page.html'
COVER_TEMPLATE = 'invenio_theme/page_cover.html'
THEME_TRACKINGCODE_TEMPLATE = 'reroils_app/trackingcode.html'
"""Template for including a tracking code for web analytics."""

SEARCH_UI_JSTEMPLATE_RESULTS = \
    'templates/reroils_data/brief_view_documents_items.html'
SEARCH_UI_SEARCH_TEMPLATE = 'reroils_app/search.html'
SEARCH_UI_JSTEMPLATE_FACETS = 'templates/reroils_app/facets.html'
SEARCH_UI_JSTEMPLATE_RANGE = 'templates/reroils_app/range.html'
SEARCH_UI_JSTEMPLATE_COUNT = 'templates/reroils_app/count.html'

SETTINGS_TEMPLATE = 'invenio_theme/page_settings.html'
THEME_FOOTER_TEMPLATE = 'reroils_app/footer.html'
THEME_LOGO = 'images/logo_rero_ils.png'

# WARNING: Do not share the secret key - especially do not commit it to
# version control.
SECRET_KEY = 'vdJLhU0z3elI6NyfB0y8ZSJwabuJ4B3mgjXtVxBKUGaqKxfoirLUrVjJAMQx3zKCzPqo6YwT0cprOsamTEI2vVMWdmOTp7Xn0GjzcIFs1n3baDQlicLhbI5dzyWqGBrKZS6rOpipZMdnwP1yMBtmu5dTBVfVjLd5yaTCx1iUKHjLNYMdY6k4XWUWDSIdNMfM5GF63Ar1qfRcCtzivQtYMX4UujM03rC5Ciu6osoxDMsxEwfwaMXhkUn1Py6WtttM'

# Theme
THEME_SITENAME = _('reroils-app')

# For dev. Set to false when testing on localhost in no debug mode
APP_ENABLE_SECURE_HEADERS = False

# no needs for redis
CACHE_TYPE = 'simple'


USER_EMAIL = 'software@rero.ch'
USER_PASS = 'uspass123'

SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://reroils:dbpass123@postgresql:5432/reroils'
SEARCH_ELASTIC_HOSTS = 'elasticsearch'
CELERY_BROKER_URL = 'amqp://guest:guest@rabbitmq:5672//'
CELERY_RESULT_BACKEND = 'redis://redis:6379/1'

CIRCULATION_ITEM_SCHEMA = 'items/item-v0.0.1.json'

JSONSCHEMAS_ENDPOINT = '/schema'
JSONSCHEMAS_HOST = 'ils.test.rero.ch'
JSONSCHEMAS_REGISTER_ENDPOINTS_UI = True
JSONSCHEMAS_REGISTER_ENDPOINTS_API = True
JSONSCHEMAS_REPLACE_REFS = True
JSONSCHEMAS_RESOLVE_SCHEMA = True

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
                'reroils_data.documents_items.serializers'
                ':documents_items_csv_v1_response'
            ),
        },
        search_serializers={
            'text/csv': (
                'reroils_data.documents_items.serializers'
                ':documents_items_csv_v1_search'
            ),
        },
        list_route='/export/documents/csv/',
        item_route='/export/documents/csv/<pid(doc):pid_value>',
        default_media_type='text/csv',
        max_result_window=20000,
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
    )
)

RECORDS_UI_ENDPOINTS = {
    "doc": {
        "pid_type": "doc",
        "route": "/documents/<pid_value>",
        "template": "reroils_data/detailed_view_documents_items.html",
        "view_imp": "reroils_data.documents_items.views.doc_item_view_method",
        "record_class": "reroils_data.documents_items.api:DocumentsWithItems"
    },
    "doc_export": {
        "pid_type": "doc",
        "route": "/documents/<pid_value>/export/<format>",
        "view_imp": "invenio_records_ui.views.export",
        "template": "reroils_data/export_documents_items.html",
        "record_class": 'reroils_data.documents_items.api:DocumentsWithItems',
    },
    "org": {
        "pid_type": "org",
        "route": "/organisations/<pid_value>",
        "template": "reroils_data/detailed_view_organisations_members.html",
        "record_class":
            "reroils_data.organisations_members.api:OrganisationWithMembers",
        "permission_factory_imp":
            "reroils_record_editor.permissions.cataloguer_permission_factory"
    },
    "memb": {
        "pid_type": "memb",
        "route": "/members/<pid_value>",
        "template": "reroils_data/detailed_view_members_locations.html",
        "record_class":
            "reroils_data.members_locations.api:MemberWithLocations",
        "permission_factory_imp":
            "reroils_record_editor.permissions.cataloguer_permission_factory"
    },
    "loc": {
        "pid_type": "loc",
        "route": "/locations/<pid_value>",
        "template": "reroils_data/detailed_view_locations.html",
        "record_class": 'reroils_data.locations.api:Location',
        "permission_factory_imp":
            "reroils_record_editor.permissions.cataloguer_permission_factory"
    },
    "item": {
        "pid_type": "item",
        "route": "/items/<pid_value>",
        "template": "reroils_data/detailed_view_items.html",
        "view_imp": "reroils_data.items.views.item_view_method",
        "record_class": 'reroils_data.items.api:Item',
        "permission_factory_imp":
            "reroils_record_editor.permissions.cataloguer_permission_factory"
    },
    "ptrn": {
        "pid_type": "ptrn",
        "route": "/patrons/<pid_value>",
        "template": "reroils_data/detailed_view_patrons.html",
        "record_class": 'reroils_data.patrons.api:Patron',
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
                    size=0
                )
            ),
            location=dict(
                terms=dict(
                    field='itemslist.location_name',
                    size=0
                )
            ),
            language=dict(
                terms=dict(
                    field='languages.language',
                    size=0
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
                    size=0
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
        results_template='templates/reroils_data/brief_view_documents_items.html',
        editor_template='reroils_data/document_editor.html',
        schema='documents/document-v0.0.1.json',
        form_options=('reroils_data.documents.form_options',
                      'documents/document-v0.0.1.json'),
        record_class=DocumentsWithItems,
        form_options_create_exclude=['pid']
    ),
    _('item'): dict(
        editor_template='reroils_data/item_editor.html',
        schema='items/item-v0.0.1.json',
        form_options=('reroils_data.items.form_options',
                      'items/item-v0.0.1.json'),
        save_record='reroils_data.documents_items.utils:save_item',
        delete_record='reroils_data.documents_items.utils:delete_item',
        record_class=Item,
        form_options_create_exclude=['pid']
    ),
    _('ptrn'): dict(
        api='/api/patrons/',
        schema='patrons/patron-v0.0.1.json',
        form_options=('reroils_data.patrons.form_options',
                      'patrons/patron-v0.0.1.json'),
        save_record='reroils_data.patrons.utils:save_patron',
        editor_template='reroils_data/patron_editor.html',
        search_template='reroils_record_editor/search.html',
        results_template='templates/reroils_data/brief_view_patrons.html',
        record_class=Patron,
    ),
    _('org'): dict(
        schema='organisations/organisation-v0.0.1.json',
        form_options=('reroils_data.organisations.form_options',
                      'organisations/organisation-v0.0.1.json'),
        record_class=OrganisationWithMembers,
        form_options_create_exclude=['pid']
    ),
    _('memb'): dict(
        api='/api/members/',
        search_template='reroils_record_editor/search.html',
        results_template='templates/reroils_data/brief_view_members_locations.html',
        editor_template='reroils_data/member_editor.html',
        schema='members/member-v0.0.1.json',
        form_options=('reroils_data.members.form_options',
                      'members/member-v0.0.1.json'),
        save_record='reroils_data.organisations_members.utils:save_member',
        delete_record='reroils_data.organisations_members.utils:delete_member',
        record_class=MemberWithLocations,
        form_options_create_exclude=['pid']
    ),
    _('loc'): dict(
        editor_template='reroils_data/location_editor.html',
        schema='locations/location-v0.0.1.json',
        form_options=('reroils_data.locations.form_options',
                      'locations/location-v0.0.1.json'),
        save_record='reroils_data.members_locations.utils:save_location',
        delete_record='reroils_data.members_locations.utils:delete_location',
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

SECURITY_CHANGEABLE = False
"""Allow password change by users."""

SECURITY_CONFIRMABLE = True
"""Allow user to confirm their email address."""

SECURITY_RECOVERABLE = True
"""Allow password recovery by users."""

SECURITY_REGISTERABLE = True
"""Allow users to register."""

SECURITY_SEND_REGISTER_EMAIL = True
"""Allow sending registration email."""

SECURITY_LOGIN_WITHOUT_CONFIRMATION = False
"""Allow users to login without first confirming their email address."""

#: Beat schedule
CELERY_BEAT_SCHEDULE = {
    'indexer': {
        'task': 'invenio_indexer.tasks.process_bulk_queue',
        'schedule': timedelta(minutes=5),
    },
    'session-cleaner': {
        'task': 'invenio_accounts.tasks.clean_session_table',
        'schedule': timedelta(hours=24),
    },
    'ebooks-harvester': {
        'task': 'invenio_oaiharvester.tasks.list_records_from_dates',
        'schedule': timedelta(minutes=60),
        'kwargs': dict(name='ebooks')
    },
}
