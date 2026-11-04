# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Patron Query factories for REST API."""

from datetime import datetime

from invenio_search.engine import dsl


def patron_expiration_filter(expired=True):
    """Create a filter for the patron account expiration status.

    :param expired: if True, filter expired accounts (expiration_date <= now),
                    if False, filter active accounts (expiration_date > now OR no expiration_date).
    """

    def inner(values):
        if not values or values[0] != "true":
            return dsl.Q()
        if expired:
            return dsl.Q("range", patron__expiration_date={"lte": datetime.now()})
        return dsl.Q("range", patron__expiration_date={"gt": datetime.now()}) | ~dsl.Q(
            "exists", field="patron.expiration_date"
        )

    return inner
