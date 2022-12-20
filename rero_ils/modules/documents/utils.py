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

"""Documents utils."""

from __future__ import absolute_import, print_function

import json
import re

import requests
from elasticsearch_dsl.utils import AttrDict
from flask import current_app
from flask import request as flask_request
from invenio_jsonschemas.proxies import current_jsonschemas
from werkzeug.local import LocalProxy

from rero_ils.dojson.utils import remove_trailing_punctuation

from ..utils import get_schema_for_resource, memoized
from ...utils import get_i18n_supported_languages

_records_state = LocalProxy(lambda: current_app.extensions['invenio-records'])


@memoized(timeout=3600)
def get_document_types_from_schema(schema='doc'):
    """Create document type definition from schema."""
    path = current_jsonschemas.url_to_path(get_schema_for_resource(schema))
    schema = current_jsonschemas.get_schema(path=path)
    schema = _records_state.replace_refs(schema)
    schema_types = schema\
        .get('properties', {})\
        .get('type', {})\
        .get('items', {})\
        .get('oneOf', [])
    doc_types = {}
    for schema_type in schema_types:
        schema_title = schema_type['title']
        sub_types = schema_type\
            .get('properties', {})\
            .get('subtype', {})\
            .get('enum', [])
        doc_types[schema_title] = {sub_type: True for sub_type in sub_types}
    return doc_types


def filter_document_type_buckets(buckets):
    """Removes unwanted subtypes from `document_type` buckets."""
    # TODO :: write an unitest
    if doc_types := get_document_types_from_schema():
        if buckets:
            for term in buckets:
                main_type = term['key']
                term['document_subtype']['buckets'] = [
                    subtype_bucket
                    for subtype_bucket in term['document_subtype']['buckets']
                    if doc_types.get(main_type, {}).get(subtype_bucket['key'])
                ]


def clean_text(data):
    """Delete all _text from data."""
    if isinstance(data, list):
        data = [clean_text(val) for val in data]
    elif isinstance(data, dict):
        if '_text' in data:
            del data['_text']
        data = {key: clean_text(val) for key, val in data.items()}
    return data


def publication_statement_text(provision_activity):
    """Create publication statement from place, agent and date values."""
    punctuation = {
        'bf:Place': ' ; ',
        'bf:Agent': ' ; ',
        'Date': ', '
    }
    statement_with_language = {'default': ''}
    last_statement_type = None
    # Perform each statement entries to build the best possible string
    for statement in provision_activity.get('statement', []):
        for label in statement['label']:
            language = label.get('language', 'default')
            statement_with_language.setdefault(language, '')
            if statement_with_language[language]:
                if last_statement_type == statement['type']:
                    statement_with_language[language] += punctuation[
                        last_statement_type
                    ]
                elif statement['type'] == 'bf:Place':
                    statement_with_language[language] += ' ; '
                elif statement['type'] == 'Date':
                    statement_with_language[language] += ', '
                else:
                    statement_with_language[language] += ' : '

            statement_with_language[language] += label['value']
        last_statement_type = statement['type']
    # date field: remove ';' and append
    statement_text = []
    for key, value in statement_with_language.items():
        value = remove_trailing_punctuation(value)
        if display_alternate_graphic_first(key):
            statement_text.insert(0, {'value': value, 'language': key})
        else:
            statement_text.append({'value': value, 'language': key})
    return statement_text


def series_statement_format_text(serie_statement):
    """Format series statement for template."""
    def get_title_language(data):
        """Get title and language."""
        output = {}
        for value in data:
            language = value.get('language', 'default')
            title = value.get('value', '')
            language_title = output.get(language, [])
            language_title.append(title)
            output[language] = language_title
        return output

    serie_title = get_title_language(serie_statement.get('seriesTitle', []))
    serie_enum = get_title_language(
        serie_statement.get('seriesEnumeration', [])
    )
    subserie_data = []
    for subserie in serie_statement.get('subseriesStatement', []):
        subserie_title = get_title_language(subserie.get('subseriesTitle', []))
        subserie_enum = get_title_language(
            subserie.get('subseriesEnumeration', [])
        )
        subserie_data.append({'title': subserie_title, 'enum': subserie_enum})

    intermediate_output = {}
    for key, value in serie_title.items():
        intermediate_output[key] = ', '.join(value)
    for key, value in serie_enum.items():
        value = ', '.join(value)
        intermediate_value = intermediate_output.get(key, '')
        intermediate_value = f'{intermediate_value}; {value}'
        intermediate_output[key] = intermediate_value
    for intermediate_subserie in subserie_data:
        for key, value in intermediate_subserie.get('title', {}).items():
            value = ', '.join(value)
            intermediate_value = intermediate_output.get(key, '')
            intermediate_value = f'{intermediate_value}. {value}'
            intermediate_output[key] = intermediate_value
        for key, value in subserie_enum.items():
            value = ', '.join(value)
            intermediate_value = intermediate_output.get(key, '')
            intermediate_value = f'{intermediate_value}; {value}'
            intermediate_output[key] = intermediate_value

    serie_statement_text = []
    for key, value in intermediate_output.items():
        if display_alternate_graphic_first(key):
            serie_statement_text.insert(0, {'value': value, 'language': key})
        else:
            serie_statement_text.append({'value': value, 'language': key})

    return serie_statement_text


