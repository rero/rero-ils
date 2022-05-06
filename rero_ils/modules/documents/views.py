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

from typing import Optional

import click
from elasticsearch_dsl.query import Q
from flask import Blueprint, abort, current_app, jsonify, render_template
from flask import request as flask_request
from flask_babelex import gettext as _
from flask_login import current_user
from invenio_records_ui.signals import record_viewed

from .api import Document, DocumentsSearch
from .commons import SubjectFactory
from .utils import create_authorized_access_point, \
    display_alternate_graphic_first, edition_format_text, get_remote_cover, \
    publication_statement_text, series_statement_format_text, \
    title_format_text_alternate_graphic, title_format_text_head, \
    title_variant_format_text
from ..collections.api import CollectionsSearch
from ..contributions.api import Contribution
from ..holdings.models import HoldingNoteTypes
from ..items.models import ItemCirculationAction
from ..libraries.api import Library
from ..locations.api import Location
from ..organisations.api import Organisation
from ..patrons.api import current_patrons
from ..utils import cached, extracted_data_from_ref


def doc_item_view_method(pid, record, template=None, **kwargs):
    """Display default view.

    Sends record_viewed signal and renders template.
    :param pid: PID object.
    :param record: Record object.
    :param template: Template to render.
    :param **kwargs: Additional view arguments based on URL rule.
    :return: The rendered template.
    """
    record_viewed.send(
        current_app._get_current_object(), pid=pid, record=record)

    viewcode = kwargs['viewcode']
    organisation = None
    if viewcode != current_app.config.get('RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'):
        organisation = Organisation.get_record_by_viewcode(viewcode)

    record['available'] = Document.is_available(record.pid, viewcode)

    # build provision activity
    provision_activities = record.get('provisionActivity', [])
    for provision_activity in provision_activities:
        pub_state_text = publication_statement_text(provision_activity)
        if pub_state_text:
            provision_activity['_text'] = pub_state_text

    # Counting holdings to display the get button
    from ..holdings.api import HoldingsSearch
    query = HoldingsSearch()\
        .filter('term', document__pid=pid.pid_value)
    query = query.filter('bool', must_not=[Q('term', _masked=True)])
    if organisation:
        query = query.filter('term', organisation__pid=organisation.pid)
    holdings_count = query.count()

    return render_template(
        template,
        pid=pid,
        record=record,
        holdings_count=holdings_count,
        viewcode=viewcode,
        recordType='documents'
    )


api_blueprint = Blueprint(
    'api_documents',
    __name__
)


@api_blueprint.route('/cover/<isbn>')
@cached(timeout=300, query_string=True)
def cover(isbn):
    """Document cover service."""
    return jsonify(get_remote_cover(isbn))


