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


from json import loads

from dojson import utils
from dojson.utils import force_list
from pkg_resources import resource_string

from rero_ils.dojson.utils import ReroIlsUnimarcOverdo, TitlePartList, \
    add_note, get_field_items, make_year, remove_trailing_punctuation

unimarc = ReroIlsUnimarcOverdo()


@unimarc.over('type', 'leader')
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


@unimarc.over('identifiedBy', '^003')
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


@unimarc.over('title', '^200..')
@utils.ignore_value
def unimarc_title(self, key, value):
    """Get title data.

    field 200: non repetitive
        $a : repetitive
        $e : repetitive
        $f : repetitive
        $g : repetitive
        $h : repetitive
        $i : repetitive
    field 510,512,514,515,516,517,518,519,532: repetitive
        $a : non repetitive
        $e : repetitive
        $h : repetitive
        $i : repetitive
    """
    title_list = []
    title = self.get('title', [])
    # this function will be called for each fields 200, but as we already
    # process all of them in the first run and the tittle is already build,
    # there is nothing to do if the title has already been build.
    if not title:
        language = unimarc.lang_from_101
        responsibilites = []
        for tag in ['200', '510',
                    '512', '514', '515', '516', '517', '518', '519', '532']:
            for field in unimarc.get_alt_graphic_fields(tag=tag):
                title_data = {}
                part_list = TitlePartList(
                    part_number_code='h',
                    part_name_code='i'
                )
                subfields_6 = unimarc.get_subfields(field, '6')
                subfields_7 = unimarc.get_subfields(field, '7')
                subfields_a = unimarc.get_subfields(field, 'a')
                subfields_e = unimarc.get_subfields(field, 'e')
                language_script_code = ''
                if subfields_7:
                    language_script_code = \
                        unimarc.get_language_script(subfields_7[0])
                title_type = 'bf:VariantTitle'
                if tag == '200':
                    title_type = 'bf:Title'
                elif tag == '510':
                    title_type = 'bf:ParallelTitle'
                # build title parts
                index = 1
                link = ''
                if subfields_6:
                    link = subfields_6[0]
                items = get_field_items(field['subfields'])
                for blob_key, blob_value in items:
                    if blob_key == 'a':
                        value_data = \
                            unimarc.build_value_with_alternate_graphic(
                                tag, blob_key, blob_value,
                                index, link, ',.', ':;/-=')
                        title_data['mainTitle'] = value_data
                    if blob_key == 'e':
                        value_data = \
                            unimarc.build_value_with_alternate_graphic(
                                tag, blob_key, blob_value,
                                index, link, ',.', ':;/-=')
                        title_data['subtitle'] = value_data
                    if blob_key in ['f', 'g'] and tag == '200':
                        value_data = \
                            unimarc.build_value_with_alternate_graphic(
                                tag, blob_key, blob_value,
                                index, link, ',.', ':;/-=')
                        responsibilites.append(value_data)
                    if blob_key in ['h', 'i']:
                        part_list.update_part(
                            [dict(value=blob_value)], blob_key, blob_value)
                    if blob_key != '__order__':
                        index += 1
                title_data['type'] = title_type
                the_part_list = part_list.get_part_list()
                if the_part_list:
                    title_data['part'] = the_part_list
                if title_data:
                    title_list.append(title_data)

        # extract responsibilities
        if responsibilites:
            new_responsibility = self.get('responsibilityStatement', [])
            for resp in responsibilites:
                new_responsibility.append(resp)
            self['responsibilityStatement'] = new_responsibility
    return title_list or None


@unimarc.over('titlesProper', '^500..')
@utils.for_each_value
@utils.ignore_value
def unimarc_titles_proper(self, key, value):
    """Test dojson unimarctitlesProper.

    titleProper: 500$a
    """
    return value.get('a', '')


@unimarc.over('language', '^101')
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


@unimarc.over('authors', '7[01][012]..')
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
    author['name'] = ', '.join(utils.force_list(value.get('a', '')))
    author['type'] = 'person'
    if key[1] == '1':
        author['type'] = 'organisation'
    if author['name']:
        if value.get('b'):
            author['name'] += \
                ', ' + ', '.join(utils.force_list(value.get('b')))
        if value.get('d'):
            author['name'] += ' ' + ' '.join(utils.force_list(value.get('d')))

    if value.get('c'):
        author['qualifier'] = value.get('c')

    if value.get('f'):
        date = utils.force_list(value.get('f'))[0]
        date = date.replace('-....', '-')
        author['date'] = date
    return author


