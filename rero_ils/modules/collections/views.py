# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2020 RERO
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

"""Blueprint used for loading templates."""

from __future__ import absolute_import, print_function

from flask import Blueprint, abort, current_app, render_template
from invenio_records_ui.signals import record_viewed

from rero_ils.filter import format_date_filter

from ..documents.api import Document
from ..libraries.api import Library
from ..organisations.api import Organisation

blueprint = Blueprint(
    'collections',
    __name__,
    template_folder='templates',
    static_folder='static',
)


def collection_view_method(pid, record, template=None, **kwargs):
    """Display default view.

    Sends record_viewed signal and renders template.
    :param pid: PID object.
    """
    record_viewed.send(
        current_app._get_current_object(), pid=pid, record=record)

    viewcode = kwargs['viewcode']
    org_pid = Organisation.get_record_by_viewcode(viewcode)['pid']
    rec = record.replace_refs()
    libraries = []

    if org_pid != rec.get('organisation').get('pid'):
        abort(
            404, 'The collections is not referenced for this organisation'
        )
    # Get items and document title
    rec['items'] = record.get_items()
    for item in rec['items']:
        item['document'] = Document.get_record_by_pid(
            item.replace_refs().get('document').get('pid'))
    # Get libraries names
    for library in rec.get('libraries'):
        libraries.append(
            Library.get_record_by_pid(library['pid']).get('name')
        )
    rec['libraries'] = ', '.join(libraries)
    # Format date
    rec['date'] = _start_end_date(
        record.get('start_date'), record.get('end_date'))

    return render_template(
        template,
        record=rec,
        viewcode=viewcode
    )


def _start_end_date(start_date, end_date):
    """Format date."""
    return '{start} - {end}'.format(start=format_date_filter(
        start_date, date_format='short', time_format=None, locale='fr'),
        end=format_date_filter(
            end_date, date_format='short', time_format=None, locale='fr')
    )


@blueprint.app_template_filter()
def get_teachers(record):
    """Get teachers.

    :param record: record
    :return: list of teachers of the collection
    """
    teachers = filter(
        None, [teacher.get('name') for teacher in record.get('teachers', [])]
    )
    return ', '.join(teachers)
