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

"""Identifier provider."""

from __future__ import absolute_import, print_function

import click
import sqlalchemy
from invenio_db import db
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_pidstore.providers.base import BaseProvider


def append_fixtures_new_identifiers(identifier, pids, pid_type):
    """Insert pids into the indentifier table and update its sequence."""
    idx = 0
    for idx, pid in enumerate(pids):
        db.session.add(identifier(recid=pid))
        if idx > 0 and idx % 100000 == 0:
            click.echo('DB commit append: {idx}'.format(idx=idx))
            db.session.commit()
    max_pid = PersistentIdentifier.query.filter_by(
        pid_type=pid_type
    ).order_by(sqlalchemy.desc(
        sqlalchemy.cast(PersistentIdentifier.pid_value, sqlalchemy.Integer)
    )).first().pid_value
    identifier._set_sequence(max_pid)
    click.echo('DB commit append: {idx}'.format(idx=idx))
    db.session.commit()


class Provider(BaseProvider):
    """CircPolicy identifier provider.

    'identifier' and 'pid_type' must be set as following example
    OrganisationProvider = type(
        'OrganisationProvider',
        (Provider,),
        dict(identifier=OrganisationIdentifier, pid_type='org')
    )
    """

    identifier = None

    pid_type = None
    """Type of persistent identifier."""

    pid_provider = None
    """Provider name.
    The provider name is not recorded in the PID since the provider does not
    provide any additional features besides creation of CircPolicy ids.
    """

    @classmethod
    def create(cls, object_type=None, object_uuid=None, **kwargs):
        """Create a new identifier."""
        pid_value = kwargs.get('pid_value')
        if not pid_value:
            kwargs['pid_value'] = str(cls.identifier.next())
        # TODO: to insert pid to the identifer table, enable if needed

        try:
            return cls.get(kwargs['pid_value'], cls.pid_type)
        except PIDDoesNotExistError:
            kwargs.setdefault('status', cls.default_status)
            if object_type and object_uuid:
                kwargs['status'] = PIDStatus.REGISTERED
            return super(Provider, cls).create(
                object_type=object_type, object_uuid=object_uuid, **kwargs
            )
