# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
# Copyright (C) 2021 UCLouvain
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

"""Document record extension to add the MEF pid in the database."""


from invenio_db import db
from invenio_records.extensions import RecordExtension


class AddMEFPidExtension(RecordExtension):
    """Adds the MEF pid for contributions and subjects."""

    def add_mef_pid(self, record):
        """Injects the MEF pid in the contribution.

        :params record: dict - a document record.
        """
        from rero_ils.modules.contributions.api import Contribution
        agents = record.get('subjects', []) +\
            record.get('subjects_imported', []) + \
            [contrib['entity'] for contrib in
                record.get('contribution', []) if 'entity' in contrib]
        for agent in agents:
            if contrib_ref := agent.get('$ref'):
                cont, _ = Contribution.get_record_by_ref(
                    contrib_ref)
                if cont:
                    # inject mef pid
                    agent['pid'] = cont['pid']

    def post_create(self, record):
        """Called after a record is initialized.

        :param record: dict - the record to be modified.
        """
        self.add_mef_pid(record)
        if record.model:
            with db.session.begin_nested():
                record.model.data = record
                db.session.add(record.model)

    def post_commit(self, record):
        """Called before a record is committed.

        :param record: dict - the record to be modified.
        """
        self.add_mef_pid(record)
        if record.model:
            with db.session.begin_nested():
                record.model.data = record
                # Note: session merge is not required as it is done by the
                #       record.commit
