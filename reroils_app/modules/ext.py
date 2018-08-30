# -*- coding: utf-8 -*-
#
# This file is part of REROILS.
# Copyright (C) 2017 RERO.
#
# REROILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# REROILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with REROILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""REROILS invenio module declaration."""

from __future__ import absolute_import, print_function

from invenio_oaiharvester.signals import oaiharvest_finished

from ..filter import format_date_filter, item_status_text, to_pretty_json
from .ebooks.receivers import publish_harvested_records


class REROILSAPP(object):
    """reroils-app extension."""

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
        app.extensions['reroils-app'] = self

    def init_config(self, app):
        """Initialize configuration."""
        # Use theme's base template if theme is installed
        if 'BASE_TEMPLATE' in app.config:
            app.config.setdefault(
                'REROILS_APP_BASE_TEMPLATE',
                app.config['BASE_TEMPLATE'],
            )
        for k in dir(app.config):
            if k.startswith('REROILS_APP_'):
                app.config.setdefault(k, getattr(app.config, k))

    def register_signals(self):
        """Register signals."""
        from .items.signals import item_at_desk
        from .patrons.listener import listener_item_at_desk
        item_at_desk.connect(listener_item_at_desk)
        oaiharvest_finished.connect(publish_harvested_records,
                                    weak=False)
