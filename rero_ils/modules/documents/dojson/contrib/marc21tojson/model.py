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

from rero_ils.dojson.utils import ReroIlsMarc21Overdo, error_print, \
    get_field_items, get_field_link_data, make_year, not_repetitive, \
    remove_trailing_punctuation

marc21tojson = ReroIlsMarc21Overdo()


def get_language_script(script):
    """Build the language script code.

    This code is built according to the format
    <lang_code>-<script_code> for example: chi-hani;
    the <lang_code> is retrived from field 008 and 041
    the <script_code> is received as parameter
    """
    languages_scripts = {
        'arab': ('ara', 'per'),
        'cyrl': ('bel', 'chu', 'mac', 'rus', 'srp', 'ukr'),
        'grek': ('grc', 'gre'),
        'hani': ('chi', 'jpn'),
        'hebr': ('heb', 'lad', 'yid'),
        'jpan': ('jpn', ),
        'kore': ('kor', ),
        'zyyy': ('chi', )
    }
    if script in languages_scripts:
        languages = ([marc21tojson.lang_from_008] +
                     marc21tojson.langs_from_041_a +
                     marc21tojson.langs_from_041_h)
        for lang in languages:
            if lang in languages_scripts[script]:
                return '-'.join([lang, script])
        error_print('WARNING LANGUAGE SCRIPTS:', marc21tojson.bib_id,
                    script,  '008:', marc21tojson.lang_from_008,
                    '041$a:', marc21tojson.langs_from_041_a,
                    '041$h:', marc21tojson.langs_from_041_h)
    return '-'.join(['und', script])


def get_mef_person_link(bibid, id, key, value):
    """Get mef person link."""
    # https://mef.test.rero.ch/api/mef/?q=rero.rero_pid:A012327677
    PROD_HOST = 'mef.rero.ch'
    if os.environ.get('RERO_ILS_MEF_HOST'):
        DEV_HOST = os.environ.get('RERO_ILS_MEF_HOST')
    else:
        DEV_HOST = 'mef.test.rero.ch'
    mef_url = None
    try:
        identifier = id[1:].split(')')
        url = "{mef}/?q={org}.pid:{pid}".format(
            mef="https://{host}/api/mef".format(host=DEV_HOST),
            org=identifier[0].lower(),
            pid=identifier[1]
        )
        request = requests.get(url=url)
        if request.status_code == requests.codes.ok:
            data = request.json()
            hits = data.get('hits', {}).get('hits')
            if hits:
                mef_url = hits[0].get('links').get('self')
                mef_url = mef_url.replace(DEV_HOST, PROD_HOST)
            # else:
            #     error_print('WARNING MEF NOT FOUND:', bibid, url,
            #                 key, value)
        else:
            error_print('ERROR MEF REQUEST:', bibid, url,
                        request.status_code)
    except Exception as err:
        error_print('WARNING NOT MEF REF:', bibid, id, key, value)
    return mef_url


@marc21tojson.over('type', 'leader')
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


@marc21tojson.over('pid', '^001')
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


@marc21tojson.over('language', '^008')
@utils.ignore_value
def marc21_to_language(self, key, value):
    """Get languages.

    languages: 008 and 041 [$a, repetitive]
    """
    lang_codes = []
    language = self.get('language', [])
    if marc21tojson.lang_from_008:
        language.append({
            'value': marc21tojson.lang_from_008,
            'type': 'bf:Language'
        })
        lang_codes.append(marc21tojson.lang_from_008)
    for lang_value in marc21tojson.langs_from_041_a:
        if lang_value not in lang_codes:
            language.append({
                'value': lang_value.strip(),
                'type': 'bf:Language'
            })
            lang_codes.append(lang_value)
    # if not language:
    #     error_print('ERROR LANGUAGE:', marc21tojson.bib_id, 'set to "und"')
    #     language = [{'value': 'und', 'type': 'bf:Language'}]
    return language or None


@marc21tojson.over('title', '^245..')
@utils.ignore_value
def marc21_to_title(self, key, value):
    """Get title.

    title: 245$a
    without the punctuaction. If there's a $b, then 245$a : $b without the " /"
    """
    data = not_repetitive(marc21tojson.bib_id, key, value, 'a')
    main_title = remove_trailing_punctuation(data)
    sub_title = not_repetitive(marc21tojson.bib_id, key, value, 'b')
    if sub_title:
        main_title += ' : ' + ' : '.join(
            utils.force_list(
                remove_trailing_punctuation(sub_title))
        )
    return main_title


