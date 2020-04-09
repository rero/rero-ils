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

import re

from elasticsearch_dsl.utils import AttrDict

from .dojson.contrib.marc21tojson.model import remove_trailing_punctuation


def localized_data_name(data, language):
    """Get localized name."""
    return data.get(
        'name_{language}'.format(language=language),
        data.get('name', '')
    )


def clean_text(data):
    """Delete all _text from data."""
    if isinstance(data, list):
        new_val = []
        for val in data:
            new_val.append(clean_text(val))
        data = new_val
    elif isinstance(data, dict):
        if '_text' in data:
            del data['_text']
        new_data = {}
        for key, val in data.items():
            new_data[key] = clean_text(val)
        data = new_data
    return data


def publication_statement_text(provision_activity):
    """Create publication statement from place, agent and date values."""
    punctuation = {
        'bf:Place': ' ; ',
        'bf:Agent': ', '
    }

    statement_with_language = {'default': ''}
    statement_type = None

    for statement in provision_activity['statement']:
        labels = statement['label']

        for label in labels:
            language = label.get('language', 'default')

            if not statement_with_language.get(language):
                statement_with_language[language] = ''

            if statement_with_language[language]:
                if statement_type == statement['type']:
                    statement_with_language[language] += punctuation[
                        statement_type
                    ]
                else:
                    if statement['type'] == 'bf:Place':
                        statement_with_language[language] += ' ; '
                    elif statement['type'] == 'Date':
                        statement_with_language[language] += ', '
                    else:
                        statement_with_language[language] += ' : '

            statement_with_language[language] += label['value']
        statement_type = statement['type']

    # date field: remove ';' and append
    statement_text = []
    for key, value in statement_with_language.items():
        value = remove_trailing_punctuation(value)
        if display_alternate_graphic_first(key):
            statement_text.insert(0, {'value': value, 'language': key})
        else:
            statement_text.append({'value': value, 'language': key})
    return statement_text


def series_format_text(serie):
    """Format series for template."""
    output = []
    if serie.get('name'):
        output.append(serie.get('name'))
    if serie.get('number'):
        output.append(', ' + serie.get('number'))
    return ''.join(str(x) for x in output)


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


def title_format_text_head(titles, with_subtitle=True):
    """Format title head for display purpose.

    :param titles: titles object list
    :type titles: JSON object list
    :param with_subtitle: `True` for including the subtitle in the output
    :type with_subtitle: bool, optional
    :return: a title string formated for display purpose
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
                for title_text in title_texts:
                    language = title_text.get('language')
                    if display_alternate_graphic_first(language):
                        head_titles.append(title_text.get('value'))
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
    return output_value


def title_format_text_alternate_graphic(titles):
    """Build a list of alternate graphic title text for display.

    :param titles: titles object list
    :type titles: JSON object list
    :return: a list of alternate graphic title string formated for display
    :rtype: list
    """
    altgr_titles = {}
    parallel_titles = {}
    for title in titles:
        if title.get('type') == 'bf:Title':
            title_texts = \
                title_format_text(title=title, with_subtitle=True)
            # the first title is remove because it is alreday used for the
            # headding tilte
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
            # the first parallel title is remove because it is alreday used
            # for the headding tilte
            for parallel_title_text in parallel_title_texts:
                language = parallel_title_text.get('language')
                if language in parallel_titles:
                    parallel_titles.get(language, [])
                    parallel_titles[language].append(
                        parallel_title_text.get('value')
                    )
    output = []
    for language in altgr_titles.keys():
        altgr_text = '. '.join(altgr_titles[language])
        if language in parallel_titles:
            parallel_title_text = ' = '.join(parallel_titles[language])
            altgr_text += ' = ' + str(parallel_title_text)
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
    main_titles = title.get('mainTitle', [])
    subtitles = title.get('subtitle', [])

    # build main_title string per language
    main_title_output = {}
    for main_title in main_titles:
        language = main_title.get('language', 'default')
        value = main_title.get('value', '')
        main_title_output[language] = value

    # build subtitle string per language
    subtitle_output = {}
    if with_subtitle:
        subtitles = title.get('subtitle', [])
        for subtitle in subtitles:
            language = subtitle.get('language', 'default')
            value = subtitle.get('value', '')
            subtitle_output[language] = value

    # build part strings per language
    parts = title.get('part', [])
    part_output = {}
    for part in parts:
        part_strings = {}
        language = 'default'
        for part_key in ('partNumber', 'partName'):
            if part_key in part:
                for part_data in part[part_key]:
                    language = part_data.get('language', 'default')
                    value = part_data.get('value', '')
                    if value:
                        if language not in part_strings:
                            part_strings[language] = []
                        part_strings[language].append(value)
        for language in part_strings:
            part_output[language] = ', '.join(part_strings[language])

    # build title text strings lists,
    # if a vernacular title exists it will be place on top of the title list
    title_text = []
    for key, value in main_title_output.items():
        value = main_title_output.get(key)
        if subtitle_output and with_subtitle and key in subtitle_output:
            value = ' : '.join((value, subtitle_output.get(key)))
        if part_output and key in part_output and part_output.get(key):
            value = '. '.join((value, part_output.get(key)))
        if display_alternate_graphic_first(key):
            title_text.insert(0, {'value': value, 'language': key})
        else:
            title_text.append({'value': value, 'language': key})
    return title_text
