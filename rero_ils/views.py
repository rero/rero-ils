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

"""Blueprint used for loading templates."""

from __future__ import absolute_import, print_function

import copy
import re
from functools import partial

from flask import Blueprint, current_app, jsonify, redirect, render_template, \
    request
from flask_babelex import gettext as _
from flask_login import current_user
from flask_menu import current_menu
from invenio_i18n.ext import current_i18n
from invenio_jsonschemas import current_jsonschemas
from invenio_jsonschemas.errors import JSONSchemaNotFound

from rero_ils.modules.patrons.api import Patron

from .modules.babel_extractors import translate
from .utils import i18n_to_str
from .version import __version__

blueprint = Blueprint(
    'rero_ils',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.before_app_request
def init_menu():
    """Create the header menus."""
    item = current_menu.submenu('main.menu')
    item.register(
        endpoint=None,
        text='{icon} <span class="{visible}">{menu}'.format(
            icon='<i class="fa fa-bars"></i>',
            visible='visible-md-inline visible-lg-inline',
            menu=_('Menu')
        ),
        order=0
    )

    order = 10

    def return_language(lang):
        return dict(lang_code=lang)

    def hide_language(lang):
        return current_i18n.language != lang

    for language_item in current_i18n.get_locales():
        item = current_menu.submenu(
            'main.menu.lang_{language}'.format(
                language=language_item.language))
        item.register(
            endpoint='invenio_i18n.set_lang',
            endpoint_arguments_constructor=partial(
                return_language, language_item.language),
            text='{icon} {language}'.format(
                icon='<i class="fa fa-language"></i>',
                language=_(i18n_to_str(language_item.language))
            ),
            visible_when=partial(hide_language, language_item.language),
            order=order
        )
        order += 1

    item = current_menu.submenu('main.menu.help')
    item.register(
        endpoint='rero_ils.help',
        text='{icon} {help}'.format(
            icon='<i class="fa fa-info"></i>',
            help=_('Help')
        ),
        order=100
    )

    item = current_menu.submenu('main.profile')
    account = _('My Account')
    if current_user.is_authenticated:
        patron = Patron.get_patron_by_email(current_user.email)
        if patron:
            account = patron.initial
    item.register(
        endpoint=None,
        text='{icon} <span class="{visible}">{account}</span>'.format(
            icon='<i class="fa fa-user"></i>',
            visible='visible-md-inline visible-lg-inline',
            account=account
        ),
        order=1
    )

    item = current_menu.submenu('main.profile.login')
    item.register(
        endpoint='security.login',
        endpoint_arguments_constructor=lambda: dict(next=request.path),
        visible_when=lambda: not current_user.is_authenticated,
        text='{icon} {login}'.format(
            icon='<i class="fa fa-sign-in"></i>',
            login=_('Login')
        ),
        order=1
    )

    item = current_menu.submenu('main.profile.logout')
    item.register(
        endpoint='security.logout',
        visible_when=lambda: current_user.is_authenticated,
        text='{icon} {logout}'.format(
            icon='<i class="fa fa-sign-out"></i>',
            logout=_('Logout')
        ),
        order=1
    )

    item = current_menu.submenu('main.profile.signup')
    item.register(
        endpoint='security.register',
        visible_when=lambda: not current_user.is_authenticated,
        text='{icon} {signup}'.format(
            icon='<i class="fa fa-user-plus"></i>',
            signup=_('Sign Up')
        ),
        order=2
    )


@blueprint.route('/ping', methods=['HEAD', 'GET'])
def ping():
    """Load balancer ping view."""
    return 'OK'


@blueprint.route('/')
def index():
    """Home Page."""
    return render_template('rero_ils/frontpage.html',
                           version=__version__)


@blueprint.route('/help')
def help():
    """Help Page."""
    return redirect(
        current_app.config.get('RERO_ILS_APP_HELP_PAGE'),
        code=302)


@blueprint.app_template_filter()
def nl2br(string):
    r"""Replace \n to <br>."""
    return string.replace("\n", "<br>")


def prepare_jsonschema(schema):
    """."""
    schema = copy.deepcopy(schema)
    del schema['$schema']
    schema['required'].remove('pid')
    return translate(schema)


def prepare_form_option(form_option):
    """."""
    form_option = copy.deepcopy(form_option)
    return translate(form_option)


@blueprint.route('/schemaform/<document_type>')
def schemaform(document_type):
    """Return schema and form options for the editor."""
    doc_type = document_type
    doc_type = re.sub('ies$', 'y', doc_type)
    doc_type = re.sub('s$', '', doc_type)
    data = {}
    schema = None
    schema_name = None
    try:
        current_jsonschemas.get_schema.cache_clear()
        schema_name = '{}/{}-v0.0.1.json'.format(document_type, doc_type)
        schema = current_jsonschemas.get_schema(schema_name)
        # del data['jsonschema']['$schema']
    except JSONSchemaNotFound:
        pass
    data['schema'] = prepare_jsonschema(schema)

    try:
        form = current_jsonschemas.get_schema(
            'form_{}/{}-v0.0.1.json'.format(document_type, doc_type))
        data['layout'] = prepare_form_option(form)
    except JSONSchemaNotFound as e:
        raise(e)
        pass
    return jsonify(data)
