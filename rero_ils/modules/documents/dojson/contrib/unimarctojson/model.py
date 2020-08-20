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


import jsonref
from dojson import utils
from dojson.utils import GroupableOrderedDict
from pkg_resources import resource_string

from rero_ils.dojson.utils import ReroIlsUnimarcOverdo, TitlePartList, \
    add_note, get_field_items, make_year, not_repetitive, \
    remove_trailing_punctuation
from rero_ils.modules.documents.api import Document

_ISSUANCE_MAIN_TYPE_PER_BIB_LEVEL = {
    'a': 'rdami:1001',
    'c': 'rdami:1001',
    'i': 'rdami:1004',
    'm': 'rdami:1001',
    's': 'rdami:1003'
}

_ISSUANCE_SUBTYPE_PER_BIB_LEVEL = {
    'a': 'article',
    'c': 'privateFile',
    'm': 'materialUnit'
}

_ISSUANCE_SUBTYPE_PER_SERIAL_TYPE = {
    'a': 'periodical',
    'b': 'monographicSeries',
    'e': 'updatingLoose-leaf',
    'f': 'updatingWebsite',
    'g': 'updatingWebsite',
    'h': 'updatingWebsite'
}

unimarc = ReroIlsUnimarcOverdo()


@unimarc.over('type_and_issuance', 'leader')
@utils.ignore_value
def unimarc_type_and_issuance(self, key, value):
    """
    Get document type and mode of issuance.

    Books: LDR/6-7: am
    Journals: LDR/6-7: as
    Articles: LDR/6-7: aa + add field 773 (journal title)
    Scores: LDR/6: c|d
    Videos: LDR/6: g + 007/0: m|v
    Sounds: LDR/6: i|j
    E-books (imported from Cantook)
    """
    type = None
    if unimarc.record_type == 'a':
        if unimarc.bib_level == 'm':
            type = 'book'
        elif unimarc.bib_level == 's':
            type = 'journal'
        elif unimarc.bib_level == 'a':
            type = 'article'
    elif unimarc.record_type in ['c', 'd']:
        type = 'score'
    elif unimarc.record_type in ['i', 'j']:
        type = 'sound'
    elif unimarc.record_type == 'g':
        type = 'video'
        # Todo 007
    self['type'] = type

    # get the mode of issuance
    self['issuance'] = {}
    main_type = _ISSUANCE_MAIN_TYPE_PER_BIB_LEVEL.get(
        unimarc.bib_level, 'rdami:1001')
    sub_type = 'NOT_DEFINED'
    if unimarc.bib_level in _ISSUANCE_SUBTYPE_PER_BIB_LEVEL:
        sub_type = _ISSUANCE_SUBTYPE_PER_BIB_LEVEL[unimarc.bib_level]
    if unimarc.serial_type in _ISSUANCE_SUBTYPE_PER_SERIAL_TYPE:
        sub_type = _ISSUANCE_SUBTYPE_PER_SERIAL_TYPE[unimarc.serial_type]
    self['issuance'] = dict(main_type=main_type, subtype=sub_type)


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


@unimarc.over('part_of', '^(410|46[234])..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_part_of(self, key, value):
    """Get part_of."""
    part_of = {}
    subfield_x = not_repetitive(
        unimarc.bib_id, key, value, 'x', default='').strip()
    linked_pid = None
    if subfield_x:
        for pid in Document.get_document_pids_by_issn(subfield_x):
            linked_pid = pid
            break
    if linked_pid:
        part_of['document'] = {
            '$ref':
                'https://ils.rero.ch/api/documents/{pid}'.format(
                    pid=linked_pid
                )
        }
        subfield_v = not_repetitive(
            unimarc.bib_id, key, value, 'v', default='').strip()
        if subfield_v:
            part_of['numbering'] = subfield_v
        self['partOf'] = self.get('partOf', [])
        self['partOf'].append(part_of)


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
        'rero_ils.jsonschemas',
        'common/languages-v0.0.1.json'
    )
    schema = jsonref.loads(schema_in_bytes.decode('utf8'))
    langs = schema['language']['enum']

    for language in languages:
        if language in langs:
            to_return.append({'value': language, 'type': 'bf:Language'})

    translatedsfrom = utils.force_list(value.get('c'))
    if translatedsfrom:
        self['translatedFrom'] = []
        for translatedfrom in translatedsfrom:
            self['translatedFrom'].append(translatedfrom)

    return to_return


