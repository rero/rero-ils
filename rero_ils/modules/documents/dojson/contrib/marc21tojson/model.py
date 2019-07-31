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

import re
import sys

import requests
from dojson import Overdo, utils

marc21tojson = Overdo()


def list_of_langs(data):
    """Construct list of language codes from data."""
    lang_codes = []
    for lang_data in data:
        lang_codes.append(lang_data.get('value'))
    return lang_codes


def remove_punctuation(data):
    """Remove punctuation from data."""
    try:
        if data[-1:] == ',':
            data = data[:-1]
        if data[-2:] == ' :':
            data = data[:-2]
        if data[-2:] == ' ;':
            data = data[:-2]
        if data[-2:] == ' /':
            data = data[:-2]
        if data[-2:] == ' -':
            data = data[:-2]
    except Exception:
        pass
    return data


def get_mef_person_link(id, key, value):
    """Get mef person link."""
    # https://mef.test.rero.ch/api/mef/?q=rero.rero_pid:A012327677
    PROD_HOST = 'mef.rero.ch'
    DEV_HOST = 'mef.test.rero.ch'
    mef_url = None
    if id:
        identifier = id[1:].split(')')
        url = "{mef}/?q={org}.{org}_pid:{pid}".format(
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
            else:
                print(
                    'ERROR: MEF person not found',
                    url,
                    key,
                    value,
                    file=sys.stderr
                )
        else:
            print(
                'ERROR: MEF request',
                url,
                request.status_code,
                file=sys.stderr
            )
    return mef_url


# @marc21tojson.over('__order__', '__order__')
# def order(self, key, value):
#     """Preserve order of datafields."""
#     order = []
#     for field in value:
#         name = marc21tojson.index.query(field)
#         if name:
#             name = name[0]
#         else:
#             name = field
#         order.append(name)
#
#     return order

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
    type = None
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


@marc21tojson.over('title', '^245..')
@utils.ignore_value
def marc21_to_title(self, key, value):
    """Get title.

    title: 245$a
    without the punctuaction. If there's a $b, then 245$a : $b without the " /"
    """
    main_title = remove_punctuation(value.get('a'))
    sub_title = value.get('b')
    # responsability = value.get('c')
    if sub_title:
        main_title += ' : ' + ' : '.join(
            utils.force_list(remove_punctuation(sub_title))
        )
    return main_title


@marc21tojson.over('titlesProper', '^730..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_titlesProper(self, key, value):
    """Test dojson marc21titlesProper.

    titleProper: 730$a
    """
    return value.get('a')


@marc21tojson.over('language', '^008')
@utils.ignore_value
def marc21_to_language(self, key, value):
    """Get languages.

    languages: 008 and 041 [$a, repetitive]
    """
    language = self.get('language', [])
    lang_codes = list_of_langs(language)
    # check len(value) to avoid getting char[35:38] if data is invalid
    if len(value) > 38:
        lang_value = value.strip()[35:38]
        if re.search(r'^[a-z]{3}$', lang_value):
            if lang_value not in lang_codes:
                lang = {
                    'value': lang_value,
                    'type': 'bf:Language'
                }
                language.append(lang)
    return language or None


@marc21tojson.over('language', '^041..')
@utils.ignore_value
def marc21_to_translatedFrom(self, key, value):
    """Get translatedFrom.

    languages: 041 [$a, repetitive]
    if language properties is already set form 008
    it will be replaced with those present in 041
    """
    language = self.get('language', [])
    lang_codes = list_of_langs(language)
    subfield_a = value.get('a')
    if subfield_a:
        for lang_value in utils.force_list(subfield_a):
            if lang_value not in lang_codes:
                lang = {
                    'value': lang_value.strip(),
                    'type': 'bf:Language'
                }
            language.append(lang)
    return language or None


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
    if not (key[4] == '2'):
        author = {}
        author['type'] = 'person'
        if value.get('0'):
            ref = get_mef_person_link(value.get('0'), key, value)
            if ref:
                author['$ref'] = ref
        # we do not have a $ref
        if not author.get('$ref'):
            author['name'] = remove_punctuation(value.get('a'))
            author_subs = utils.force_list(value.get('b'))
            if author_subs:
                for author_sub in author_subs:
                    author['name'] += ' ' + remove_punctuation(author_sub)
            if key[:3] == '710':
                author['type'] = 'organisation'
            else:
                if value.get('c'):
                    author['qualifier'] = remove_punctuation(value.get('c'))
                if value.get('d'):
                    author['date'] = remove_punctuation(value.get('d'))
        return author
    else:
        return None


@marc21tojson.over('publishers', '^264..')
@utils.ignore_value
def marc21_to_publishers_publicationDate(self, key, value):
    """Get publisher.

    publisher.name: 264 [$b repetitive] (without the , but keep the ;)
    publisher.place: 264 [$a repetitive] (without the : but keep the ;)
    publicationDate: 264 [$c repetitive] (but take only the first one)
    """
    lasttag = '?'
    publishers = self.get('publishers', [])

    publisher = {}
    indexes = {}
    lasttag = '?'
    for tag in value['__order__']:
        index = indexes.get(tag, 0)
        data = value[tag]
        if type(data) == tuple:
            data = data[index]
        if tag == 'a' and index > 0 and lasttag != 'a':
            publishers.append(remove_punctuation(publisher))
            publisher = {}
        if tag == 'a':
            place = publisher.get('place', [])
            place.append(remove_punctuation(data))
            publisher['place'] = place
        elif tag == 'b':
            name = publisher.get('name', [])
            name.append(remove_punctuation(data))
            publisher['name'] = name
        elif tag == 'c' and index == 0:

            # 4 digits
            date = re.match(r'.*?(\d{4})', data).group(1)
            self['publicationYear'] = int(date)

            # create free form if different
            if data != str(self['publicationYear']):
                self['freeFormedPublicationDate'] = data
        indexes[tag] = index + 1
        lasttag = tag

    if publisher:
        publishers.append(publisher)
    if not publishers:
        return None
    else:
        return publishers


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
            self['extent'] = remove_punctuation(
                utils.force_list(value.get('a'))[0]
            )
    if value.get('b'):
        if self.get('otherMaterialCharacteristics', []) == []:
            self['otherMaterialCharacteristics'] = remove_punctuation(
                utils.force_list(value.get('b'))[0]
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
    return ', '.join(utils.force_list(value.get('a')))


@marc21tojson.over('identifiedBy', '^020..')
@utils.ignore_value
def marc21_to_identifiedBy_from_field_020(self, key, value):
    """Get identifier from field 020."""
    def build_identifier_from(subfield_data, status=None):
        subfield_data = subfield_data.strip()
        identifier = {'value': subfield_data}
        subfield_c = value.get('c', '').strip()
        if subfield_c:
            identifier['acquisitionsTerms'] = subfield_c
        if value.get('q'):  # $q is repetitive
            identifier['qualifier'] = \
                ', '.join(utils.force_list(value.get('q')))

        match = re.search(r'^(.+?)\s*\((.*)\)$', subfield_data)
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
    subfield_a = value.get('a')
    if subfield_a:
        build_identifier_from(subfield_a)
    subfield_z = value.get('z')
    if subfield_z:
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
        subfield_data = value.get(subfield_code, '').strip()
        if subfield_data:
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
    def populate_acquisitionsTerms_note_qualifier(identifier):
        subfield_c = value.get('c', '').strip()
        if subfield_c:
            identifier['acquisitionsTerms'] = subfield_c
        subfield_d = value.get('d', '').strip()
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
    subfield_a = value.get('a', '').strip()
    subfield_2 = value.get('2', '').strip()
    if subfield_a:
        if re.search(r'permalink\.snl\.ch', subfield_a):
            identifier.update({
                'value': subfield_a,
                'type': 'uri',
                'source': 'SNL'
            })
        elif re.search(r'bnf\.fr/ark', subfield_a):
            identifier.update({
                'value': subfield_a,
                'type': 'uri',
                'source': 'BNF'
            })
        elif subfield_2:
            identifier['value'] = subfield_a
            populate_acquisitionsTerms_note_qualifier(identifier)
            for pattern in subfield_2_regexp:
                if re.search(pattern, subfield_2, re.IGNORECASE):
                    identifier.update(subfield_2_regexp[pattern])
        else:  # without subfield $2
            ind1 = key[3]  # indicateur_1
            if ind1 in ('0', '1', '2', '3', '8'):
                populate_acquisitionsTerms_note_qualifier(identifier)
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
    subfield_a = value.get('a', '').strip()
    if subfield_a:
        identifier['value'] = subfield_a
        if value.get('q'):  # $q is repetitive
            identifier['qualifier'] = \
                ', '.join(utils.force_list(value.get('q')))
        subfield_b = value.get('b', '').strip()
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
    subfield_a = value.get('a', '').strip()
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
    subfield_a = value.get('a', '').strip()
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
    return value.get('a')


@marc21tojson.over('is_part_of', '^773..')
@utils.ignore_value
def marc21_to_is_part_of(self, key, value):
    """Get  is_part_of.

    is_part_of: [773$t repetitive]
    """
    if not self.get('is_part_of', None):
        return value.get('t')


@marc21tojson.over('subjects', '^6....')
@utils.for_each_value
@utils.ignore_value
def marc21_to_subjects(self, key, value):
    """Get subjects.

    subjects: 6xx [duplicates could exist between several vocabularies,
        if possible deduplicate]
    """
    return value.get('a')
