# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
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
from flask import current_app
from flask import request as flask_request
from invenio_jsonschemas.proxies import current_jsonschemas
from werkzeug.local import LocalProxy

from ..utils import get_schema_for_resource, memoize
from ...utils import get_i18n_supported_languages

_records_state = LocalProxy(lambda: current_app.extensions['invenio-records'])


@memoize(timeout=3600)
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
    from rero_ils.modules.entities.models import EntityType
    if agent.get('type') == EntityType.PERSON:
        date_parts = [agent.get('date_of_birth'), agent.get('date_of_death')]
        date = '-'.join(filter(None, date_parts))
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
    elif agent.get('type') == EntityType.ORGANISATION:
        if subordinate_unit := agent.get('subordinate_unit'):
            authorized_access_point += f'''. {'. '.join(subordinate_unit)}'''
        conference_data = []
        if numbering := agent.get('numbering'):
            conference_data.append(numbering)
        if conference_date := agent.get('conference_date'):
            conference_data.append(conference_date)
        if place := agent.get('place'):
            conference_data.append(place)
        if conference_data:
            authorized_access_point += f' ({" : ".join(conference_data)})'
    return authorized_access_point


def process_i18n_literal_fields(fields):
    """Normalize literal fields."""
    calculated_fields = []
    for field in fields:
        if entity := field.get('entity'):
            entity = process_i18n_literal_entity(entity)
            if subs := entity.pop('subdivisions', []):
                entity['subdivisions'] = process_i18n_literal_fields(subs)
            field['entity'] = entity
        calculated_fields.append(field)
    return calculated_fields


def process_i18n_literal_entity(entity):
    """Normalize literal entity.

    An entity could be linked to a remote $ref, or could be local.
    If entity is related to a $ref, it should be dumped to an appropriate
    dumper method before and should contain all recommended keys to be
    correctly indexed (i18n access point key, variant/parallel title, ...).

    In this method we will focus on 'literal' entity. For such entity, we don't
    have any i18n variant, or parallel/variant title, ... but for a correct
    search results, we need it. So we will build these keys based on the
    default access point.

    :param entity: the entity to transform.
    """
    if entity.get('pid'):
        # in such case, it means that's an entity linked to an `Entity` record.
        # and we don't need to transform it. Just return the current entity
        # without any modifications.
        return entity

    if access_point := entity.pop('authorized_access_point', None):
        # use the encoded access point for all supported languages if the key
        # doesn't already exists for the entity.
        for language in get_i18n_supported_languages():
            key = f'authorized_access_point_{language}'
            if key not in entity:
                entity[key] = access_point
    return entity


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
