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

"""Test loan operation logs."""

import hashlib
from copy import deepcopy

from invenio_jsonschemas import current_jsonschemas
from utils import flush_index, login_user_for_view

from rero_ils.modules.loans.logs.api import LoanOperationLog


def test_loan_operation_log(client, operation_log_data,
                            loan_validated_martigny, librarian_martigny):
    """Test operation logs creation."""
    login_user_for_view(client, librarian_martigny)

    operation_log = LoanOperationLog.create(deepcopy(loan_validated_martigny),
                                            index_refresh='wait_for')
    operation_log['$schema'] = current_jsonschemas.path_to_url(
        LoanOperationLog._schema)
    operation_log.validate()
    log_data = LoanOperationLog.get_record(operation_log.id)
    assert log_data['operation'] == 'create'
    assert log_data['user_name'] == 'Pedronni, Marie'
    assert log_data['date'] == loan_validated_martigny['transaction_date']
    assert not log_data['loan']['override_flag']
    assert log_data['loan']['transaction_channel'] == 'system'
    assert log_data['loan']['transaction_user_name'] == 'Pedronni, Marie'
    assert log_data['loan'][
        'transaction_location_name'] == 'Martigny Library Public Space'
    assert log_data['loan'][
        'pickup_location_name'] == 'Martigny Library Public Space'
    assert log_data['loan']['patron'] == {
        'name': 'Roduit, Louis',
        'type': 'children',
        'age': 74,
        'postal_code': '1920',
        'gender': 'other',
        'local_codes': ['code1']
    }
    assert log_data['loan']['item'] == {
        'category': 'standard',
        'call_number': '001313',
        'document': {
            'title':
            'titre en chinois. Part Number, Part Number = Titolo cinese : '
            'sottotitolo in cinese',
            'type':
            'docsubtype_other_book'
        },
        'holding': {
            'pid': '1',
            'location_name': 'Martigny Library Public Space'
        }
    }

    # Test SIP2
    loan = deepcopy(loan_validated_martigny)
    loan['selfcheck_terminal_id'] = 'ABCDEF'
    operation_log = LoanOperationLog.create(loan, index_refresh='wait_for')
    operation_log['$schema'] = current_jsonschemas.path_to_url(
        LoanOperationLog._schema)
    operation_log.validate()
    log_data = LoanOperationLog.get_record(operation_log.id)
    assert log_data['loan']['transaction_channel'] == 'sip2'
    assert not log_data['loan'].get('transaction_user_name')


def test_anonymize_logs(item2_on_loan_martigny_patron_and_loan_on_loan):
    """Test anonymization for loan logs."""
    item, patron, loan = item2_on_loan_martigny_patron_and_loan_on_loan

    flush_index(LoanOperationLog.index_name)

    logs = LoanOperationLog.get_logs_by_record_pid(loan['pid'])
    assert len(logs) == 2
    for log in logs:
        assert log['record']['patron_pid'] == patron['pid']
        assert log['loan']['patron']['name'] == 'Roduit, Louis'

    loan.anonymize(loan)

    logs = LoanOperationLog.get_logs_by_record_pid(loan['pid'])
    assert len(logs) == 2
    for log in logs:
        log = log.to_dict()
        md5_hash = hashlib.md5(patron['pid'].encode()).hexdigest()
        assert log['record']['patron_pid'] == f'hash-{md5_hash}'
        assert not log['loan']['patron'].get('name')
