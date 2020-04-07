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

"""rero-ils MARC21 model definition."""

import os
import re

import requests
from dojson import utils

from rero_ils.dojson.utils import BookFormatExtraction, ReroIlsMarc21Overdo, \
    TitlePartList, add_note, build_responsibility_data, error_print, \
    extract_subtitle_and_parallel_titles_from_field_245_b, get_field_items, \
    get_field_link_data, make_year, not_repetitive, \
    remove_trailing_punctuation

marc21 = ReroIlsMarc21Overdo()


def get_person_link(bibid, id, key, value):
    """Get MEF person link."""
    # https://mef.test.rero.ch/api/mef/?q=rero.rero_pid:A012327677
    prod_host = 'mef.rero.ch'
    test_host = 'mef.test.rero.ch'
    mef_url = 'https://{host}/api/mef/'.format(host=test_host)
    if os.environ.get('RERO_ILS_MEF_URL'):
        mef_url = os.environ.get('RERO_ILS_MEF_URL')
    mef_link = None
    try:
        identifier = id[1:].split(')')
        url = "{mef}/?q={org}.pid:{pid}".format(
            mef=mef_url,
            org=identifier[0].lower(),
            pid=identifier[1]
        )
        request = requests.get(url=url)
        if request.status_code == requests.codes.ok:
            data = request.json()
            hits = data.get('hits', {}).get('hits')
            if hits:
                mef_link = hits[0].get('links').get('self')
                mef_link = mef_link.replace(test_host, prod_host)
        else:
            error_print('ERROR MEF REQUEST:', bibid, url,
                        request.status_code)
    except Exception as err:
        error_print('WARNING NOT MEF REF:', bibid, id, key, value)
    return mef_link


@marc21.over('type', 'leader')
def marc21_to_type(self, key, value):
    """
    Get document type.

    Books: LDR/6-7: am
    Journals: LDR/6-7: as
    Articles: LDR/6-7: aa + add field 773 (journal title)
    Scores: LDR/6: c|d
    Videos: LDR/6: g + 007/0: m|v
    Sounds: LDR/6: i|j
    E-books (imported from Cantook)
    """
    type = 'other'
    type_of_record = value[6]
    bibliographic_level = value[7]
    if type_of_record == 'a':
        if bibliographic_level == 'm':
            type = 'book'
        elif bibliographic_level == 's':
            type = 'journal'
        elif bibliographic_level == 'a':
            type = 'article'
    elif type_of_record in ['c', 'd']:
        type = 'score'
    elif type_of_record in ['i', 'j']:
        type = 'sound'
    elif type_of_record == 'g':
        type = 'video'
        # Todo 007
    return type


@marc21.over('pid', '^001')
@utils.ignore_value
def marc21_to_pid(self, key, value):
    """Get pid.

    If 001 starts with 'REROILS:' save as pid.
    """
    pid = None
    value = value.strip().split(':')
    if value[0] == 'REROILS':
        pid = value[1]
    return pid


@marc21.over('language', '^008')
@utils.ignore_value
def marc21_to_language(self, key, value):
    """Get languages.

    languages: 008 and 041 [$a, repetitive]
    """
    lang_codes = []
    language = self.get('language', [])
    if marc21.lang_from_008:
        language.append({
            'value': marc21.lang_from_008,
            'type': 'bf:Language'
        })
        lang_codes.append(marc21.lang_from_008)
    for lang_value in marc21.langs_from_041_a:
        if lang_value not in lang_codes:
            language.append({
                'value': lang_value.strip(),
                'type': 'bf:Language'
            })
            lang_codes.append(lang_value)
    # if not language:
    #     error_print('ERROR LANGUAGE:', marc21.bib_id, 'set to "und"')
    #     language = [{'value': 'und', 'type': 'bf:Language'}]
    return language or None


