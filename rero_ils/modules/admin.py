# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2018 RERO.
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
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Admin views and actions."""

from flask_admin import BaseView, expose
from invenio_admin.permissions import \
    admin_permission_factory as default_admin_permission_factory

from ..permissions import can_edit


class ILSManager(BaseView):
    """Flask-Admin Ils view."""

    @expose('/')
    @expose('/<path:path>')
    def index(self, path=None):
        """Angular Circulation view."""
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
    'kwargs': dict(name='Circulation',
                   endpoint='circulation',
                   menu_icon_type='fa',
                   menu_icon_value='fa-barcode')
}

my_library = {
    'view_class': ILSManager,
    'kwargs': dict(
        name='My Library',
        endpoint='mylibrary',
        menu_icon_type='fa',
        menu_icon_value='fa-university'
    )
}

library = {
    'view_class': LibraryManager,
    'kwargs': dict(
        name='Libraries',
        endpoint='libraries',
        menu_icon_type='fa',
        menu_icon_value='fa-barcode'
    )
}

item_types = {
    'view_class': ILSManager,
    'kwargs': dict(
        name='Item Types',
        category='Resources',
        endpoint='records/item_types',
        menu_icon_type='fa',
        menu_icon_value='fa-barcode'
    )
}

patron_types = {
    'view_class': ILSManager,
    'kwargs': dict(
        name='Patron Types',
        category='Resources',
        endpoint='records/patron_types',
        menu_icon_type='fa',
        menu_icon_value='fa-barcode'
    )
}

circ_policies = {
    'view_class': ILSManager,
    'kwargs': dict(
        name='Circulation Policies',
        category='Resources',
        endpoint='records/circ_policies',
        menu_icon_type='fa',
        menu_icon_value='fa-barcode'
    )
}

patrons = {
    'view_class': ILSManager,
    'kwargs': dict(
        name='Patrons',
        category='Resources',
        endpoint='records/patrons',
        menu_icon_type='fa',
        menu_icon_value='fa-barcode'
    )
}

persons = {
    'view_class': ILSManager,
    'kwargs': dict(
        name='Persons',
        category='Resources',
        endpoint='records/persons',
        menu_icon_type='fa',
        menu_icon_value='fa-barcode'
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
        name='Libraries',
        category='Resources',
        endpoint='records/libraries',
        menu_icon_type='fa',
        menu_icon_value='fa-barcode'
    )
}

documents = {
    'view_class': ILSManager,
    'kwargs': dict(
        name='Documents',
        category='Resources',
        endpoint='records/documents',
        menu_icon_type='fa',
        menu_icon_value='fa-barcode'
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
