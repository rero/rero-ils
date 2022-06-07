# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
# Copyright (C) 2022 UCLouvain
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

"""Acquisition accounts serialization."""

from invenio_records_rest.serializers.response import record_responsify, \
    search_responsify

from rero_ils.modules.serializers import RecordSchemaJSONV1

from .csv import AcqAccountCSVSerializer
from .json import AcqAccountJSONSerializer
from ...response import search_responsify_file

"""JSON v1 serializer."""
_json = AcqAccountJSONSerializer(RecordSchemaJSONV1)

json_acq_account_search = search_responsify(_json, 'application/rero+json')
json_acq_account_response = record_responsify(_json, 'application/rero+json')


"""CSV serializer."""
_csv = AcqAccountCSVSerializer(
    csv_included_fields=[
        'account_pid', 'account_name', 'account_number',
        'account_allocated_amount', 'account_available_amount',
        'account_current_encumbrance', 'account_current_expenditure',
        'account_available_balance'
    ]
)

csv_acq_account_search = search_responsify_file(_csv, 'text/csv',  'csv')

__all__ = (
    'json_acq_account_search',
    'json_acq_account_response',
    'csv_acq_account_search'
)