@marc21.over('title', '^245..')
@utils.ignore_value
def marc21_to_title(self, key, value):
    """Get title data.

    The title data are extracted from the following fields:
    field 245:
        $a : non repetitive
        $b : non repetitive
        $c : non repetitive
        $n : repetitive
        $p : repetitive
        $6 : non repetitive
    field 246:
        $a : non repetitive
        $n : repetitive
        $p : repetitive
        $6 : non repetitive
    """
    # extraction and initialization of data for further processing
    subfield_245_a = ''
    subfield_245_b = ''
    fields_245 = marc21.get_fields(tag='245')
    if fields_245:
        subfields_245_a = marc21.get_subfields(fields_245[0], 'a')
        subfields_245_b = marc21.get_subfields(fields_245[0], 'b')
        if subfields_245_a:
            subfield_245_a = subfields_245_a[0]
        if subfields_245_b:
            subfield_245_b = subfields_245_b[0]
    field_245_a_end_with_equal = re.search(r'\s*=\s*$', subfield_245_a)
    field_245_a_end_with_colon = re.search(r'\s*:\s*$', subfield_245_a)
    field_245_a_end_with_semicolon = re.search(r'\s*;\s*$', subfield_245_a)
    field_245_b_contains_equal = re.search(r'=', subfield_245_b)

    fields_246 = marc21.get_fields(tag='246')
    subfield_246_a = ''
    if fields_246:
        subfields_246_a = marc21.get_subfields(fields_246[0], 'a')
        if subfields_246_a:
            subfield_246_a = subfields_246_a[0]

    tag_link, link = get_field_link_data(value)
    items = get_field_items(value)
    index = 1
    title_list = []
    title_data = {}
    part_list = TitlePartList(
                    part_number_code='n',
                    part_name_code='p'
                )
    parallel_titles = []
    pararalel_title_data_list = []
    pararalel_title_string_set = set()
    responsibility = {}

    # parse field 245 subfields for extracting:
    # main title, subtitle, parallel titles and the title parts
    subfield_selection = {'a', 'b', 'c', 'n', 'p'}
    for blob_key, blob_value in items:
        if blob_key in subfield_selection:
            value_data = marc21.build_value_with_alternate_graphic(
                '245', blob_key, blob_value, index, link, ',.', ':;/-=')
            if blob_key in {'a', 'b', 'c'}:
                subfield_selection.remove(blob_key)
            if blob_key == 'a':
                title_data['mainTitle'] = value_data
            elif blob_key == 'b':
                if subfield_246_a:
                    subtitle, parallel_titles, pararalel_title_string_set = \
                        extract_subtitle_and_parallel_titles_from_field_245_b(
                            value_data, field_245_a_end_with_equal)
                    if subtitle:
                        title_data['subtitle'] = subtitle
                elif not subfield_246_a:
                    title_data['subtitle'] = value_data
            elif blob_key == 'c':
                responsibility = build_responsibility_data(value_data)
            elif blob_key in ['n', 'p']:
                part_list.update_part(value_data, blob_key, blob_value)
        if blob_key != '__order__':
            index += 1
    title_data['type'] = 'bf:Title'
    the_part_list = part_list.get_part_list()
    if the_part_list:
        title_data['part'] = the_part_list
    if title_data:
        title_list.append(title_data)
    for parallel_title in parallel_titles:
        title_list.append(parallel_title)

    # extract variant titles
    variant_title_list = \
        marc21.build_variant_title_data(pararalel_title_string_set)
    for variant_title_data in variant_title_list:
        title_list.append(variant_title_data)

    # extract responsibilities
    if responsibility:
        new_responsibility = self.get('responsibilityStatement', [])
        for resp in responsibility:
            new_responsibility.append(resp)
        self['responsibilityStatement'] = new_responsibility
    return title_list or None


