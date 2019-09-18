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

from dojson import utils
from isbnlib import EAN13

from rero_ils.dojson.utils import ReroIlsMarc21Overdo, \
    remove_trailing_punctuation

marc21 = ReroIlsMarc21Overdo()


@marc21.over('languages', '^008')
@utils.ignore_value
def marc21_to_languages_from_008(self, key, value):
    """Get languages.

    languages: 008 and 041 [$a, repetitive]
    """
    language = self.get('language', [])

    # put 008 language in first place
    language.insert(0, {'type': 'bf:Language', 'value': value.strip()[35:38]})
    return language


@marc21.over('identifiedBy', '^020..')
@utils.ignore_value
def marc21_to_identifier_isbn(self, key, value):
    """Get identifier isbn.

    identifiers_isbn: 020 $a
    """
    isbn13 = EAN13(value.get('a'))
    if isbn13:
        identifiers = self.get('identifiedBy', [])
        identifier = {
            'type': 'bf:Isbn',
            'value': isbn13
        }
        identifiers.append(identifier)
        return identifiers
    return None


@marc21.over('type', '^0248.$')
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
    if value.get('a').find('cantook') > -1:
        return 'ebook'
    return None


@marc21.over('identifiedBy', '^035..')
@utils.ignore_value
def marc21_to_identifier_rero_id(self, key, value):
    """Get identifier reroId.

    identifiers:reroID: 035$a
    """
    identifiers = self.get('identifiedBy', [])
    identifier = {
        'type': 'bf:Local',
        'value': value.get('a')
    }
    identifiers.append(identifier)
    return identifiers


@marc21.over('translatedFrom', '^041..')
@utils.ignore_value
def marc21_to_translated_from(self, key, value):
    """Get translatedFrom.

    translatedFrom: 041 [$h repetitive]
    languages: 008 and 041 [$a, repetitive]
    """
    languages = self.get('language', [])
    unique_lang = []
    if languages != []:
        for language in languages:
            unique_lang.append(language['value'])

    language = value.get('a')
    if language:
        for lang in utils.force_list(language):
            if lang not in unique_lang:
                unique_lang.append(lang)
                languages.append({'type': 'bf:Language', 'value': lang})

    self['language'] = languages

    translated = value.get('h')
    if translated:
        return list(utils.force_list(translated))

    return None


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
    if not (key[4] == '2' and (key[:3] == '710' or key[:3] == '700')):
        author = {}
        author['type'] = 'person'
        author['name'] = remove_trailing_punctuation(value.get('a'))
        author_subs = utils.force_list(value.get('b'))
        if author_subs:
            for author_sub in author_subs:
                author['name'] += ' ' + remove_trailing_punctuation(author_sub)
        if key[:3] == '710':
            author['type'] = 'organisation'
        else:
            if value.get('c'):
                author['qualifier'] = remove_trailing_punctuation(
                    value.get('c')
                )
            if value.get('d'):
                author['date'] = remove_trailing_punctuation(value.get('d'))
        return author


@marc21.over('title', '^245..')
@utils.ignore_value
def marc21_to_title(self, key, value):
    """Get title.

    title: 245$a
    without the punctuaction. If there's a $b, then 245$a : $b without the ' /'
    """
    main_title = remove_trailing_punctuation(value.get('a'))
    sub_title = value.get('b')
    # responsability = value.get('c')
    if sub_title:
        main_title += ' : ' + ' : '.join(
            utils.force_list(remove_trailing_punctuation(sub_title))
        )
    return main_title


@marc21.over('copyrightDate', '^264.4')
@utils.ignore_value
def marc21_to_copyright_date(self, key, value):
    """Get Copyright Date."""
    copyright_dates = self.get('copyrightDate', [])
    copyright_date = value.get('c')
    if copyright_date:
        match = re.search(r'^([©℗])+\s*(\d{4}.*)', copyright_date)
        if match:
            copyright_date = ' '.join((
                match.group(1),
                match.group(2)
            ))
        else:
            raise ValueError('Bad format of copyright date')
    copyright_dates.append(copyright_date)
    return copyright_dates or None


