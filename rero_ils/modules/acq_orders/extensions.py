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

"""Acquisition Order record extensions."""

from invenio_records.extensions import RecordExtension


class TotalAmountExtension(RecordExtension):
    """Update the total amount by summing the order lines."""

    def pre_dump(self, record, dumper=None):
        """Called before a record is dumped.

        :param record: the record metadata.
        :param dumper: the record dumper.
        """
        record['total_amount'] = record.get_order_total_amount()

    def pre_load(self, data, loader=None):
        """Called before a record is loaded.

        :param record: the record metadata.
        :param loader: the record loader.
        """
        data.pop('total_amount', None)
