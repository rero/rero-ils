# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""RERO ILS invenio module declaration."""

from __future__ import absolute_import, print_function

from invenio_admin import current_admin

from ..filter import admin_menu_is_visible, format_date_filter, jsondumps, \
    resource_can_create, to_pretty_json
from ..permissions import can_edit


class REROILSAPP(object):
    """rero-ils extension."""

    def __init__(self, app=None):
        """RERO ILS App module."""
        if app:
            self.init_app(app)
            app.add_template_filter(format_date_filter, name='format_date')
            app.add_template_filter(to_pretty_json, name='tojson_pretty')
            app.add_template_filter(can_edit, name='can_edit')
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
        app.context_processor(lambda: dict(
            admin_root_menu=current_admin.admin.menu()))

    def init_config(self, app):
        """Initialize configuration."""
        # Use theme's base template if theme is installed
        for k in dir(app.config):
            if k.startswith('RERO_ILS_APP_'):
                app.config.setdefault(k, getattr(app.config, k))

    def register_signals(self):
        """Register signals."""
        from invenio_indexer.signals import before_record_index
        from .loans.listener import enrich_loan_data
        before_record_index.connect(enrich_loan_data)
        from .documents.listener import enrich_document_data
        before_record_index.connect(enrich_document_data)

        from .patrons.listener import listener_item_at_desk
        from .items.signals import item_at_desk
        item_at_desk.connect(listener_item_at_desk)

        from invenio_oaiharvester.signals import oaiharvest_finished
        from .ebooks.receivers import publish_harvested_records
        oaiharvest_finished.connect(publish_harvested_records, weak=False)

        from .apiharvester.signals import apiharvest_part
        from .mef_persons.receivers import publish_api_harvested_records
        apiharvest_part.connect(publish_api_harvested_records, weak=False)
