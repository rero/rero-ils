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

"""rero-ils UNIMARC model definition."""


import re
from json import loads

from dojson import utils
from dojson.utils import GroupableOrderedDict, force_list
from pkg_resources import resource_string

from rero_ils.dojson.utils import ReroIlsOverdo, remove_trailing_punctuation

unimarctojson = ReroIlsOverdo()


@unimarctojson.over('type', 'leader')
def unimarc_type(self, key, value):
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


@unimarctojson.over('identifiedBy', '^003')
@utils.ignore_value
def unimarc_bnf_id(self, key, value):
    """Get ID.

    identifier bnfID 003
    """
    identifiers = self.get('identifiedBy', [])
    if value.startswith('http://catalogue.bnf.fr/'):
        identifiers.append({
            "type": "bf:Local",
            "source": "BNF",
            "value":  value.replace('http://catalogue.bnf.fr/', '')
        })
    return identifiers


@unimarctojson.over('title', '^200..')
@utils.ignore_value
def unimarc_title(self, key, value):
    """Get title.

    title: 200$a
    If there's a $e, then 245$a : $e
    """
    main_title = value.get('a')
    sub_title = value.get('e')
    # responsability = value.get('c')
    if sub_title:
        main_title += ' : ' + ' : '.join(
            utils.force_list(sub_title)
        )
    return main_title


@unimarctojson.over('titlesProper', '^500..')
@utils.for_each_value
@utils.ignore_value
def unimarc_titles_proper(self, key, value):
    """Test dojson unimarctitlesProper.

    titleProper: 500$a
    """
    return value.get('a')


@unimarctojson.over('language', '^101')
@utils.ignore_value
def unimarc_languages(self, key, value):
    """Get languages.

    languages: 008 and 041 [$a, repetitive]
    """
    languages = utils.force_list(value.get('a'))
    to_return = []
    schema_in_bytes = resource_string(
        'rero_ils.modules.documents.jsonschemas',
        'documents/document-v0.0.1.json'
    )
    schema = loads(schema_in_bytes.decode('utf8'))
    langs = schema[
        'properties']['language']['items']['properties']['value']['enum']
    for language in languages:
        if language in langs:
            to_return.append({'value': language, 'type': 'bf:Language'})

    translatedsfrom = utils.force_list(value.get('c'))
    if translatedsfrom:
        self['translatedFrom'] = []
        for translatedfrom in translatedsfrom:
            self['translatedFrom'].append(translatedfrom)

    return to_return


@unimarctojson.over('authors', '7[01][012]..')
@utils.for_each_value
@utils.ignore_value
def unimarc_to_author(self, key, value):
    """Get author.

    authors: loop:
    700 Nom de personne – Responsabilité principale
    701 Nom de personne – Autre responsabilité principale
    702 Nom de personne – Responsabilité secondaire
    710 Nom de collectivité – Responsabilité principale
    711 Nom de collectivité – Autre responsabilité principale
    712 Nom de collectivité – Responsabilité secondaire
    """
    author = {}
    author['name'] = value.get('a')
    author['type'] = 'person'
    if key[1] == '1':
        author['type'] = 'organisation'

    if value.get('b'):
        author['name'] += ', ' + value.get('b')
    if value.get('d'):
        author['name'] += ' ' + value.get('d')

    if value.get('c'):
        author['qualifier'] = value.get('c')

    if value.get('f'):
        date = value.get('f')
        date = date.replace('-....', '-')
        author['date'] = date
    return author


