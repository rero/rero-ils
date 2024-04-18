# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

"""RERO ILS invenio module declaration."""

import logging

import jinja2
from flask import Blueprint
from flask_bootstrap import Bootstrap4
from flask_login.signals import user_loaded_from_cookie, user_logged_in, \
    user_logged_out
from flask_principal import identity_loaded
from flask_wiki import Wiki
from invenio_base.signals import app_loaded
from invenio_base.utils import obj_or_import_string
from invenio_circulation.signals import loan_state_changed
from invenio_indexer.signals import before_record_index
from invenio_oaiharvester.signals import oaiharvest_finished
from invenio_records.signals import after_record_insert, after_record_update, \
    before_record_update
from invenio_records_rest.errors import JSONSchemaValidationError
from jsonschema.exceptions import ValidationError

from rero_ils.filter import address_block, empty_data, format_date_filter, \
    get_record_by_ref, jsondumps, message_filter, node_assets, text_to_id, \
    to_pretty_json, translate
from rero_ils.modules.acquisition.acq_accounts.listener import \
    enrich_acq_account_data
from rero_ils.modules.acquisition.acq_order_lines.listener import \
    enrich_acq_order_line_data
from rero_ils.modules.acquisition.acq_orders.listener import \
    enrich_acq_order_data
from rero_ils.modules.acquisition.acq_receipt_lines.listener import \
    enrich_acq_receipt_line_data
from rero_ils.modules.acquisition.acq_receipts.listener import \
    enrich_acq_receipt_data
from rero_ils.modules.acquisition.budgets.listener import \
    budget_is_active_changed
from rero_ils.modules.collections.listener import enrich_collection_data
from rero_ils.modules.ebooks.receivers import publish_harvested_records
from rero_ils.modules.holdings.listener import enrich_holding_data, \
    update_items_locations_and_types
from rero_ils.modules.ill_requests.listener import enrich_ill_request_data
from rero_ils.modules.imports.views import ImportsListResource, \
    ImportsResource, ResultNotFoundOnTheRemoteServer
from rero_ils.modules.item_types.listener import negative_availability_changes
from rero_ils.modules.items.listener import enrich_item_data
from rero_ils.modules.items.views.filters import issue_client_reference
from rero_ils.modules.loans.listener import enrich_loan_data, \
    listener_loan_state_changed
from rero_ils.modules.normalizer_stop_words import NormalizerStopWords
from rero_ils.modules.notifications.listener import enrich_notification_data
from rero_ils.modules.patron_transaction_events.listener import \
    enrich_patron_transaction_event_data
from rero_ils.modules.patron_transactions.listener import \
    enrich_patron_transaction_data
from rero_ils.modules.patrons.api import current_librarian, current_patrons
from rero_ils.modules.patrons.listener import \
    create_subscription_patron_transaction, enrich_patron_data
from rero_ils.modules.permissions import LibraryNeed, OrganisationNeed, \
    OwnerNeed
from rero_ils.modules.sru.views import SRUDocumentsSearch
from rero_ils.modules.templates.listener import prepare_template_data
from rero_ils.modules.users.listener import user_register_forms, \
    user_reset_password_forms
from rero_ils.modules.users.views import UsersCreateResource, UsersResource
from rero_ils.modules.utils import remove_user_name, set_user_name
from rero_ils.version import __version__

from .receivers import set_boosting_query_fields


@identity_loaded.connect
def on_identity_loaded(sender, identity):
    """Add ``Needs`` to manage RERO-ILS permissions.

    Add custom RERO-ILS ``Needs`` that will be used to manage policies on
    application resources.
    Assuming that ``RoleNeed`` and ``UserNeed`` are already populated by
    flask modules.

    @param sender: the sender application.
    @param identity: the identity to enrich.
    """
    if current_librarian:
        identity.provides.update([
            OwnerNeed(current_librarian.pid),
            OrganisationNeed(current_librarian.organisation_pid)
        ])
        # for a `full_permission` user, the manageable libraries are all
        # libraries from the organisation ; otherwise, this is the libraries
        # referenced into the ``Patron`` profile.
        library_pids = current_librarian.library_pids
        if current_librarian.has_full_permissions:
            library_pids = current_librarian.organisation.get_libraries_pids()
        for library_pid in library_pids:
            identity.provides.add(LibraryNeed(library_pid))
    # patrons
    elif current_patrons:
        for patron in current_patrons:
            identity.provides.update([
                OwnerNeed(patron.pid),
                OrganisationNeed(patron.organisation_pid)
            ])


