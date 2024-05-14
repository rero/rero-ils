# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLOUVAIN
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


import contextlib
import re
import sys

from dojson import utils
from dojson.utils import GroupableOrderedDict
from iso639 import find

from rero_ils.dojson.utils import _LANGUAGES, TitlePartList, add_note, \
    build_identifier, build_responsibility_data, build_string_from_subfields, \
    error_print, extract_subtitle_and_parallel_titles_from_field_245_b, \
    get_field_items, get_field_link_data, get_mef_link, not_repetitive, \
    re_identified, remove_trailing_punctuation
from rero_ils.modules.documents.utils import create_authorized_access_point
from rero_ils.modules.entities.models import EntityType

_DOCUMENT_RELATION_PER_TAG = {
    '770': 'supplement',
    '772': 'supplementTo',
    '775': 'otherEdition',
    '776': 'otherPhysicalFormat',
    '777': 'issuedWith',
    '780': 'precededBy',
    '785': 'succeededBy',
    '787': 'relatedTo',
    '533': 'hasReproduction',
    '534': 'reproductionOf'
}

_REPRODUCTION_SUBFIELDS_PER_TAG = {
    '533': 'abcdemn',
    '534': 'cep'
}

_ISSUANCE_MAIN_TYPE_PER_BIB_LEVEL = {
    'a': 'rdami:1001',
    'b': 'rdami:1003',
    'c': 'rdami:1001',
    'd': 'rdami:1001',
    'i': 'rdami:1004',
    'm': 'rdami:1001',  # rdami:1002 if top_level record
    's': 'rdami:1003'
}

_ISSUANCE_SUBTYPE_PER_BIB_LEVEL = {
    'a': 'article',
    'b': 'serialInSerial',
    'c': 'privateFile',
    'd': 'privateSubfile'
}

_ISSUANCE_SUBTYPE_PER_SERIAL_TYPE = {
    'd': 'updatingWebsite',
    'w': 'updatingWebsite',
    'l': 'updatingLoose-leaf',
    'm': 'monographicSeries',
    'p': 'periodical'
}

_CONTRIBUTION_ROLE = [
    'aut', 'cmp', 'ctb', 'edt', 'hnr', 'ill', 'pht', 'prf', 'trl', 'abr',
    'act', 'adi', 'adp', 'aft', 'anm', 'ann', 'ape', 'apl', 'aqt', 'arc',
    'arr', 'art', 'ato', 'auc', 'aui', 'aus', 'bkd', 'bnd', 'brd', 'brl',
    'bsl', 'cas', 'chr', 'cll', 'clr', 'clt', 'cwt', 'cmm', 'cnd', 'cng',
    'cns', 'col', 'com', 'cor', 'cou', 'cre', 'crt', 'csl', 'cst', 'ctg',
    'ctr', 'cur', 'dfd', 'dgg', 'dgs', 'dnc', 'dnr', 'dpt', 'drm', 'drt',
    'dsr', 'dst', 'dte', 'dto', 'dub', 'edm', 'egr', 'enj', 'etr', 'exp',
    'fac', 'fds', 'fmd', 'fmk', 'fmo', 'fmp', 'his', 'hst', 'ill', 'ilu',
    'ins', 'inv', 'isb', 'itr', 'ive', 'ivr', 'jud', 'jug', 'lbt', 'lgd',
    'lsa', 'ltg', 'lyr', 'med', 'mfr', 'mod', 'msd', 'mtk', 'mus', 'nrt',
    'orm', 'osp', 'oth', 'own', 'pan', 'pat', 'pbd', 'pbl', 'plt', 'ppm',
    'ppt', 'pra', 'pre', 'prg', 'prm', 'prn', 'pro', 'prs', 'prt', 'ptf',
    'rcd', 'rce', 'rcp', 'rdd', 'res', 'rpc', 'rsp', 'rsr', 'scl', 'sds',
    'sgd', 'sll', 'sng', 'spk', 'spn', 'srv', 'stl', 'tch', 'tld', 'tlp',
    'trc', 'vac', 'vdg', 'wac', 'wal', 'wat', 'win', 'wpr', 'wst'
]

_INTENDED_AUDIENCE_REGEXP = {
    # understanding_level
    'target_understanding_children':
        re.compile(r'^(Enfants*|Kinder)$', re.IGNORECASE),
    'target_understanding_children_0_3':
        re.compile(
            r'(Enfants* \(0-3 ans\)|Kinder \(0-3 Jahre\))', re.IGNORECASE),
    'target_understanding_children_3_6':
        re.compile(
            r'(Enfants* \(3-6 ans\)|Kinder \(3-6 Jahre\))', re.IGNORECASE),
    'target_understanding_children_6_9':
        re.compile(
            r'(Enfants* \(6-9 ans\)|Kinder \(6-9 Jahre\))', re.IGNORECASE),
    'target_understanding_children_9_12':
        re.compile(
            r'(Enfants* \(9-12 ans\)|Kinder \(9-12 Jahre\))', re.IGNORECASE),
    'target_understanding_teenagers':
        re.compile(r'^(Adolescents*|Jugendliche)$', re.IGNORECASE),
    'target_understanding_teenagers_12_15':
        re.compile(
            r'(Adolescents* \(12-15 ans\)|Jugendliche \(12-15 Jahre\))',
            re.IGNORECASE),
    'target_understanding_teenagers_15_18':
        re.compile(
            r'(Adolescents* \(15-18 ans\)|Jugendliche \(15-18 Jahre\))',
            re.IGNORECASE),
    'target_understanding_secondary_level_2':
        re.compile(
            r'(Degré secondaire 2|Weiterführende Schulen)', re.IGNORECASE),
    'target_understanding_tertiary':
        re.compile(r'(Tertiaire|Tertiär)', re.IGNORECASE),
    'target_understanding_apprentices':
        re.compile(r'(Apprentis*|Lehrlinge)', re.IGNORECASE),
    'target_understanding_bachelor_students':
        re.compile(
            r'(Etudiants* niveau Bachelor|Studierende Bachelor)',
            re.IGNORECASE),
    'target_understanding_master_students':
        re.compile(
            r'(Etudiants* niveau Master|Studierende Master)', re.IGNORECASE),
    'target_understanding_doctoral_students':
        re.compile(r'(Doctorants*|Doktoranden)', re.IGNORECASE),
    'target_understanding_beginners':
        re.compile(r'(Débutants*|Anfänger)', re.IGNORECASE),
    'target_understanding_intermediaries':
        re.compile(r'(Intermédiaires*|Mittelstufe)', re.IGNORECASE),
    'target_understanding_advanced':
        re.compile(r'(Avancés*|Fortgeschrittene)', re.IGNORECASE),
    'target_understanding_specialists':
        re.compile(r'(Spécialistes*|Spezialisten)', re.IGNORECASE),
    'target_understanding_adults':
        re.compile(r'^(Adultes*|Erwachsene)$', re.IGNORECASE),
    'target_understanding_allophone_adults':
        re.compile(
            r'(Adultes* allophones*|Fremdsprachige Erwachsene)',
            re.IGNORECASE),
    'target_understanding_all_audience':
        re.compile(r'(Tous publics*|Alle Zielgruppen)', re.IGNORECASE),
    'target_understanding_teachers_harmos_degree':
        re.compile(
            r'(Enseignants* \(degré Harmos\)|Lehrpersonen \(Harmos\))',
            re.IGNORECASE),
    'target_understanding_teachers_secondary_level_2':
        re.compile(
            r'(Enseignants* Degré secondaire 2|Lehrpersonen Sek II)',
            re.IGNORECASE),
    'target_understanding_hep_trainers':
        re.compile(r'(Formateurs* HEP|PH-Dozierende)', re.IGNORECASE),
    'target_understanding_parents':
        re.compile(r'(Parents*|Eltern)', re.IGNORECASE),
    'target_understanding_caregivers':
        re.compile(r'(Soignants*|Pflegepersonal)', re.IGNORECASE),
    # school_level
    'target_school_harmos1':
        re.compile(r'(Harmos1|Kindergarten)', re.IGNORECASE),
    'target_school_harmos2':
        re.compile(r'(Harmos2|Kindergarten)', re.IGNORECASE),
    'target_school_harmos3':
        re.compile(r'(Harmos3|Primarschule \(1\.-2\. Kl\.\))', re.IGNORECASE),
    'target_school_harmos4':
        re.compile(r'(Harmos4|Primarschule \(1\.-2\. Kl\.\))', re.IGNORECASE),
    'target_school_harmos5':
        re.compile(r'(Harmos5|Primarschule \(3\.-4\. Kl\.\))', re.IGNORECASE),
    'target_school_harmos6':
        re.compile(r'(Harmos6|Primarschule \(3\.-4\. Kl\.\))', re.IGNORECASE),
    'target_school_harmos7':
        re.compile(r'(Harmos7|Primarschule \(5\.-6\. Kl\.\))', re.IGNORECASE),
    'target_school_harmos8':
        re.compile(r'(Harmos8|Primarschule \(5\.-6\. Kl\.\))', re.IGNORECASE),
    'target_school_harmos9':
        re.compile(
            r'(Harmos9|Orientierungsschule \(7\.-9\. Kl\.\))', re.IGNORECASE),
    'target_school_harmos10':
        re.compile(
            r'(Harmos10|Orientierungsschule \(7\.-9\. Kl\.\))', re.IGNORECASE),
    'target_school_harmos11':
        re.compile(
            r'(Harmos11|Orientierungsschule \(7\.-9\. Kl\.\))', re.IGNORECASE),
    'target_school_upper_secondary':
        re.compile(
            r'(Degré secondaire 2|Weiterführende Schulen)', re.IGNORECASE),
    'target_school_tertiary':
        re.compile(r'^(Tertiaire|Studierende)$', re.IGNORECASE),
    'target_school_bachelor':
        re.compile(
            r'(Etudiants* niveau Bachelor|Studierende Bachelor)',
            re.IGNORECASE),
    'target_school_master':
        re.compile(
            r'(Etudiants* niveau Master|Studierende Master)', re.IGNORECASE),
    # filmage_ch
    'from the age of 18':
        re.compile(r'(Dès 18 ans|Ab 18 Jahre)', re.IGNORECASE),
    'from the age of 16':
        re.compile(r'(Dès 16 ans|Ab 16 Jahre)', re.IGNORECASE),
    'from the age of 14':
        re.compile(r'(Dès 14 ans|Ab 14 Jahre)', re.IGNORECASE),
    'from the age of 12':
        re.compile(r'(Dès 12 ans|Ab 12 Jahre)', re.IGNORECASE),
    'from the age of 10':
        re.compile(r'(Dès 10 ans|Ab 10 Jahre)', re.IGNORECASE),
    'from the age of 7':
        re.compile(r'(Dès 7 ans|Ab 7 Jahre)', re.IGNORECASE),
    'from the age of 5':
        re.compile(r'(Dès 5 ans|Ab 5 Jahre)', re.IGNORECASE),
    'from the age of 2':
        re.compile(r'(Dès 2 ans|Ab 2 Jahre)', re.IGNORECASE)}