@marc21.over('titlesProper', '^730..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_titlesProper(self, key, value):
    """Test dojson marc21titlesProper.

    titleProper: 730$a
    """
    return not_repetitive(marc21.bib_id, key, value, 'a')


@marc21.over('authors', '[17][01]0..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_author(self, key, value):
    """Get author.

    authors: loop:
    authors.name: 100$a [+ 100$b if it exists] or
        [700$a (+$b if it exists) repetitive] or
        [ 710$a repetitive (+$b if it exists, repetitive)]
    authors.date: 100 $d or 700 $d (facultatif)
    authors.qualifier: 100 $c or 700 $c (facultatif)
    authors.type: if 100 or 700 then person, if 710 then organisation
    """
    if not key[4] == '2':
        author = {}
        author['type'] = 'person'
        if value.get('0'):
            refs = utils.force_list(value.get('0'))
            for ref in refs:
                ref = get_person_link(marc21.bib_id, ref, key, value)
                if ref:
                    author['$ref'] = ref
        # we do not have a $ref
        if not author.get('$ref'):
            author['name'] = ''
            if value.get('a'):
                data = not_repetitive(marc21.bib_id, key, value, 'a')
                author['name'] = remove_trailing_punctuation(data)
            author_subs = utils.force_list(value.get('b'))
            if author_subs:
                for author_sub in author_subs:
                    author['name'] += ' ' + \
                        remove_trailing_punctuation(author_sub)
            if key[:3] == '710':
                author['type'] = 'organisation'
            else:
                if value.get('c'):
                    data = not_repetitive(marc21.bib_id, key, value, 'c')
                    author['qualifier'] = remove_trailing_punctuation(data)
                if value.get('d'):
                    data = not_repetitive(marc21.bib_id, key, value, 'd')
                    author['date'] = remove_trailing_punctuation(data)
        return author
    else:
        return None


@marc21.over('copyrightDate', '^264.4')
@utils.ignore_value
def marc21_to_copyright_date(self, key, value):
    """Get Copyright Date."""
    copyright_dates = self.get('copyrightDate', [])
    copyrights_date = utils.force_list(value.get('c'))
    if copyrights_date:
        for copyright_date in copyrights_date:
            match = re.search(r'^([©℗])+\s*(\d{4}.*)', copyright_date)
            if match:
                copyright_date = ' '.join((
                    match.group(1),
                    match.group(2)
                ))
                copyright_dates.append(copyright_date)
            # else:
            #     raise ValueError('Bad format of copyright date')
    return copyright_dates or None


@marc21.over('editionStatement', '^250..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_edition_statement(self, key, value):
    """Get edition statement data.

    editionDesignation: 250 [$a non repetitive] (without trailing /)
    responsibility: 250 [$b non repetitive]
    """
    key_per_code = {
        'a': 'editionDesignation',
        'b': 'responsibility'
    }

    tag_link, link = get_field_link_data(value)
    items = get_field_items(value)
    index = 1
    edition_data = {}
    subfield_selection = {'a', 'b'}
    for blob_key, blob_value in items:
        if blob_key in subfield_selection:
            subfield_selection.remove(blob_key)
            edition_data[key_per_code[blob_key]] = \
                marc21.build_value_with_alternate_graphic(
                    '250', blob_key, blob_value, index, link, ',.', ':;/-=')
        if blob_key != '__order__':
            index += 1
    return edition_data or None


@marc21.over('provisionActivity', '^264.[ 0-3]')
@utils.for_each_value
@utils.ignore_value
def marc21_to_provisionActivity(self, key, value):
    """Get publisher data.

    publisher.name: 264 [$b repetitive] (without the , but keep the ;)
    publisher.place: 264 [$a repetitive] (without the : but keep the ;)
    publicationDate: 264 [$c repetitive] (but take only the first one)
    """
    def build_statement(field_value, ind2):

        def build_agent_data(code, label, index, link):
            type_per_code = {
                'a': 'bf:Place',
                'b': 'bf:Agent'
            }
            agent_data = {
                'type': type_per_code[code],
                'label': [{'value': remove_trailing_punctuation(label)}]
            }
            try:
                alt_gr = marc21.alternate_graphic['264'][link]
                subfield = \
                    marc21.get_subfields(alt_gr['field'])[index]
                agent_data['label'].append({
                    'value': remove_trailing_punctuation(subfield),
                    'language': marc21.get_language_script(
                        alt_gr['script'])
                })
            except Exception as err:
                pass
            return agent_data

        # function build_statement start here
        tag_link, link = get_field_link_data(field_value)
        items = get_field_items(field_value)
        statement = []
        index = 1
        for blob_key, blob_value in items:
            if blob_key in ('a', 'b'):
                agent_data = build_agent_data(
                    blob_key, blob_value, index, link)
                statement.append(agent_data)
            if blob_key != '__order__':
                index += 1
        return statement

    def build_place():
        place = {}
        if marc21.cantons:
            place['canton'] = marc21.cantons[0]
        if marc21.country:
            place['country'] = marc21.country
        if place:
            place['type'] = 'bf:Place'
        return place

    # the function marc21_to_provisionActivity start here
    ind2 = key[4]
    type_per_ind2 = {
        ' ': 'bf:Publication',
        '0': 'bf:Production',
        '1': 'bf:Publication',
        '2': 'bf:Distribution',
        '3': 'bf:Manufacture'
    }
    publication = {
        'type': type_per_ind2[ind2],
        'statement': [],
    }

    subfields_c = utils.force_list(value.get('c'))
    if ind2 in (' ', '1'):
        start_date = make_year(marc21.date1_from_008)
        if start_date:
            publication['startDate'] = start_date
        end_date = make_year(marc21.date2_from_008)
        if end_date:
            publication['endDate'] = end_date
        if (marc21.date_type_from_008 == 'q' or
                marc21.date_type_from_008 == 'n'):
            publication['note'] = 'Date(s) incertaine(s) ou inconnue(s)'
        place = build_place()
        if place:
            publication['place'] = [place]
    publication['statement'] = build_statement(value, ind2)
    if subfields_c:
        subfield_c = subfields_c[0]
        date = {
            'label': [{'value': subfield_c}],
            'type': 'Date'
        }

        tag_link, link = get_field_link_data(value)
        try:
            alt_gr = marc21.alternate_graphic['264'][link]
            subfield = \
                marc21.get_subfields(alt_gr['field'], code='c')
            date['label'].append({
                    'value': subfield[0],
                    'language': marc21.get_language_script(
                        alt_gr['script'])
            })
        except Exception as err:
            pass

        publication['statement'].append(date)
    return publication or None


@marc21.over('extent', '^300..')
@utils.ignore_value
def marc21_to_description(self, key, value):
    """Get physical description.

    Extract:
        - extent
        - duration
        - colorContent
        - productionMethod
        - illustrativeContent
        - note of type otherPhysicalDetails and accompanyingMaterial
        - book_formats
        - dimensions

    300 [$a repetitive]: extent, duration:
    300 [$a non repetitive]: colorContent, productionMethod,
        illustrativeContent, note of type otherPhysicalDetails
    300 [$c repetitive]: dimensions, book_formats
    """
    marc21.extract_description_from_marc_field(key, value, self)
    return None


@marc21.over('series', '^490..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_series(self, key, value):
    """Get series.

    series.name: [490$a repetitive]
    series.number: [490$v repetitive]
    """
    series = {}
    name = value.get('a')
    if name:
        series['name'] = ', '.join(utils.force_list(name))
    number = value.get('v')
    if number:
        series['number'] = ', '.join(utils.force_list(number))
    return series


@marc21.over('abstracts', '^520..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_abstracts(self, key, value):
    """Get abstracts.

    abstract: [520$a repetitive]
    """
    abstracts = None
    if value.get('a'):
        abstracts = ', '.join(utils.force_list(value.get('a')))
    return abstracts


@marc21.over('identifiedBy', '^020..')
@utils.ignore_value
def marc21_to_identifiedBy_from_field_020(self, key, value):
    """Get identifier from field 020."""
    def build_identifier_from(subfield_data, status=None):
        subfield_data = subfield_data.strip()
        identifier = {'value': subfield_data}
        subfield_c = not_repetitive(
            marc21.bib_id, key, value, 'c', default='').strip()
        if subfield_c:
            identifier['acquisitionTerms'] = subfield_c
        if value.get('q'):  # $q is repetitive
            identifier['qualifier'] = \
                ', '.join(utils.force_list(value.get('q')))

        match = re.search(r'^(.+?)\s*\((.+)\)$', subfield_data)
        if match:
            # match.group(2) : parentheses content
            identifier['qualifier'] = ', '.join(
                filter(
                    None,
                    [match.group(2), identifier.get('qualifier', '')]
                )
            )
            # value without parenthesis and parentheses content
            identifier['value'] = match.group(1)
        if status:
            identifier['status'] = status
        identifier['type'] = 'bf:Isbn'
        identifiedBy.append(identifier)

    identifiedBy = self.get('identifiedBy', [])
    subfield_a = not_repetitive(marc21.bib_id, key, value, 'a')
    if subfield_a:
        build_identifier_from(subfield_a)
    subfields_z = value.get('z')
    if subfields_z:
        for subfield_z in utils.force_list(subfields_z):
            build_identifier_from(subfield_z, status='invalid or cancelled')
    return identifiedBy or None


@marc21.over('identifiedBy', '^022..')
@utils.ignore_value
def marc21_to_identifiedBy_from_field_022(self, key, value):
    """Get identifier from field 022."""
    status_for = {
        'm': 'cancelled',
        'y': 'invalid'
    }
    type_for = {
        'a': 'bf:Issn',
        'l': 'bf:IssnL',
        'm': 'bf:IssnL',
        'y': 'bf:Issn'
    }

    identifiedBy = self.get('identifiedBy', [])
    for subfield_code in ['a', 'l', 'm', 'y']:
        subfields_data = value.get(subfield_code)
        if subfields_data:
            if isinstance(subfields_data, str):
                subfields_data = [subfields_data]
            for subfield_data in subfields_data:
                subfield_data = subfield_data.strip()
                identifier = {}
                identifier['type'] = type_for[subfield_code]
                identifier['value'] = subfield_data
                if subfield_code in status_for:
                    identifier['status'] = status_for[subfield_code]
                identifiedBy.append(identifier)
    return identifiedBy or None


@marc21.over('identifiedBy', '^024..')
@utils.ignore_value
def marc21_to_identifiedBy_from_field_024(self, key, value):
    """Get identifier from field 024."""
    def populate_acquisitionTerms_note_qualifier(identifier):
        subfield_c = not_repetitive(
            marc21.bib_id, key, value, 'c', default='').strip()
        if subfield_c:
            identifier['acquisitionTerms'] = subfield_c
        subfield_d = not_repetitive(
            marc21.bib_id, key, value, 'd', default='').strip()
        if subfield_d:
            identifier['note'] = subfield_d
        if value.get('q'):  # $q is repetitive
            identifier['qualifier'] = \
                ', '.join(utils.force_list(value.get('q')))

    subfield_2_regexp = {
        'doi': {
            'type': 'bf:Doi'
        },
        'urn': {
            'type': 'bf:Urn'
        },
        'nipo': {
            'type': 'bf:Local',
            'source': 'NIPO'
        },
        'danacode': {
            'type': 'bf:Local',
            'source': 'danacode'
        },
        'vd18': {
            'type': 'bf:Local',
            'source': 'vd18'
        },
        'gtin-14': {
            'type': 'bf:Gtin14Number'
        }
    }

    type_for_ind1 = {
        '0': {'type': 'bf:Isrc'},
        '1': {'type': 'bf:Upc'},
        '2': {
            'pattern': r'^(M|9790|979-0)',
            'matching_type': 'bf:Ismn'
        },
        '3': {
            'pattern': r'^97',
            'matching_type': 'bf:Ean'
        },
        '8': {
            # 33 chars example: 0000-0002-A3B1-0000-0-0000-0000-2
            'pattern': r'^(.{24}|.{26}|(.{4}-){4}.-(.{4}\-){2}.)$',
            'matching_type': 'bf:Isan'
        }
    }

    identifier = {}
    subfield_a = not_repetitive(
        marc21.bib_id, key, value, 'a', default='').strip()
    subfield_2 = not_repetitive(
        marc21.bib_id, key, value, '2', default='').strip()
    if subfield_a:
        if re.search(r'permalink\.snl\.ch', subfield_a, re.IGNORECASE):
            identifier.update({
                'value': subfield_a,
                'type': 'uri',
                'source': 'SNL'
            })
        elif re.search(r'bnf\.fr/ark', subfield_a, re.IGNORECASE):
            identifier.update({
                'value': subfield_a,
                'type': 'uri',
                'source': 'BNF'
            })
        elif subfield_2:
            identifier['value'] = subfield_a
            populate_acquisitionTerms_note_qualifier(identifier)
            for pattern in subfield_2_regexp:
                if re.search(pattern, subfield_2, re.IGNORECASE):
                    identifier.update(subfield_2_regexp[pattern])
        else:  # without subfield $2
            ind1 = key[3]  # indicateur_1
            if ind1 in ('0', '1', '2', '3', '8'):
                populate_acquisitionTerms_note_qualifier(identifier)
                match = re.search(r'^(.+?)\s*\((.*)\)$', subfield_a)
                if match:
                    # match.group(2) : parentheses content
                    identifier['qualifier'] = ', '.join(
                        filter(
                            None,
                            [match.group(2), identifier.get('qualifier', '')]
                        )
                    )
                    # value without parenthesis and parentheses content
                    identifier['value'] = match.group(1)
                else:
                    identifier['value'] = subfield_a
                if 'type' in type_for_ind1[ind1]:  # ind1 0,1
                    identifier['type'] = type_for_ind1[ind1]['type']
                else:  # ind1 in (2, 3, 8)
                    data = subfield_a
                    if ind1 == '8':
                        data = identifier['value']
                    if re.search(type_for_ind1[ind1]['pattern'], data):
                        identifier['type'] = \
                            type_for_ind1[ind1]['matching_type']
                    else:
                        identifier['type'] = 'bf:Identifier'
            else:  # ind1 not in (0, 1, 2, 3, 8)
                identifier.update({
                    'value': subfield_a,
                    'type': 'bf:Identifier'
                })
        identifiedBy = self.get('identifiedBy', [])
        if not identifier.get('type'):
            identifier['type'] = 'bf:Identifier'
        identifiedBy.append(identifier)
    return identifiedBy or None


@marc21.over('identifiedBy', '^028..')
@utils.ignore_value
def marc21_to_identifiedBy_from_field_028(self, key, value):
    """Get identifier from field 028."""
    type_for_ind1 = {
        '0': 'bf:AudioIssueNumber',
        '1': 'bf:MatrixNumber',
        '2': 'bf:MusicPlate',
        '3': 'bf:MusicPublisherNumber',
        '4': 'bf:VideoRecordingNumber',
        '5': 'bf:PublisherNumber',
        '6': 'bf:MusicDistributorNumber'
    }

    identifier = {}
    subfield_a = not_repetitive(
        marc21.bib_id, key, value, 'a', default='').strip()
    if subfield_a:
        identifier['value'] = subfield_a
        if value.get('q'):  # $q is repetitive
            identifier['qualifier'] = \
                ', '.join(utils.force_list(value.get('q')))
        subfield_b = not_repetitive(
            marc21.bib_id, key, value, 'b', default='').strip()
        if subfield_b:
            identifier['source'] = subfield_b
        # key[3] is the indicateur_1
        identifier['type'] = type_for_ind1.get(key[3], 'bf:Identifier')
        identifiedBy = self.get('identifiedBy', [])
        identifiedBy.append(identifier)
    return identifiedBy or None


@marc21.over('identifiedBy', '^035..')
@utils.ignore_value
def marc21_to_identifiedBy_from_field_035(self, key, value):
    """Get identifier from field 035."""
    subfield_a = not_repetitive(
        marc21.bib_id, key, value, 'a', default='').strip()
    if subfield_a:
        identifier = {
            'value': subfield_a,
            'type': 'bf:Local',
            'source': 'RERO'
        }
        identifiedBy = self.get('identifiedBy', [])
        identifiedBy.append(identifier)
    return identifiedBy or None


@marc21.over('electronicLocator', '^856..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_electronicLocator_from_field_856(self, key, value):
    """Get electronicLocator from field 856."""
    electronic_locator_type = {
        '0': 'resource',
        '1': 'versionOfResource',
        '2': 'relatedResource',
        '8': 'hiddenUrl'
    }
    electronic_locator_content = [
        'poster',
        'audio',
        'postcard',
        'addition',
        'debriefing',
        'exhibitionDocumentation',
        'erratum',
        'bookplate',
        'extract',
        'educationalSheet',
        'illustrations',
        'coverImage',
        'deliveryInformation',
        'biographicalInformation',
        'introductionPreface',
        'classReading',
        "teachersKit",
        "publishersNote",
        'noteOnContent',
        'titlePage',
        'photography',
        'summarization'
        "summarization",
        "onlineResourceViaRERODOC",
        "pressReview",
        "webSite",
        "tableOfContents",
        "fullText",
        "video"
    ]
    indicator2 = key[4]
    electronic_locator = {
        'url': value.get('u'),
        'type': electronic_locator_type.get(indicator2, 'noInfo')
    }
    content = value.get('3')
    public_note = []
    if content:
        if content in electronic_locator_content:
            electronic_locator['content'] = content
        else:
            public_note.append(content)
    if value.get('z'):
        public_note += utils.force_list(value.get('z'))
        electronic_locator['publicNote'] = public_note
    return electronic_locator


@marc21.over('identifiedBy', '^930..')
@utils.ignore_value
def marc21_to_identifiedBy_from_field_930(self, key, value):
    """Get identifier from field 930."""
    subfield_a = not_repetitive(
        marc21.bib_id, key, value, 'a', default='').strip()
    if subfield_a:
        identifier = {}
        match = re.search(r'^\((.+?)\)\s*(.*)$', subfield_a)
        if match:
            # match.group(1) : parentheses content
            identifier['source'] = match.group(1)
            # value without parenthesis and parentheses content
            identifier['value'] = match.group(2)
        else:
            identifier['value'] = subfield_a
        identifier['type'] = 'bf:Local'
        identifiedBy = self.get('identifiedBy', [])
        identifiedBy.append(identifier)
    return identifiedBy or None


@marc21.over('note', '^500..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_notes(self, key, value):
    """Get  notes.

    note: [500$a repetitive]
    """
    add_note(
        dict(
            noteType='general',
            label=not_repetitive(marc21.bib_id, key, value, 'a')
        ),
        self)

    return None


@marc21.over('is_part_of', '^773..')
@utils.ignore_value
def marc21_to_is_part_of(self, key, value):
    """Get  is_part_of.

    is_part_of: [773$t repetitive]
    """
    if not self.get('is_part_of', None):
        return not_repetitive(marc21.bib_id, key, value, 't')


@marc21.over('subjects', '^6....')
@utils.for_each_value
@utils.ignore_value
def marc21_to_subjects(self, key, value):
    """Get subjects.

    subjects: 6xx [duplicates could exist between several vocabularies,
        if possible deduplicate]
    """
    return value.get('a')
