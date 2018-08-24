# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 RERO.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
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

"""API for manipulating patrons."""

from flask import current_app
from invenio_search.api import RecordsSearch
from werkzeug.local import LocalProxy

from ..api import IlsRecord
from ..documents_items.api import DocumentsWithItems
from ..members.api import Member
from ..organisations_members.api import OrganisationWithMembers
from .fetchers import patron_id_fetcher
from .minters import patron_id_minter
from .providers import PatronProvider

_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


class BorrowedDocumentsSearch(RecordsSearch):
    """RecordsSearch for borrowed documents."""

    class Meta:
        """Search only on documents index."""

        index = 'documents'


class PatronsSearch(RecordsSearch):
    """RecordsSearch for borrowed documents."""

    class Meta:
        """Search only on patrons index."""

        index = 'patrons'


class Patron(IlsRecord):
    """Define API for patrons mixing."""

    minter = patron_id_minter
    fetcher = patron_id_fetcher
    provider = PatronProvider

    @classmethod
    def get_patron_by_user(cls, user):
        """Get patron by user."""
        return cls.get_patron_by_email(email=user.email)

    @classmethod
    def get_patron_by_email(cls, email=None):
        """Get patron by email."""
        uuid, pid_value = cls._get_uuid_pid_by_email(email)
        if uuid:
            return super(IlsRecord, cls).get_record(uuid)
        else:
            return None

    @classmethod
    def get_patron_by_barcode(cls, barcode=None):
        """Get patron by barcode."""
        search = PatronsSearch()
        result = search.filter(
            'term',
            barcode=barcode
        ).source(includes='pid').execute().to_dict()
        try:
            result = result['hits']['hits'][0]
            return super(IlsRecord, cls).get_record(result['_id'])
        except Exception:
            return None

    @classmethod
    def _get_uuid_pid_by_email(cls, email):
        """Get record by email."""
        search = PatronsSearch()
        result = search.filter(
            'term',
            email=email
        ).source(includes='pid').execute().to_dict()
        try:
            result = result['hits']['hits'][0]
            return result['_id'], result['_source']['pid']
        except Exception:
            return None, None

    @classmethod
    def delete_by_email(cls, email, deluser=False, delindex=False):
        """Delete user by email."""
        patron = cls.get_patron_by_email(email)
        if patron:
            patron.delete(delindex)
        datastore = LocalProxy(
            lambda: current_app.extensions['security'].datastore
        )
        user = datastore.find_user(email=email)
        if user:
            datastore.delete_user(user)
            datastore.commit()

    def get_borrowed_documents_pids(self):
        """Get pid values borrowed documents for given patron."""
        pids = [p.pid for p in BorrowedDocumentsSearch().filter(
            'term',
            itemslist___circulation__holdings__patron_barcode=self.get(
                'barcode'
            )
        ).source(includes=['id', 'pid']).scan()]
        return pids

    def get_borrowed_documents(self):
        """Get borrowed documents."""
        pids = self.get_borrowed_documents_pids()
        to_return = []
        for pid_value in pids:
            rec = DocumentsWithItems.get_record_by_pid(pid_value)
            to_return.append(rec)
        return to_return

    def add_role(self, role_name, reindex=False):
        """Add a given role to a user."""
        email = self.get('email')
        user = _datastore.find_user(email=email)
        role = _datastore.find_role(role_name)
        if _datastore.add_role_to_user(user, role):
            _datastore.commit()
            if reindex:
                self.reindex()
            return True
        return False

    def remove_role(self, role_name, reindex=False):
        """Remove a given role from a user."""
        email = self.get('email')
        user = _datastore.find_user(email=email)
        role = _datastore.find_role(role_name)
        if _datastore.remove_role_from_user(user, role):
            _datastore.commit()
            if reindex:
                self.reindex()
            return True
        return False

    def has_role(self, role_name):
        """Check if a user has a given role."""
        email = self.get('email')
        user = _datastore.find_user(email=email)
        # role = _datastore.find_role(role_name)
        return user.has_role(role_name)

    def dumps(self, **kwargs):
        """Return pure Python dictionary with record metadata."""
        data = super(IlsRecord, self).dumps(**kwargs)
        data['roles'] = self.role_names
        data['name'] = ', '.join((
            data.get('last_name', ''),
            data.get('first_name', '')
        ))
        return data

    @property
    def roles(self):
        """Return user roles."""
        email = self.get('email')
        user = _datastore.find_user(email=email)
        if user:
            return user.roles
        return []

    @property
    def role_names(self):
        """Return user role names."""
        return [v.name for v in self.roles]

    @property
    def organisation_pid(self):
        """Get Organisation pid of the logged in patron."""
        member_pid = self.get('member_pid')
        member = Member.get_record_by_pid(member_pid)
        organisation = OrganisationWithMembers.get_organisation_by_memberid(
            member.id
        )
        return organisation.pid
