# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 RERO.
#
# reroils-app is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""REROILS invenio module declaration."""

from __future__ import absolute_import, print_function

from flask_babelex import gettext as _
from invenio_oaiharvester.signals import oaiharvest_finished

from ..filter import format_date_filter, item_status_text, to_pretty_json
from .ebooks.receivers import publish_harvested_records


class REROILSAPP(object):
    """rerpils-app extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        # TODO: This is an example of translation string with comment. Please
        # remove it.
        # NOTE: This is a note to a translator.
        _('A translation string')
        if app:
            self.init_app(app)
            app.add_template_filter(format_date_filter, name='format_date')
            app.add_template_filter(to_pretty_json, name='tojson_pretty')
            app.add_template_filter(item_status_text, name='item_status_text')
            self.register_signals()

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions['rerpils-app'] = self

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