@unimarc.over('contribution', '7[01][0123]..')
@utils.for_each_value
@utils.ignore_value
def unimarc_to_contribution(self, key, value):
    """Get contribution.

    contribution: loop:
    700 Nom de personne – Responsabilité principale
    701 Nom de personne – Autre responsabilité principale
    702 Nom de personne – Responsabilité secondaire
    710 Nom de collectivité – Responsabilité principale
    711 Nom de collectivité – Autre responsabilité principale
    712 Nom de collectivité – Responsabilité secondaire
    """
    agent = {}
    agent['preferred_name'] = ', '.join(utils.force_list(value.get('a', '')))
    agent['type'] = 'bf:Person'
    if agent['preferred_name']:
        if value.get('b'):
            agent['preferred_name'] += \
                ', ' + ', '.join(utils.force_list(value.get('b')))

    if key[:3] in ['700', '701', '702', '703']:
        if value.get('d'):
            agent['numeration'] = value.get('d')

        if value.get('c'):
            agent['qualifier'] = value.get('c')

        if value.get('f'):
            date = utils.force_list(value.get('f'))[0]
            date = date.replace('-....', '-')
            dates = date.split('-')
            try:
                date_of_birth = dates[0].strip()
                if date_of_birth:
                    agent['date_of_birth'] = date_of_birth
            except Exception:
                pass
            try:
                date_of_death = dates[1].strip()
                if date_of_death:
                    agent['date_of_death'] = date_of_death
            except Exception:
                pass

    if key[:3] in ['710', '711', '712']:
        agent['type'] = 'bf:Organisation'
        agent['conference'] = key[3] == '1'
        if agent['preferred_name']:
            if value.get('c'):
                agent['preferred_name'] += \
                    ', ' + ', '.join(utils.force_list(value.get('c')))
        if value.get('d'):
            conference_number = utils.force_list(value.get('d'))[0]
            agent['conference_number'] = remove_trailing_punctuation(
                conference_number
            ).lstrip('(').rstrip(')')
        if value.get('e'):
            conference_place = utils.force_list(value.get('e'))[0]
            agent['conference_place'] = remove_trailing_punctuation(
                conference_place
            ).lstrip('(').rstrip(')')
        if value.get('f'):
            conference_date = utils.force_list(value.get('f'))[0]
            agent['conference_date'] = remove_trailing_punctuation(
                conference_date
            ).lstrip('(').rstrip(')')
    IDREF_ROLE_CONV = {
        "070": "aut",
        "230": "cmp",
        "205": "ctb",
        "340": "edt",
        "420": "hnr",
        "440": "ill",
        "600": "pht",
        "590": "prf",
        "730": "trl",
        "080": "aui",
        "160": "bsl",
        "220": "com",
        "300": "drt",
        "430": "ilu",
        "651": "pbd",
        "350": "egr",
        "630": "pro",
        "510": "ltg",
        "365": "exp",
        "727": "dgs",
        "180": "ctg",
        "220": "com",
        "210": "cmm",
        "200": "chr",
        "110": "bnd",
        "720": "ato",
        "030": "arr",
        "020": "ann",
        "632": "adi",
        "005": "act",
        "390": "fmo",
        "545": "mus"
    }
    roles = []
    if value.get('4'):
        for role in utils.force_list(value.get('4')):
            role_conv = IDREF_ROLE_CONV.get(role)
            if role_conv:
                roles.append(role_conv)
        roles = list(set(roles))
    if not roles:
        roles = ['aut']

    return {
        'agent': agent,
        'role': roles
    }


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
            field_d = utils.force_list(field_d)[0]
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
                start_date = make_year(dates[0])
                if start_date:
                    publication['startDate'] = start_date
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
def unimarc_series_statement(self, key, value):
    """Get seriesStatement.

    series.name: [225$a repetitive]
    series.number: [225$v repetitive]
    """
    # normalize the value by building couple of $a, $v
    # $v can be missing  in a couple
    items = get_field_items(value)
    new_data = []
    fist_a_value = None
    pending_v_values = []
    subfield_selection = {'a', 'e', 'i', 'v'}
    for blob_key, blob_value in items:
        if blob_key in subfield_selection:
            if blob_key == 'a':
                fist_a_value = blob_value
                subfield_selection.remove('a')
            elif blob_key == 'e':
                fist_a_value += ': ' + blob_value
            elif blob_key == 'i':
                # we keep on the $e associeted to the $a
                subfield_selection.remove('e')
                if fist_a_value:
                    new_data.append(('a', fist_a_value))
                    for v_value in pending_v_values:
                        new_data.append(('v', v_value))
                    fist_a_value = None
                    pending_v_values = []
                new_data.append(('a', blob_value))
            elif blob_key == 'v':
                pending_v_values.append(blob_value)
    if fist_a_value:
        new_data.append(('a', fist_a_value))
    for v_value in pending_v_values:
        new_data.append(('v', v_value))

    new_value = GroupableOrderedDict(tuple(new_data))
    unimarc.extract_series_statement_from_marc_field(key, new_value, self)


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