@marc21tojson.over('titlesProper', '^730..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_titlesProper(self, key, value):
    """Test dojson marc21titlesProper.

    titleProper: 730$a
    """
    return not_repetitive(marc21tojson.bib_id, key, value, 'a')


@marc21tojson.over('authors', '[17][01]0..')
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
                ref = get_mef_person_link(marc21tojson.bib_id, ref, key, value)
                if ref:
                    author['$ref'] = ref
        # we do not have a $ref
        if not author.get('$ref'):
            author['name'] = ''
            if value.get('a'):
                data = not_repetitive(marc21tojson.bib_id, key, value, 'a')
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
                    data = not_repetitive(marc21tojson.bib_id, key, value, 'c')
                    author['qualifier'] = remove_trailing_punctuation(data)
                if value.get('d'):
                    data = not_repetitive(marc21tojson.bib_id, key, value, 'd')
                    author['date'] = remove_trailing_punctuation(data)
        return author
    else:
        return None


@marc21tojson.over('copyrightDate', '^264.4')
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


@marc21tojson.over('editionStatement', '^250..')
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

    def build_edition_data(code, label, index, link):
        data = [{'value': remove_trailing_punctuation(label)}]
        try:
            alt_gr = marc21tojson.alternate_graphic['250'][link]
            subfield = \
                marc21tojson.get_subfields(alt_gr['field'])[index]
            data.append({
                'value': remove_trailing_punctuation(subfield),
                'language': get_language_script(alt_gr['script'])
            })
        except Exception as err:
            pass
        return data

    tag_link, link = get_field_link_data(value)
    items = get_field_items(value)
    index = 1
    edition_data = {}
    subfield_selection = {'a', 'b'}
    for blob_key, blob_value in items:
        if blob_key in subfield_selection:
            subfield_selection.remove(blob_key)
            edition_data[key_per_code[blob_key]] = \
                build_edition_data(blob_key, blob_value, index, link)
        if blob_key != '__order__':
            index += 1
    return edition_data or None


@marc21tojson.over('provisionActivity', '^264.[ 0-3]')
@utils.for_each_value
@utils.ignore_value
def marc21_to_provisionActivity(self, key, value):
    """Get publisher data.

    publisher.name: 264 [$b repetitive] (without the , but keep the ;)
    publisher.place: 264 [$a repetitive] (without the : but keep the ;)
    publicationDate: 264 [$c repetitive] (but take only the first one)
    """
    def build_statement(field_value, ind2):

        def build_place_or_agent_data(code, label, index, link, add_country):
            type_per_code = {
                'a': 'bf:Place',
                'b': 'bf:Agent'
            }
            place_or_agent_data = {
                'type': type_per_code[code],
                'label': [{'value': remove_trailing_punctuation(label)}]
            }

            if add_country:
                if marc21tojson.cantons:
                    place_or_agent_data['canton'] = marc21tojson.cantons
                if marc21tojson.country:
                    place_or_agent_data['country'] = marc21tojson.country
            try:
                alt_gr = marc21tojson.alternate_graphic['264'][link]
                subfield = \
                    marc21tojson.get_subfields(alt_gr['field'])[index]
                place_or_agent_data['label'].append({
                    'value': remove_trailing_punctuation(subfield),
                    'language': get_language_script(alt_gr['script'])
                })
            except Exception as err:
                pass
            return place_or_agent_data

        # function build_statement start here
        tag_link, link = get_field_link_data(field_value)
        items = get_field_items(field_value)
        statement = []
        index = 1
        add_country = ind2 in (' ', '1')
        for blob_key, blob_value in items:
            if blob_key in ('a', 'b'):
                place_or_agent_data = build_place_or_agent_data(
                    blob_key, blob_value, index, link, add_country)
                if blob_key == 'a':
                    add_country = False
                statement.append(place_or_agent_data)
            if blob_key != '__order__':
                index += 1
        return statement

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
    if subfields_c:
        subfield_c = subfields_c[0]
        publication['date'] = subfield_c
    if ind2 in (' ', '1'):
        start_date = make_year(marc21tojson.date1_from_008)
        if start_date:
            publication['startDate'] = start_date
        end_date = make_year(marc21tojson.date2_from_008)
        if end_date:
            publication['endDate'] = end_date
        if (marc21tojson.date_type_from_008 == 'q' or
                marc21tojson.date_type_from_008 == 'n'):
            publication['note'] = 'Date(s) incertaine(s) ou inconnue(s)'
    publication['statement'] = build_statement(value, ind2)
    return publication or None


@marc21tojson.over('formats', '^300..')
@utils.ignore_value
def marc21_to_description(self, key, value):
    """Get extent, otherMaterialCharacteristics, formats.

    extent: 300$a (the first one if many)
    otherMaterialCharacteristics: 300$b (the first one if many)
    formats: 300 [$c repetitive]
    """
    if value.get('a'):
        if not self.get('extent', None):
            self['extent'] = remove_trailing_punctuation(
                not_repetitive(marc21tojson.bib_id, key, value, 'a')
            )
    if value.get('b'):
        if self.get('otherMaterialCharacteristics', []) == []:
            self['otherMaterialCharacteristics'] = remove_trailing_punctuation(
                not_repetitive(marc21tojson.bib_id, key, value, 'b')
            )
    if value.get('c'):
        formats = self.get('formats', None)
        if not formats:
            data = value.get('c')
            formats = list(utils.force_list(data))
        return formats
    else:
        return None


@marc21tojson.over('series', '^490..')
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


@marc21tojson.over('abstracts', '^520..')
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


@marc21tojson.over('identifiedBy', '^020..')
@utils.ignore_value
def marc21_to_identifiedBy_from_field_020(self, key, value):
    """Get identifier from field 020."""
    def build_identifier_from(subfield_data, status=None):
        subfield_data = subfield_data.strip()
        identifier = {'value': subfield_data}
        subfield_c = not_repetitive(
            marc21tojson.bib_id, key, value, 'c', default='').strip()
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
    subfield_a = not_repetitive(marc21tojson.bib_id, key, value, 'a')
    if subfield_a:
        build_identifier_from(subfield_a)
    subfields_z = value.get('z')
    if subfields_z:
        for subfield_z in utils.force_list(subfields_z):
            build_identifier_from(subfield_z, status='invalid or cancelled')
    return identifiedBy or None


@marc21tojson.over('identifiedBy', '^022..')
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


@marc21tojson.over('identifiedBy', '^024..')
@utils.ignore_value
def marc21_to_identifiedBy_from_field_024(self, key, value):
    """Get identifier from field 024."""
    def populate_acquisitionTerms_note_qualifier(identifier):
        subfield_c = not_repetitive(
            marc21tojson.bib_id, key, value, 'c', default='').strip()
        if subfield_c:
            identifier['acquisitionTerms'] = subfield_c
        subfield_d = not_repetitive(
            marc21tojson.bib_id, key, value, 'd', default='').strip()
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
        marc21tojson.bib_id, key, value, 'a', default='').strip()
    subfield_2 = not_repetitive(
        marc21tojson.bib_id, key, value, '2', default='').strip()
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


