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

"""Blueprint used for loading templates."""


from __future__ import absolute_import, print_function

from flask import Blueprint, abort, current_app, render_template
from invenio_records_ui.signals import record_viewed

from .api import Holding
from ..documents.api import Document
from ..item_types.api import ItemType
from ..libraries.api import Library
from ..locations.api import Location


def holding_view_method(pid, record, template=None, **kwargs):
    r"""Display default view.

    Sends record_viewed signal and renders template.
    :param pid: PID object.
    :param record: Record object.
    :param template: Template to render.
    :param \*\*kwargs: Additional view arguments based on URL rule.
    :returns: The rendered template.
    """
    record_viewed.send(
        current_app._get_current_object(), pid=pid, record=record
    )
    document = Document.get_record_by_pid(
        record.replace_refs()['document']['pid'])
    holding = record.replace_refs()
    location = Location.get_record_by_pid(holding['location']['pid'])
    library = Library.get_record_by_pid(
        location.replace_refs()['library']['pid'])
    circulation_category = ItemType.get_record_by_pid(
        holding['circulation_category']['pid'])
    items = record.get_items_filter_by_viewcode(kwargs['viewcode'])
    return render_template(
        template, pid=pid, record=record, document=document,
        location=location, circulation_category=circulation_category,
        library=library, viewcode=kwargs['viewcode'], items=items)


blueprint = Blueprint(
    'holding',
    __name__,
    url_prefix='/holding',
    template_folder='templates',
    static_folder='static',
)


@blueprint.app_template_filter()
def holding_loan_condition_filter(holding_pid):
    """HTTP GET request for holding loan condition."""
    holding = Holding.get_record_by_pid(holding_pid)
    if not holding:
        abort(404)
    return holding.get_holding_loan_conditions()


@blueprint.app_template_filter()
def holding_location(holding):
    """Returns holding location name as text."""
    location_pid = holding.get('location').get('pid')
    location = Location.get_record_by_pid(location_pid)
    return '{lib}: {loc}'.format(
        lib=location.get_library().get('name'), loc=location.get('name'))


@blueprint.app_template_filter()
def holding_circulation_category(holding):
    """Returns holding location name as text."""
    holding = Holding.get_record_by_pid(holding.get('pid'))
    return holding.get_holding_loan_conditions()
