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

"""RERO ILS invenio module declaration."""

from __future__ import absolute_import, print_function

import jinja2
from flask import Blueprint
from flask_bootstrap import Bootstrap4
from flask_login.signals import user_loaded_from_cookie, user_logged_in, \
    user_logged_out
from flask_wiki import Wiki
from invenio_circulation.signals import loan_state_changed
from invenio_indexer.signals import before_record_index
from invenio_oaiharvester.signals import oaiharvest_finished
from invenio_records.signals import after_record_insert, after_record_update, \
    before_record_update
from invenio_records_rest.errors import JSONSchemaValidationError
from invenio_userprofiles.signals import after_profile_update
from jsonschema.exceptions import ValidationError

from rero_ils.filter import address_block, empty_data, format_date_filter, \
    get_record_by_ref, jsondumps, node_assets, text_to_id, to_pretty_json
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
from rero_ils.modules.contributions.listener import enrich_contributions_data
from rero_ils.modules.documents.listener import enrich_document_data
from rero_ils.modules.ebooks.receivers import publish_harvested_records
from rero_ils.modules.holdings.listener import enrich_holding_data, \
    update_items_locations_and_types
from rero_ils.modules.ill_requests.listener import enrich_ill_request_data
from rero_ils.modules.imports.views import ImportsListResource, \
    ImportsResource, ResultNotFoundOnTheRemoteServer
from rero_ils.modules.item_types.listener import negative_availability_changes
from rero_ils.modules.items.listener import enrich_item_data
from rero_ils.modules.loans.listener import enrich_loan_data, \
    listener_loan_state_changed
from rero_ils.modules.locations.listener import enrich_location_data
from rero_ils.modules.normalizer_stop_words import NormalizerStopWords
from rero_ils.modules.notifications.listener import enrich_notification_data
from rero_ils.modules.patron_transaction_events.listener import \
    enrich_patron_transaction_event_data
from rero_ils.modules.patron_transactions.listener import \
    enrich_patron_transaction_data
from rero_ils.modules.patrons.listener import \
    create_subscription_patron_transaction, enrich_patron_data, \
    update_from_profile
from rero_ils.modules.sru.views import SRUDocumentsSearch
from rero_ils.modules.templates.listener import prepare_template_data
from rero_ils.modules.users.views import UsersCreateResource, UsersResource
from rero_ils.modules.utils import remove_user_name, set_user_name
from rero_ils.version import __version__


class REROILSAPP(object):
    """rero-ils extension."""

    def __init__(self, app=None):
        """RERO ILS App module."""
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
            app.add_template_filter(
                get_record_by_ref, name='get_record_by_ref')
            app.add_template_filter(format_date_filter, name='format_date')
            app.add_template_global(node_assets, name='node_assets')
            app.add_template_filter(to_pretty_json, name='tojson_pretty')
            app.add_template_filter(text_to_id, name='text_to_id')
            app.add_template_filter(jsondumps, name='jsondumps')
            app.add_template_filter(empty_data, name='empty_data')
            app.add_template_filter(address_block, name='address_block')
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
        # import logging
        # logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    @staticmethod
    def register_import_api_blueprint(app):
        """Imports blueprints initialization."""

        def handle_bad_request(e):
            return 'not found', 404

        api_blueprint = Blueprint('api_imports', __name__)
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
            api_blueprint.add_url_rule(search_path, view_func=search_view)

            # record view
            record_view_name = f'import_{key}_record'
            record_path = f'/import_{key}/<id>'
            record_view = ImportsResource.as_view(
                record_view_name,
                import_class=config.get('import_class')
            )
            api_blueprint.add_url_rule(record_path, view_func=record_view)

        api_blueprint.register_error_handler(
            ResultNotFoundOnTheRemoteServer,
            handle_bad_request
        )
        app.register_blueprint(api_blueprint)

    @staticmethod
    def register_users_api_blueprint(app):
        """User blueprints initialization."""
        api_blueprint = Blueprint('api_users', __name__)

        @api_blueprint.errorhandler(ValidationError)
        def validation_error(error):
            """Catch validation errors."""
            return JSONSchemaValidationError(error=error).get_response()

        api_blueprint.add_url_rule(
            '/users/<id>',
            view_func=UsersResource.as_view('users_item')
        )
        api_blueprint.add_url_rule(
            '/users/',
            view_func=UsersCreateResource.as_view('users_list')
        )
        app.register_blueprint(api_blueprint)

    @staticmethod
    def register_sru_api_blueprint(app):
        """SRU blueprints initialization."""
        api_blueprint = Blueprint('api_sru', __name__)
        sru_documents_search = SRUDocumentsSearch.as_view('documents')
        api_blueprint.add_url_rule(
            '/sru/documents',
            view_func=sru_documents_search
        )
        app.register_blueprint(api_blueprint)

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
        before_record_index.connect(enrich_document_data, sender=app)
        before_record_index.connect(enrich_contributions_data, sender=app)
        before_record_index.connect(enrich_item_data, sender=app)
        before_record_index.connect(enrich_patron_data, sender=app)
        before_record_index.connect(enrich_location_data, sender=app)
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

        # invenio-userprofiles signal
        after_profile_update.connect(update_from_profile)

        # store the username in the session
        user_logged_in.connect(set_user_name)
        user_logged_out.connect(remove_user_name)
        user_loaded_from_cookie.connect(set_user_name)