blueprint = Blueprint(
    'documents',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.app_template_filter()
def note_general(notes):
    """Preprocess notes to extract only general type."""
    return sort_by_type(
        list(filter(lambda t: t['noteType'] == 'general', notes)))


@blueprint.app_template_filter()
def notes_except_general(notes):
    """Preprocess notes to extract all note except general type."""
    return sort_by_type(
        list(filter(lambda t: t['noteType'] != 'general', notes)))


def sort_by_type(notes):
    """Sort notes by type."""
    by_type = {}
    for note in notes:
        by_type.setdefault(note['noteType'], [])
        by_type[note['noteType']].append(note['label'])
    return by_type


@blueprint.app_template_filter()
def cartographic_attributes(attributes):
    """Preprocess cartographic attributes."""
    return [
        attribute
        for attribute in attributes
        if 'projection' in attribute
        or attribute.get('coordinates', {}).get('label')
    ]


@blueprint.app_template_filter()
def provision_activity(provisions):
    """Preprocess provision activity."""
    output = {}
    provisions = list(
        filter(lambda t: '_text' in t and 'statement' in t, provisions))
    for provision in provisions:
        if provision['type'] not in output:
            output.setdefault(provision['type'], [])
        for text in provision['_text']:
            output[provision['type']].append(text)
    return output


@blueprint.app_template_filter()
def provision_activity_publication(provisions):
    """Extact only publication of provision activity."""
    return {
        'bf:Publication': provisions.get('bf:Publication', [])
    }


@blueprint.app_template_filter()
def provision_activity_not_publication(provisions):
    """Extact other than publication of provision activity."""
    if 'bf:Publication' in provisions:
        provisions.pop('bf:Publication')
    return provisions


@blueprint.app_template_filter()
def provision_activity_original_date(provisions):
    """Preprocess provision activity original date."""
    return [
        provision['original_date']
        for provision in provisions
        if 'original_date' in provision
    ]


@blueprint.app_template_filter()
def title_variants(titles):
    """Preprocess title variants."""
    variants = {}
    bf_titles = list(filter(lambda t: t['type'] != 'bf:Title', titles))
    for title in bf_titles:
        result = []
        variants.setdefault(title['type'], [])
        result.append(title['mainTitle'][0]['value'])
        if 'subtitle' in title:
            result.append(title['subtitle'][0]['value'])
        variants[title['type']].append(': '.join(result))
    return variants


@blueprint.app_template_filter()
def identified_by(identifiedby):
    """Preprocess identified by."""
    output = []
    for identifier in identifiedby:
        details = []
        # Replace bf:Local by source
        id_type = identifier.get('type')
        if id_type == 'bf:Local':
            id_type = identifier.get('source')
        # Format qualifier, status and note
        if identifier.get('qualifier'):
            details.append(identifier.get('qualifier'))
        if identifier.get('status'):
            details.append(identifier.get('status'))
        if identifier.get('note'):
            details.append(identifier.get('note'))
        output.append({
            'type': id_type,
            'value': identifier.get('value'),
            'details': ', '.join(details)
        })
    return output


@blueprint.app_template_filter()
def can_request(item):
    """Check if the current user can request a given item."""
    if current_user.is_authenticated:
        patron = None
        for p in current_patrons:
            if p.organisation_pid == item.organisation_pid:
                patron = p
        if patron:
            can, reasons = item.can(
                ItemCirculationAction.REQUEST,
                patron=patron,
                library=Library.get_record_by_pid(patron.library_pid)
            )
            return can, reasons
    return False, []


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
        cont_pid = contribution['agent'].get('pid')
        if cont_pid:
            contrib = Contribution.get_record_by_pid(cont_pid)
            # add link <a href="url">link text</a>
            authorized_access_point = contrib.get_authorized_access_point(
                language=language
            )
            contribution_type = 'persons'
            if contrib.get('type') == 'bf:Organisation':
                contribution_type = 'corporate-bodies'
            line = \
                '<a href="/{viewcode}/{c_type}/{pid}">{text}</a>'.format(
                    viewcode=viewcode,
                    c_type=contribution_type,
                    pid=cont_pid,
                    text=authorized_access_point
                )
        else:
            line = create_authorized_access_point(contribution['agent'])

        if role:
            roles = [_(role) for role in contribution.get('role', [])]
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
def part_of_format(part_of):
    """Format 'part of' data for template."""
    document_pid = extracted_data_from_ref(part_of.get('document'), data='pid')
    document = Document.get_record_by_pid(document_pid)
    nums = part_of.get('numbering')
    # Set host document pid
    output = {'document_pid': document_pid}
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
def record_library_pickup_locations(record):
    """Get the pickup locations of the library of the given item or holding."""
    location_pid = extracted_data_from_ref(record.get('location'))
    location = Location.get_record_by_pid(location_pid)
    # Either the location defines some 'restrict_pickup_to' either not.
    # * If 'restrict_pickup_to' is defined, then only these locations are
    #   eligible as possible pickup_locations
    # * Otherwise, get all organisation pickup locations
    #   of the record belongs to
    if 'restrict_pickup_to' in location:
        # Get all pickup locations as Location objects and append it to the
        # location record (removing possible None values)
        pickup_locations = [
            Location.get_record_by_pid(loc_pid)
            for loc_pid in location.restrict_pickup_to
        ]
    else:
        org = Organisation.get_record_by_pid(location.organisation_pid)
        # Get the pickup location from each library of the record organisation
        # (removing possible None value)
        pickup_locations = []
        for library in org.get_libraries():
            for location_pid in list(library.get_pickup_locations_pids()):
                pickup_locations.append(
                    Location.get_record_by_pid(location_pid))

    return sorted(
        list(filter(None, pickup_locations)),
        key=lambda location: location.get('pickup_name', location.get('code'))
    )


@blueprint.app_template_filter()
def work_access_point(work_access_point):
    """Process work access point data."""
    wap = []
    for work in work_access_point:
        agent_formatted = ''
        if 'agent' in work:
            agent = work['agent']
            if agent['type'] == 'bf:Person':
                # Person
                name = []
                if 'preferred_name' in agent:
                    name.append(agent['preferred_name'])
                if 'numeration' in agent:
                    name.append(agent['numeration'])
                elif 'fuller_form_of_name' in agent:
                    name.append(f"({agent['fuller_form_of_name']})")
                if len(name):
                    agent_formatted += f"{', '.join(name)}, "
                if 'numeration' in agent and 'qualifier' in agent:
                    agent_formatted += f"{agent['qualifier']}, "
                dates = [
                    agent[key]
                    for key in ['date_of_birth', 'date_of_death']
                    if key in agent
                ]
                if len(dates):
                    agent_formatted += f"{'-'.join(dates)}. "
                if 'numeration' not in agent and 'qualifier' in agent:
                    agent_formatted += f"{agent['qualifier']}. "
            else:
                # Organisation
                if 'preferred_name' in agent:
                    agent_formatted += agent['preferred_name'] + '. '
                if 'subordinate_unit' in agent:
                    for unit in agent['subordinate_unit']:
                        agent_formatted += unit + '. '
                if 'numbering' in agent or 'conference_date' in agent or \
                   'place' in agent:
                    conf = [
                        agent[key]
                        for key in ['numbering', 'conference_date', 'place']
                    ]
                    if len(conf):
                        agent_formatted += f"({' : '.join(conf)}) "
        agent_formatted += f"{work['title']}. "
        if 'part' in work:
            for part in work['part']:
                for key in ['partNumber', 'partName']:
                    if key in part:
                        agent_formatted += f"{part[key]}. "
        if 'miscellaneous_information' in work:
            agent_formatted += f"{work['miscellaneous_information']}. "
        if 'language' in work:
            agent_formatted += f"{_('lang_'+work['language'])}. "
        if 'medium_of_performance_for_music' in work:
            agent_formatted += \
                f"{'. '.join(work['medium_of_performance_for_music'])}. "
        if 'key_for_music' in work:
            agent_formatted += f"{work['key_for_music']}. "
        if 'arranged_statement_for_music' in work:
            agent_formatted += f"{work['arranged_statement_for_music']}. "
        if 'date_of_work' in work:
            agent_formatted += f"{work['date_of_work']}. "
        wap.append(agent_formatted.strip())
    return wap


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
        'availability': Document.is_available(document_pid, view_code)
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
def get_cover_art(record, save_cover_url=True, verbose=False):
    """Get cover art.

    :param isbn: isbn of document
    :param save_cover_url: save cover url from isbn if no electronicLocator
                           with coverImage exists
    :param verbose: verbose
    :return: url for cover art or None
    """
    # electronicLocator
    for electronic_locator in record.get('electronicLocator', []):
        e_content = electronic_locator.get('content')
        e_type = electronic_locator.get('type')
        if e_content == 'coverImage' and e_type == 'relatedResource':
            return electronic_locator.get('url')
    # ISBN
    isbns = [
        identified_by.get('value')
        for identified_by in record.get('identifiedBy', [])
        if identified_by.get('type') == 'bf:Isbn'
    ]
    for isbn in sorted(isbns):
        isbn_cover = get_remote_cover(isbn)
        if isbn_cover and isbn_cover.get('success'):
            url = isbn_cover.get('image')
            if save_cover_url:
                pid = record.get('pid')
                record_db = Document.get_record_by_pid(pid)
                record_db.add_cover_url(url=url, dbcommit=True, reindex=True)
                msg = f'Add cover art url: {url} do document: {pid}'
                if verbose:
                    click.echo(msg)
            return url


@blueprint.app_template_filter()
def get_other_accesses(record):
    """Length for electronic locator.

    :param record: record
    :return: dictonary list of other access informations
    """
    accesses = []

    def filter_type(electronic_locator):
        """Filter electronic locator for related resources and no info."""
        return electronic_locator.get('type') in [
            'noInfo', 'resource', 'relatedResource', 'versionOfResource'
        ] and electronic_locator.get('content') != 'coverImage'

    filtered_electronic_locators = filter(
        filter_type,
        record.get('electronicLocator', [])
    )
    for electronic_locator in filtered_electronic_locators:
        url = electronic_locator.get('url')
        content = _(electronic_locator.get('content'))
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
def create_title_text(titles, responsibility_statement=None):
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
def create_title_alternate_graphic(titles, responsibility_statement=None):
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


@blueprint.app_template_filter()
def document_types(record, translate: bool = True) -> list[str]:
    """Get document types.

    :param record: record
    :param translate: is document types should be localized
    :return: list of document types
    """
    doc_types = record.document_types  # always a not-empty list
    if translate:
        doc_types = [_(doc_type) for doc_type in doc_types]
    return doc_types


@blueprint.app_template_filter()
def document_main_type(record, translate: bool = True) -> Optional[str]:
    """Get first document main type.

    :param record: record
    :param translate: is the response should be localized
    :return: the document main type
    """
    if 'type' in record:
        doc_type = record['type'][0]['main_type']
        return _(doc_type) if translate else doc_type


@blueprint.app_template_filter()
def get_articles(record):
    """Get articles for serial.

    :return: list of articles with title and pid-
    """
    search = DocumentsSearch() \
        .filter('term', partOf__document__pid=record.get('pid')) \
        .source(['pid', 'title'])
    return [
        {'title': title_format_text_head(hit.title), 'pid': hit.pid}
        for hit in search.scan()
    ]


@blueprint.app_template_filter()
def online_holdings(document_pid, viewcode='global'):
    """Find holdings by document pid and viewcode.

    :param document_pid: document pid
    :param viewcode: symbol of organisation viewcode
    :return: list of holdings
    """
    from ..holdings.api import HoldingsSearch
    organisation = None
    if viewcode != current_app.config.get('RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'):
        organisation = Organisation.get_record_by_viewcode(viewcode)
    query = HoldingsSearch()\
        .filter('term', document__pid=document_pid)\
        .filter('bool', must_not=[Q('term', _masked=True)])

    if organisation:
        query = query.filter('term', organisation__pid=organisation.pid)
    results = query.source(['library', 'electronic_location',
                            'enumerationAndChronology', 'notes']).scan()

    holdings = {}
    for record in results:
        library = Library.get_record_by_pid(record.library.pid)
        library_holdings = holdings.get(library['name'], [])
        record.library.name = library['name']
        public_notes_content = [
            n['content']
            for n in record.to_dict().get('notes', [])
            if n['type'] in HoldingNoteTypes.PUBLIC
        ]
        if public_notes_content:
            record.notes = public_notes_content
        library_holdings.append(record)
        holdings[library['name']] = library_holdings
    return holdings


@blueprint.app_template_filter()
def subject_format(subject_data, language):
    """Format the subject according to the available keys.

    :param subject_data: the record subject.
    :param language: current language on interface.
    """
    try:
        return SubjectFactory \
            .create_subject(subject_data) \
            .render(language=language)
    except (AttributeError, TypeError) as err:
        # print(str(err))
        return 'Subject parsing error !'


@blueprint.app_template_filter()
def series_statement_format(series):
    """Series statement format."""
    return [series_statement_format_text(serie) for serie in series]


@blueprint.app_template_filter()
def main_title_text(title):
    """Extract title with type bf:Title.

    :param title: array of the field title.
    """
    return list(filter(
        lambda t: t.get('type') == 'bf:Title',
        title
    ))
