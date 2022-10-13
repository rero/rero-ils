# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""Test monitoring."""

from click.testing import CliRunner
from utils import flush_index

from rero_ils.modules.documents.api import Document, DocumentsSearch
from rero_ils.modules.monitoring.api import Monitoring
from rero_ils.modules.monitoring.cli import es_db_counts_cli, es_db_missing_cli
from rero_ils.modules.operation_logs.api import OperationLog


def test_monitoring(app, document_sion_items_data, script_info):
    """Test monitoring."""
    for index in OperationLog.get_indices():
        flush_index(index)
    cli_output = [
        'DB - ES    type      count                      index      count',
        '----------------------------------------------------------------',
        '      0    acac          0               acq_accounts          0',
        '      0    acin          0               acq_invoices          0',
        '      0    acol          0            acq_order_lines          0',
        '      0    acor          0                 acq_orders          0',
        '      0    acre          0               acq_receipts          0',
        '      0    acrl          0          acq_receipt_lines          0',
        '      0    budg          0                    budgets          0',
        '      0    cipo          0              circ_policies          0',
        '      0    coll          0                collections          0',
        '      0    cont          0              contributions          0',
        '      1     doc          1                  documents          0',
        '      0    hold          0                   holdings          0',
        '      0    illr          0               ill_requests          0',
        '      0    item          0                      items          0',
        '      0    itty          0                 item_types          0',
        '      0     lib          0                  libraries          0',
        '      0  loanid          0                      loans          0',
        '      0     loc          0                  locations          0',
        '      0    lofi          0               local_fields          0',
        '      0   notif          0              notifications          0',
        '      0    oplg          0             operation_logs          1',
        '      0     org          0              organisations          0',
        '      0    ptre          0  patron_transaction_events          0',
        '      0    ptrn          0                    patrons          0',
        '      0    pttr          0        patron_transactions          0',
        '      0    ptty          0               patron_types          0',
        '      0  stacfg          0                  stats_cfg          0',
        '      0    stat          0                      stats          0',
        '      0    tmpl          0                  templates          0',
        '      0    vndr          0                    vendors          0'
    ]

    mon = Monitoring(time_delta=0)
    assert mon.get_es_count('xxx') == 'No >>xxx<< in ES'
    assert mon.get_db_count('xxx') == 'No >>xxx<< in DB'
    doc = Document.create(
        data=document_sion_items_data,
        delete_pid=False,
        dbcommit=True,
        reindex=False
    )
    doc_pid = doc.pid
    assert mon.get_db_count('doc') == 1
    assert mon.get_es_count('documents') == 0
    assert mon.check() == {'doc': {'db_es': 1}}
    assert mon.missing('doc') == {'DB': [], 'ES': ['doc3'], 'ES duplicate': []}
    # not flushed by default
    flush_index('operation_logs')
    assert mon.info() == {
        'acac': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'acq_accounts'},
        'acin': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'acq_invoices'},
        'acol': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'acq_order_lines'},
        'acor': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'acq_orders'},
        'acre': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'acq_receipts'},
        'acrl': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'acq_receipt_lines'},
        'budg': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'budgets'},
        'cipo': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'circ_policies'},
        'coll': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'collections'},
        'cont': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'contributions'},
        'doc': {'db': 1, 'db-es': 1, 'es': 0, 'index': 'documents'},
        'hold': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'holdings'},
        'illr': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'ill_requests'},
        'item': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'items'},
        'itty': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'item_types'},
        'lib': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'libraries'},
        'loanid': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'loans'},
        'loc': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'locations'},
        'lofi': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'local_fields'},
        'notif': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'notifications'},
        'oplg': {'db': 0, 'db-es': 0, 'es': 1, 'index': 'operation_logs'},
        'org': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'organisations'},
        'ptre': {'db': 0, 'db-es': 0, 'es': 0,
                 'index': 'patron_transaction_events'},
        'ptrn': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'patrons'},
        'pttr': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'patron_transactions'},
        'ptty': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'patron_types'},
        'stacfg': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'stats_cfg'},
        'stat': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'stats'},
        'tmpl': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'templates'},
        'vndr': {'db': 0, 'db-es': 0, 'es': 0, 'index': 'vendors'}
    }
    assert mon.__str__().split('\n') == cli_output + ['']

    runner = CliRunner()
    res = runner.invoke(es_db_missing_cli, ['doc', '-d', 0], obj=script_info)
    assert res.output == f'ES missing doc: {doc.pid}\n'

    runner = CliRunner()
    res = runner.invoke(es_db_counts_cli, ['-m', '-d', 0], obj=script_info)
    assert res.output.split('\n') == cli_output + [
        f'ES missing doc: {doc.pid}',
        ''
    ]

    # we have to get the doc again because we lost the session after the use
    # of the CliRunner
    doc = Document.get_record_by_pid(doc_pid)
    doc.reindex()
    flush_index(DocumentsSearch.Meta.index)
    assert mon.get_es_count('documents') == 1
    assert mon.check() == {}
    assert mon.missing('doc') == {'DB': [], 'ES': [], 'ES duplicate': []}
    doc.delete(dbcommit=True)
    for index in OperationLog.get_indices():
        flush_index(index)
    assert mon.get_db_count('doc') == 0
    assert mon.get_es_count('documents') == 1
    assert mon.check() == {'doc': {'db_es': -1}}
    assert mon.missing('doc') == {'DB': ['doc3'], 'ES': [], 'ES duplicate': []}