@unimarc.over('editionStatement', '^205..')
@utils.for_each_value
@utils.ignore_value
def unimarc_to_edition_statement(self, key, value):
    """Get edition statement data.

    editionDesignation: 205 [$a non repetitive] (without trailing ponctuation)
    responsibility: 205 [$f non repetitive]
    """
    edition_data = {}
    subfields_a = utils.force_list(value.get('a'))
    if subfields_a:
        subfield_a = subfields_a[0]
        edition_data['editionDesignation'] = [{'value': subfield_a}]
    subfields_f = utils.force_list(value.get('f'))
    if subfields_f:
        subfield_f = subfields_f[0]
        edition_data['responsibility'] = [{'value': subfield_f}]
    return edition_data or None


@unimarc.over('provisionActivity', '^21[04]..')
@utils.for_each_value
@utils.ignore_value
def unimarc_publishers_provision_activity_publication(self, key, value):
    """Get provision activity dates."""
    def build_place_or_agent_data(code, label, index):
        type_per_code = {
            'a': 'bf:Place',
            'c': 'bf:Agent'
        }
        place_or_agent_data = {
            'type': type_per_code[code],
            'label': [{'value': remove_trailing_punctuation(label)}]
        }
        return place_or_agent_data

    def build_place():
        # country from 102
        place = {}
        field_102 = unimarc.get_fields(tag='102')
        if field_102:
            field_102 = field_102[0]
            country_codes = unimarc.get_subfields(field_102, 'a')
            if country_codes:
                place['country'] = country_codes[0].lower()
                place['type'] = 'bf:Place'
        return place

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
        statement = []
        items = get_field_items(value)
        index = 1
        for blob_key, blob_value in items:
            if blob_key in ('a', 'c'):
                place_or_agent_data = build_place_or_agent_data(
                    blob_key, blob_value, index)
                statement.append(place_or_agent_data)
            if blob_key != '__order__':
                index += 1
        if statement:
            publication['statement'] = statement
        if ind2 in (' ', '_', '0'):
            place = build_place()
            if place:
                publication['place'] = [place]

        subfields_d = utils.force_list(value.get('d'))
        if subfields_d:
            subfield_d = subfields_d[0]
            publication['statement'].append({
                'label': [{'value': subfield_d}],
                'type': 'Date'
            })
            if ind2 in (' ', '_', '0'):
                dates = subfield_d.replace('[', '').replace(']', '').split('-')
                try:
                    start_date = make_year(dates[0])
                    if start_date:
                        publication['startDate'] = start_date
                except Exception:
                    pass
                try:
                    end_date = make_year(dates[1])
                    if end_date:
                        publication['endDate'] = end_date
                except Exception:
                    pass

    if not publication.get('statement'):
        publication = None
    return publication or None


@unimarc.over('extent', '^215..')
@utils.ignore_value
def unimarc_description(self, key, value):
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

    215 [$a repetitive (the first one if many)]: extent, duration:
    215 [$c non repetitive]: colorContent, productionMethod,
        illustrativeContent, note of type otherPhysicalDetails
    215 [$d repetitive]: dimensions, book_formats
    215 [$e repetitive]: accompanying material note
    """
    unimarc.extract_description_from_marc_field(key, value, self)
    return None


@unimarc.over('series', '^225..')
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


@unimarc.over('abstracts', '^330..')
@utils.for_each_value
@utils.ignore_value
def unimarc_abstracts(self, key, value):
    """Get abstracts.

    abstract: [330$a repetitive]
    """
    return ', '.join(utils.force_list(value.get('a', '')))


@unimarc.over('identifiedBy', '^073..')
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


@unimarc.over('note', '^300..')
@utils.for_each_value
@utils.ignore_value
def unimarc_notes(self, key, value):
    """Get  notes.

    note: [300$a repetitive]
    """
    add_note(
        dict(
            noteType='general',
            label=value.get('a', '')
        ),
        self)

    return None


@unimarc.over('subjects', '^6((0[0-9])|(1[0-7]))..')
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
        to_return += ', ' + ', '.join(utils.force_list(value.get('b')))
    if value.get('d'):
        to_return += ' ' + ' '.join(utils.force_list(value.get('d')))
    if value.get('c'):
        to_return += ', ' + ', '.join(utils.force_list(value.get('c')))
    if value.get('f'):
        to_return += ', ' + ', '.join(utils.force_list(value.get('f')))
    return to_return


@unimarc.over('electronicLocator', '^8564.')
@utils.for_each_value
@utils.ignore_value
def marc21_to_electronicLocator_from_field_856(self, key, value):
    """Get electronicLocator from field 856."""
    electronic_locator = None
    if value.get('u'):
        electronic_locator = {
            'url': value.get('u'),
            'type': 'resource'
        }
    return electronic_locator