_INTENDED_AUDIENCE_TYPE_REGEXP = {
    'understanding_level': re.compile(r'^target_understanding'),
    'school_level': re.compile(r'^target_school'),
    'filmage_ch': re.compile(r'^from the age of')
}

_LONGITUDE = re.compile(r'^[EW0-9.+-]+(\\s[EW0-9.+-]+)?')
_LATITUDE = re.compile(r'^[NS0-9.+-]+(\\s[NS0-9.+-]+)?')

_PERIOD_CODE = re.compile(r'^([a-z][0-9-]){2}$')

_SCALE_TYPE = {
    'a': 'Linear scale',
    'b': 'Angular scale',
    'z': 'Other'
}

re_reroils = re.compile(r'(^REROILS:)(.*)')
re_electonic_locator = re.compile(r'^(ftps?|https?)://.*$')


def do_issuance(data, marc21):
    """Get document content/Media/Carrier type and mode of issuance."""
    if marc21.content_media_carrier_type:
        data['contentMediaCarrier'] = marc21.content_media_carrier_type
    if marc21.langs_from_041_h:
        data['originalLanguage'] = marc21.langs_from_041_h
    if marc21.admin_meta_data:
        data['adminMetadata'] = marc21.admin_meta_data
    main_type = _ISSUANCE_MAIN_TYPE_PER_BIB_LEVEL.get(
        marc21.bib_level, 'rdami:1001')
    sub_type = 'NOT_DEFINED'
    error = False
    if marc21.bib_level == 'm':
        if marc21.is_top_level_record:
            main_type = 'rdami:1002'
            sub_type = 'set'
        else:
            sub_type = 'materialUnit'
    elif marc21.bib_level in _ISSUANCE_SUBTYPE_PER_BIB_LEVEL:
        sub_type = _ISSUANCE_SUBTYPE_PER_BIB_LEVEL[marc21.bib_level]
    elif marc21.serial_type in _ISSUANCE_SUBTYPE_PER_SERIAL_TYPE:
        sub_type = _ISSUANCE_SUBTYPE_PER_SERIAL_TYPE[marc21.serial_type]
    if main_type == 'rdami:1001':
        if sub_type not in [
                'article', 'materialUnit', 'privateFile', 'privateSubfile'
        ]:
            error = True
            sub_type = 'materialUnit'
    elif main_type == 'rdami:1002':
        if sub_type not in [
                'set', 'partIndependentTitle', 'partDependantTitle'
        ]:
            error = True
            sub_type = 'set'
    elif main_type == 'rdami:1003':
        if sub_type not in [
            'serialInSerial', 'monographicSeries', 'periodical'
        ]:
            error = True
            sub_type = 'periodical'
    elif main_type == 'rdami:1004':
        if sub_type not in ['updatingWebsite', 'updatingLoose-leaf']:
            error = True
            sub_type = 'updatingWebsite'
    if error:
        error_print('WARNING ISSUANCE:', marc21.bib_id, marc21.rero_id,
                    main_type, sub_type, marc21.bib_level, marc21.serial_type)
    data['issuance'] = {'main_type': main_type, 'subtype': sub_type}


def do_type(data, marc21):
    """Get document type."""
    doc_type = [{"main_type": "docmaintype_other"}]
    if marc21.record_type == 'a':
        if marc21.bib_level == 'm':
            doc_type = [{
                "main_type": "docmaintype_book",
                "subtype": "docsubtype_other_book"
            }]

            field_008 = None
            field_008 = marc21.get_fields('008')
            # if it's an electronic book
            if field_008[0]['data'][23] in ('o', 's'):
                doc_type = [{
                    "main_type": "docmaintype_book",
                    "subtype": "docsubtype_e-book"
                 }]
        elif marc21.bib_level == 's':
            doc_type = [{
                "main_type": "docmaintype_serial"
            }]
        elif marc21.bib_level == 'a':
            doc_type = [{
                "main_type": "docmaintype_article",
            }]
        elif marc21.record_type in ['c', 'd']:
            doc_type = [{
                "main_type": "docmaintype_score",
                "subtype": "docsubtype_printed_score"
            }]
        elif marc21.record_type in ['i', 'j']:
            doc_type = [{
                "main_type": "docmaintype_audio",
                "subtype": "docsubtype_music"
            }]
        elif marc21.record_type == 'g':
            doc_type = [{
                "main_type": "docmaintype_movie_series",
                "subtype": "docsubtype_movie"
            }]
    data['type'] = doc_type


