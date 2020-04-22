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
from functools import wraps

import requests
import six
from dojson.contrib.marc21.utils import create_record, split_stream
from flask import Blueprint, abort, current_app, jsonify, render_template
from flask import request as flask_request
from flask_babelex import gettext as _
from flask_login import current_user
from invenio_records_ui.signals import record_viewed

from .api import Document
from .dojson.contrib.unimarctojson import unimarc
from .utils import display_alternate_graphic_first, edition_format_text, \
    localized_data_name, note_format_text, publication_statement_text, \
    series_format_text, title_format_text_alternate_graphic, \
    title_format_text_head, title_variant_format_text
from ..holdings.api import Holding
from ..items.api import Item
from ..items.models import ItemStatus
from ..libraries.api import Library
from ..loans.api import Loan
from ..loans.utils import can_be_requested
from ..locations.api import Location
from ..organisations.api import Organisation
from ..patrons.api import Patron
from ..persons.api import Person
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

    viewcode = kwargs['viewcode']

    record['available'] = record.is_available(viewcode)

    holdings = [
        Holding.get_record_by_pid(holding_pid).replace_refs()
        for holding_pid in Holding.get_holdings_by_document_by_view_code(
            document_pid=pid.pid_value, viewcode=viewcode
        )
    ]

    return render_template(
        template,
        pid=pid,
        record=record,
        holdings=holdings,
        viewcode=viewcode,
        recordType='documents'
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
    """Document cover service."""
    cover_service = current_app.config.get('RERO_ILS_THUMBNAIL_SERVICE_URL')
    url = cover_service + '?height=60px&jsonpCallbackParam=callback'\
                          '&type=isbn&width=60px&callback=thumb&value=' + isbn
    response = requests.get(
        url, headers={'referer': flask_request.host_url})
    return jsonify(json.loads(response.text[len('thumb('):-1]))


@api_blueprint.route("/import/bnf/<int:ean>")
@check_permission
def import_bnf_ean(ean):
    """Import record from BNFr given a isbn 13 without dashes.

    See: https://catalogue.bnf.fr/api/test.do
    """
    bnf_url = current_app.config['RERO_ILS_APP_IMPORT_BNF_EAN']
    try:
        with requests.get(bnf_url.format(ean)) as response:
            if not response.ok:
                status_code = 502
                response = {
                    'metadata': {},
                    'errors': {
                        'code': status_code,
                        'title': 'The BNF server returns a bad status code.',
                        'detail': 'Status code: {}'.format(
                            response.status_code)
                    }
                }
                current_app.logger.error(
                    '{title}: {detail}'.format(
                        title=response.get('title'),
                        detail=response.get('detail')))

            else:
                # read the xml date from the HTTP response
                xml_data = response.content

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
                record = unimarc.do(json_data)
                response = {
                    'metadata': record
                }
                status_code = 200
    # no record found!
    except StopIteration:
        status_code = 404
        response = {
            'metadata': {},
            'errors': {
                'code': status_code,
                'title': 'The EAN was not found on the BNF server.'
            }
        }
    # other errors
    except Exception as error:
        status_code = 500
        response = {
            'metadata': {},
            'errors': {
                'code': status_code,
                'title': 'An unexpected error has been raise.',
                'detail': 'Error: {error}'.format(error=error)
            }
        }
        current_app.logger.error(
            '{title}: {detail}'.format(
                title=response.get('title'),
                detail=response.get('detail')))

    return jsonify(response), status_code


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
                # Complete metadata before Loan creation
                loan_metadata = dict(item)
                if 'item_pid' not in loan_metadata:
                    loan_metadata['item_pid'] = item.pid
                if 'patron_pid' not in loan_metadata:
                    loan_metadata['patron_pid'] = patron.pid
                # Create "virtual" Loan (not registered)
                loan = Loan(loan_metadata)
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


@blueprint.app_template_filter()
def authors_format(pid, language, viewcode):
    """Format authors for template in given language."""
    doc = Document.get_record_by_pid(pid)
    doc = doc.replace_refs()
    output = []
    for author in doc.get('authors', []):
        line = []
        author_pid = author.get('pid')
        if author_pid:
            if (Person.get_record_by_pid(author_pid)):
                author = \
                    Person.get_record_by_pid(author_pid).dumps_for_document()
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
def edition_format(editions):
    """Format edition for template."""
    output = []
    for edition in editions:
        languages = edition_format_text(edition)
        if languages:
            for edition_text in languages:
                output.append(edition_text.get('value'))
    return output


@blueprint.app_template_filter()
def note_format(notes):
    """Format note for template."""
    return note_format_text(notes)


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
        output.append(series_format_text(serie))
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
        if location:
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
                item.get_item_end_date(format=format),
                format=format,
                locale=locale
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
        if (not status or status == 'valid') and id_type != 'bf:Local':
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
        language_code = 'lang_{code}'.format(code=lang.get('value'))
        output.append(_(language_code))
    return ", ".join(output)


@api_blueprint.route('/availabilty/<document_pid>', methods=['GET'])
def document_availability(document_pid):
    """HTTP GET request for document availability."""
    view_code = flask_request.args.get('view_code')
    if not view_code:
        view_code = 'global'
    document = Document.get_record_by_pid(document_pid)
    if not document:
        abort(404)
    return jsonify({
        'availability': document.is_available(view_code)
    })


@blueprint.app_template_filter()
def create_publication_statement(provision_activity):
    """Create publication statement from place, agent and date values."""
    output = []
    publication_texts = publication_statement_text(provision_activity)
    for publication_text in publication_texts:
        language = publication_text.get('language', 'default')
        if display_alternate_graphic_first(language):
            output.insert(0, publication_text.get('value'))
        else:
            output.append(publication_text.get('value'))
    return output


@blueprint.app_template_filter()
def get_cover_art(record):
    """Get cover art.

    :param record: record
    :return: url for cover art or None
    """
    for electronic_locator in record.get('electronicLocator', []):
        type = electronic_locator.get('type')
        content = electronic_locator.get('content')
        if type == 'relatedResource' and content == 'coverImage':
            return electronic_locator.get('url')
    return None


@blueprint.app_template_filter()
def get_accesses(record):
    """Get electronic locator text.

    :param record: record
    :return: dictonary list of access informations
    """
    accesses = []

    def filter_type(electronic_locator):
        """Filter electronic locator for resources and not cover image."""
        types = ['resource', 'versionOfResource']
        if electronic_locator.get('type') in types:
            return True
        else:
            return False

    filtered_electronic_locators = filter(
        filter_type,
        record.get('electronicLocator', [])
    )
    for electronic_locator in filtered_electronic_locators:
        url = electronic_locator.get('url')
        content = electronic_locator.get('content', url)
        public_notes = electronic_locator.get('publicNote', [])
        public_note = ', '.join(public_notes)
        accesses.append({
            'type': electronic_locator.get('type'),
            'url': url,
            'content': content,
            'public_note': public_note
        })
    return accesses


@blueprint.app_template_filter()
def get_other_accesses(record):
    """Length for electronic locator.

    :param record: record
    :return: dictonary list of other access informations
    """
    accesses = []

    def filter_type(electronic_locator):
        """Filter electronic locator for related resources and no info."""
        if electronic_locator.get('type') in ['relatedResource', 'noInfo'] \
                and electronic_locator.get('content') != 'coverImage':
            return True
        else:
            return False

    filtered_electronic_locators = filter(
        filter_type,
        record.get('electronicLocator', [])
    )
    for electronic_locator in filtered_electronic_locators:
        url = electronic_locator.get('url')
        content = electronic_locator.get('content', url)
        public_notes = electronic_locator.get('publicNote', [])
        public_note = ', '.join(public_notes)
        accesses.append({
            'type': electronic_locator.get('type'),
            'url': url,
            'content': content,
            'public_note': public_note
        })
    return accesses


@blueprint.app_template_filter()
def create_title_text(titles, responsibility_statement=[]):
    """Create the title text for display purpose.

    :param titles: list of title objects
    :type titles: list
    :param responsibility_statement: list of title objects
    :type responsibility_statement: list
    :return: the title text for display purpose
    :rtype: str
    """
    return title_format_text_head(titles, responsibility_statement,
                                  with_subtitle=True)


@blueprint.app_template_filter()
def create_title_alternate_graphic(titles, responsibility_statement=[]):
    """Create the list of alternate graphic titles as text for detail view.

    :param titles: list of title objects
    :type titles: list
    :param responsibility_statement: list of title objects
    :type responsibility_statement: list
    :return: list of alternate graphic titles as text for detail view
    :rtype: list
    """
    output = []
    altgr_texts = title_format_text_alternate_graphic(titles,
                                                      responsibility_statement)
    for altgr_text in altgr_texts:
        value = altgr_text.get('value')
        if value not in output:
            output.append(value)
    return output


@blueprint.app_template_filter()
def create_title_variants(titles):
    """Create the list of variant titles as text for detail view.

    :param titles: list of title objects
    :type titles: list
    :return: list of variant titles as text for detail view
    :rtype: list
    """
    output = []
    title_variant_texts = \
        title_variant_format_text(titles=titles, with_subtitle=True)
    for title_variant_text in title_variant_texts:
        value = title_variant_text.get('value')
        if value not in output:
            output.append(value)
    return output


@blueprint.app_template_filter()
def create_title_responsibilites(responsibilityStatement):
    """Create the list of title responsibilites as text for detail view.

    :param responsibilityStatement: list of responsibilityStatement
    :type responsibilityStatement: list
    :return: list of title responsibilites as text for detail view
    :rtype: list

    """
    output = []
    for responsibility in responsibilityStatement:
        for responsibility_language in responsibility:
            value = responsibility_language.get('value')
            if value not in output:
                language = responsibility_language.get('language', 'default')
                if display_alternate_graphic_first(language):
                    output.insert(0, value)
                else:
                    output.append(value)
    return output
