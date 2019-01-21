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
import sys
from functools import wraps
from urllib.request import urlopen

import six
from dojson.contrib.marc21.utils import create_record, split_stream
from flask import Blueprint, abort, current_app, jsonify, render_template
from flask_babelex import gettext as _
from flask_login import current_user
from invenio_records_ui.signals import record_viewed

from ...filter import format_date_filter
from ...permissions import login_and_librarian
from ..items.api import Item, ItemStatus
from ..libraries.api import Library
from ..locations.api import Location
from ..patrons.api import Patron
from .dojson.contrib.unimarctojson import unimarctojson


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
    items = [
        Item.get_record_by_pid(item_pid)
        for item_pid in Item.get_items_pid_by_document_pid(pid.pid_value)
    ]
    return render_template(
        template,
        pid=pid,
        record=record,
        items=items
    )


api_blueprint = Blueprint(
    'api_documents',
    __name__
)


def check_permission(fn):
    """."""
    @wraps(fn)
    def decorated_view(*args, **kwargs):
        """."""
        login_and_librarian()
        return fn(*args, **kwargs)
    return decorated_view


@api_blueprint.route("/editor/import/bnf/ean/<int:ean>")
@check_permission
def import_bnf_ean(ean):
    """Import record from BNFr given a isbn 13 without dashes."""
    bnf_url = current_app.config['RERO_ILS_APP_IMPORT_BNF_EAN']
    try:
        with urlopen(bnf_url % ean) as response:
            if response.status != 200:
                abort(502)
            # read the xml date from the HTTP response
            xml_data = response.read()

            # create a xml file in memory
            xml_file = six.BytesIO()
            xml_file.write(xml_data)
            xml_file.seek(0)

            # get the record in xml if exists
            # note: the request should returns one record max
            xml_record = next(split_stream(xml_file))

            # convert xml in marc json
            json_data = create_record(xml_record)

            # convert marc json to local json format
            record = unimarctojson.do(json_data)
            response = {
                'metadata': record
            }
            return jsonify(response)
    # no record found!
    except StopIteration:
        response = {
            'record': {}
        }
        return jsonify(response), 404
    # other errors
    except Exception:
        sys.stdout.flush()
        response = {
            'record': {}
        }
        return jsonify(response), 500


blueprint = Blueprint(
    'documents',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.app_template_filter()
def can_request(item):
    """Check if the current user can request a given item."""
    if current_user.is_authenticated:
        patron = Patron.get_patron_by_user(current_user)
        if patron:
            if 'patron' in patron.get('roles'):
                patron_barcode = patron.get('barcode')
                item_status = item.get('status')
                if item_status != 'missing':
                    loaned_to_patron = item.is_loaned_to_patron(patron_barcode)
                    request = item.is_requested_by_patron(patron_barcode)
                    if not (request or loaned_to_patron):
                        return True
    return False


@blueprint.app_template_filter()
def requested_this_item(item):
    """Check if the current user has requested a given item."""
    if current_user.is_authenticated:
        patron = Patron.get_patron_by_user(current_user)
        if patron and 'patron' in patron.get('roles'):
            patron_barcode = patron.get('barcode')
            request = item.is_requested_by_patron(patron_barcode)
            if request:
                return True
    return False


@blueprint.app_template_filter()
def number_of_requests(item):
    """Get number of requests for a given item."""
    return item.number_of_requests()


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


@blueprint.app_template_filter()
def item_library_locations(item_pid):
    """Get the locations of the library of the given item."""
    location_pid = Item.get_record_by_pid(item_pid)['location_pid']
    location = Location.get_record_by_pid(location_pid)
    library = Library.get_library_by_locationid(location.id)
    locations = library.locations
    return locations


@blueprint.app_template_filter()
def item_library_pickup_locations(item):
    """Get the pickup locations of the library of the given item."""
    location_pid = item.replace_refs()['location']['pid']
    location = Location.get_record_by_pid(location_pid)
    library_pid = location.replace_refs()['library']['pid']
    library = Library.get_record_by_pid(library_pid)
    return [Location.get_record_by_pid(library.get_pickup_location_pid())]


@blueprint.app_template_filter()
def item_status_text(item, format='medium', locale='en'):
    """Text for item status."""
    if item.available:
        text = _('available')
        if item.dumps().get('item_type') == 'on_site_consultation':
            text += ' ({0})'.format(_('on_site consultation'))
    else:
        text = _('not available')
        if item.status == ItemStatus.ON_LOAN:
            due_date = format_date_filter(
                item.get_item_end_date(), format=format, locale=locale
            )
            text += ' ({0} {1})'.format(_('due until'), due_date)
        elif item.number_of_requests() > 0:
            text += ' ({0})'.format(_('requested'))
        elif item.status == ItemStatus.IN_TRANSIT:
            text += ' ({0})'.format(_(ItemStatus.IN_TRANSIT))
    return text
