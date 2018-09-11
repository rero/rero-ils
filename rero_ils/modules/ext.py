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

from ..filter import format_date_filter, item_status_text, to_pretty_json


class REROILSAPP(object):
    """rero-ils extension."""

    def __init__(self, app=None):
        """RERO ILS App module."""
        if app:
            self.init_app(app)
            app.add_template_filter(format_date_filter, name='format_date')
            app.add_template_filter(to_pretty_json, name='tojson_pretty')
            app.add_template_filter(item_status_text, name='item_status_text')
            self.register_signals()

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions['rero-ils'] = self

    def init_config(self, app):
        """Initialize configuration."""
        # Use theme's base template if theme is installed
        if 'BASE_TEMPLATE' in app.config:
            app.config.setdefault(
                'RERO_ILS_APP_BASE_TEMPLATE',
                app.config['BASE_TEMPLATE'],
            )
        for k in dir(app.config):
            if k.startswith('RERO_ILS_APP_'):
                app.config.setdefault(k, getattr(app.config, k))

    def register_signals(self):
        """Register signals."""
        from .patrons.listener import listener_item_at_desk
        from .items.signals import item_at_desk
        item_at_desk.connect(listener_item_at_desk)
        from invenio_oaiharvester.signals import oaiharvest_finished
        from .ebooks.receivers import publish_harvested_records
        oaiharvest_finished.connect(publish_harvested_records, weak=False)
        from .apiharvester.signals import apiharvest_part
        from .mef.receivers import publish_api_harvested_records
        apiharvest_part.connect(publish_api_harvested_records, weak=False)