@marc21.over('provisionActivity', '^(260..|264.[ 0-3])')
@utils.for_each_value
@utils.ignore_value
def marc21_to_provision_activity(self, key, value):
    """Get publisher data.

    publisher.name: 264 [$b repetitive]
    publisher.place: 264 [$a repetitive]
    publicationDate: 264 [$c repetitive] (but take only the first one)
    """
    def build_statement(field_value, ind2):

        def build_place_or_agent_data(code, label, add_country):
            place_or_agent_data = None
            type_per_code = {
                'a': 'bf:Place',
                'b': 'bf:Agent'
            }
            value = remove_trailing_punctuation(label)
            if value:
                place_or_agent_data = {
                    'type': type_per_code[code],
                    'label': [{'value': value}]
                }
            if add_country and marc21.country:
                place_or_agent_data['country'] = marc21.country
            return place_or_agent_data

        # function build_statement start here
        statement = []
        if isinstance(field_value, utils.GroupableOrderedDict):
            items = field_value.iteritems(repeated=True)
        else:
            items = utils.iteritems(field_value)
        add_country = ind2 in (' ', '1')
        for blob_key, blob_value in items:
            if blob_key in ('a', 'b'):
                place_or_agent_data = build_place_or_agent_data(
                    blob_key, blob_value, add_country)
                if blob_key == 'a':
                    add_country = False
                if place_or_agent_data:
                    statement.append(place_or_agent_data)
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
    if key[:3] == '260':
        ind2 = '1'  # to force type to bf:Publication for field 260
    publication = {
        'type': type_per_ind2[ind2],
        'statement': [],
    }

    subfields_c = utils.force_list(value.get('c'))
    if subfields_c:
        subfield_c = subfields_c[0]
        publication['date'] = subfield_c
        if ind2 in (' ', '1'):
            dates = subfield_c.replace('[', '').replace(']', '').split('-')
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

    publication['statement'] = build_statement(value, ind2)
    return publication or None


@marc21.over('formats', '^300..')
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
                utils.force_list(value.get('a'))[0])
    if value.get('b'):
        if self.get('otherMaterialCharacteristics', []) == []:
            self['otherMaterialCharacteristics'] = remove_trailing_punctuation(
                utils.force_list(value.get('b'))[0]
            )
    if value.get('c'):
        formats = self.get('formats', None)
        if not formats:
            data = value.get('c')
            formats = list(utils.force_list(data))
        return formats


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


@marc21.over('notes', '^500..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_notes(self, key, value):
    """Get  notes.

    note: [500$a repetitive]
    """
    return value.get('a')


@marc21.over('abstracts', '^520..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_abstracts(self, key, value):
    """Get abstracts.

    abstract: [520$a repetitive]
    """
    if not value.get('a'):
        return None
    return ', '.join(utils.force_list(value.get('a')))


@marc21.over('subjects', '^6....')
@utils.for_each_value
@utils.ignore_value
@utils.ignore_value
def marc21_to_subjects(self, key, value):
    """Get subjects.

    subjects: 6xx [duplicates could exist between several vocabularies,
        if possible deduplicate]
    """
    subjects = self.get('subjects', [])
    for subject in utils.force_list(value.get('a')):
        subjects.append(subject)
    self['subjects'] = subjects
    return None


@marc21.over('titlesProper', '^730..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_titles_proper(self, key, value):
    """Test dojson marc21titlesProper.

    titleProper: 730$a
    """
    return value.get('a')


@marc21.over('is_part_of', '^773..')
@utils.ignore_value
def marc21_to_is_part_of(self, key, value):
    """Get  is_part_of.

    is_part_of: [773$t repetitive]
    """
    if not self.get('is_part_of', None):
        return value.get('t')


@marc21.over('electronic_location', '^85640')
@utils.for_each_value
@utils.ignore_value
def marc21_electronic_location(self, key, value):
    """Get electronic_location data."""
    res = {}
    if value.get('x'):
        res['source'] = value.get('x')
    if value.get('u'):
        res['uri'] = value.get('u')
    return res or None


@marc21.over('cover_art', '^85642')
@utils.for_each_value
@utils.ignore_value
def marc21_cover_art(self, key, value):
    """Get cover_art data."""
    if value.get('3') == 'Image de couverture':
        self.setdefault('cover_art', value.get('u'))