def do_language(data, marc21):
    """Get languages.

    languages: 008 and 041 [$a, repetitive]
    """
    language = data.get('language', [])
    lang_codes = [v.get('value') for v in language]
    if marc21.lang_from_008:
        lang_value = marc21.lang_from_008
        if lang_value != '|||' and lang_value not in lang_codes:
            language.append({
                'value': lang_value,
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
    # language note
    if fields_546 := marc21.get_fields(tag='546'):
        subfields_546_a = marc21.get_subfields(fields_546[0], 'a')
        if subfields_546_a and language:
            language[0]['note'] = subfields_546_a[0]

    if not language:
        error_print(
            'ERROR LANGUAGE:', marc21.bib_id, f'f{language} set to "und"')
        language = [{'value': 'und', 'type': 'bf:Language'}]
    return language or None


def do_abbreviated_title(data, marc21, key, value):
    """Get abbreviated title data.

    * bf:AbbreviatedTitle = 210
    * bf:KeyTitle = 222
    * mainTitle = $a
    * subtitle = $e
    * responsibilityStatement = $f|$g
    * language = voir $7
    * partNumber = $h
    * partName = $i
    """
    title_list = data.get('title', [])
    title = {}
    if value.get('a'):
        main_title = not_repetitive(
            marc21.bib_id, marc21.bib_id, key, value, 'a')
        title_type = 'bf:KeyTitle' if key[:3] == '222' \
            else 'bf:AbbreviatedTitle'
        title = {
            'type': title_type,
            'mainTitle': [{'value': main_title}]
        }
        if value.get('b'):
            subtitle = not_repetitive(
                marc21.bib_id, marc21.bib_id, key, value, 'b')
            title['subtitle'] = [{'value': subtitle}]
        for resp_tag in ['f', 'g']:
            if datas := utils.force_list(value.get(resp_tag)):
                for data in datas:
                    if responsibility := build_responsibility_data(data):
                        new_responsibility = data.get(
                            'responsibilityStatement', [])
                        for resp in responsibility:
                            new_responsibility.append(resp)
                        data['responsibilityStatement'] = new_responsibility
    if title:
        title_list.append(title)
    return title_list or None


def do_title(data, marc21, value):
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
    if fields_245 := marc21.get_fields(tag='245'):
        subfields_245_a = marc21.get_subfields(fields_245[0], 'a')
        subfields_245_b = marc21.get_subfields(fields_245[0], 'b')
        if subfields_245_a:
            subfield_245_a = subfields_245_a[0]
        if subfields_245_b:
            subfield_245_b = subfields_245_b[0]
    field_245_a_end_with_equal = re.search(r'\s*=\s*$', subfield_245_a)

    fields_246 = marc21.get_fields('246')
    subfield_246_a = ''
    if fields_246:
        if subfields_246_a := marc21.get_subfields(fields_246[0], 'a'):
            subfield_246_a = subfields_246_a[0]

    _, link = get_field_link_data(value)
    items = get_field_items(value)
    index = 1
    title_list = data.get('title', [])
    title_data = {}
    part_list = TitlePartList(part_number_code='n', part_name_code='p')
    parallel_titles = []
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
                if value_data:
                    # if title contains << >>, remove it
                    # Ex: <<Les>> beaux dégâts
                    value_data[0]['value'] = value_data[0]['value']\
                        .replace('<<', '').replace('>>', '')
                    title_data['mainTitle'] = value_data
            elif blob_key == 'b':
                if subfield_246_a:
                    subtitle, parallel_titles, pararalel_title_string_set = \
                        extract_subtitle_and_parallel_titles_from_field_245_b(
                            value_data, field_245_a_end_with_equal)
                    if subtitle:
                        title_data['subtitle'] = subtitle
                elif value_data:
                    title_data['subtitle'] = value_data
            elif blob_key == 'c' and value_data:
                responsibility = build_responsibility_data(value_data)
            elif blob_key in ['n', 'p']:
                part_list.update_part(value_data, blob_key, blob_value)

        if blob_key != '__order__':
            index += 1
    title_data['type'] = 'bf:Title'
    if the_part_list := part_list.get_part_list():
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
        new_responsibility = data.get('responsibilityStatement', [])
        for resp in responsibility:
            new_responsibility.append(resp)
        data['responsibilityStatement'] = new_responsibility
    return title_list or None


def build_agent(marc21, key, value):
    """Build agent."""
    agent_data = {}
    if value.get('a'):
        agent_data['preferred_name'] = remove_trailing_punctuation(
            not_repetitive(marc21.bib_id, marc21.bib_id, key, value, 'a'))
    # 100|700|240 Person
    if key[:3] in ['100', '700']:
        agent_data['type'] = EntityType.PERSON
        if value.get('b'):
            numeration = not_repetitive(
                marc21.bib_id, marc21.bib_id, key, value, 'b')
            agent_data['numeration'] = remove_trailing_punctuation(
                numeration)
        if value.get('c'):
            qualifier = not_repetitive(
                marc21.bib_id, marc21.bib_id, key, value, 'c')
            agent_data['qualifier'] = remove_trailing_punctuation(
                qualifier)
        if value.get('d'):
            date = not_repetitive(
                marc21.bib_id, marc21.bib_id, key, value, 'd')
            date = date.rstrip(',')
            dates = remove_trailing_punctuation(date).split('-')
            with contextlib.suppress(Exception):
                if date_of_birth := dates[0].strip():
                    agent_data['date_of_birth'] = date_of_birth
            with contextlib.suppress(Exception):
                if date_of_death := dates[1].strip():
                    agent_data['date_of_death'] = date_of_death
        if value.get('q'):
            fuller_form_of_name = not_repetitive(
                marc21.bib_id, marc21.bib_id, key, value, 'q')
            agent_data[
                'fuller_form_of_name'] = remove_trailing_punctuation(
                fuller_form_of_name
            ).lstrip('(').rstrip(')')

    # 710|711 Organisation
    if key[:3] in ['710', '711']:
        agent_data['type'] = EntityType.ORGANISATION
        agent_data['conference'] = key[:3] == '711'
        if value.get('b'):
            subordinate_units = [
                remove_trailing_punctuation(subordinate_unit, ',.')
                for subordinate_unit in utils.force_list(value.get('b'))
            ]
            agent_data['subordinate_unit'] = subordinate_units
        if value.get('n'):
            numbering = not_repetitive(
                marc21.bib_id, marc21.bib_id, key, value, 'n')

            if numbering := remove_trailing_punctuation(
                    numbering).lstrip('(').rstrip(')'):
                agent_data['numbering'] = numbering
        if value.get('d'):
            conference_date = not_repetitive(
                marc21.bib_id, marc21.bib_id, key, value, 'd')
            agent_data['conference_date'] = remove_trailing_punctuation(
                conference_date
            ).lstrip('(').rstrip(')')
        if value.get('c'):
            place = not_repetitive(
                marc21.bib_id, marc21.bib_id, key, value, 'c')
            agent_data['place'] = remove_trailing_punctuation(
                place
            ).lstrip('(').rstrip(')')
    if not agent_data:
        return
    return {
        'type': agent_data.get('type'),
        'authorized_access_point': create_authorized_access_point(agent_data)
        }, agent_data


def do_contribution(data, marc21, key, value):
    """Get contribution."""
    # exclude work access points
    if key[:3] in ['700', '710'] and value.get('t'):
        if work_access_point := do_work_access_point(marc21, key, value):
            data.setdefault('work_access_point', [])
            data['work_access_point'].append(work_access_point)
        return None

    agent = {}
    if value.get('a'):
        agent_data = build_agent(marc21=marc21, key=key, value=value)[0]

        if ref := get_mef_link(
            bibid=marc21.bib_id,
            reroid=marc21.rero_id,
            entity_type=EntityType.PERSON,
            ids=utils.force_list(value.get('0')),
            key=key
        ):
            agent = {
                '$ref': ref,
                '_text':  agent_data['authorized_access_point']
            }
        else:
            agent = agent_data

        if value.get('4'):
            roles = set()
            for role in utils.force_list(value.get('4')):
                role = role.split('/')[-1].lower()
                if len(role) != 3:
                    error_print('WARNING CONTRIBUTION ROLE LENGTH:',
                                marc21.bib_id, marc21.rero_id, role)
                if role == 'sce':
                    error_print('WARNING CONTRIBUTION ROLE SCE:',
                                marc21.bib_id, marc21.rero_id,
                                'sce --> aus')
                    role = 'aus'
                if role not in _CONTRIBUTION_ROLE:
                    error_print('WARNING CONTRIBUTION ROLE DEFINITION:',
                                marc21.bib_id, marc21.rero_id, role)
                    role = 'ctb'
                roles.add(role)
        elif key[:3] == '100':
            roles = ['cre']
        elif key[:3] == '711':
            roles = ['aut']
        else:
            roles = ['ctb']
        if agent:
            return {
                'entity': agent,
                'role': list(roles)
            }


def do_specific_document_relation(data, marc21, key, value):
    """Get document relation."""
    tag = key[:3]
    relation = None
    if tag in ['533', '534']:
        label = build_string_from_subfields(
            value,
            _REPRODUCTION_SUBFIELDS_PER_TAG[tag]
        )
        relation = {'label': label}
    elif subfield_w := not_repetitive(
            marc21.bib_id, marc21.rero_id,
            key, value, 'w', default='').strip():
        pid = None
        if match := re_reroils.match(subfield_w):
            source = match.group(1)
            pid = match.group(2)
        if pid and source == ('REROILS:'):
            # TODO: find a way to use a parameter for ref
            ref = f'https://bib.rero.ch/api/documents/{pid}'
            relation = {'$ref': ref}
        else:
            label = build_string_from_subfields(value, 'ctw')
            relation = {'label': label}
    if relation and (relation.get('label') or relation.get('$ref')):
        relation_tag = _DOCUMENT_RELATION_PER_TAG[tag]
        relation_list = data.get(relation_tag, [])
        relation_list.append(relation)
        data[relation_tag] = relation_list


def do_copyright_date(data, value):
    """Get Copyright Date."""
    copyright_dates = data.get('copyrightDate', [])
    for copyright_date in utils.force_list(value.get('c', [])):
        if match := re.search(r'^([©℗])+\s*(\d{4}.*)', copyright_date):
            copyright_date = ' '.join((match[1], match[2]))
            copyright_dates.append(copyright_date)
            # else:
            #     raise ValueError('Bad format of copyright date')
    return copyright_dates or None


def do_edition_statement(marc21, value):
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
            edition_designation = marc21.build_value_with_alternate_graphic(
                '250', blob_key, blob_value, index, link, ',.', ':;/-=')
            if edition_designation:
                edition_data[key_per_code[blob_key]] = edition_designation
        if blob_key != '__order__':
            index += 1
    return edition_data or None


def do_provision_activity(data, marc21, key, value):
    """Get publisher data.

    publisher.name: 264 [$b repetitive] (without the , but keep the ;)
    publisher.place: 264 [$a repetitive] (without the : but keep the ;)
    publicationDate: 264 [$c repetitive] (but take only the first one)
    """
    tag = key[:3]

    def correct_b_after_e(field_value):
        """Corrects wrong $b after $e."""
        new_field_values = []
        last_key = ''
        for blob_key, blob_value in get_field_items(field_value):
            if last_key == 'e' and blob_key == 'b':
                blob_key = 'f'
            new_field_values.append((blob_key, blob_value))
            last_key = blob_key
        return GroupableOrderedDict(new_field_values)

    def build_statement(field_value, subtags=('a', 'b')):

        def build_agent_data(code, label, index, link):
            type_per_code = {
                'a': EntityType.PLACE,
                'b': EntityType.AGENT,
                'e': EntityType.PLACE,
                'f': EntityType.AGENT
            }
            label = remove_trailing_punctuation(label)
            if label and code == 'e':
                label = label.lstrip('(')
            if label and code == 'f':
                label = label.rstrip(')')

            if not label:
                return None
            agent_data = {
                'type': type_per_code[code],
                'label': [{'value': label}]
            }
            with contextlib.suppress(Exception):
                alt_gr = marc21.alternate_graphic[tag][link]
                subfield = \
                    marc21.get_subfields(alt_gr['field'])[index]
                if subfield := remove_trailing_punctuation(subfield):
                    agent_data['label'].append({
                        'value': subfield,
                        'language': marc21.get_language_script(
                            alt_gr['script'])
                    })
            if identifier := build_identifier(value):
                agent_data['identifiedBy'] = identifier

            return agent_data

        # function build_statement start here
        _, link = get_field_link_data(field_value)
        items = get_field_items(field_value)
        statement = []
        index = 1
        for blob_key, blob_value in items:
            if blob_key in subtags:
                agent_data = build_agent_data(
                    blob_key, blob_value, index, link)
                if agent_data:
                    statement.append(agent_data)
            if blob_key != '__order__':
                index += 1
        return statement or None

    # the function marc21_to_provision_activity start here
    ind2 = key[4]
    type_per_ind2 = {
        ' ': 'bf:Publication',
        '_': 'bf:Publication',
        '0': 'bf:Production',
        '1': 'bf:Publication',
        '2': 'bf:Distribution',
        '3': 'bf:Manufacture'
    }
    if tag == '260':
        ind2 = '1'
        value = correct_b_after_e(value)
    publication = {'type': type_per_ind2[ind2]}

    if ind2 in ('_', ' ', '1'):
        publication['startDate'] = marc21.date['start_date']
        if 'end_date' in marc21.date:
            publication['endDate'] = marc21.date['end_date']
        if 'note' in marc21.date:
            publication['note'] = marc21.date['note']

        places = []
        place = marc21.build_place()
        if place and place.get('country') != 'xx':
            places.append(place)
        # parce the link skipping the fist (already used by build_place)
        for i in range(1, len(marc21.links_from_752)):
            place = {
                'country': 'xx'
            }
            if marc21.links_from_752:
                place['identifiedBy'] = marc21.links_from_752[i]
            places.append(place)
        if places:
            publication['place'] = places
    subfield_3 = not_repetitive(
        marc21.bib_id, marc21.rero_id, key, value, '3')
    if subfield_3:
        notes = []
        if pub_notes := publication.get('note'):
            notes = [pub_notes]
        notes.append(subfield_3)
        publication['note'] = ', '.join(notes)

    if statement := build_statement(value):
        publication['statement'] = statement

    if subfields_c := utils.force_list(value.get('c', [])):
        subfield_c = subfields_c[0]
        date = {
            'label': [{'value': subfield_c}],
            'type': 'Date'
        }

        _, link = get_field_link_data(value)
        with contextlib.suppress(Exception):
            alt_gr = marc21.alternate_graphic['264'][link]
            subfield = \
                marc21.get_subfields(alt_gr['field'], code='c')
            date['label'].append({
                    'value': subfield[0],
                    'language': marc21.get_language_script(
                        alt_gr['script'])
            })
        publication.setdefault('statement', [])
        publication['statement'].append(date)
    # make second provision activity for 260 $ e $f $g
    if tag == '260':
        publication_260 = {'type': 'bf:Manufacture'}
        if statement := build_statement(value, ('e', 'f')):
            publication_260['statement'] = statement
        if subfields_g := utils.force_list(value.get('g', [])):
            subfield_g = subfields_g[0]
            date = {
                'label': [{'value': subfield_g}],
                'type': 'Date'
            }
            publication_260.setdefault('statement', [])
            publication_260['statement'].append(date)
        if statement or subfields_g:
            publications = data.setdefault('provisionActivity', [])
            if publication:
                publications.append(publication)
                publication = None
            publications.append(publication_260)
            data['provisionActivity'] = publications

    return publication or None


def do_table_of_contents(data, value):
    """Get tableOfContents from repetitive field 505."""
    if table_of_contents := build_string_from_subfields(value, 'agtr'):
        table_of_contents_list = data.get('tableOfContents', [])
        table_of_contents_list.append(table_of_contents)
        data['tableOfContents'] = table_of_contents_list


def do_usage_and_access_policy_from_field_506_540(marc21, key, value):
    """Get usageAndAccessPolicy from fields: 506, 540."""
    if subfield_a := not_repetitive(
            marc21.bib_id, marc21.rero_id,
            key, value, 'a', default='').strip():
        return {'type': 'bf:UsageAndAccessPolicy', 'label': subfield_a}


def do_frequency_field_310_321(marc21, key, value):
    """Get frequency from fields: 310, 321."""
    subfield_a = not_repetitive(
        marc21.bib_id, marc21.rero_id,
        key, value, 'a', default='missing_label').strip()
    subfield_b = not_repetitive(
        marc21.bib_id, marc21.rero_id,
        key, value, 'b', default='').strip()

    frequency = {
        'label': remove_trailing_punctuation(
                    data=subfield_a,
                    punctuation=',',
                    spaced_punctuation=','
                )
        }
    if subfield_b:
        frequency['date'] = subfield_b
    return frequency


def do_dissertation(marc21, value):
    """Get dissertation from repetitive field 502."""
    # parse field 502 subfields for extracting dissertation
    _, link = get_field_link_data(value)
    items = get_field_items(value)
    index = 1
    dissertation = {}
    subfield_selection = {'a'}
    for blob_key, blob_value in items:
        if blob_key in subfield_selection:
            subfield_selection.remove(blob_key)
            if blob_key == 'a':
                dissertation_data = marc21.build_value_with_alternate_graphic(
                    '502', blob_key, blob_value, index, link, ',.', ':;/-=')
            else:
                dissertation_data = blob_value
            if dissertation_data:
                dissertation['label'] = dissertation_data
        if blob_key != '__order__':
            index += 1
    return dissertation or None


def do_summary(marc21, value):
    """Get summary from repetitive field 520."""
    key_per_code = {
        'a': 'label',
        'c': 'source'
    }
    # parse field 520 subfields for extracting:
    # summary and source parts
    tag_link, link = get_field_link_data(value)
    items = get_field_items(value)
    index = 1
    summary = {}
    subfield_selection = {'a', 'c'}
    for blob_key, blob_value in items:
        if blob_key in subfield_selection:
            subfield_selection.remove(blob_key)
            if blob_key == 'a':
                summary_data = marc21.build_value_with_alternate_graphic(
                    '520', blob_key, blob_value, index, link, ',.', ':;/-=')
            else:
                summary_data = blob_value
            if summary_data:
                summary[key_per_code[blob_key]] = summary_data
        if blob_key != '__order__':
            index += 1
    return summary or None


def do_intended_audience(data, value):
    """Get intendedAudience from field 521."""
    intended_audience_set = set()
    for subfield_a in utils.force_list(value.get('a')):
        audiance_found = False
        for audiance in _INTENDED_AUDIENCE_REGEXP:
            regexp = _INTENDED_AUDIENCE_REGEXP[audiance]
            if regexp.search(subfield_a):
                intended_audience_set.add(audiance)
                audiance_found = True
        if not audiance_found:
            intended_audience_set.add(subfield_a)

    intended_audience_list = data.get('intendedAudience', [])
    for intended_audience_str in intended_audience_set:
        intended_audience = {}
        # get the audiance_type
        for audiance_type in _INTENDED_AUDIENCE_TYPE_REGEXP:
            regexp = _INTENDED_AUDIENCE_TYPE_REGEXP[audiance_type]
            if regexp.search(intended_audience_str):
                intended_audience['audienceType'] = audiance_type
        if 'audienceType' not in intended_audience:
            intended_audience['audienceType'] = 'undefined'
        intended_audience['value'] = intended_audience_str
        intended_audience_list.append(intended_audience)
        data['intendedAudience'] = intended_audience_list


def do_identified_by_from_field_010(data, marc21, key, value):
    """Get identifier from field 010."""
    def build_identifier_from(subfield_data, identified_by):
        subfield_data = subfield_data.strip()
        identifier = {'value': subfield_data}
        if not_repetitive(marc21.bib_id, marc21.rero_id,
                          key, value, 'a', default='').strip():
            identifier['type'] = 'bf:Lccn'
            identified_by.append(identifier)
        return identified_by

    identified_by = data.get('identifiedBy', [])
    subfield_a = not_repetitive(marc21.bib_id, marc21.rero_id, key, value, 'a')
    if subfield_a:
        identified_by = build_identifier_from(subfield_a, identified_by)
        data['identifiedBy'] = identified_by


def do_identified_by_from_field_020(data, marc21, key, value):
    """Get identifier from field 020."""
    def build_identifier_from(subfield_data, identified_by, status=None):
        subfield_data = subfield_data.strip()
        identifier = {'value': subfield_data}
        if value.get('q'):  # $q is repetitive
            identifier['qualifier'] = \
                ', '.join(utils.force_list(value.get('q')))

        if match := re.search(r'^(.+?)\s*\((.+)\)$', subfield_data):
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
        identified_by.append(identifier)
        return identified_by

    identified_by = data.get('identifiedBy', [])
    subfield_a = not_repetitive(marc21.bib_id, marc21.rero_id, key, value, 'a')
    if subfield_a:
        build_identifier_from(subfield_a, identified_by)
    subfield_c = not_repetitive(marc21.bib_id, marc21.rero_id,
                                key, value, 'c', default='').strip()
    if subfield_c:
        acquisition_terms = data.get('acquisitionTerms', [])
        acquisition_terms.append(subfield_c)
        data['acquisitionTerms'] = acquisition_terms
    for subfield_z in utils.force_list(value.get('z', [])):
        identified_by = build_identifier_from(
            subfield_z, identified_by, status='invalid or cancelled')
    if identified_by:
        data['identifiedBy'] = identified_by


def do_identified_by_from_field_022(data, value):
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

    identified_by = data.get('identifiedBy', [])
    for subfield_code in ['a', 'l', 'm', 'y']:
        if subfields_data := value.get(subfield_code):
            if isinstance(subfields_data, str):
                subfields_data = [subfields_data]
            for subfield_data in subfields_data:
                subfield_data = subfield_data.strip()
                identifier = {
                    'type': type_for[subfield_code], 'value': subfield_data}
                if subfield_code in status_for:
                    identifier['status'] = status_for[subfield_code]
                identified_by.append(identifier)
    if identified_by:
        data['identifiedBy'] = identified_by


def do_identified_by_from_field_024(data, marc21, key, value):
    """Get identifier from field 024."""
    def populate_acquisitionTerms_note_qualifier(identifier):
        if subfield_c := not_repetitive(
                marc21.bib_id,
                marc21.rero_id,
                key, value, 'c', default='').strip():
            acquisition_terms = data.get('acquisitionTerms', [])
            acquisition_terms.append(subfield_c)
            data['acquisitionTerms'] = acquisition_terms
        if subfield_d := not_repetitive(
                marc21.bib_id, marc21.rero_id,
                key, value, 'd', default='').strip():
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
    subfield_a = not_repetitive(marc21.bib_id,  marc21.rero_id,
                                key, value, 'a', default='').strip()
    subfield_2 = not_repetitive(marc21.bib_id, marc21.rero_id,
                                key, value, '2', default='').strip()
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
                    identifier['qualifier'] = ', '.join(filter(
                        None,
                        [match.group(2), identifier.get('qualifier', '')]
                    ))
                    # value without parenthesis and parentheses content
                    identifier['value'] = match.group(1)
                else:
                    identifier['value'] = subfield_a
                if 'type' in type_for_ind1[ind1]:  # ind1 0,1
                    identifier['type'] = type_for_ind1[ind1]['type']

                else:  # ind1 in (2, 3, 8)
                    tmp = subfield_a
                    if ind1 == '8':
                        tmp = identifier['value']
                    if re.search(type_for_ind1[ind1]['pattern'], tmp):
                        identifier['type'] = \
                            type_for_ind1[ind1]['matching_type']
                    else:
                        identifier['type'] = 'bf:Identifier'
            else:  # ind1 not in (0, 1, 2, 3, 8)
                identifier.update({
                    'value': subfield_a,
                    'type': 'bf:Identifier'
                })
        if not identifier.get('type'):
            identifier['type'] = 'bf:Identifier'
        identified_by = data.get('identifiedBy', [])
        identified_by.append(identifier)
        data['identifiedBy'] = identified_by


def do_identified_by_from_field_028(data, marc21, key, value):
    """Get identifier from field 028."""
    identified_by = data.get('identifiedBy', [])
    if subfield_a := not_repetitive(
            marc21.bib_id, marc21.rero_id,
            key, value, 'a', default='').strip():
        identifier = {'value': subfield_a}
        if value.get('q'):  # $q is repetitive
            identifier['qualifier'] = \
                ', '.join(utils.force_list(value.get('q')))
        if subfield_b := not_repetitive(
                marc21.bib_id, marc21.rero_id,
                key, value, 'b', default='').strip():
            identifier['source'] = subfield_b
        type_for_ind1 = {
            '0': 'bf:AudioIssueNumber',
            '1': 'bf:MatrixNumber',
            '2': 'bf:MusicPlate',
            '3': 'bf:MusicPublisherNumber',
            '4': 'bf:VideoRecordingNumber',
            '5': 'bf:PublisherNumber',
            '6': 'bf:MusicDistributorNumber'
        }

        # key[3] is the indicateur_1
        identifier['type'] = type_for_ind1.get(key[3], 'bf:Identifier')
        identified_by.append(identifier)
        data['identifiedBy'] = identified_by


def do_identified_by_from_field_035(data, marc21, key, value, source=None):
    """Get identifier from field 035."""
    identified_by = data.get('identifiedBy', [])
    if subfield_a := not_repetitive(
            marc21.bib_id, marc21.rero_id,
            key, value, 'a', default='').strip():
        value = subfield_a
        # search source between parenthesis
        if match := re_identified.match(subfield_a):
            source = match.group(1)
            value = match.group(2)
        if source and value:
            identifier = {
                'value': value,
                'source': source,
                'type': 'bf:Local',
            }
            identified_by.append(identifier)
            data['identifiedBy'] = identified_by


def do_acquisition_terms_from_field_037(data, value):
    """Get acquisition terms field 037."""
    acquisition_terms = data.get('acquisitionTerms', [])
    if subfields_c := utils.force_list(value.get('c')):
        for subfield_c in subfields_c:
            acquisition_terms.append(subfield_c.strip())
        data['acquisitionTerms'] = acquisition_terms


def do_electronic_locator_from_field_856(data, marc21, key, value):
    """Get electronicLocator from field 856."""
    electronic_locators = data.get('electronicLocator', [])
    if value.get('u'):
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
        content = utils.force_list(value.get('3'))[0] if value.get('3') else \
            None
        public_note = []
        if content and content not in electronic_locator_content:
            public_note.append(content)
        if value.get('y'):
            public_note.extend(iter(utils.force_list(value.get('y'))))
        if value.get('z'):
            public_note.extend(iter(utils.force_list(value.get('z'))))
        for url in utils.force_list(value.get('u')):
            electronic_locator = {
                'url': url,
                'type': electronic_locator_type.get(indicator2, 'noInfo')
            }
            if content and content in electronic_locator_content:
                electronic_locator['content'] = content
            if public_note:
                electronic_locator['publicNote'] = public_note
            if re_electonic_locator.match(url):
                electronic_locators.append(electronic_locator)
            else:
                error_print('WARNING ELECTRONICLOCATOR:', marc21.bib_id,
                            marc21.rero_id, url)
    return electronic_locators or None


def do_notes_and_original_title(data, key, value):
    """Get notes and original title."""
    subfield_a = None
    if value.get('a'):
        subfield_a = utils.force_list(value.get('a'))[0]
        is_original_title_data = False
        is_general_note_to_add = False
        if key[:3] == '510':
            items = get_field_items(value)
            subfield_selection = {'a', 'c', 'x'}
            note_str = ''.join(f'{blob_value} ' for blob_key, blob_value
                               in items if blob_key in subfield_selection)

            add_note(
                dict(noteType='cited_by', label=note_str.strip()),
                data
            )
        elif key[:3] == '500':
            # extract the original title
            regexp = re.compile(
                r'\[?(Trad.+?de|Über.+?von|Trans.+?from|Titre original|'
                r'Originaltitel|Original title)\s?\:\]?\s?(.+)',
                re.IGNORECASE)
            match = regexp.search(subfield_a)
            if match and match.group(2):
                original_title = match.group(2).strip()
                original_titles = data.get('originalTitle', [])
                original_titles.append(original_title)
                data['originalTitle'] = original_titles
            else:
                is_general_note_to_add = True
        else:
            is_general_note_to_add = True

        if is_general_note_to_add:
            add_note(
                dict(noteType='general', label=subfield_a),
                data
            )


def do_credits(key, value):
    """Get notes and original title."""
    if value.get('a'):
        subfield_a = utils.force_list(value.get('a'))[0]
        if key[:3] == '511':
            subfield_a = f'Participants ou interprètes: {subfield_a}'
        return subfield_a


def do_sequence_numbering(data, value):
    """Get notes and original title."""
    if value.get('a'):
        subfield_a = utils.force_list(value.get('a'))[0]
        sequence_numbering = data.get('sequence_numbering', '')
        if sequence_numbering:
            sequence_numbering += f' ; {subfield_a}'
        else:
            sequence_numbering = subfield_a
        data['sequence_numbering'] = sequence_numbering


def do_classification(data, key, value):
    """Get classification and subject from 980."""
    classification_type_per_tag = {
        '050': 'bf:ClassificationLcc',
        '060': 'bf:ClassificationNlm',
        '080': 'bf:ClassificationUdc',
        '082': 'bf:ClassificationDdc',
    }

    tag = key[:3]
    indicator1 = key[3]
    indicator2 = key[4]
    subfield_2 = None
    if subfields_2 := utils.force_list(value.get('2')):
        subfield_2 = subfields_2[0]
    for subfield_a in utils.force_list(value.get('a', [])):
        classification = {
            'classificationPortion': subfield_a,
            'type': classification_type_per_tag[tag]
        }
        # LCC classification
        if tag == '050' and indicator2 == '0':
            classification['assigner'] = 'LOC'
        # NLM classification
        elif tag == '060' and indicator2 == '0':
            classification['assigner'] = 'NLM'
        # UDC classification
        elif tag == '080':
            if subfields_x := utils.force_list(value.get('x')):
                classification['subdivision'] = list(subfields_x)
            edition_parts = []
            if indicator1 == '0':
                edition_parts.append('Full edition')
            elif indicator1 == '1':
                edition_parts.append('Abridged edition')
            if subfield_2:
                edition_parts.append(subfield_2)
            if edition_parts:
                classification['edition'] = ', '.join(edition_parts)
        # DDC classification
        elif tag == '082':
            subfields_q = utils.force_list(value.get('q'))
            subfield_q = None
            edition_parts = []
            if subfields_q:
                subfield_q = subfields_q[0]
            if indicator2 == '0':
                classification['assigner'] = 'LOC'
            elif subfield_q:
                classification['assigner'] = subfield_q
            if indicator1 == '0':
                edition_parts.append('Full edition')
            elif indicator1 == '1':
                edition_parts.append('Abridged edition')
            if subfield_2:
                edition_parts.append(subfield_2)
            if edition_parts:
                classification['edition'] = ', '.join(edition_parts)

        if classification:
            data.setdefault('classification', []).append(classification)


def do_part_of(data, marc21, key, value):
    r"""Get part_of.

    The 773 $g can have multiple pattern, most important is to find the year
    (94% of $g start with pattern '\d{4}'
    - a/b/c/d > a=year, b=vol, c=issue, d=pages
      (if a != year pattern, then abandon data)
    - a/b/c > a=year, b=issue, c=pages
      (if a != year pattern, then put a in vol, and b in issue, and c in pages)
    - a/b > a=year, b=pages
      (if a != year pattern, then put it in vol, and b in issue)
    - a > a=year (if a != year pattern, then put it in pages)
    For b, c, d: check that the values match the integer or pages patterns,
    otherwise abandon data.
    pages pattern: \d+(-\d+)?  examples: 12-25, 837, 837-838

    When a field 773, 800 or 830 has no link specified,
    then a seriesStatement must be generated instead of a partOf.
    But, in this case, a seriesStatement does not be generated
    for a field 773 if a field 580 exists
    and for the fields 800 and 830 if a field 490 exists
    """

    class Numbering(object):
        """The purpose of this class is to build the `Numbering` data."""

        def __init__(self):
            """Constructor method."""
            self._numbering = {}
            self._year_regexp = re.compile(r'^\d{4}')
            self._string_regexp = re.compile(r'.*')
            self._pages_regexp = re.compile(r'^\d+(-\d+)?$')
            self._pattern_per_key = {
                'year': self._year_regexp,
                'pages': self._pages_regexp,
                'issue': self._string_regexp,
                'volume': self._string_regexp
            }

        def add_numbering_value(self, key, value):
            """Add numbering `key: value` to `Numbering` data.

            The `Numbering` object is progressively build with the data col-
            lected by the succesive calls of the method `add_numbering_value`.

            :param key: key code of data to be added
            :type key: str
            :param value: value data to be associated the given `key`
            :type value: str
            """
            if self._pattern_per_key[key].search(value):
                self._numbering[key] = value
            elif key != 'year':
                self._numbering['discard'] = True

        def has_year(self):
            """Check if `year` key is present in `Numbering` data."""
            return 'year' in self._numbering

        def is_valid(self):
            """Check if `Numbering` data is valid."""
            return self._numbering and 'discard' not in self._numbering

        def get(self):
            """Get the  `Numbering` data object."""
            return self._numbering

    def add_author_to_subfield_t(value):
        """Get author from subfield_t and add it to subfield_t.

        The form 'lastname, firstname' of the author form subfield a
        is a appended to the subfield_t in the following form:
        ' / firstname lastname'
        """
        items = get_field_items(value)
        new_data = []
        author = None
        pending_g_values = []
        pending_v_values = []
        match = re.compile(r'\. -$')  # match the trailing '. -'
        subfield_selection = {'a', 't', 'g', 'v'}
        for blob_key, blob_value in items:
            if blob_key in subfield_selection:
                if blob_key == 'a':
                    # remove the trailing '. -'
                    author = match.sub('', blob_value)
                    # reverse first name and last name
                    author_parts = author.split(',')
                    author = ' '.join(reversed(author_parts)).strip()
                    subfield_selection.remove('a')
                elif blob_key == 't':
                    subfield_t = blob_value
                    if author:
                        subfield_t += f' / {author}'
                    new_data.append(('t', subfield_t))
                elif blob_key == 'g':
                    pending_g_values.append(blob_value)
                elif blob_key == 'v':
                    pending_v_values.append(blob_value)
        new_data.extend(('g', g_value) for g_value in pending_g_values)
        new_data.extend(('v', v_value) for v_value in pending_v_values)
        return GroupableOrderedDict(tuple(new_data))

    if key[:3] == '773' and marc21.bib_level == 'm':
        if not marc21.has_field_580:
            # the author in subfield $a is appended to subfield $t
            value = add_author_to_subfield_t(value)
            # create a seriesStatement instead of a partOf
            marc21.extract_series_statement_from_marc_field(
                key, value, data
            )
    else:  # 800, 830
        if not marc21.has_field_490:
            # create a seriesStatement instead of a partOf
            if key[:3] == '800':
                # the author in subfield $a is appended to subfield $t
                value = add_author_to_subfield_t(value)
            marc21.extract_series_statement_from_marc_field(key, value, data)


def do_work_access_point(marc21, key, value):
    """Get work access point."""
    """
    * "creator": {
    *   "type": "bf:Person", (700.2) | "bf:Organisation", (710.2)
    *   "preferred_name": "700.2$a",
    *   "numeration": "700.2$b",
    *   "date_of_birth": "700.2$d - 1ère date",
    *   "date_of_death": "700.2$d - 2e date",
    *   "qualifier": ["700.2$c"]
    *   "conference": false, (710.2)
    *   "preferred_name": "710.2$a",
    *   "subordinate_unit": ["710.2$b"]
    * }
    * "title": "130|700$t|730$a",
    * "date_of_work": "130|730$f",
    * "miscellaneous_information": "130|730$g",
    * "language": "130|730$l",
    * "part": [{
    *   "partNumber": "130|730$n",
    *   "partName": "130|730$p"
    * }],
    * "form_subdivision": ["130|730$k"],
    * "medium_of_performance_for_music": ["130|730$m"],
    * "arranged_statement_for_music": "130|730$o",
    * "key_for_music": "130|730$r",
    * "identifiedBy": {
    *   "type": "RERO",
    *   "value": "[ID autorité RERO]"
    * }
   """
    tag = key[:3]
    title_tag = 'a'
    work_access_point = {}
    bib_id = marc21.bib_id
    # work_access_point.creator
    if (tag in ['700', '800'] and value.get('t')) or tag == '710':
        title_tag = 't'
        if (creator_data := _do_work_access_point_creator(marc21, key, value))\
           and creator_data.get('preferred_name'):
            work_access_point['creator'] = creator_data
    # work_access_point.title
    if value.get(title_tag):
        work_access_point['title'] = remove_trailing_punctuation(
            not_repetitive(bib_id, bib_id, key, value, title_tag), ',.'
        ).replace('\u009c', '')

        if not work_access_point.get('title'):
            error_print('WARNING WORK ACCESS POINT:', bib_id, marc21.rero_id,
                        'no title')
            return None
    # work_access_point.date_of_work
    if value.get('f'):
        work_access_point['date_of_work'] = \
            not_repetitive(bib_id, bib_id, key, value, 'f')
    # work_access_point.miscellaneous_information
    if value.get('g'):
        work_access_point['miscellaneous_information'] = \
            remove_trailing_punctuation(not_repetitive(
                bib_id, bib_id, key, value, 'g'), ',.')
    # work_access_point.language
    if value.get('l'):
        language = not_repetitive(bib_id, bib_id, key, value, 'l')\
            .lstrip('(')\
            .rstrip('.')\
            .rstrip(')')
        lang = language
        if language not in _LANGUAGES:
            if len(language.split('-')) > 1 or language == 'mehrsprachig':
                lang = 'mul'
            elif iso_language := find(language):
                lang = iso_language.get('iso639_2_b')
        if lang in _LANGUAGES:
            work_access_point['language'] = lang
        if lang == 'mul' or lang not in _LANGUAGES:
            error_print('WARNING WORK ACCESS POINT LANGUAGE:', bib_id,
                        marc21.rero_id, language)
            if misc_info := work_access_point.get('miscellaneous_information'):
                work_access_point['miscellaneous_information'] = \
                    f'{misc_info} | language: {language}'
            else:
                work_access_point['miscellaneous_information'] = \
                    f'language: {language}'
    # work_access_point.part
    part_list = TitlePartList(part_number_code='n', part_name_code='p')
    items = get_field_items(value)
    index = 1
    for blob_key, blob_value in items:
        if blob_key in ['n', 'p']:
            part_list.update_part(blob_value, blob_key, blob_value)
        if blob_key != '__order__':
            index += 1
    if the_part_list := part_list.get_part_list():
        for part in the_part_list:
            if part_name := part.get('partName'):
                part['partName'] = remove_trailing_punctuation(part_name)
        work_access_point['part'] = the_part_list
    # work_access_point.form_subdivision
    if value.get('k'):
        work_access_point['form_subdivision'] = list(filter(None, [
            remove_trailing_punctuation(form_subdivision, ',.')
            for form_subdivision in list(utils.force_list(value.get('k')))
        ]))
    # work_access_point.medium_of_performance_for_music
    if value.get('m'):
        work_access_point['medium_of_performance_for_music'] = list(
            utils.force_list(value.get('m')))
    # work_access_point.arranged_statement_for_music
    if value.get('o'):
        work_access_point['arranged_statement_for_music'] = not_repetitive(
            bib_id, bib_id, key, value, 'o')
    # work_access_point.key_for_music
    if value.get('r'):
        work_access_point['key_for_music'] = remove_trailing_punctuation(
            not_repetitive(bib_id, bib_id, key, value, 'r'), ',.')

    return work_access_point or None


def _do_work_access_point_creator(marc21, key, value):
    """Create the structure for the work_access_point.creator field.

    :param marc21: the marc record.
    :param key: the MARC tag code and indicator.
    :param value: the MARC tag content (subfields).
    :return the work_access_point.creator structure as a dict
    :rtype dict
    """
    tag = key[:3]
    bib_id = marc21.bib_id
    data = {}
    if tag in ['100', '700', '800']:
        data = {'type': EntityType.PERSON}
        if value.get('a'):
            data['preferred_name'] = remove_trailing_punctuation(
                not_repetitive(bib_id, bib_id, key, value, 'a',)).rstrip('.')
        if value.get('b'):
            data['numeration'] = remove_trailing_punctuation(
                not_repetitive(bib_id, bib_id, key, value, 'b'))
        if date := not_repetitive(bib_id, bib_id, key, value, 'd'):
            date_parts = [d.strip().rstrip('.') for d in date.split('-')]
            if date_parts and date_parts[0]:
                data['date_of_birth'] = date_parts[0]
            if len(date_parts) > 1 and date_parts[1]:
                data['date_of_death'] = date_parts[1]
        if value.get('c'):
            data['qualifier'] = remove_trailing_punctuation(
                not_repetitive(bib_id, bib_id, key, value, 'c')).rstrip('.')

    # bf:Organisation
    if tag == '710':
        data = {
            'type': EntityType.ORGANISATION,
            'conference': False
        }
        if value.get('a'):
            data['name'] = remove_trailing_punctuation(
                not_repetitive(bib_id, bib_id, key, value, 'a',)).rstrip('.')
        if value.get('b'):
            data['subordinate_unit'] = list(filter(None, [
                remove_trailing_punctuation(unit).rstrip('.')
                for unit in list(utils.force_list(value.get('b')))
            ]))

    if data and (identifier := build_identifier(value)):
        data['identifiedBy'] = identifier
    return data


def do_work_access_point_240(marc21, key, value):
    """Get work access point from 240."""
    work_access_points = {}
    part_list = TitlePartList(
        part_number_code='n',
        part_name_code='p'
    )
    part_selection = {'n', 'p'}
    for blob_key, blob_value in get_field_items(value):
        if blob_key in {'a'}:
            title = remove_trailing_punctuation(
                blob_value.replace('\u009c', ''))
            work_access_points['title'] = title

        if blob_key in part_selection:
            part_list.update_part(blob_value, blob_key, blob_value)

    if field_100 := marc21.get_fields('100'):
        if agent := build_agent(marc21, '100', field_100[0]['subfields'])[1]:
            work_access_points['creator'] = agent

    if the_part_list := part_list.get_part_list():
        work_access_points['part'] = the_part_list

    if work_access_points:
        return work_access_points


def do_scale_and_cartographic(data, marc21, key, value):
    """Get scal and cartographic data.

    Si 255$a, créer la propriété "scale"
        * créer un objet de "scale" pour chaque 255
          * "label": "255$a" - retirer le ";" en fin de zone
          * "type": "034$a" [1]
          * "ratio_linear_horizontal":"034$b"
            (si $b répétitf, créer plusieurs valeurs)
          * "ratio_linear_vertical":"034$c"
            (si $c répétitif, créer plusieurs valeurs)
    Si 255 (l'un des sous-champs bc), créer la propriété
    "cartographicAttributes"
    * créer un objet de "cartographicAttributes" pour chaque 255
      * créer la propriété "coordinates"
        * "label": "255$c" - retirer les parenthèses en début et fin de zone
          et le point final  ;
        * "longitude": "034$d 034$e" - concaténer les valeurs et les séparer
          si nécessaire d'un espace
        * "latitude": "034$f 034$g" - concaténer les valeurs et les séparer
          si nécessaire d'un espace
      * "projection": "255$b"
    [1]
    a > Linear scale
    b > Angular scale
    z > Other
    """
    fields_034 = marc21.get_fields(tag='034')

    index = 0
    if value.get('a'):
        scales = data.get('scale', [])
        index = len(scales)
        scale = {
            'label': remove_trailing_punctuation(value.get('a'))
        }
        if fields_034 and len(fields_034) > index:
            subfields_034_a = marc21.get_subfields(fields_034[index], 'a')
            subfields_034_b = marc21.get_subfields(fields_034[index], 'b')
            subfields_034_c = marc21.get_subfields(fields_034[index], 'c')

            if subfields_034_a:
                scale['type'] = _SCALE_TYPE.get(
                    subfields_034_a[0].strip(), _SCALE_TYPE['z'])
            if subfields_034_b:
                ratio_linear_horizontal = subfields_034_b[0]
                try:
                    scale['ratio_linear_horizontal'] = \
                        int(ratio_linear_horizontal)
                except Exception:
                    error_print(
                        f'WARNING ratio_linear_horizontal is not an integer '
                        f'for [{marc21.bib_id}]: {ratio_linear_horizontal}'
                    )
            if subfields_034_c:
                ratio_linear_vertical = subfields_034_c[0]
                try:
                    scale['ratio_linear_vertical'] = \
                        int(ratio_linear_vertical)
                except Exception:
                    error_print(
                        f'WARNING ratio_linear_vertical is not an integer '
                        f'for [{marc21.bib_id}]: {ratio_linear_vertical}',
                    )

        scales.append(scale)
        data['scale'] = scales

    subfield_b = value.get('b')
    subfield_c = value.get('c')
    cartographic_attribute = {}
    if subfield_b:
        cartographic_attribute['projection'] = subfield_b
    coordinates = {'label': subfield_c} if subfield_c else {}

    if fields_034 and len(fields_034) > index:
        """
        * "longitude": "034$d 034$e" - concaténer les valeurs et les séparer
          si nécessaire d'un espace
        * "latitude": "034$f 034$g" - concaténer les valeurs et les séparer
          si nécessaire d'un espace
        """
        subfields_034_d = marc21.get_subfields(fields_034[index], 'd')
        subfields_034_e = marc21.get_subfields(fields_034[index], 'e')
        subfields_034_f = marc21.get_subfields(fields_034[index], 'f')
        subfields_034_g = marc21.get_subfields(fields_034[index], 'g')

        longitude_parts = []
        latitude_parts = []
        if subfields_034_d:
            longitude_parts.append(subfields_034_d[0])
        if subfields_034_e:
            longitude_parts.append(subfields_034_e[0])
        if subfields_034_f:
            latitude_parts.append(subfields_034_f[0])
        if subfields_034_g:
            latitude_parts.append(subfields_034_g[0])
        longitude = ' '.join(longitude_parts)
        latitude = ' '.join(latitude_parts)
        if _LONGITUDE.match(longitude):
            coordinates['longitude'] = longitude
        if _LATITUDE.match(latitude):
            coordinates['latitude'] = latitude
    if coordinates:
        cartographic_attribute['coordinates'] = coordinates
    if cartographic_attribute:
        cartographic_attributes = data.get('cartographicAttributes', [])
        cartographic_attributes.append(cartographic_attribute)
        data['cartographicAttributes'] = cartographic_attributes


def do_temporal_coverage(marc21, key, value):
    """Get temporal coverage.

    Plusieurs dates simples
    Si 045 ind1=0 ou ind1=1, créer la propriété "temporalCoverage"
    * créer un objet *date simple* de "temporalCoverage" pour chaque
       paire 045$b et chaque 045$c
    * "type": "time"
    * "date": "045$b|045$c"
    * "period_code": ["045$a"] - si répétés, récupérer tous les codes comme
       valeurs séparées de "period_code"

    Si 045 ind1=2
    * "type": "period"
    * "start_date": "045$b|045$c" - prendre le 1er sous-champ
    * "end_date": "045$b|045$c" - prendre le 2e sous-champ
    * "period_code": ["045$a"] - si répétés, récupérer tous les codes comme
      valeurs séparées de "period_code"

    Sinon (045 ind1=vide ou autre)
    * "type": "period"
    * "period_code": ["045$a"] - si répétés, récupérer tous les codes comme
      valeurs séparées de "period_code"

    [1] Convertir la date dans le format suivant:
    (+/-)yyyyyyyyyyy-mm-ddTHH-MM-SS La saisie des mm, dd, HH est facultative.
    Si HH est saisi, MM et SS doivent être saisis. Voir regex dans colonne M.
    Les dates dans $b suivent le format (c|d)yyyymmddhh. "c" est avant JC,
    devient -. "d" est après JC, devient +.
    Les dates dans $c suivent le format yyyyy...
    (autant de chiffres que nécessaires). Ces dates sont toutes négatives
    (à convertir avec un -).
    """
    def test_min_max(data, minimum, maximum):
        with contextlib.suppress(ValueError):
            number = int(data)
            return minimum <= number <= maximum
        return False

    def format_date_b(date):
        date = date.replace(' ', '')
        if date[0] == 'c':
            date = f'-{date[1:]}'
        elif date[0] == 'd':
            date = f'+{date[1:]}'
        else:
            date = f'+{date}'
        date_str = date[0]
        year = date[1:5]
        if test_min_max(year, 0, 9999):
            date_str = f'{date_str}{year}'
            month = date[5:7].zfill(2)
            if test_min_max(month, 1, 12):
                date_str = f'{date_str}-{month}'
                day = date[7:9].zfill(2) if test_min_max(
                    date[7:9], 1, 31) else '01'
                date_str = f'{date_str}-{day}'
                hour = date[9:11]
                if test_min_max(hour, 0, 23):
                    minute = date[11:13] if \
                        test_min_max(date[11:13], 0, 59) else '00'
                    second = date[13:15] if \
                        test_min_max(date[13:15], 0, 59) else '00'
                    date_str = f'{date_str}T{hour}:{minute}:{second}'
        if len(date_str) > 1:
            return date_str

    def format_date_c(date):
        if test_min_max(date, 0, sys.maxsize):
            return f'-{date}'

    ind1 = key[3]
    coverage_type = 'time' if ind1 in ['0', '1'] else 'period'
    temporal_coverage = {}
    if subfields_a := utils.force_list(value.get('a')):
        correct_subfields_a = []
        for subfield_a in subfields_a:
            subfield_a = subfield_a.lower()
            # duplicate periode_code for the type time
            if coverage_type == 'time' and len(subfield_a) == 2:
                subfield_a = f'{subfield_a}{subfield_a}'
            if _PERIOD_CODE.match(subfield_a):
                correct_subfields_a.append(subfield_a)
            else:
                error_print('WARNING PERIOD CODE:', marc21.bib_id,
                            marc21.rero_id, subfield_a)
        if correct_subfields_a:
            temporal_coverage['period_code'] = correct_subfields_a
    if coverage_type == 'time':
        if subfield_b := not_repetitive(marc21.bib_id, marc21.bib_id, key,
                                        value, 'b'):
            temporal_coverage['date'] = format_date_b(subfield_b)
        elif subfield_c := not_repetitive(marc21.bib_id, marc21.bib_id, key,
                                          value, 'c'):
            temporal_coverage['date'] = format_date_c(subfield_c)
    else:
        if subfields_b := utils.force_list(value.get('b')):
            if start_date := format_date_b(subfields_b[0]):
                temporal_coverage['start_date'] = start_date
                if len(subfields_b) > 1:
                    if end_date := format_date_b(subfields_b[1]):
                        temporal_coverage['end_date'] = end_date
        elif subfields_c := utils.force_list(value.get('c')):
            if start_date := format_date_c(subfields_c[0]):
                temporal_coverage['start_date'] = start_date
                if len(subfields_c) > 1:
                    if end_date := format_date_c(subfields_c[1]):
                        temporal_coverage['end_date'] = end_date
    if temporal_coverage:
        temporal_coverage['type'] = coverage_type
        return temporal_coverage


def perform_subdivisions(field, value):
    """Perform subject subdivisions from MARC field."""
    subdivisions = {
        'v': EntityType.TOPIC,
        'x': EntityType.TOPIC,
        'y': EntityType.TEMPORAL,
        'z': EntityType.PLACE
    }
    for tag, val in value.items():
        if tag in subdivisions:
            for v in utils.force_list(val):
                field.setdefault('subdivisions', []).append(dict(entity={
                        'type': subdivisions[tag],
                        'authorized_access_point': v
                }))