@app_loaded.connect
def load_actions(sender, app):
    """Register actions use to control permissions on the applications.

    Why doing this here and not into pyproject.toml ::
        Official `invenio-access` documentation describe how to automatically
        register actions using the  `invenio-access.actions` entrypoint.
        see : https://invenio-access.readthedocs.io/en/latest/
              usage.html#registering-actions

        But, using this approach all actions will also be loaded for any CLI
        application. As this task is time-consuming (100 actions ~= 15 seconds)
        we choose to load these actions only when the application is fully
        loaded (so we ensure than invenio-access module is available).

    :param sender: the application factory function.
    :param app: the Flask application instance.
    """
    # We can't use the `current_access` proxy from `invenio-access` because
    # we need the application context to use it. At this time, the context
    # isn't define ; get the invenio-access extension directly from app.
    access_ext = app.extensions['invenio-access']
    for action in app.config.get('RERO_ILS_PERMISSIONS_ACTIONS', []):
        access_ext.register_action(obj_or_import_string(action))

    # add jsonschema resolution from local:// and bib.rero.ch
    data = app.extensions["invenio-jsonschemas"].refresolver_store()
    cfg = app.config
    schema_url = f'{cfg["JSONSCHEMAS_URL_SCHEME"]}://'\
                 f'{cfg["JSONSCHEMAS_HOST"]}'\
                 f'{cfg["JSONSCHEMAS_ENDPOINT"]}/'

    app.extensions['rero-ils'].jsonschema_store = dict(
        **data,
        **{
            k.replace('local://', schema_url): v
            for k, v in data.items()
        }
    )


