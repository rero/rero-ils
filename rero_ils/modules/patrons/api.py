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

"""API for manipulating patrons."""

from functools import partial

from flask import current_app
from flask_login import current_user
from flask_security.confirmable import confirm_user
from flask_security.recoverable import send_reset_password_instructions
from invenio_accounts.ext import hash_password
from invenio_circulation.proxies import current_circulation
from invenio_search.api import RecordsSearch
from werkzeug.local import LocalProxy
from werkzeug.utils import cached_property

from .models import PatronIdentifier
from ..api import IlsRecord
from ..fetchers import id_fetcher
from ..libraries.api import Library
from ..minters import id_minter
from ..organisations.api import Organisation
from ..providers import Provider

_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)

current_patron = LocalProxy(lambda: Patron.get_patron_by_user(current_user))

# provider
PatronProvider = type(
    'PatronProvider',
    (Provider,),
    dict(identifier=PatronIdentifier, pid_type='ptrn')
)
# minter
patron_id_minter = partial(id_minter, provider=PatronProvider)
# fetcher
patron_id_fetcher = partial(id_fetcher, provider=PatronProvider)


class PatronsSearch(RecordsSearch):
    """PatronsSearch."""

    class Meta:
        """Search only on patrons index."""

        index = 'patrons'


class Patron(IlsRecord):
    """Define API for patrons mixing."""

    minter = patron_id_minter
    fetcher = patron_id_fetcher
    provider = PatronProvider
    available_roles = ['system_librarian', 'librarian', 'patron']

    @classmethod
    def create(cls, data, id_=None, delete_pid=False,
               dbcommit=False, reindex=False, **kwargs):
        """Patron record creation."""
        record = super(Patron, cls).create(
            data, id_, delete_pid, dbcommit, reindex, **kwargs)
        record._update_roles()
        return record

    def delete(self, force=False, delindex=False):
        """Delete record and persistent identifier."""
        self._remove_roles()
        super(Patron, self).delete(force, delindex)
        return self

    def update(self, data, dbcommit=False, reindex=False):
        """Update data for record."""
        super(Patron, self).update(data, dbcommit, reindex)
        self._update_roles()
        return self

    @cached_property
    def user(self):
        """Invenio user of a patron."""
        email = self.get('email')
        user = _datastore.find_user(email=email)
        if not user:
            password = hash_password(email)

            _datastore.create_user(email=email, password=password)
            _datastore.commit()
            # send password reset
            user = _datastore.find_user(email=email)
            send_reset_password_instructions(user)
            confirm_user(user)
        return user

    def _update_roles(self):
        """Update user roles."""
        db_roles = self.user.roles
        for role in self.available_roles:
            in_db = role in db_roles
            in_record = role in self.get('roles', [])
            if in_record and not in_db:
                self.add_role(role)
            if not in_record and in_db:
                self.remove_role(role)

    def _remove_roles(self):
        """Remove roles."""
        db_roles = self.user.roles
        for role in self.available_roles:
            if role in db_roles:
                self.remove_role(role)

    @classmethod
    def get_patron_by_user(cls, user):
        """Get patron by user."""
        if hasattr(user, 'email'):
            return cls.get_patron_by_email(email=user.email)

    @classmethod
    def get_patron_by_email(cls, email=None):
        """Get patron by email."""
        pid_value = cls.get_pid_by_email(email)
        if pid_value:
            return cls.get_record_by_pid(pid_value)
        else:
            return None

    @classmethod
    def get_pid_by_email(cls, email):
        """Get uuid pid by email."""
        result = PatronsSearch().filter(
            'term',
            email=email
        ).source(includes='pid').scan()
        try:
            return next(result).pid
        except StopIteration:
            return None

    @classmethod
    def get_librarian_pickup_location_pid(cls):
        """Returns pickup locations for a librarian."""
        if 'librarian' in current_patron['roles']:
            library = Library.get_record_by_pid(
                current_patron.replace_refs()['library']['pid']
            )
            return library.get_pickup_location_pid()
        return None

    @classmethod
    def get_patron_by_barcode(cls, barcode=None):
        """Get patron by barcode."""
        search = PatronsSearch()
        result = search.filter(
            'term',
            barcode=barcode
        ).source(includes='pid').scan()
        try:
            patron_pid = next(result).pid
            return super(Patron, cls).get_record_by_pid(patron_pid)
        except StopIteration:
            return None

    def add_role(self, role_name):
        """Add a given role to a user."""
        role = _datastore.find_role(role_name)
        _datastore.add_role_to_user(self.user, role)
        _datastore.commit()

    def remove_role(self, role_name):
        """Remove a given role from a user."""
        role = _datastore.find_role(role_name)
        _datastore.remove_role_from_user(self.user, role)
        _datastore.commit()

    @property
    def initial(self):
        """Return the initials of the patron first name."""
        initial = ''
        firsts = self['first_name'].split(' ')
        for first in firsts:
            initial += first[0]
        lasts = self['last_name'].split(' ')
        for last in lasts:
            if last[0].isupper():
                initial += last[0]

        return initial

    @property
    def patron_type_pid(self):
        """Shortcut for patron type pid."""
        if self.get('patron_type'):
            patron_type_pid = self.replace_refs().get('patron_type').get('pid')
            return patron_type_pid
        return None

    def get_number_of_loans(self):
        """Get number of loans."""
        search = current_circulation.loan_search
        search = search.filter("term", patron_pid=self.pid)
        exclude_states = ['CANCELLED', 'ITEM_RETURNED']
        search = search.exclude("terms", state=exclude_states)
        results = search.source().count()
        return results

    def get_links_to_me(self):
        """Get number of links."""
        links = {}
        loans = self.get_number_of_loans()
        if loans:
            links['loans'] = loans
        return links

    def reasons_to_keep(self):
        """Reasons aside from record_links to keep a user.

        prevent users with role librarian to delete a system_librarian.
        """
        others = {}
        if current_patron:
            if not current_patron.is_system_librarian and \
               self.is_system_librarian:
                others['permission denied'] = True
        return others

    def reasons_not_to_delete(self):
        """Get reasons not to delete policy."""
        cannot_delete = {}
        others = self.reasons_to_keep()
        links = self.get_links_to_me()
        if others:
            cannot_delete['others'] = others
        if links:
            cannot_delete['links'] = links
        return cannot_delete

    def get_organisation(self):
        """Return organisation."""
        from ..patron_types.api import PatronType

        patron = self.replace_refs()
        if self.get('library'):
            lib = Library.get_record_by_pid(patron['library']['pid'])
            return Organisation.get_record_by_pid(
                lib.replace_refs()['organisation']['pid'])
        if self.get('patron_type'):
            ptty = PatronType.get_record_by_pid(patron['patron_type']['pid'])
            return Organisation.get_record_by_pid(
                ptty.replace_refs()['organisation']['pid'])
        return None

    @property
    def library_pid(self):
        """Shortcut for patron library pid."""
        if self.get('library'):
            library_pid = self.replace_refs().get('library').get('pid')
            return library_pid
        return None

    @property
    def is_librarian(self):
        """Shortcut to check if user has librarian role."""
        if self.is_system_librarian or 'librarian' in self.get('roles'):
            return True
        return False

    @property
    def is_system_librarian(self):
        """Shortcut to check if user has system_librarian role."""
        if 'system_librarian' in self.get('roles'):
            return True
        return False

    @property
    def organisation_pid(self):
        """Get organisation pid for patron."""
        from ..patron_types.api import PatronType

        if self.library_pid:
            library = Library.get_record_by_pid(self.library_pid)
            return library.organisation_pid

        if self.patron_type_pid:
            patron_type = PatronType.get_record_by_pid(self.patron_type_pid)
            return patron_type.organisation_pid
        return None
