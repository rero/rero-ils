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

from invenio_admin import current_admin
from invenio_circulation.signals import loan_state_changed
from invenio_indexer.signals import before_record_index
from invenio_oaiharvester.signals import oaiharvest_finished
from invenio_records.signals import after_record_delete, after_record_insert, \
    after_record_revert, after_record_update

from .apiharvester.signals import apiharvest_part
from .documents.listener import enrich_document_data, mef_person_delete, \
    mef_person_insert, mef_person_revert, mef_person_update
from .ebooks.receivers import publish_harvested_records
from .items.listener import enrich_item_data
from .items.signals import item_at_desk
from .loans.listener import enrich_loan_data, listener_loan_state_changed
from .locations.listener import enrich_location_data
from .mef_persons.receivers import publish_api_harvested_records
from .notifications.listener import enrich_notification_data
from .patrons.listener import enrich_patron_data, listener_item_at_desk
from ..filter import admin_menu_is_visible, format_date_filter, jsondumps, \
    resource_can_create, text_to_id, to_pretty_json


class REROILSAPP(object):
    """rero-ils extension."""

    def __init__(self, app=None):
        """RERO ILS App module."""
        from ..permissions import can_access_item, can_edit
        if app:
            self.init_app(app)
            app.add_template_filter(format_date_filter, name='format_date')
            app.add_template_filter(to_pretty_json, name='tojson_pretty')
            app.add_template_filter(can_edit, name='can_edit')
            app.add_template_filter(
                can_access_item,
                name='can_access_item'
            )
            app.add_template_filter(text_to_id, name='text_to_id')
            app.add_template_filter(jsondumps, name='jsondumps')
            app.add_template_filter(
                resource_can_create,
                name='resource_can_create')
            app.add_template_filter(
                admin_menu_is_visible,
                name='admin_menu_is_visible'
            )
            app.jinja_env.add_extension('jinja2.ext.do')
            self.register_signals()

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions['rero-ils'] = self

        # invenio-admin is not available for the wsgi_api application
        def get_admin_menu():
            if app.extensions.get('invenio-admin'):
                return dict(admin_root_menu=current_admin.admin.menu())
            return dict()

        app.context_processor(get_admin_menu)

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
        before_record_index.connect(enrich_item_data)
        before_record_index.connect(enrich_patron_data)
        before_record_index.connect(enrich_location_data)
        before_record_index.connect(enrich_notification_data)

        item_at_desk.connect(listener_item_at_desk)

        loan_state_changed.connect(listener_loan_state_changed, weak=False)

        oaiharvest_finished.connect(publish_harvested_records, weak=False)

        apiharvest_part.connect(publish_api_harvested_records, weak=False)

        after_record_insert.connect(mef_person_insert)
        after_record_update.connect(mef_person_update)
        after_record_delete.connect(mef_person_delete)
        after_record_revert.connect(mef_person_revert)
