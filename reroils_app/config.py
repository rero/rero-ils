# -*- coding: utf-8 -*-

"""reroils-app base Invenio configuration."""

from __future__ import absolute_import, print_function

from invenio_search import RecordsSearch


# Identity function for string extraction
def _(x):
    return x

# Default language and timezone
BABEL_DEFAULT_LANGUAGE = 'en_US'
BABEL_DEFAULT_TIMEZONE = 'Europe/Zurich'
I18N_LANGUAGES = [
    ('fr', _('French')),
    ('de', _('German')),
    ('it', _('Italian'))
]

HEADER_TEMPLATE = 'invenio_theme/header.html'
BASE_TEMPLATE = 'reroils_app/page.html'
REROILS_RECORD_EDITOR_BASE_TEMPLATE = 'reroils_app/page.html'
COVER_TEMPLATE = 'invenio_theme/page_cover.html'
SEARCH_UI_JSTEMPLATE_RESULTS = \
    'templates/reroils_app/briefview.html'
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
CACHE_TYPE='simple'


USER_EMAIL='software@rero.ch'
USER_PASS='uspass123'

SQLALCHEMY_DATABASE_URI='postgresql+psycopg2://reroils:dbpass123@postgresql:5432/reroils'
SEARCH_ELASTIC_HOSTS='elasticsearch'
CELERY_BROKER_URL='amqp://guest:guest@rabbitmq:5672//'
CELERY_RESULT_BACKEND='redis://redis:6379/1'

CIRCULATION_ITEM_SCHEMA = 'records/item-v0.0.1.json'

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
        search_index='records-record-v0.0.1',
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
    },
    "recid_export": {
        "pid_type": "recid",
        "route": "/records/<pid_value>/export/<format>",
        "view_imp": "invenio_records_ui.views.export",
        "template": "invenio_records_ui/export.html",
    },
    "crcitm": {
        "pid_type": "crcitm",
        "route": "/items/<pid_value>",
        "template": "reroils_app/fullview_items.html",
    }
}

INDEXER_REPLACE_REFS = False

REROILS_RECORD_EDITOR_FORM_OPTIONS = (
    'reroils_data.form_options',
    'records/record-v0.0.1.json'
)

REROILS_RECORD_EDITOR_JSONSCHEMA = 'records/record-v0.0.1.json'

SEARCH_UI_SEARCH_TEMPLATE = "reroils_app/search.html"