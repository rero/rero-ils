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

"""RERO ILS common record extensions."""


from invenio_records.extensions import RecordExtension


class AddMEFPidExtension(RecordExtension):
    """Adds the MEF pid for contributions."""

    def add_mef_pid(self, record):
        """Injects the MEF pid in the contribution.

        :params record: a document record.
        """
        from rero_ils.modules.contributions.api import Contribution
        for contribution in record.get('contribution', []):
            if contrib_ref := contribution.get('agent', {}).get('$ref'):
                cont, _ = Contribution.get_record_by_ref(
                    contrib_ref)
                if cont:
                    # inject mef pid
                    contribution['agent']['pid'] = cont['pid']

    def post_init(self, record, data, model=None, **kwargs):
        """Called after a record is initialized."""
        self.add_mef_pid(record)

    def pre_commit(self, record):
        """Called before a record is committed."""
        self.add_mef_pid(record)
