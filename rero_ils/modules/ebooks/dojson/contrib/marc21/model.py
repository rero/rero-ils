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

from dojson import Overdo, utils
from isbnlib import EAN13

marc21 = Overdo()


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
def marc21_to_identifier_reroID(self, key, value):
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
def marc21_to_translatedFrom(self, key, value):
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


@marc21.over('title', '^245..')
@utils.ignore_value
def marc21_to_title(self, key, value):
    """Get title.

    title: 245$a
    without the punctuaction. If there's a $b, then 245$a : $b without the ' /'
    """
    main_title = remove_punctuation(value.get('a'))
    sub_title = value.get('b')
    # responsability = value.get('c')
    if sub_title:
        main_title += ' : ' + ' : '.join(
            utils.force_list(remove_punctuation(sub_title))
        )
    return main_title


@marc21.over('publishers', '^(260..|264.1)')
@utils.ignore_value
def marc21_to_publishers_publicationDate(self, key, value):
    """Get publisher.

    publisher.name: 260 [$b repetitive] (without the , but keep the ;)
    publisher.place: 260 [$a repetitive] (without the : but keep the ;)
    publicationDate: 260 [$c repetitive] (but take only the first one)
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
        if tag == 'a' and data:
            place = publisher.get('place', [])
            place.append(remove_punctuation(data))
            publisher['place'] = place
        elif tag == 'b' and data:
            name = publisher.get('name', [])
            name.append(remove_punctuation(data))
            publisher['name'] = name
        elif tag == 'c' and index == 0 and data:

            # 4 digits
            date = re.match(r'.*?(\d{4}).*?', data).group(1)
            self['publicationYear'] = int(date)

            # # create free form if different
            # if data != str(self['publicationYear']):
            #     self['freeFormedPublicationDate'] = data
        indexes[tag] = index + 1
        lasttag = tag
    if publisher:
        publishers.append(publisher)
    if not publishers:
        return None
    return publishers


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
            self['extent'] = remove_punctuation(
                utils.force_list(value.get('a'))[0])
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
def marc21_to_titlesProper(self, key, value):
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


@marc21.over('electronic_location', '^8564.')
@utils.for_each_value
@utils.ignore_value
def marc21_online_resources(self, key, value):
    """Get online_resources data."""
    res = {'uri': value.get('u')}

    if value.get('3') == 'Image de couverture':
        self.setdefault('cover_art', value.get('u'))
        res = None
    else:
        res = {'uri': value.get('u')}
    return res
