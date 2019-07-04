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

"""Admin views and actions."""

from flask_admin import BaseView, expose
from flask_babelex import gettext as _
from invenio_admin.permissions import \
    admin_permission_factory as default_admin_permission_factory

from ..permissions import can_edit


class ILSManager(BaseView):
    """Flask-Admin Ils view."""

    @expose('/')
    @expose('/<path:path>')
    def index(self, path=None):
        """Angular professional view."""
        return self.render('rero_ils/page_admin.html')

    def is_accessible(self):
        """Access control."""
        return (can_edit() or default_admin_permission_factory(self).can())


class LibraryManager(BaseView):
    """Flask-Admin Library view."""

    @expose('/')
    @expose('/<path:path>')
    def index(self, path=None):
        """Index."""
        return self.render('rero_ils/page_admin.html')

    def is_visible(self):
        """Visible control."""
        return False

    def is_accessible(self):
        """Access control."""
        return (can_edit() or default_admin_permission_factory(self).can())


circulation = {
    'view_class': ILSManager,
    'kwargs': dict(name=_('Circulation'),
                   category=_('User Services'),
                   endpoint='circulation',
                   menu_icon_type='fa',
                   menu_icon_value='fa-exchange')
}

my_library = {
    'view_class': ILSManager,
    'kwargs': dict(
        name=_('My Library'),
        category=_('Admin & Monitoring'),
        endpoint='mylibrary',
        menu_icon_type='fa',
        menu_icon_value='fa-university'
    )
}

library = {
    'view_class': LibraryManager,
    'kwargs': dict(
        name=_('Libraries'),
        category=_('Admin & Monitoring'),
        endpoint='libraries',
        menu_icon_type='fa',
        menu_icon_value='fa-university'
    )
}

item_types = {
    'view_class': ILSManager,
    'kwargs': dict(
        name=_('Item Types'),
        category=_('Admin & Monitoring'),
        endpoint='records/item_types',
        menu_icon_type='fa',
        menu_icon_value='fa-file-o'
    )
}

patron_types = {
    'view_class': ILSManager,
    'kwargs': dict(
        name=_('Patron Types'),
        category=_('Admin & Monitoring'),
        endpoint='records/patron_types',
        menu_icon_type='fa',
        menu_icon_value='fa-users'
    )
}

circ_policies = {
    'view_class': ILSManager,
    'kwargs': dict(
        name=_('Circulation Policies'),
        category=_('Admin & Monitoring'),
        endpoint='records/circ_policies',
        menu_icon_type='fa',
        menu_icon_value='fa-exchange'
    )
}

patrons = {
    'view_class': ILSManager,
    'kwargs': dict(
        name=_('Patrons'),
        category=_('User Services'),
        endpoint='records/patrons',
        menu_icon_type='fa',
        menu_icon_value='fa-users'
    )
}

persons = {
    'view_class': ILSManager,
    'kwargs': dict(
        name=_('Persons'),
        category=_('Catalogue'),
        endpoint='records/persons',
        menu_icon_type='fa',
        menu_icon_value='fa-user'
    )
}

locations = {
    'view_class': LibraryManager,
    'kwargs': dict(
        name='Locations',
        category='Resources',
        endpoint='records/locations',
        menu_icon_type='fa',
        menu_icon_value='fa-barcode'
    )
}

libraries = {
    'view_class': ILSManager,
    'kwargs': dict(
        name=_('Libraries'),
        category=_('Admin & Monitoring'),
        endpoint='records/libraries',
        menu_icon_type='fa',
        menu_icon_value='fa-university'
    )
}

documents = {
    'view_class': ILSManager,
    'kwargs': dict(
        name=_('Documents'),
        category=_('Catalogue'),
        endpoint='records/documents',
        menu_icon_type='fa',
        menu_icon_value='fa-file-o'
    )
}

documents_create = {
    'view_class': ILSManager,
    'kwargs': dict(
        name=_('Create a bibliographic record'),
        category=_('Catalogue'),
        endpoint='records/documents/new',
        menu_icon_type='fa',
        menu_icon_value='fa-file-o'
    )
}

items = {
    'view_class': LibraryManager,
    'kwargs': dict(
        name='Items',
        category='Resources',
        endpoint='records/items',
        menu_icon_type='fa',
        menu_icon_value='fa-barcode'
    )
}
