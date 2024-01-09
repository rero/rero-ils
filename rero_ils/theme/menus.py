# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
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

"""Application Menus."""

from functools import partial

from flask import current_app, request, session
from flask_babel import lazy_gettext as _
from flask_login import current_user
from flask_menu import current_menu
from invenio_i18n.ext import current_i18n

from rero_ils.modules.patrons.api import current_librarian, current_patrons

from ..permissions import admin_permission, librarian_permission


# -------------- Utilities -----------------
class TextWithIcon():
    """Create a dynamic text menu item property to support translations."""

    def __init__(self, icon, text):
        """Constructor."""
        self.icon = icon
        self.text = text

    def __html__(self):
        """Jinja call this method during the rendering."""
        return f'{self.icon} {_(self.text)}'


class UserName():
    """Create a dynamic menu text user name property."""

    def __html__(self):
        """Jinja call this method during the rendering."""
        account = session.get(
            'user_name', _('My Account')
        ) if current_user.is_authenticated else _('My Account')
        if len(account) > 30:
            account = f'{account[0:30]}...'
        # TODO: fix the unclosed span tag
        return f'''
<span class="btn btn-sm btn-success">
    <i class="fa fa-user"></i>
    <span>{account}</span>
'''


class CurrentLanguage():
    """Create a dynamic menu property with the current language."""

    def __html__(self):
        """Jinja call this method during the rendering."""
        ui_language = f'ui_language_{current_i18n.language}'
        return f'<i class="fa fa-language"></i> {_(ui_language)}'


def rero_register(
    item,
    endpoint=None,
    text=None,
    order=0,
    external_url=None,
    endpoint_arguments_constructor=None,
    dynamic_list_constructor=None,
    active_when=None,
    visible_when=None,
    expected_args=None,
        **kwargs):
    """Take care each element in kwargs doesn't already exists in item."""
    # Check which option in kwargs already exists in `item`.
    to_delete = []
    for option in kwargs.keys():
        if hasattr(item, option):
            to_delete.append(option)
    # Delete all existing options in kwargs
    for element in to_delete:
        del kwargs[element]

    return item.register(
        endpoint,
        text,
        order,
        external_url,
        endpoint_arguments_constructor,
        dynamic_list_constructor,
        active_when,
        visible_when,
        expected_args,
        **kwargs)


# ---------- Menu definitions ---------------
def init_menu_tools():
    """Create the header tool menu."""
    item = current_menu.submenu('main.tool')
    rero_register(
        item,
        endpoint=None,
        text=TextWithIcon(
            icon='<i class="fa fa-wrench"></i>',
            text='Tools'
        ),
        order=0,
        id='tools-menu'
    )

    item = current_menu.submenu('main.tool.ill_request')
    rero_register(
        item,
        endpoint='ill_requests.ill_request_form',
        endpoint_arguments_constructor=lambda: dict(
            viewcode=request.view_args.get(
                'viewcode', current_app.config.get(
                    'RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'))),
        visible_when=lambda: bool(current_patrons),
        text=TextWithIcon(
            icon='<i class="fa fa-shopping-basket"></i>',
            text='Interlibrary loan request'
        ),
        order=10,
        id='ill-request-menu'
    )

    item = current_menu.submenu('main.tool.stats_billing')
    rero_register(
        item,
        endpoint='stats.stats_billing',
        visible_when=lambda: admin_permission.require().can(),
        text=TextWithIcon(
            icon='<i class="fa fa-money"></i>',
            text='Statistics billing'
        ),
        order=20,
        id='stats-menu-billing'
    )

    item = current_menu.submenu('main.tool.stats_librarian')
    rero_register(
        item,
        endpoint='stats.stats_librarian',
        visible_when=lambda: librarian_permission.require().can(),
        text=TextWithIcon(
            icon='<i class="fa fa-bar-chart"></i>',
            text='Statistics'
        ),
        order=20,
        id='stats-menu-librarian'
    )

    item = current_menu.submenu('main.tool.collections')
    rero_register(
        item,
        endpoint='rero_ils.search',
        endpoint_arguments_constructor=lambda: dict(
            viewcode=request.view_args.get(
                'viewcode', current_app.config.get(
                    'RERO_ILS_SEARCH_GLOBAL_VIEW_CODE')),
            recordType='collections'
        ),
        visible_when=lambda: current_app.config.get(
            'RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'
            ) != request.view_args.get(
                'viewcode', current_app.config.get(
                    'RERO_ILS_SEARCH_GLOBAL_VIEW_CODE')),
        text=TextWithIcon(
            icon='<i class="fa fa-graduation-cap"></i>',
            text='Exhibition/course'
        ),
        order=2,
        id='collections-menu'
    )

    item = current_menu.submenu('main.tool.help')
    rero_register(
        item,
        endpoint='wiki.page',
        endpoint_arguments_constructor=lambda: {'url': 'public'},
        text=TextWithIcon(
            icon='<i class="fa fa-info"></i>',
            text='Help'
        ),
        order=100,
        id='help-menu'
    )