def edition_format_text(edition):
    """Format edition for _text."""
    designations = edition.get('editionDesignation', [])
    responsibilities = edition.get('responsibility', [])
    designation_output = {}
    for designation in designations:
        language = designation.get('language', 'default')
        value = designation.get('value', '')
        designation_output[language] = value
    responsibility_output = {}
    for responsibility in responsibilities:
        language = responsibility.get('language', 'default')
        value = responsibility.get('value', '')
        responsibility_output[language] = value

    edition_text = []
    for key, value in designation_output.items():
        value = remove_trailing_punctuation(
            '{designation} / {responsibility}'.format(
                designation=designation_output.get(key),
                responsibility=responsibility_output.get(key, ''),
            )
        )
        if display_alternate_graphic_first(key):
            edition_text.insert(0, {'value': value, 'language': key})
        else:
            edition_text.append({'value': value, 'language': key})

    return edition_text


def display_alternate_graphic_first(language):
    """Display alternate graphic first.

    This function return true if the given language code is corresponding
    to an alternate graphic value to display first

    :param language: language code
    :type language: str
    :return: true if the alternate graphic value must be display first
    :rtype: bool
    """
    return not re.search(r'(default|^und-|-zyyy$)', language)


def title_format_text_head(titles, responsabilities=None, with_subtitle=True):
    """Format title head for display purpose.

    :param titles: titles object list
    :type titles: JSON object list
    :param with_subtitle: `True` for including the subtitle in the output
    :type with_subtitle: bool, optional
    :return: a title string formatted for display purpose
    :rtype: str
    """
    head_titles = []
    parallel_titles = []
    for title in titles:
        if isinstance(title, AttrDict):
            # force title to dict because ES gives AttrDict
            title = title.to_dict()
        title = dict(title)
        if title.get('type') == 'bf:Title':
            title_texts = \
                title_format_text(title=title, with_subtitle=with_subtitle)
            if len(title_texts) == 1:
                head_titles.append(title_texts[0].get('value'))
            else:
                languages = [title.get('language') for title in title_texts]

                def filter_list(value):
                    """Check if a value should be removed from the languages.

                    :returns: True if the language type is latin and a
                              vernacular from exits
                    """
                    # keep simple language such as `default`
                    if '-' not in value:
                        return True
                    lang, charset = value.split('-')
                    # remove the latin form if a vernacular form exists
                    if value.endswith('-latn') and sum(
                            v.startswith(f'{lang}-') for v in languages) > 1:
                        return False
                    return True
                # list of selected language
                filtered_languages = list(filter(filter_list, languages))

                for title_text in title_texts:
                    language = title_text.get('language')
                    if language not in filtered_languages:
                        continue
                    if display_alternate_graphic_first(language):
                        head_titles.append(title_text.get('value'))
                # If I don't have a title available,
                # I get the last value of the array
                if not len(head_titles):
                    head_titles.append(title_texts[-1].get('value'))
        elif title.get('type') == 'bf:ParallelTitle':
            parallel_title_texts = title_format_text(
                title=title, with_subtitle=with_subtitle)
            if len(parallel_title_texts) == 1:
                parallel_titles.append(parallel_title_texts[0].get('value'))
            else:
                for parallel_title_text in parallel_title_texts:
                    language = parallel_title_text.get('language')
                    if display_alternate_graphic_first(language):
                        parallel_titles.append(
                            parallel_title_text.get('value')
                        )
    output_value = '. '.join(head_titles)
    for parallel_title in parallel_titles:
        output_value += ' = ' + str(parallel_title)
    responsabilities = responsabilities or []
    for responsibility in responsabilities:
        if len(responsibility) == 1:
            output_value += ' / ' + responsibility[0].get('value')
        else:
            for responsibility_language in responsibility:
                value = responsibility_language.get('value')
                language = responsibility_language.get('language', 'default')
                if display_alternate_graphic_first(language):
                    output_value += ' / ' + value
    return output_value