@unimarctojson.over('provisionActivity', '^21[04]..')
@utils.for_each_value
@utils.ignore_value
def unimarc_publishers_provision_activity_publication(self, key, value):
    """Get provision activity dates."""
    def build_place_or_agent_data(code, label, index, add_country):
        type_per_code = {
            'a': 'bf:Place',
            'c': 'bf:Agent'
        }
        place_or_agent_data = {
            'type': type_per_code[code],
            'label': [{'value': remove_trailing_punctuation(label)}]
        }
        if add_country:
            # country from 102
            field_102 = unimarctojson.get_fields(tag='102')
            if field_102:
                field_102 = field_102[0]
                country_codes = unimarctojson.get_subfields(field_102, 'a')
                if country_codes:
                    place_or_agent_data['country'] = country_codes[0].lower()
        return place_or_agent_data

    publication = {}
    ind2 = key[4]
    type_per_ind2 = {
        ' ': 'bf:Publication',
        '_': 'bf:Publication',
        '0': 'bf:Publication',
        '1': 'bf:Production',
        '2': 'bf:Distribution',
        '3': 'bf:Manufacture'
    }
    if ind2 == '4':
        field_d = value.get('d')
        if field_d:
            field_d = force_list(field_d)[0]
            copyright_date = self.get('copyrightDate', [])
            if field_d[0] == 'P':
                copyright_date.append('℗ ' + field_d[2:])
            else:
                copyright_date.append('© ' + field_d)
            self['copyrightDate'] = copyright_date
    else:
        publication = {
            'type': type_per_ind2[ind2],
            'statement': [],
        }
        subfields_d = utils.force_list(value.get('d'))
        if subfields_d:
            subfield_d = subfields_d[0]
            publication['date'] = subfield_d
            if ind2 in (' ', '_', '0'):
                dates = subfield_d.replace('[', '').replace(']', '').split('-')
                try:
                    if re.search(r'(^\[?\d{4}$)', dates[0]):
                        publication['startDate'] = dates[0]
                except Exception:
                    pass
                try:
                    if re.search(r'(^\d{4}\]?$)', dates[1]):
                        publication['endDate'] = dates[1]
                except Exception:
                    pass

        # TODO: dates from 100 not working !!!!
        # if ind2 in (' ', '_', '1'):
        #     # startDate: 100, pos. 9-12 endDate: 100, pos. 13-16
        #     field_100 = unimarctojson.get_fields(tag='100')
        #     if field_100:
        #         field_100 = field_100[0]
        #         data = unimarctojson.get_subfields(field_100, 'a')
        #         if data:
        #             try:
        #                 publication['startDate'] = str(int(data[0][9:13]))
        #             except Exception:
        #                 pass
        #             try:
        #                 publication['endDate'] = str(int(data[0][13:17]))
        #             except Exception:
        #                 pass

        statement = []
        if isinstance(value, GroupableOrderedDict):
            items = value.iteritems(repeated=True)
        else:
            items = utils.iteritems(value)

        index = 1
        add_country = ind2 in (' ', '_', '0')
        for blob_key, blob_value in items:
            if blob_key in ('a', 'c'):
                place_or_agent_data = build_place_or_agent_data(
                    blob_key, blob_value, index, add_country)
                if blob_key == 'a':
                    add_country = False
                statement.append(place_or_agent_data)
            if blob_key != '__order__':
                index += 1

        publication['statement'] = statement
    return publication or None


@unimarctojson.over('formats', '^215..')
@utils.ignore_value
def unimarc_description(self, key, value):
    """Get extent, otherMaterialCharacteristics, formats.

    extent: 215$a (the first one if many)
    otherMaterialCharacteristics: 215$b (the first one if many)
    formats: 215 [$c repetitive]
    """
    if value.get('a'):
        if not self.get('extent', None):
            self['extent'] = (
                utils.force_list(value.get('a'))[0]
            )
    if value.get('c'):
        if self.get('otherMaterialCharacteristics', []) == []:
            self['otherMaterialCharacteristics'] = (
                utils.force_list(value.get('c'))[0]
            )
    if value.get('d'):
        formats = self.get('formats', None)
        if not formats:
            data = value.get('d')
            formats = list(utils.force_list(data))
        return formats
    else:
        return None


@unimarctojson.over('series', '^225..')
@utils.for_each_value
@utils.ignore_value
def unimarc_series(self, key, value):
    """Get series.

    series.name: [225$a repetitive]
    series.number: [225$v repetitive]
    """
    series = {}
    name = value.get('a')
    if name:
        series['name'] = ', '.join(utils.force_list(name))
    number = value.get('v')
    if number:
        series['number'] = ', '.join(utils.force_list(number))
    return series


@unimarctojson.over('abstracts', '^330..')
@utils.for_each_value
@utils.ignore_value
def unimarc_abstracts(self, key, value):
    """Get abstracts.

    abstract: [330$a repetitive]
    """
    return ', '.join(utils.force_list(value.get('a')))


@unimarctojson.over('identifiedBy', '^073..')
@utils.ignore_value
def unimarc_identifier_isbn(self, key, value):
    """Get identifier isbn.

    identifiers:isbn: 010$a
    """
    from isbnlib import EAN13
    identifiers = self.get('identifiedBy', [])
    if value.get('a'):
        ean = {
            "type": "bf:Ean",
            "value": value.get('a')
        }
        check_ean = EAN13(value.get('a'))
        # Do we have to check also cancelled status?
        if not check_ean:
            ean['status'] = 'invalid'
        identifiers.append(ean)
    return identifiers


@unimarctojson.over('notes', '^300..')
@utils.for_each_value
@utils.ignore_value
def unimarc_notes(self, key, value):
    """Get  notes.

    note: [300$a repetitive]
    """
    return value.get('a')


@unimarctojson.over('subjects', '^6((0[0-9])|(1[0-7]))..')
@utils.for_each_value
@utils.ignore_value
def unimarc_subjects(self, key, value):
    """Get subjects.

    subjects: 6xx [duplicates could exist between several vocabularies,
        if possible deduplicate]
    """
    to_return = ''
    if value.get('a'):
        to_return = value.get('a')
    if value.get('b'):
        to_return += ', ' + value.get('b')
    if value.get('d'):
        to_return += ' ' + value.get('d')
    if value.get('c'):
        to_return += ', ' + value.get('c')
    if value.get('f'):
        to_return += ', ' + value.get('f')
    return to_return
