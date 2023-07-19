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

"""ILL request record extensions."""


import contextlib

from rero_ils.modules.operation_logs.extensions import \
    OperationLogObserverExtension


class IllRequestOperationLogObserverExtension(OperationLogObserverExtension):
    """Observer on ``ILLRequest`` to build operation log when it changes."""

    def get_additional_informations(self, record):
        """Additional information about Ill request operation log.

        :param record: the observed record.
        :return a dict with additional informations.
        """
        data = {'ill_request': {
            'status': record.get('status')
        }}
        # if the location or library doesn't exist anymore,
        # we do not inject the library pid in the operation log
        with contextlib.suppress(Exception):
            data['ill_request']['library_pid'] = record.get_library().pid
        if loan_status := record.get('loan_status'):
            data['ill_request']['loan_status'] = loan_status
        return data