def init_menu_lang():
    """Create the header language menu."""
    item = current_menu.submenu('main.menu')
    # Bug: when you reload the page with register(**kwargs), it failed
    # We so check that 'id' already exists. If yes, do not create again
    # the item.

    rero_register(
        item,
        endpoint=None,
        text=CurrentLanguage(),
        order=0,
        id='language-menu'
    )

    order = 10

    def return_language(lang):
        return dict(lang_code=lang)

    def hide_language(lang):
        return current_i18n.language != lang

    for language_item in current_i18n.get_locales():
        item = current_menu.submenu(f'main.menu.lang_{language_item.language}')
        ui_language = f'ui_language_{language_item.language}'
        rero_register(
            item,
            endpoint='invenio_i18n.set_lang',
            endpoint_arguments_constructor=partial(
                return_language, language_item.language),
            text=TextWithIcon(
                icon='<i class="fa fa-language"></i>',
                text=ui_language
            ),
            visible_when=partial(hide_language, language_item.language),
            order=order,
            id=f'language-menu-{language_item.language}'
        )
        order += 1


def init_menu_profile():
    """Create the profile header menu."""

    def is_not_read_only():
        """Hide element menu if the flag is ready only."""
        return not current_app.config.get(
            'RERO_PUBLIC_USERPROFILES_READONLY', False) and \
            current_user.is_authenticated

    item = current_menu.submenu('main.profile')
    rero_register(
        item,
        endpoint=None,
        text=UserName(),
        order=1,
        id='my-account-menu',
        cssClass='py-1'
    )

    item = current_menu.submenu('main.profile.login')
    rero_register(
        item,
        endpoint='security.login',
        endpoint_arguments_constructor=lambda: dict(
            next=request.full_path
        ),
        visible_when=lambda: not current_user.is_authenticated,
        text=TextWithIcon(
            icon='<i class="fa fa-sign-in"></i>',
            text='Login'
        ),
        order=1,
        id='login-menu',
    )

    item = current_menu.submenu('main.profile.professional')
    rero_register(
        item,
        endpoint='rero_ils.professional',
        visible_when=lambda: current_librarian,
        text=TextWithIcon(
            icon='<i class="fa fa-briefcase"></i>',
            text='Professional interface'
        ),
        order=1,
        id='professional-interface-menu',
    )

    item = current_menu.submenu('main.profile.logout')
    viewcode = request.view_args.get(
        'viewcode',
        current_app.config.get('RERO_ILS_SEARCH_GLOBAL_VIEW_CODE')
    )
    rero_register(
        item,
        endpoint='security.logout',
        endpoint_arguments_constructor=lambda: dict(next=f'/{viewcode}'),
        visible_when=lambda: current_user.is_authenticated,
        text=TextWithIcon(
            icon='<i class="fa fa-sign-out"></i>',
            text='Logout'
        ),
        order=2,
        id='logout-menu',
    )

    item = current_menu.submenu('main.profile.profile')
    profile_endpoint = 'patrons.profile'
    rero_register(
        item,
        endpoint=profile_endpoint,
        endpoint_arguments_constructor=lambda: dict(
            viewcode=request.view_args.get(
                'viewcode', current_app.config.get(
                    'RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'))),
        visible_when=lambda: len(current_patrons) > 0,
        text=TextWithIcon(
            icon='<i class="fa fa-book"></i>',
            text='My Account'
        ),
        order=1,
        id='profile-menu',
    )

    item = current_menu.submenu('main.profile.edit_profile')
    rero_register(
        item,
        endpoint='users.profile',
        endpoint_arguments_constructor=lambda: dict(
            viewcode=request.view_args.get(
                'viewcode', current_app.config.get(
                    'RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'))),
        visible_when=lambda: is_not_read_only(),
        text=TextWithIcon(
            icon='<i class="fa fa-user"></i>',
            text='Edit my profile'
        ),
        order=1,
        id='profile-menu',
    )

    item = current_menu.submenu('main.profile.change_password')
    rero_register(
        item,
        endpoint='users.password',
        endpoint_arguments_constructor=lambda: dict(
            viewcode=request.view_args.get(
                'viewcode', current_app.config.get(
                    'RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'))),
        visible_when=lambda: is_not_read_only(),
        text=TextWithIcon(
            icon='<i class="fa fa-lock"></i>',
            text='Change password'
        ),
        order=1,
        id='profile-menu',
    )

    # Endpoint for:
    # Application: invenio_oauth2server_settings.index
    # Security: invenio_accounts.security
    item = current_menu.submenu('main.profile.signup')
    rero_register(
        item,
        endpoint='security.register',
        visible_when=lambda: not current_app.config.get(
            'RERO_PUBLIC_USERPROFILES_READONLY', False) and
        not current_user.is_authenticated,
        text=TextWithIcon(
            icon='<i class="fa fa-user-plus"></i>',
            text='Sign Up'
        ),
        order=2,
        id='signup-menu',
    )