def title_format_text_alternate_graphic(titles, responsabilities=None):
    """Build a list of alternate graphic title text for display.

    :param titles: titles object list
    :type titles: JSON object list
    :return: a list of alternate graphic title string formatted for display
    :rtype: list
    """
    altgr_titles = {}
    parallel_titles = {}
    for title in titles:
        if title.get('type') == 'bf:Title':
            title_texts = \
                title_format_text(title=title, with_subtitle=True)
            # the first title is remove because it is already used for the
            # heading title
            title_texts.pop(0)
            for title_text in title_texts:
                language = title_text.get('language')
                altgr = altgr_titles.get(language, [])
                altgr.append(title_text.get('value'))
                altgr_titles[language] = altgr
        elif title.get('type') == 'bf:ParallelTitle':
            parallel_title_texts = title_format_text(
                title=title, with_subtitle=True)
            parallel_title_texts.pop(0)
            # the first parallel title is removed because it is already used
            # for the heading title
            for parallel_title_text in parallel_title_texts:
                language = parallel_title_text.get('language')
                parallel_title = parallel_titles.get(language, [])
                parallel_title.append(parallel_title_text.get('value'))
                parallel_titles[language] = parallel_title
                # if language in parallel_titles:
                #     parallel_titles.get(language, [])
                #     parallel_titles[language].append(
                #         parallel_title_text.get('value')
                #     )
    responsibilities_text = {}
    responsabilities = responsabilities or []
    for responsibility in responsabilities:
        for responsibility_language in responsibility:
            language = responsibility_language.get('language', 'default')
            responsibility_text = responsibilities_text.get(language, [])
            responsibility_text.append(responsibility_language.get('value'))
            responsibilities_text[language] = responsibility_text

    output = []
    for language in altgr_titles:
        altgr_text = '. '.join(altgr_titles[language])
        if language in parallel_titles:
            parallel_title_text = ' = '.join(parallel_titles[language])
            altgr_text += ' = ' + str(parallel_title_text)
        if language in responsibilities_text:
            responsibility_text = ' / '.join(responsibilities_text[language])
            altgr_text += ' / ' + str(responsibility_text)

        output.append({'value': altgr_text, 'language': language})
    return output


def title_variant_format_text(titles, with_subtitle=True):
    """Build a list of variant titles in the display text form.

    If a vernacular variant exists it will be place on top of the variant list.
    :param titles: list of titles in JSON
    :param with_subtitle: TRUE for including the subtitle in the output
    :return: a list of variant titles in text format
    """
    variant_title_texts = []
    for title in titles:
        if title.get('type') == 'bf:VariantTitle':
            title_texts = \
                title_format_text(title=title, with_subtitle=with_subtitle)
            variant_title_texts.extend(title_texts)
    return variant_title_texts


def title_format_text(title, with_subtitle=True):
    """Build a list of titles in the display text form.

    If a vernacular title exists it will be place on top of the title list.
    :param title: title in JSON
    :param with_subtitle: TRUE for including the subtitle in the output
    :return: a list of titles in the display text form
    :rtype: list
    """
    # build main_title string per language
    main_title_output = {}
    for main_title in title.get('mainTitle', []):
        language = main_title.get('language', 'default')
        value = main_title.get('value', '')
        main_title_output.setdefault(language, []).append(value)

    # build subtitle string per language
    subtitle_output = {}
    if with_subtitle:
        subtitles = title.get('subtitle', [])
        for subtitle in subtitles:
            language = subtitle.get('language', 'default')
            value = subtitle.get('value', '')
            subtitle_output.setdefault(language, []).append(value)

    # build part strings per language
    part_output = {}
    for part in title.get('part', []):
        data = {}
        # part number first
        for part_type in ['partNumber', 'partName']:
            part_type_values = part.get(part_type, {})
            # again repeatable
            for part_type_value in part_type_values:
                language = part_type_value.get('language', 'default')
                if value := part_type_value.get('value'):
                    data.setdefault(language, []).append(value)
        # each part number and part name are separate by a comma
        for key, value in data.items():
            part_output.setdefault(key, []).append(', '.join(value))
    # each part are separate by a point
    part_output = {
        key: '. '.join(values)
        for key, values in part_output.items()
    }
    # build title text strings lists,
    # if a vernacular title exists it will be place on top of the title list
    title_text = []
    for language, main_title in main_title_output.items():
        text = '. '.join(main_title)
        if language in subtitle_output:
            subtitle_text = ' : '.join(subtitle_output[language])
            text = f'{text} : {subtitle_text}'
        if language in part_output:
            text = f'{text}. {part_output[language]}'
        data = {'value': text, 'language': language}
        if display_alternate_graphic_first(language):
            title_text.insert(0, data)
        else:
            title_text.append(data)
    return title_text


