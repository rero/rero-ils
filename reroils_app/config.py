# -*- coding: utf-8 -*-

"""reroils-app base Invenio configuration."""

from __future__ import absolute_import, print_function

from invenio_records_rest.facets import range_filter, terms_filter
from invenio_records_rest.query import es_search_factory
from invenio_search import RecordsSearch


# Identity function for string extraction
def _(x):
    return x


# Default language and timezone
BABEL_DEFAULT_LANGUAGE = 'en'
BABEL_DEFAULT_TIMEZONE = 'Europe/Zurich'
I18N_LANGUAGES = [
    ('fr', _('French')),
    ('de', _('German'))
]

HEADER_TEMPLATE = 'reroils_app/header.html'
THEME_HEADER_TEMPLATE = HEADER_TEMPLATE
BASE_TEMPLATE = 'reroils_app/page.html'
REROILS_RECORD_EDITOR_BASE_TEMPLATE = 'reroils_app/page.html'
COVER_TEMPLATE = 'invenio_theme/page_cover.html'

SEARCH_UI_JSTEMPLATE_RESULTS = \
    'templates/reroils_app/briefview.html'
SEARCH_UI_SEARCH_TEMPLATE = 'reroils_app/search.html'
SEARCH_UI_JSTEMPLATE_FACETS = 'templates/reroils_app/facets.html'

SETTINGS_TEMPLATE = 'invenio_theme/page_settings.html'
THEME_FOOTER_TEMPLATE = 'reroils_app/footer.html'
THEME_LOGO = 'images/logo_rero_ils.png'

# WARNING: Do not share the secret key - especially do not commit it to
# version control.
SECRET_KEY = 'vdJLhU0z3elI6NyfB0y8ZSJwabuJ4B3mgjXtVxBKUGaqKxfoirLUrVjJAMQx3zKCzPqo6YwT0cprOsamTEI2vVMWdmOTp7Xn0GjzcIFs1n3baDQlicLhbI5dzyWqGBrKZS6rOpipZMdnwP1yMBtmu5dTBVfVjLd5yaTCx1iUKHjLNYMdY6k4XWUWDSIdNMfM5GF63Ar1qfRcCtzivQtYMX4UujM03rC5Ciu6osoxDMsxEwfwaMXhkUn1Py6WtttM'

# Theme
THEME_SITENAME = _('reroils-app')

# For dev
# APP_ENABLE_SECURE_HEADERS=False

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
    recid=dict(
        pid_type='recid',
        pid_minter='bibid',
        pid_fetcher='bibid',
        search_class=RecordsSearch,
        search_index='records',
        search_type=None,
        record_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_response'),
        },
        search_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        list_route='/records/',
        item_route='/records/<pid(recid):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
    ),
    recid_excel=dict(
        pid_type='recid',
        pid_minter='bibid',
        pid_fetcher='bibid',
        search_class=RecordsSearch,
        search_index='records',
        search_type=None,
        record_serializers={
            'text/csv': ('reroils_app.serializers'
                                 ':text_v1_response'),
        },
        search_serializers={
            'text/csv': ('reroils_app.serializers'
                                 ':text_v1_search'),
        },
        list_route='/export/records/csv/',
        item_route='/export/records/csv/<pid(recid):pid_value>',
        default_media_type='text/csv',
        max_result_window=20000,
    ),
    crcitm=dict(
        pid_type='crcitm',
        pid_minter='itemid',
        pid_fetcher='itemid',
        search_class=RecordsSearch,
        search_index='records-item-v0.0.1',
        record_class='invenio_circulation.api:Item',
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
        item_route='/items/<pid(crcitm):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
    )
)

RECORDS_UI_ENDPOINTS = {
    "recid": {
        "pid_type": "recid",
        "route": "/records/<pid_value>",
        "template": "reroils_app/fullview.html",
        "record_class": "reroils_data.api:Record"
    },
    "recid_export": {
        "pid_type": "recid",
        "route": "/records/<pid_value>/export/<format>",
        "view_imp": "invenio_records_ui.views.export",
        "template": "reroils_app/export.html",
        "record_class": 'reroils_data.api.Record',
    },
    "crcitm": {
        "pid_type": "crcitm",
        "route": "/items/<pid_value>",
        "template": "reroils_app/fullview_items.html",
    }
}

RECORDS_UI_EXPORT_FORMATS = {
    'recid': {
        'json': dict(
            title='JSON',
            serializer='invenio_records_rest.serializers'
                                     ':json_v1',
            order=1,
        )
    }
}

REROILS_APP_SORT_FACETS = {
    'records': 'language,author,location,status'
}

# SEARCH_UI_SEARCH_INDEX = 'records-record-v0.0.1'

RECORDS_REST_FACETS = {
    'records': dict(
        aggs=dict(
            status=dict(
                terms=dict(
                    field='citems._circulation.status',
                    size=0
                )
            ),
            location=dict(
                terms=dict(
                    field='citems.location',
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
            _('status'): terms_filter('citems._circulation.status'),
            _('location'): terms_filter('citems.location'),
            _('language'): terms_filter('languages.language'),
            _('author'): terms_filter('facet_authors')
        },
        post_filters={
            _('years'):range_filter(
                'publicationYear',
                format='yyyy',
                end_date_math='/y'
            )
        }
    )
}

# sort
RECORDS_REST_SORT_OPTIONS = {
    'records': dict(
        # title=dict(
        #     fields=['title'],
        #     title='Title',
        #     default_order='asc',
        #     order=1
        # ),
        # author=dict(
        #     fields=['authors.name'],
        #     title='Author',
        #     default_order='asc',
        #     order=2
        # ),
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

#default sort
RECORDS_REST_DEFAULT_SORT = {
    'records': dict(query='bestmatch', noquery='mostrecent'),
}


INDEXER_REPLACE_REFS = False

REROILS_RECORD_EDITOR_FORM_OPTIONS = (
    'reroils_data.form_options',
    'records/record-v0.0.1.json'
)

REROILS_RECORD_EDITOR_JSONSCHEMA = 'records/record-v0.0.1.json'
REROILS_RECORD_EDITOR_PERMALINK_RERO_URL = 'http://data.rero.ch/'
REROILS_RECORD_EDITOR_PERMALINK_BNF_URL = 'http://catalogue.bnf.fr/ark:/12148/'

SECURITY_CHANGEABLE = False
"""Allow password change by users."""

SECURITY_CONFIRMABLE = False
"""Allow user to confirm their email address."""

SECURITY_RECOVERABLE = False
"""Allow password recovery by users."""

SECURITY_REGISTERABLE = False
"""Allow users to register."""
