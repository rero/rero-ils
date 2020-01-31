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
from invenio_circulation.signals import loan_state_changed
from invenio_indexer.signals import before_record_index
from invenio_oaiharvester.signals import oaiharvest_finished
from invenio_records.signals import after_record_delete, after_record_insert, \
    after_record_revert, after_record_update

from .apiharvester.signals import apiharvest_part
from .documents.listener import enrich_document_data
from .ebooks.receivers import publish_harvested_records
from .holdings.listener import enrich_holding_data
from .items.listener import enrich_item_data
from .loans.listener import enrich_loan_data, listener_loan_state_changed
from .locations.listener import enrich_location_data
from .notifications.listener import enrich_notification_data
from .patron_transaction_events.listener import \
    enrich_patron_transaction_event_data
from .patron_transactions.listener import enrich_patron_transaction_data
from .patrons.listener import enrich_patron_data
from .persons.listener import enrich_persons_data
from .persons.receivers import publish_api_harvested_records
from ..filter import format_date_filter, jsondumps, text_to_id, to_pretty_json


class REROILSAPP(object):
    """rero-ils extension."""

    def __init__(self, app=None):
        """RERO ILS App module."""
        from ..permissions import can_access_item, can_edit
        if app:
            self.init_app(app)
            # force to load ils template before others
            # it is require for Flask-Security see:
            # https://pythonhosted.org/Flask-Security/customizing.html#emails
            ils_loader = jinja2.ChoiceLoader([
                jinja2.PackageLoader('rero_ils', 'templates'),
                app.jinja_loader
            ])
            app.jinja_loader = ils_loader

            # register filters
            app.add_template_filter(format_date_filter, name='format_date')
            app.add_template_filter(to_pretty_json, name='tojson_pretty')
            app.add_template_filter(can_edit, name='can_edit')
            app.add_template_filter(
                can_access_item,
                name='can_access_item'
            )
            app.add_template_filter(text_to_id, name='text_to_id')
            app.add_template_filter(jsondumps, name='jsondumps')
            app.jinja_env.add_extension('jinja2.ext.do')
            self.register_signals()

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions['rero-ils'] = self

    def init_config(self, app):
        """Initialize configuration."""
        # Use theme's base template if theme is installed
        for k in dir(app.config):
            if k.startswith('RERO_ILS_APP_'):
                app.config.setdefault(k, getattr(app.config, k))

    def register_signals(self):
        """Register signals."""
        before_record_index.connect(enrich_loan_data)
        before_record_index.connect(enrich_document_data)
        before_record_index.connect(enrich_persons_data)
        before_record_index.connect(enrich_item_data)
        before_record_index.connect(enrich_patron_data)
        before_record_index.connect(enrich_location_data)
        before_record_index.connect(enrich_holding_data)
        before_record_index.connect(enrich_notification_data)
        before_record_index.connect(enrich_patron_transaction_event_data)
        before_record_index.connect(enrich_patron_transaction_data)

        loan_state_changed.connect(listener_loan_state_changed, weak=False)

        oaiharvest_finished.connect(publish_harvested_records, weak=False)

        apiharvest_part.connect(publish_api_harvested_records, weak=False)
