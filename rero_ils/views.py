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

"""Blueprint used for loading templates."""

from __future__ import absolute_import, print_function

import copy
import re
from functools import partial, wraps

from flask import Blueprint, abort, current_app, jsonify, redirect, \
    render_template, request, session, url_for
from flask_babelex import gettext as _
from flask_login import current_user
from flask_menu import current_menu
from invenio_i18n.ext import current_i18n
from invenio_jsonschemas import current_jsonschemas
from invenio_jsonschemas.errors import JSONSchemaNotFound

from rero_ils.modules.organisations.api import Organisation
from rero_ils.modules.patrons.api import current_patron
from rero_ils.permissions import can_access_professional_view

from .modules.babel_extractors import translate
from .version import __version__

blueprint = Blueprint(
    'rero_ils',
    __name__,
    template_folder='templates',
    static_folder='static',
)


def init_menu_lang():
    """Create the header language menu."""
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
        ui_language = 'ui_language_{lang}'.format(lang=language_item.language)
        item.register(
            endpoint='invenio_i18n.set_lang',
            endpoint_arguments_constructor=partial(
                return_language, language_item.language),
            text='{icon} {language}'.format(
                icon='<i class="fa fa-language"></i>',
                language=_(ui_language)
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


def init_menu_profile():
    """Create the profile header menu."""
    item = current_menu.submenu('main.profile')
    if current_patron:
        session['user_initials'] = current_patron.initial
    else:
        try:
            session['user_initials'] = current_user.email
        # AnonymousUser
        except AttributeError:
            session.pop('user_initials', None)
    account = session.get('user_initials', _('My Account'))

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
        endpoint_arguments_constructor=lambda: dict(
            next=request.full_path
        ),
        visible_when=lambda: not current_user.is_authenticated,
        text='{icon} {login}'.format(
            icon='<i class="fa fa-sign-in"></i>',
            login=_('Login')
        ),
        order=1
    )

    item = current_menu.submenu('main.profile.professional')
    item.register(
        endpoint='rero_ils.professional',
        visible_when=lambda: current_patron.is_librarian,
        text='{icon} {professional}'.format(
            icon='<i class="fa fa-briefcase"></i>',
            professional=_('Switch to professional view')
        ),
        order=1
    )

    item = current_menu.submenu('main.profile.logout')
    item.register(
        endpoint='security.logout',
        endpoint_arguments_constructor=lambda: dict(
            next='/{viewcode}'.format(viewcode=request.view_args.get(
                'viewcode', current_app.config.get(
                    'RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'))
            )
        ),
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


@blueprint.before_app_request
def init_menu():
    """Create the header menus."""
    if (request.endpoint not in ['patrons.logged_user',
                                 'rero_ils.schemaform',
                                 'invenio_i18n.set_lang',
                                 'static',
                                 'security.login',
                                 'patrons.logged_user',
                                 '_debug_toolbar.static'] and
            request.method == 'GET'):
        init_menu_lang()
        init_menu_profile()


def check_organisation_viewcode(fn):
    """Check if viewcode parameter is defined."""
    @wraps(fn)
    def decorated_view(*args, **kwargs):
        viewCodes = Organisation.all_code()
        # Add default view code
        viewCodes.append(current_app.config.get(
            'RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'))
        if not kwargs['viewcode'] in viewCodes:
            abort(404)
        return fn(*args, **kwargs)

    return decorated_view


@blueprint.route('/error')
def error():
    """Error to generate exception for test purposes."""
    raise Exception('this is an error for test purposes')


@blueprint.route('/')
def index():
    """Home Page."""
    return render_template('rero_ils/frontpage.html',
                           version=__version__,
                           organisations=Organisation.get_all(),
                           viewcode=current_app.config.get(
                               'RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'))


@blueprint.route('/<string:viewcode>')
@blueprint.route('/<string:viewcode>/')
@check_organisation_viewcode
def index_with_view_code(viewcode):
    """Home Page."""
    if viewcode == current_app.config.get('RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'):
        return redirect(url_for(
            'rero_ils.index'
        ))
    else:
        return render_template(
            'rero_ils/frontpage.html',
            version=__version__,
            viewcode=viewcode
        )


@blueprint.route('/help')
def help():
    """Help Page."""
    return redirect(
        current_app.config.get('RERO_ILS_APP_HELP_PAGE'),
        code=302)


@blueprint.route('/language', methods=['POST', 'PUT'])
def set_language():
    """Set language in session.

    The call should be a POST or a PUT HTTP request with a JSON body as follow:

    .. code-block:: json

        {
            "lang": "fr"
        }
    """
    data = request.get_json()
    if not data or not data.get('lang'):
        return jsonify(
            {'errors': [{'code': 400, 'title': 'missing lang property'}]}), 400
    lang_code = data.get('lang')
    languages = dict(current_app.extensions['invenio-i18n'].get_languages())
    if lang_code not in languages:
        return jsonify(
            {'errors': [{'code': 400, 'title': 'unsupported language'}]}), 400
    session[current_app.config['I18N_SESSION_KEY']] = lang_code.lower()
    return jsonify({'lang': lang_code})


@blueprint.route('/<string:viewcode>/search/<recordType>')
@check_organisation_viewcode
def search(viewcode, recordType):
    """Search page ui."""
    return render_template(current_app.config.get('SEARCH_UI_SEARCH_TEMPLATE'),
                           viewcode=viewcode)


@blueprint.app_template_filter()
def nl2br(string):
    r"""Replace \n to <br>."""
    return string.replace("\n", "<br>")


def prepare_jsonschema(schema):
    """Json schema prep."""
    schema = copy.deepcopy(schema)
    if schema.get('$schema'):
        del schema['$schema']
    schema['required'].remove('pid')
    keys = current_app.config['RERO_ILS_BABEL_TRANSLATE_JSON_KEYS']
    return translate(schema, keys=keys)


def prepare_form_option(form_option):
    """Option prep."""
    form_option = copy.deepcopy(form_option)
    keys = current_app.config['RERO_ILS_BABEL_TRANSLATE_JSON_KEYS']
    return translate(form_option, keys=keys)


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
        data['schema'] = prepare_jsonschema(schema)
    except JSONSchemaNotFound:
        abort(404)

    # try:
    #     form = current_jsonschemas.get_schema(
    #         'form_{}/{}-v0.0.1.json'.format(document_type, doc_type))
    #     data['layout'] = prepare_form_option(form)
    # except JSONSchemaNotFound as error:
    #     raise(error)
    return jsonify(data)


@blueprint.route('/professional/', defaults={'path': ''})
@blueprint.route('/professional/<path:path>')
@can_access_professional_view
def professional(path):
    """Return professional view."""
    return render_template('rero_ils/professional.html')
