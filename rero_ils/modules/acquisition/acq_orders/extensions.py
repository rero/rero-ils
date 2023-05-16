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

"""Acquisition Order record extensions."""

from invenio_records.extensions import RecordExtension

from rero_ils.modules.utils import extracted_data_from_ref


class AcquisitionOrderExtension(RecordExtension):
    """Defines the methods needed by an extension."""

    def pre_dump(self, record, dumper=None):
        """Called before a record is dumped.

        :param record: the record metadata.
        :param dumper: the record dumper.
        """
        if record.order_date:
            record['order_date'] = record.order_date
        record['account_statement'] = \
            record.get_account_statement()
        record['status'] = record.status

    def pre_load(self, data, loader=None):
        """Called before a record is loaded.

        :param data: the data to load.
        :param loader: the record loader.
        """
        data.pop('account_statement', None)
        data.pop('status', None)
        data.pop('order_date', None)

    def pre_delete(self, record, force=False):
        """Called before a record is deleted.

        :param record: the record metadata.
        :param force: force the deleting of the record.
        """
        # For pending orders, we are allowed to delete all of its
        # line orders without further checks.
        # there is no need to check if it is a pending order or not because
        # the can_delete is already execute in the method self.delete
        for line in record.get_order_lines():
            line.delete(force=force, delindex=True)


class AcquisitionOrderCompleteDataExtension(RecordExtension):
    """Complete data about an acquisition order."""

    @staticmethod
    def populate_currency(record):
        """Add vendor currency to order data."""
        vendor = record.get('vendor')
        if vendor:
            vendor = extracted_data_from_ref(vendor, data='record')
            record['currency'] = vendor.get('currency')

    # TODO : This hook doesn't work as expected now.
    #   The record is well updated with currency key, but this key isn't store
    #   into the database json blob record
    # def pre_create(self, record):
    #     """Called Called before a record is created.
    #
    #     :param record: the record metadata.
    #     """
    #     # The vendor currency could change over time, but when an order is
    #     # created the currency used couldn't change if we update the vendor
    #     # currency. So we need to store the currency into the order instead
    #     # of just use a vendor reference.
    #     AcquisitionOrderCompleteDataExtension.populate_currency(record)

    def post_create(self, record):
        """Called after the record is created.

        If no reference is provided, use the PID as auto incremented sequence
        to use as reference order.

        :param record: the record metadata.
        """
        if not record.get('reference'):
            record['reference'] = f'ORDER-{record.pid}'
            record.update(record, dbcommit=True, reindex=True)

    def pre_commit(self, record):
        """Called before a record is committed.

        :param record: the record metadata.
        """
        # If we update the vendor, we need to change the order currency.
        original_record = record.__class__.get_record_by_pid(record.pid)
        if original_record and original_record.vendor_pid != record.vendor_pid:
            AcquisitionOrderCompleteDataExtension.populate_currency(record)
