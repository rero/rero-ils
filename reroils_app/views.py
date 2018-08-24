# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 RERO.
#
# reroils-app is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Blueprint used for loading templates.

The sole purpose of this blueprint is to ensure that Invenio can find the
templates and static files located in the folders of the same names next to
this file.
"""

from __future__ import absolute_import, print_function

from flask import Blueprint, current_app, redirect, render_template

from .version import __version__

blueprint = Blueprint(
    'reroils_app',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.route('/ping', methods=['HEAD', 'GET'])
def ping():
    """Load balancer ping view."""
    return 'OK'


@blueprint.route('/')
def index():
    """Home Page."""
    return render_template('reroils_app/frontpage.html',
                           version=__version__)


@blueprint.route('/help')
def help():
    """Help Page."""
    return redirect(
        current_app.config.get('REROILS_APP_HELP_PAGE'),
        code=302)
