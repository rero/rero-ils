# -*- coding: utf-8 -*-

"""reroils-app base Invenio configuration."""

from __future__ import absolute_import, print_function


# Identity function for string extraction
def _(x):
    return x

# Default language and timezone
BABEL_DEFAULT_LANGUAGE = 'en'
BABEL_DEFAULT_TIMEZONE = 'Europe/Zurich'
I18N_LANGUAGES = [
]

HEADER_TEMPLATE = 'invenio_theme/header.html'
BASE_TEMPLATE = 'invenio_theme/page.html'
COVER_TEMPLATE = 'invenio_theme/page_cover.html'
SETTINGS_TEMPLATE = 'invenio_theme/page_settings.html'

# WARNING: Do not share the secret key - especially do not commit it to
# version control.
SECRET_KEY = 'vdJLhU0z3elI6NyfB0y8ZSJwabuJ4B3mgjXtVxBKUGaqKxfoirLUrVjJAMQx3zKCzPqo6YwT0cprOsamTEI2vVMWdmOTp7Xn0GjzcIFs1n3baDQlicLhbI5dzyWqGBrKZS6rOpipZMdnwP1yMBtmu5dTBVfVjLd5yaTCx1iUKHjLNYMdY6k4XWUWDSIdNMfM5GF63Ar1qfRcCtzivQtYMX4UujM03rC5Ciu6osoxDMsxEwfwaMXhkUn1Py6WtttM'

# Theme
THEME_SITENAME = _('reroils-app')

# For dev
APP_ENABLE_SECURE_HEADERS=False

# no needs for redis
CACHE_TYPE='simple'


USER_EMAIL='software@rero.ch'
USER_PASS='uspass123'
POSTGRESQL_HOST='postgresql'
SQLALCHEMY_DATABASE_URI='postgresql+psycopg2://reroils:dbpass123@postgresql:5432/reroils'
REDIS_HOST='redis'
SEARCH_ELASTIC_HOSTS='elasticsearch'
RABBITMQ_HOST='rabbitmq'
BROKER_URL='amqp://guest:guest@rabbitmq:5672//'
CELERY_BROKER_URL='amqp://guest:guest@rabbitmq:5672//'
CELERY_RESULT_BACKEND='redis://redis:6379/1'
JSONSCHEMAS_ENDPOINT='/schema'
JSONSCHEMAS_HOST='localhost:5000'