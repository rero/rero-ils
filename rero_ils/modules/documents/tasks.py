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

"""Celery tasks to documents."""

from __future__ import absolute_import, print_function

from celery import shared_task

from .utils_mef import ReplaceMefIdentifiedByContribution, \
    ReplaceMefIdentifiedBySubjects
from ..contributions.api import Contribution


def get_contribution_or_create(ref_pid, ref_type, count_found, count_exists,
                               count_no_data, count_no_mef):
    """Get existing contribution or greate new one."""
    ref = f'{ref_type}/{ref_pid}'
    if ref_type and ref_pid:
        # Try to get existing contribution
        cont = Contribution.get_contribution(ref_type, ref_pid)
        if cont:
            # contribution exist allready
            count_exists.setdefault(ref, 0)
            count_exists[ref] += 1
        else:
            # contribution does not exist
            try:
                # try to get the contribution online
                data = Contribution._get_mef_data_by_type(ref_type, ref_pid)
                if (
                    data.get('idref') or
                    data.get('gnd') or
                    data.get('rero')
                ):
                    count_found.setdefault(
                        ref,
                        {'count': 0, 'mef': data.get('pid')}
                    )
                    count_found[ref]['count'] += 1
                    # delete mef $schema
                    data.pop('$schema', None)
                    # create local contribution
                    cont = Contribution.create(
                        data=data, dbcommit=True, reindex=True)
                else:
                    # online contribution has no IdREf, GND or RERO
                    count_no_data.setdefault(ref, 0)
                    count_no_data[ref] += 1
            except Exception:
                # no online contribution found
                count_no_mef.setdefault(ref, 0)
                count_no_mef[ref] += 1
    return cont, count_found, count_exists, count_no_data, count_no_mef


@shared_task(ignore_result=True)
def replace_idby_contribution(verbose=False, details=False, debug=False,
                              timestamp=True):
    """Replace identifiedBy contributions with $ref.

    :param verbose: Verbose print.
    :param details: Details print.
    :param debug: Debug print.
    :returns: count found, count exists,
              count Idref, GND not found, count MEF not found
    """
    replace_contribution = ReplaceMefIdentifiedByContribution(
        verbose=verbose, debug=debug)
    replace_contribution.process()
    if timestamp:
        replace_contribution.set_timestamp()
    if details:
        replace_contribution.print_details()
    return replace_contribution.counts_len


@shared_task(ignore_result=True)
def replace_idby_subjects(verbose=False, details=False, debug=False,
                          subjects='subjects', timestamp=True):
    """Replace identifiedBy subjects with $ref.

    :param verbose: Verbose print.
    :param details: Details print.
    :param debug: Debug print.
    ::param subjects: [subjects, subjects_imported].
    :returns: count found, count exists,
              count Idref, GND not found, count MEF not found
    """
    replace_subjects = ReplaceMefIdentifiedBySubjects(
        verbose=verbose, debug=debug, subjects=subjects)
    replace_subjects.process()
    if timestamp:
        replace_subjects.set_timestamp()
    if details:
        replace_subjects.print_details()
    return replace_subjects.counts_len
