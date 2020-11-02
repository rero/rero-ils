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
from functools import wraps

import requests
from flask import Blueprint, abort, current_app, jsonify, render_template
from flask import request as flask_request
from flask_babelex import gettext as _
from flask_login import current_user
from invenio_records_ui.signals import record_viewed

from .api import Document
from .utils import create_authorized_access_point, \
    display_alternate_graphic_first, edition_format_text, \
    publication_statement_text, series_statement_format_text, \
    title_format_text_alternate_graphic, title_format_text_head, \
    title_variant_format_text
from ..collections.api import CollectionsSearch
from ..holdings.api import Holding
from ..items.models import ItemCirculationAction, ItemNoteTypes
from ..libraries.api import Library
from ..locations.api import Location
from ..organisations.api import Organisation
from ..patrons.api import Patron, current_patron
from ..persons.api import Person
from ..utils import extracted_data_from_ref
from ...permissions import login_and_librarian


def doc_item_view_method(pid, record, template=None, **kwargs):
    r"""Display default view.

    Sends record_viewed signal and renders template.
    :param pid: PID object.
    :param record: Record object.
    :param template: Template to render.
    :param \*\*kwargs: Additional view arguments based on URL rule.
    :return: The rendered template.
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


blueprint = Blueprint(
    'documents',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.app_template_filter()
def item_and_patron_in_same_organisation(item):
    """Check if the current user belongs to the same organisation than item."""
    return current_patron and current_patron.organisation_pid == \
        item.organisation_pid


@blueprint.app_template_filter()
def can_request(item):
    """Check if the current user can request a given item."""
    if current_user.is_authenticated:
        patron = Patron.get_patron_by_user(current_user)
        if patron and patron.is_patron:
            can, reasons = item.can(
                ItemCirculationAction.REQUEST,
                patron=patron,
                library=Library.get_record_by_pid(patron.library_pid)
            )
            return can, reasons
    return False, []


@blueprint.app_template_filter()
def get_public_notes(item):
    """Get public notes related to an item."""
    return [n for n in item.notes if n.get('type') in ItemNoteTypes.PUBLIC]


@blueprint.app_template_filter()
def get_note(record, note_type):
    """Get a note by its type for a given holdings or item.

    :param record: the record to check.
    :param note_type: the type of note to find.
    :return the requested note, None if no corresponding note is found.
    """
    return record.get_note(note_type)


@blueprint.app_template_filter()
def contribution_format(pid, language, viewcode, role=False):
    """Format contribution for template in given language.

    :param pid: pid for document.
    :param language: language to use.
    :param viewcode: viewcode to use.
    :param role: display roles.
    :return the contribution in formatted form.
    """
    doc = Document.get_record_by_pid(pid)
    doc = doc.replace_refs()
    output = []
    for contribution in doc.get('contribution', []):
        pers_pid = contribution['agent'].get('pid')
        if pers_pid:
            person = Person.get_record_by_pid(pers_pid)
            # add link <a href="url">link text</a>
            authorized_access_point = person.get_authorized_access_point(
                language=language
            )
            line = '<a href="/{viewcode}/persons/{pid}">{text}</a>'.format(
                viewcode=viewcode,
                pid=pers_pid,
                text=authorized_access_point
            )
        else:
            line = create_authorized_access_point(contribution['agent'])

        if role:
            roles = []
            for role in contribution.get('role'):
                roles.append(_(role))
            if roles:
                line += '<span class="text-secondary"> ({role})</span>'.format(
                    role=', '.join(roles)
                )

        output.append(line)
    return '&#8239;; '.join(output)


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
    notes_text = {}
    for note in notes:
        note_type = note.get('noteType')
        notes_text.setdefault(note_type, [])
        notes_text[note_type].append(note.get('label'))
    return notes_text


@blueprint.app_template_filter()
def part_of_format(part_of):
    """Format 'part of' data for template."""
    document_pid = extracted_data_from_ref(part_of.get('document'), data='pid')
    document = Document.get_record_by_pid(document_pid)
    nums = part_of.get('numbering')
    output = {}
    # Set host document pid
    output['document_pid'] = document_pid
    # Set label
    subtype = document.get('issuance').get('subtype')
    if subtype == 'periodical':
        output['label'] = _('Journal')
    elif subtype == 'monographicSeries':
        output['label'] = _('Series')
    else:
        output['label'] = _('Published in')
    # Set title
    bf_titles = list(filter(
        lambda t: t['type'] == 'bf:Title', document.get('title')
    ))
    for title in bf_titles:
        for main_title in title.get('mainTitle', []):
            if not main_title.get('language'):
                output['title'] = main_title.get('value')
    # Format and set numbering (example: 2020, vol. 2, nr. 3, p. 302)
    if nums is not None:
        for num in nums:
            numbering = []
            if num.get('year'):
                numbering.append(num.get('year'))
            if num.get('volume'):
                volume = [_('vol'), str(num.get('volume'))]
                numbering.append(". ".join(volume))
            if num.get('issue'):
                issue = [_('nr'), str(num.get('issue'))]
                numbering.append(". ".join(issue))
            if num.get('pages'):
                pages = [_('p'), str(num.get('pages'))]
                numbering.append(". ".join(pages))
            output.setdefault('numbering', [])
            output['numbering'].append(", ".join(numbering))
    return output


@blueprint.app_template_filter()
def series_format(serie):
    """Format series for template."""
    return series_statement_format_text(serie)


@blueprint.app_template_filter()
def item_library_pickup_locations(item):
    """Get the pickup locations of the library of the given item."""
    location_pid = item.replace_refs()['location']['pid']
    location = Location.get_record_by_pid(location_pid)
    # Either the location defines some 'restrict_pickup_to' either not.
    # * If 'restrict_pickup_to' is defined, then only these locations are
    #   eligible as possible pickup_locations
    # * Otherwise, get all organisation pickup locations of the item belongs to
    if 'restrict_pickup_to' in location:
        # Get all pickup locations as Location objects and append it to the
        # location item (removing possible None values)
        pickup_locations = list(filter(None, [
            Location.get_record_by_pid(loc_pid)
            for loc_pid in location.restrict_pickup_to
        ]))
    else:
        org = Organisation.get_record_by_pid(location.organisation_pid)
        # Get the pickup location from each library of the item organisation
        # (removing possible None value)
        pickup_locations = list(filter(None, [
            Location.get_record_by_pid(library.get_pickup_location_pid())
            for library in org.get_libraries()
        ]))
    return sorted(
        pickup_locations,
        key=lambda location: location.get('pickup_name', location.get('code'))
    )


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


@blueprint.app_template_filter()
def in_collection(item_pid):
    """Find item in published collection(s).

    :param item_pid: item pid
    :return: list of collections whose item is present
    """
    return list(
        CollectionsSearch()
        .filter('term', items__pid=item_pid)
        .filter('term', published=True)
        .scan()
    )
