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

import json
import re
import sys
from functools import wraps
from urllib.request import urlopen

import pycountry
import requests
import six
from babel import Locale
from dojson.contrib.marc21.utils import create_record, split_stream
from flask import Blueprint, abort, current_app, jsonify, render_template, \
    request
from flask_babelex import gettext as _
from flask_login import current_user
from invenio_records_ui.signals import record_viewed

from .api import Document
from .dojson.contrib.unimarctojson import unimarctojson
from ..holdings.api import Holding
from ..items.api import Item, ItemStatus
from ..libraries.api import Library
from ..loans.utils import can_be_requested
from ..locations.api import Location
from ..organisations.api import Organisation
from ..patrons.api import Patron
from ...filter import format_date_filter
from ...permissions import login_and_librarian


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

    holdings = [
        Holding.get_record_by_pid(holding_pid)
        for holding_pid in Holding.get_holdings_pid_by_document_pid(
            pid.pid_value
        )
    ]

    viewcode = kwargs['viewcode']

    return render_template(
        template,
        pid=pid,
        record=record,
        holdings=holdings,
        viewcode=viewcode
    )


api_blueprint = Blueprint(
    'api_documents',
    __name__
)


def check_permission(fn):
    """Check user permissions."""
    @wraps(fn)
    def decorated_view(*args, **kwargs):
        """Decorated view."""
        login_and_librarian()
        return fn(*args, **kwargs)
    return decorated_view


@api_blueprint.route('/cover/<isbn>')
def cover(isbn):
    """Documenet cover service."""
    cover_service = current_app.config.get('RERO_ILS_THUMBNAIL_SERVICE_URL')
    url = cover_service + '?height=60px&jsonpCallbackParam=callback'\
                          '&type=isbn&width=60px&callback=thumb&value=' + isbn
    response = requests.get(
        url, headers={'referer': request.host_url})
    return jsonify(json.loads(response.text[len('thumb('):-1]))


@api_blueprint.route("/import/bnf/<int:ean>")
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
            if 'patron' in patron.get('roles') and \
                patron.get_organisation()['pid'] == \
                    item.get_library().replace_refs()['organisation']['pid']:
                # TODO: Virtual Loan
                loan = {
                    'item_pid': item.pid,
                    'patron_pid': patron.pid
                }
                if not can_be_requested(loan):
                    return False
                patron_barcode = patron.get('barcode')
                item_status = item.get('status')
                if item_status != 'missing':
                    loaned_to_patron = item.is_loaned_to_patron(patron_barcode)
                    requested = item.is_requested_by_patron(patron_barcode)
                    if not (requested or loaned_to_patron):
                        return True
    return False


@blueprint.app_template_filter()
def requested_this_item(item):
    """Check if the current user has requested a given item."""
    if current_user.is_authenticated:
        patron = Patron.get_patron_by_user(current_user)
        if patron and 'patron' in patron.get('roles'):
            patron_barcode = patron.get('barcode')
            requested = item.is_requested_by_patron(patron_barcode)
            if requested:
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


def localized_data_name(data, language):
    """Get localized name."""
    return data.get(
        'name_{language}'.format(language=language),
        data.get('name', '')
    )


@blueprint.app_template_filter()
def authors_format(pid, language, viewcode):
    """Format authors for template."""
    doc = Document.get_record_by_pid(pid)
    doc = doc.replace_refs()
    output = []
    for author in doc.get('authors', []):
        line = []
        name = localized_data_name(data=author, language=language)
        line.append(name)
        qualifier = author.get('qualifier')
        if qualifier:
            line.append(qualifier)
        date = author.get('date')
        if date:
            line.append(date)
        mef_pid = author.get('pid')
        if mef_pid:
            # add link <a href="url">link text</a>
            line = '<a href="/{viewcode}/persons/{pid}">{text}</a>'.format(
                viewcode=viewcode,
                pid=mef_pid,
                text=', '.join(line)
            )
        else:
            line = ', '.join(str(x) for x in line)
        output.append(line)

    return '; '.join(output)


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
def item_library_pickup_locations(item):
    """Get the pickup locations of the library of the given item."""
    location_pid = item.replace_refs()['location']['pid']
    location = Location.get_record_by_pid(location_pid)
    library_pid = location.replace_refs()['library']['pid']
    library = Library.get_record_by_pid(library_pid).replace_refs()
    organisation = Organisation.get_record_by_pid(
        library['organisation']['pid'])
    locations = []
    for library in organisation.get_libraries():
        location = Location.get_record_by_pid(
            library.get_pickup_location_pid())
        locations.append(location)
    return locations


@blueprint.app_template_filter()
def item_status_text(item, format='medium', locale='en'):
    """Text for item status."""
    if item.available:
        text = _('available')
    else:
        text = _('not available')
        if item.status == ItemStatus.ON_LOAN:
            due_date = format_date_filter(
                item.get_item_end_date(), format=format, locale=locale
            )
            text += ' ({0} {1})'.format(_('due until'), due_date)
        elif item.number_of_requests() > 0:
            text += ' ({0})'.format(_('requested'))
            if item.status == ItemStatus.IN_TRANSIT:
                text += ' ({0})'.format(_(ItemStatus.IN_TRANSIT))
    return text


@blueprint.app_template_filter()
def identifiedby_format(identifiedby):
    """Format identifiedby for template."""
    output = []
    for identifier in identifiedby:
        status = identifier.get('status')
        id_type = identifier.get('type')
        if not status and id_type != 'bf:Local':
            if id_type.find(':') != -1:
                id_type = id_type.split(':')[1]
            output.append({'type': id_type, 'value': identifier.get('value')})
    return output


@blueprint.app_template_filter()
def document_isbn(identifiedby):
    """Returns document isbn."""
    for identifier in identifiedby:
        if identifier.get('type') == 'bf:Isbn':
            return {'isbn': identifier.get('value')}
    return {}


@blueprint.app_template_filter()
def language_format(langs_list, language_interface):
    """Converts language code to langauge name.

    langs_list: a code or a list of language codes
    language_interface: the code of the language of the interface
    Returns a comma separated list of language names.
    """
    output = []
    if isinstance(langs_list, str):
        langs_list = [{'type': 'bf:Language', 'value': langs_list}]
    for lang in langs_list:
        try:
            lang_name = pycountry.languages.get(
                bibliographic=lang.get('value')).alpha_2
        except:
            lang_name = pycountry.languages.get(
                alpha_3=lang.get('value')).alpha_2
        lang_display = Locale(lang_name).get_language_name(
            language_interface).lower()
        output.append(lang_display)
    return ", ".join(output)
