# -*- coding: utf-8 -*-

"""reroils-app base Invenio configuration."""

from __future__ import absolute_import, print_function

from flask import Blueprint, redirect, render_template

from .version import __version__

blueprint = Blueprint(
    'reroils_app',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.route("/")
def index():
    """Home Page."""
    return render_template('reroils_app/frontpage.html',
                           version=__version__)


@blueprint.route("/help")
def help():
    """Help Page."""
    return redirect(
        "https://github.com/rero/reroils-app/wiki/Public-demo-help",
        code=302)