def create_authorized_access_point(agent):
    """Create the authorized_access_point for an agent.

    :param agent: Agent to create the authorized_access_point for.
    :returns: authorized access point.
    """
    if not agent:
        return None
    authorized_access_point = agent.get('preferred_name')
    from ..contributions.models import ContributionType
    if agent.get('type') == ContributionType.PERSON:
        date_of_birth = agent.get('date_of_birth')
        date_of_death = agent.get('date_of_death')
        date = date_of_birth or ''
        if date_of_death:
            date += f'-{date_of_death}'
        numeration = agent.get('numeration')
        fuller_form_of_name = agent.get('fuller_form_of_name')
        qualifier = agent.get('qualifier')

        if numeration:
            authorized_access_point += f' {numeration}'
            if qualifier:
                authorized_access_point += f', {qualifier}'
            if date:
                authorized_access_point += f', {date}'
        else:
            if fuller_form_of_name:
                authorized_access_point += f' ({fuller_form_of_name})'
            if date:
                authorized_access_point += f', {date}'
            if qualifier:
                authorized_access_point += f', {qualifier}'
    elif agent.get('type') == ContributionType.ORGANISATION:
        subordinate_unit = agent.get('subordinate_unit')
        if subordinate_unit:
            authorized_access_point += f'''. {'. '.join(subordinate_unit)}'''
        conference_data = []
        numbering = agent.get('numbering')
        if numbering:
            conference_data.append(numbering)
        conference_date = agent.get('conference_date')
        if conference_date:
            conference_data.append(conference_date)
        place = agent.get('place')
        if place:
            conference_data.append(place)
        if conference_data:
            authorized_access_point += ' ({conference})'.format(
                conference=' : '.join(conference_data)
            )
    return authorized_access_point


def create_contributions(contributions):
    """Create contribution."""
    from ..contributions.api import Contribution
    calculated_contributions = []
    for contribution in contributions:
        cont_pid = contribution['agent'].get('pid')
        if cont_pid:
            contrib = Contribution.get_record_by_pid(cont_pid)
            if contrib:
                contribution['agent'] = contrib.dumps_for_document()
        else:
            # transform local data for indexing
            agent = {
                'type': contribution['agent']['type'],
                'preferred_name': contribution['agent']['preferred_name'],
            }
            authorized_access_point = create_authorized_access_point(
                contribution['agent']
            )
            agent['authorized_access_point'] = authorized_access_point
            for language in get_i18n_supported_languages():
                agent[f'authorized_access_point_{language}'] = \
                    authorized_access_point
            variant_access_point = contribution['agent'].get(
                'variant_access_point')
            if variant_access_point:
                agent['variant_access_point'] = variant_access_point
            parallel_access_point = contribution['agent'].get(
                'parallel_access_point')
            if parallel_access_point:
                agent['parallel_access_point'] = parallel_access_point
            if contribution['agent'].get('identifiedBy'):
                agent['identifiedBy'] = contribution['agent']['identifiedBy']
            contribution['agent'] = agent

        calculated_contributions.append(contribution)
    return calculated_contributions


def get_remote_cover(isbn):
    """Document cover service."""
    if not isbn:
        return None
    cover_service = current_app.config.get('RERO_ILS_THUMBNAIL_SERVICE_URL')
    url = f'{cover_service}' \
        '?height=244px' \
        '&width=244px' \
        '&jsonpCallbackParam=callback' \
        '&callback=thumb' \
        '&type=isbn' \
        f'&value={isbn}'
    try:
        host_url = flask_request.host_url
    except Exception:
        host_url = current_app.config.get('RERO_ILS_APP_URL', '??')
        if host_url[-1] != '/':
            host_url = f'{host_url}/'
    response = requests.get(url, headers={'referer': host_url})
    if response.status_code != 200:
        msg = f'Unable to get cover for isbn: {isbn} {response.status_code}'
        current_app.logger.debug(msg)
        return None
    result = json.loads(response.text[len('thumb('):-1])
    if result['success']:
        return result
    current_app.logger.debug(f'Unable to get cover for isbn: {isbn}')
