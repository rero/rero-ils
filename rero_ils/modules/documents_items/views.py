# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Blueprint used for loading templates."""

from __future__ import absolute_import, print_function

import re

from flask import Blueprint, current_app, render_template
from flask_login import current_user
from invenio_records_ui.signals import record_viewed

from ..items.api import Item
from ..libraries_locations.api import LibraryWithLocations
from ..locations.api import Location
from ..patrons.api import Patron

blueprint = Blueprint(
    'documents_items', __name__,
    template_folder='templates', static_folder='static'
)


@blueprint.app_template_filter()
def can_request(item):
    """Check if the current user can request a given item."""
    if current_user.is_authenticated:
        patron = Patron.get_patron_by_user(current_user)
        if patron:
            if patron.has_role('patrons'):
                patron_barcode = patron.get('barcode')
                item_status = item.get('item_status')
                if item_status != 'missing':
                    loan = Item.loaned_to_patron(item, patron_barcode)
                    request = Item.requested_by_patron(item, patron_barcode)
                    if not (request or loan):
                        return True
    return False


@blueprint.app_template_filter()
def requested_this_item(item):
    """Check if the current user has requested a given item."""
    if current_user.is_authenticated:
        patron = Patron.get_patron_by_user(current_user)
        if patron and patron['is_patron']:
            patron_barcode = patron.get('barcode')
            request = Item.requested_by_patron(item, patron_barcode)
            if request:
                return True
    return False


@blueprint.app_template_filter()
def number_of_requests(item):
    """Get number of requests for a given item."""
    return Item.number_of_item_requests(item)


@blueprint.app_template_filter()
def patron_request_rank(item):
    """Get the rank of patron in list of requests on this item."""
    if current_user.is_authenticated:
        patron = Patron.get_patron_by_user(current_user)
        if patron:
            patron_barcode = patron.get('barcode')
            return Item.patron_request_rank(item, patron_barcode)
    return False


@blueprint.app_template_filter()
def authors_format(authors):
    """Format authors for template."""
    output = []
    for author in authors:
        line = []
        line.append(author.get('name'))
        if author.get('qualifier'):
            line.append(author.get('qualifier'))
        if author.get('date'):
            line.append(author.get('date'))
        output.append(', '.join(str(x) for x in line))
    return '; '.join(str(x) for x in output)


@blueprint.app_template_filter()
def publishers_format(publishers):
    """Format publishers for template."""
    output = []
    for publisher in publishers:
        line = []
        places = publisher.get('place', [])
        if len(places) > 0:
            line.append('; '.join(str(x) for x in places) + ': ')
        names = publisher.get('name')
        line.append('; '.join(str(x) for x in names))
        output.append(''.join(str(x) for x in line))
    return '; '.join(str(x) for x in output)


@blueprint.app_template_filter()
def series_format(series):
    """Format series for template."""
    output = []
    for serie in series:
        line = []
        if serie.get('name'):
            line.append(serie.get('name'))
        if serie.get('number'):
            line.append(', ' + serie.get('number'))
        output.append(''.join(str(x) for x in line))
    return '; '.join(str(x) for x in output)


@blueprint.app_template_filter()
def abstracts_format(abstracts):
    """Format abstracts for template."""
    output = []
    for abstract in abstracts:
        output.append(re.sub(r'\n+', '\n', abstract))
    return '\n'.join(str(x) for x in output)


def doc_item_view_method(pid, record, template=None, **kwargs):
    r"""Display default view.

    Sends record_viewed signal and renders template.

    :param pid: PID object.
    :param record: Record object.
    :param template: Template to render.
    :param \*\*kwargs: Additional view arguments based on URL rule.
    :returns: The rendered template.
    """
    record_viewed.send(
        current_app._get_current_object(), pid=pid, record=record)
    # libraries = Library.get_all_libraries()
    locations = Location.get_all_locations()
    return render_template(
        template,
        pid=pid,
        record=record,
        locations=locations
    )


@blueprint.app_template_filter()
def item_library_locations(item_pid):
    """Get the locations of the library of the given item."""
    location_pid = Item.get_record_by_pid(item_pid)['location_pid']
    location = Location.get_record_by_pid(location_pid)
    library = LibraryWithLocations.get_library_by_locationid(location.id)
    locations = library.locations
    return locations


@blueprint.app_template_filter()
def item_library_pikcup_locations(item_pid):
    """Get the pickup locations of the library of the given item."""
    location_pid = Item.get_record_by_pid(item_pid)['location_pid']
    location = Location.get_record_by_pid(location_pid)
    library = LibraryWithLocations.get_library_by_locationid(location.id)
    locations = library.pickup_locations
    return locations
