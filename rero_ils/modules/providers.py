# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Identifier provider."""

from invenio_db import db
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PIDStatus
from invenio_pidstore.providers.base import BaseProvider
from sqlalchemy import text


def set_sequence(identifier):
    """Internal function to reset sequence to specific value.

    Note: this function is for PostgreSQL compatibility.

    :param identifier: The identifier to be set.
    """
    if db.engine.dialect.name == "postgresql":  # pragma: no cover
        db.session.execute(
            text(f"SELECT setval(pg_get_serial_sequence('{identifier.__tablename__}', 'recid'), :newval)"),
            {"newval": identifier.max()},
        )


def append_fixtures_new_identifiers(identifier, pids):
    """Insert pids into the indentifier table and update its sequence."""
    idx = 0
    error = ""
    try:
        with db.session.begin_nested():
            for idx, pid in enumerate(pids, 1):
                db.session.add(identifier(recid=pid))
            try:
                set_sequence(identifier)
            except Exception as err:
                error = err
    except Exception as err:
        error = f"{error} {err}"
    return idx, error


class Provider(BaseProvider):
    """Identifier provider.

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
    provide any additional features besides creation of ids.
    """

    @classmethod
    def create(cls, object_type=None, object_uuid=None, **kwargs):
        """Create a new identifier."""
        pid_value = kwargs.get("pid_value")
        if not pid_value:
            kwargs["pid_value"] = str(cls.identifier.next())
        # TODO: to insert pid to the identifer table, enable if needed

        try:
            return cls.get(kwargs["pid_value"], cls.pid_type)
        except PIDDoesNotExistError:
            kwargs.setdefault("status", cls.default_status)
            if object_type and object_uuid:
                kwargs["status"] = PIDStatus.REGISTERED
            return super().create(object_type=object_type, object_uuid=object_uuid, **kwargs)
