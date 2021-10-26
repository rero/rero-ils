# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
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

"""Acquisition Receipt line record extensions."""

from datetime import datetime

from invenio_records.extensions import RecordExtension


class AcquisitionReceiptLineCompleteDataExtension(RecordExtension):
    """Complete data about an acquisition receipt line."""

    def post_init(self, record, data, model=None, **kwargs):
        """Called after a record is initialized.

        If no receipt_date is given, use today's date as receipt_date.

        :param data: The dict passed to the record's constructor
        :param model: The model class used for initialization.
        """
        if not record.get('receipt_date'):
            record['receipt_date'] = datetime.now().strftime('%Y-%m-%d')
