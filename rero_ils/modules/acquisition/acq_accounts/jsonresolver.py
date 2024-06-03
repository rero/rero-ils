# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
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

"""AcqAccount resolver."""

import jsonresolver
from flask import current_app
from invenio_pidstore.models import PersistentIdentifier, PIDStatus


@jsonresolver.route("/api/acq_accounts/<pid>", host="bib.rero.ch")
def acq_account_resolver(pid):
    """Resolver for acq_account record."""
    persistent_id = PersistentIdentifier.get("acac", pid)
    if persistent_id.status == PIDStatus.REGISTERED:
        return dict(pid=persistent_id.pid_value)
    current_app.logger.error(
        f"Doc resolver error: /api/acq_accounts/{pid} {persistent_id}"
    )
    raise Exception("unable to resolve")