class REROILSAPP(object):
    """rero-ils extension."""

    def __init__(self, app=None):
        """RERO ILS App module."""
        # jsonschema store
        # SEE: RECORDS_REFRESOLVER_STORE for more details
        self.jsonschema_store = {}
        if app:
            self.init_app(app)
            # force to load ils template before others
            # it is required for Flask-Security see:
            # https://pythonhosted.org/Flask-Security/customizing.html#emails
            ils_loader = jinja2.ChoiceLoader([
                jinja2.PackageLoader('rero_ils', 'theme/templates'),
                app.jinja_loader
            ])
            app.jinja_loader = ils_loader

            # register filters
            app.add_template_filter(get_record_by_ref)
            app.add_template_filter(format_date_filter, name='format_date')
            app.add_template_global(node_assets)
            app.add_template_filter(to_pretty_json, name='tojson_pretty')
            app.add_template_filter(text_to_id)
            app.add_template_filter(jsondumps)
            app.add_template_filter(empty_data)
            app.add_template_filter(address_block)
            app.add_template_filter(message_filter, name='message')
            app.add_template_filter(issue_client_reference)
            app.add_template_filter(translate)
            app.jinja_env.add_extension('jinja2.ext.do')
            app.jinja_env.globals['version'] = __version__
            self.register_signals(app)

    def init_app(self, app):
        """Flask application initialization."""
        Bootstrap4(app)
        Wiki(app)
        NormalizerStopWords(app)
        self.init_config(app)
        app.extensions['rero-ils'] = self
        REROILSAPP.register_import_api_blueprint(app)
        REROILSAPP.register_users_api_blueprint(app)
        REROILSAPP.register_sru_api_blueprint(app)
        if db_log := app.config.get('RERO_ILS_DB_LOGGING'):
            logging.getLogger('sqlalchemy.engine').setLevel(db_log)
        if es_log := app.config.get('RERO_ILS_ES_LOGGING'):
            es_trace_logger = logging.getLogger('elasticsearch.trace')
            es_trace_logger.setLevel(es_log)
            handler = logging.StreamHandler()
            es_trace_logger.addHandler(handler)
        app_loaded.connect(set_boosting_query_fields)

    @staticmethod
    def register_import_api_blueprint(app):
        """Imports blueprints initialization."""

        def handle_bad_request(e):
            return 'not found', 404

        blueprint = Blueprint('api_imports', __name__)
        endpoints = app.config.get('RERO_IMPORT_REST_ENDPOINTS', {})
        for key, config in endpoints.items():
            # search view
            search_view_name = f'import_{key}'
            search_path = f'/import_{key}/'
            search_view = ImportsListResource.as_view(
                search_view_name,
                import_class=config.get('import_class'),
                import_size=config.get('import_size')
            )
            blueprint.add_url_rule(search_path, view_func=search_view)

            # record view
            record_view_name = f'import_{key}_record'
            record_path = f'/import_{key}/<id>'
            record_view = ImportsResource.as_view(
                record_view_name,
                import_class=config.get('import_class')
            )
            blueprint.add_url_rule(record_path, view_func=record_view)

        blueprint.register_error_handler(
            ResultNotFoundOnTheRemoteServer,
            handle_bad_request
        )
        app.register_blueprint(blueprint)

    @staticmethod
    def register_users_api_blueprint(app):
        """User blueprints initialization."""
        blueprint = Blueprint('api_users', __name__)

        @blueprint.errorhandler(ValidationError)
        def validation_error(error):
            """Catch validation errors."""
            return JSONSchemaValidationError(error=error).get_response()

        blueprint.add_url_rule(
            '/users/<id>',
            view_func=UsersResource.as_view('users_item')
        )
        blueprint.add_url_rule(
            '/users/',
            view_func=UsersCreateResource.as_view('users_list')
        )
        app.register_blueprint(blueprint)

    @staticmethod
    def register_sru_api_blueprint(app):
        """SRU blueprints initialization."""
        blueprint = Blueprint('api_sru', __name__)
        sru_documents_search = SRUDocumentsSearch.as_view('documents')
        blueprint.add_url_rule(
            '/sru/documents',
            view_func=sru_documents_search
        )
        app.register_blueprint(blueprint)

    def init_config(self, app):
        """Initialize configuration."""
        # Use theme's base template if theme is installed
        for k in dir(app.config):
            if k.startswith('RERO_ILS_APP_'):
                app.config.setdefault(k, getattr(app.config, k))
        # add keep alive support for angular application
        # NOTE: this will not work for werkzeug> 2.1.2
        # https://werkzeug.palletsprojects.com/en/2.2.x/changes/#version-2-1-2
        if app.config.get('DEBUG'):
            from werkzeug.serving import WSGIRequestHandler
            WSGIRequestHandler.protocol_version = "HTTP/1.1"

    def register_signals(self, app):
        """Register signals."""
        # TODO: use before_record_index.dynamic_connect() if it works
        # example:
        # before_record_index.dynamic_connect(
        #    enrich_patron_data, sender=app, index='patrons-patron-v0.0.1')
        before_record_index.connect(enrich_acq_account_data, sender=app)
        before_record_index.connect(enrich_acq_order_data, sender=app)
        before_record_index.connect(enrich_acq_receipt_data, sender=app)
        before_record_index.connect(enrich_acq_receipt_line_data, sender=app)
        before_record_index.connect(enrich_acq_order_line_data, sender=app)
        before_record_index.connect(enrich_collection_data, sender=app)
        before_record_index.connect(enrich_loan_data, sender=app)
        before_record_index.connect(enrich_item_data, sender=app)
        before_record_index.connect(enrich_patron_data, sender=app)
        before_record_index.connect(enrich_holding_data, sender=app)
        before_record_index.connect(enrich_notification_data, sender=app)
        before_record_index.connect(enrich_patron_transaction_event_data,
                                    sender=app)
        before_record_index.connect(enrich_patron_transaction_data, sender=app)
        before_record_index.connect(enrich_ill_request_data, sender=app)
        before_record_index.connect(prepare_template_data, sender=app)

        after_record_insert.connect(create_subscription_patron_transaction)
        after_record_update.connect(create_subscription_patron_transaction)
        after_record_update.connect(update_items_locations_and_types)

        before_record_update.connect(budget_is_active_changed)
        before_record_update.connect(negative_availability_changes)

        loan_state_changed.connect(listener_loan_state_changed, weak=False)

        oaiharvest_finished.connect(publish_harvested_records, weak=False)

        # store the username in the session
        user_logged_in.connect(set_user_name)
        user_logged_out.connect(remove_user_name)
        user_loaded_from_cookie.connect(set_user_name)

        # invenio-base signal: after application loaded
        app_loaded.connect(user_register_forms, weak=False)
        app_loaded.connect(user_reset_password_forms, weak=False)