@marc21tojson.over('identifiedBy', '^028..')
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
        marc21tojson.bib_id, key, value, 'a', default='').strip()
    if subfield_a:
        identifier['value'] = subfield_a
        if value.get('q'):  # $q is repetitive
            identifier['qualifier'] = \
                ', '.join(utils.force_list(value.get('q')))
        subfield_b = not_repetitive(
            marc21tojson.bib_id, key, value, 'b', default='').strip()
        if subfield_b:
            identifier['source'] = subfield_b
        # key[3] is the indicateur_1
        identifier['type'] = type_for_ind1.get(key[3], 'bf:Identifier')
        identifiedBy = self.get('identifiedBy', [])
        identifiedBy.append(identifier)
    return identifiedBy or None


@marc21tojson.over('identifiedBy', '^035..')
@utils.ignore_value
def marc21_to_identifiedBy_from_field_035(self, key, value):
    """Get identifier from field 035."""
    subfield_a = not_repetitive(
        marc21tojson.bib_id, key, value, 'a', default='').strip()
    if subfield_a:
        identifier = {
            'value': subfield_a,
            'type': 'bf:Local',
            'source': 'RERO'
        }
        identifiedBy = self.get('identifiedBy', [])
        identifiedBy.append(identifier)
    return identifiedBy or None


@marc21tojson.over('identifiedBy', '^930..')
@utils.ignore_value
def marc21_to_identifiedBy_from_field_930(self, key, value):
    """Get identifier from field 930."""
    subfield_a = not_repetitive(
        marc21tojson.bib_id, key, value, 'a', default='').strip()
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


@marc21tojson.over('notes', '^500..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_notes(self, key, value):
    """Get  notes.

    note: [500$a repetitive]
    """
    return not_repetitive(marc21tojson.bib_id, key, value, 'a')


@marc21tojson.over('is_part_of', '^773..')
@utils.ignore_value
def marc21_to_is_part_of(self, key, value):
    """Get  is_part_of.

    is_part_of: [773$t repetitive]
    """
    if not self.get('is_part_of', None):
        return not_repetitive(marc21tojson.bib_id, key, value, 't')


@marc21tojson.over('subjects', '^6....')
@utils.for_each_value
@utils.ignore_value
def marc21_to_subjects(self, key, value):
    """Get subjects.

    subjects: 6xx [duplicates could exist between several vocabularies,
        if possible deduplicate]
    """
    return value.get('a')
