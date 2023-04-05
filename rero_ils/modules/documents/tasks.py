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
