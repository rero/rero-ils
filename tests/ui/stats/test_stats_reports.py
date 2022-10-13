# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2023 RERO
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

"""Tests REST API create statistics reports."""
from datetime import datetime

import pytest
from webargs import ValidationError

from rero_ils.modules.stats.api import StatsReport


def test_statistics_reports_number_of_documents(data,
                                                stats_cfg_martigny,
                                                stats_cfg_sion,
                                                stats_cfg_martigny_3,
                                                stats_cfg_martigny_4,
                                                item_lib_martigny,
                                                item_lib_martigny_bourg,
                                                item2_lib_martigny,
                                                item4_lib_martigny):
    """Test reports for number of documents.

    stats_cfg_martigny:
        indicator: number_of_documents
        distributions: 'time_range_month' and 'library'
        org: org1
        filter: none
        period: none
    stats_cfg_sion:
        indicator: number_of_documents
        distributions: 'time_range_month' and 'library'
        org: org2
        filter: none
        period: none
    stats_cfg_martigny_3:
        indicator: number_of_documents
        distributions: none
        org: org1
        filter: none
        period: none
    stats_cfg_martigny_4:
        indicator: number_of_documents
        distributions: 'library'
        org: org1
        filter: none
        period: none
    """
    for stats_cfg in [stats_cfg_martigny,
                      stats_cfg_sion,
                      stats_cfg_martigny_3,
                      stats_cfg_martigny_4]:

        report = StatsReport().create(stats_cfg.get('pid'),
                                      dbcommit=True, reindex=True)
        assert report['type'] == 'report'
        assert report['config'] == data.get(stats_cfg.pid)

        today = datetime.now()
        today_month = '%02d' % today.month
        date = f'{today.year}-{today_month}'

        if stats_cfg.pid == 'stats_cfg1':
            assert report['values'] == [
                                {
                                    'org_pid': 'org1',
                                    'library_pid': 'lib1',
                                    'library_name':
                                        'Library of Martigny-ville',
                                    'time_range_month': date,
                                    'number_of_documents': 1
                                },
                                {
                                    'org_pid': 'org1',
                                    'library_pid': 'lib7',
                                    'library_name':
                                        'Library of Martigny-bourg',
                                    'time_range_month': date,
                                    'number_of_documents': 1
                                }
                                ]
        elif stats_cfg.pid == 'stats_cfg2':
            assert report['values'] == [{'org_pid': 'org2',
                                         'number_of_documents': 0}]
        elif stats_cfg.pid == 'stats_cfg3':
            assert report['values'] == [{'org_pid': 'org1',
                                         'number_of_documents': 1}]
        elif stats_cfg.pid == 'stats_cfg4':
            assert report['values'] == [
                                    {
                                        'org_pid': 'org1',
                                        'library_pid': 'lib1',
                                        'library_name':
                                            'Library of Martigny-ville',
                                        'number_of_documents': 1
                                    },
                                    {
                                        'org_pid': 'org1',
                                        'library_pid': 'lib7',
                                        'library_name':
                                            'Library of Martigny-bourg',
                                        'number_of_documents': 1
                                    }
                                    ]


def test_statistics_reports_number_of_serial_holdings(
        data,
        stats_cfg_martigny_9,
        holding_lib_martigny,
        holding_lib_martigny_w_patterns,
        holding_lib_sion
        ):
    """Test reports for number of serial holdings.

    stats_cfg_martigny_9:
        indicator: number_of_serial_holdings
        distributions: 'library'
        org: org1
        filter: none
        period: none
    """
    report = StatsReport().create(stats_cfg_martigny_9.get('pid'),
                                  dbcommit=True, reindex=True)
    assert report['type'] == 'report'
    assert report['config'] == data.get(stats_cfg_martigny_9.pid)

    if stats_cfg_martigny_9.pid == 'stats_cfg9':
        assert report['values'] == [
            {
                'org_pid': 'org1',
                'library_pid': 'lib1',
                'library_name':
                    'Library of Martigny-ville',
                'number_of_serial_holdings': 1
            }
            ]


def test_statistics_reports_number_of_items(data,
                                            stats_cfg_martigny_5,
                                            stats_cfg_martigny_6,
                                            item_lib_martigny,
                                            item_lib_martigny_bourg,
                                            item2_lib_martigny,
                                            item4_lib_martigny):
    """Test reports for number of items.

    stats_cfg_martigny_5:
        indicator: number_of_items
        distributions: 'library' and 'location'
        org: org1
        filter: none
        period: none
    stats_cfg_martigny_6:
        indicator: number_of_items
        distributions: 'time_range_month' and 'time_range_year'
        org: org1
        filter: none
        period: none
    """
    report = StatsReport().create(stats_cfg_martigny_5.get('pid'),
                                  dbcommit=True, reindex=True)

    loc1 = 'MARTIGNY-PUBLIC: Martigny Library Public Space'
    loc2 = 'MARTIGNY-BOURG-PUBLIC: Martigny Bourg Library Public Space'
    if stats_cfg_martigny_5.pid == 'stats_cfg5':
        assert report['type'] == 'report'
        assert report['config'] == data.get(stats_cfg_martigny_5.pid)
        assert report['values'] == [
            {
                'org_pid': 'org1',
                'library_pid': 'lib1',
                'library_name':
                    'Library of Martigny-ville',
                'location': loc1,
                'number_of_items': 3
            },
            {
                'org_pid': 'org1',
                'library_pid': 'lib7',
                'library_name': 'Library of Martigny-bourg',
                'location': loc2,
                'number_of_items': 1
            }
            ]

    msg = "Distributions should not be "\
          "both time_range_month and time_range_year"
    with pytest.raises(ValidationError, match=msg):
        StatsReport().create(stats_cfg_martigny_6.get('pid'),
                             dbcommit=True, reindex=True)


def test_statistics_reports_number_of_ill_requests(
        data,
        stats_cfg_martigny_10,
        ill_request_martigny,
        ill_request_martigny3,
        ill_request_sion):
    """Test reports for number of ill requests.

    stats_cfg_martigny_10:
        indicator: number_of_ill_requests
        distributions: 'library'
        org: org1
        filter: none
        period: none
    """
    report = StatsReport().create(stats_cfg_martigny_10.get('pid'),
                                  dbcommit=True, reindex=True)
    assert report['type'] == 'report'
    assert report['config'] == data.get(stats_cfg_martigny_10.pid)

    if stats_cfg_martigny_10.pid == 'stats_cfg10':
        assert report['values'] == [
            {
                'org_pid': 'org1',
                'library_pid': 'lib1',
                'library_name':
                    'Library of Martigny-ville',
                'number_of_ill_requests': 2
            }
            ]
