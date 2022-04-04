# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
# Copyright (C) 2021 UCLOUVAIN
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
from dojson.utils import GroupableOrderedDict
from iso639 import find

from rero_ils.dojson.utils import _LANGUAGES, TitlePartList, add_note, \
    build_identifier, build_responsibility_data, build_string_from_subfields, \
    error_print, extract_subtitle_and_parallel_titles_from_field_245_b, \
    get_contribution_link, get_field_items, get_field_link_data, \
    not_repetitive, re_identified, remove_trailing_punctuation

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
    else:
        if marc21.bib_level in _ISSUANCE_SUBTYPE_PER_BIB_LEVEL:
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
    type = [{"main_type": "docmaintype_other"}]
    if marc21.record_type == 'a':
        if marc21.bib_level == 'm':
            type = [{
                "main_type": "docmaintype_book",
                "subtype": "docsubtype_other_book"
            }]

            field_008 = None
            field_008 = marc21.get_fields(tag='008')
            # if it's an electronic book
            if field_008[0]['data'][23] in ('o', 's'):
                type = [{
                    "main_type": "docmaintype_book",
                    "subtype": "docsubtype_e-book"
                 }]
        elif marc21.bib_level == 's':
            type = [{
                "main_type": "docmaintype_serial"
            }]
        elif marc21.bib_level == 'a':
            type = [{
                "main_type": "docmaintype_article",
            }]
        elif marc21.record_type in ['c', 'd']:
            type = [{
                "main_type": "docmaintype_score",
                "subtype": "docsubtype_printed_score"
            }]
        elif marc21.record_type in ['i', 'j']:
            type = [{
                "main_type": "docmaintype_audio",
                "subtype": "docsubtype_music"
            }]
        elif marc21.record_type == 'g':
            type = [{
                "main_type": "docmaintype_movie_series",
                "subtype": "docsubtype_movie"
            }]
    data['type'] = type


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
    fields_546 = marc21.get_fields(tag='546')
    if fields_546:
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

    * bf:Title = 210|222
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
        title = {
            'type': 'bf:AbbreviatedTitle',
            'mainTitle': [{'value': main_title}]
        }
        if value.get('b'):
            subtitle = not_repetitive(
                marc21.bib_id, marc21.bib_id, key, value, 'b')
            title['subtitle'] = [{'value': subtitle}]
        for resp_tag in ['f', 'g']:
            datas = utils.force_list(value.get(resp_tag))
            if datas:
                for data in datas:
                    responsibility = build_responsibility_data(data)
                    if responsibility:
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
    fields_245 = marc21.get_fields(tag='245')
    if fields_245:
        subfields_245_a = marc21.get_subfields(fields_245[0], 'a')
        subfields_245_b = marc21.get_subfields(fields_245[0], 'b')
        if subfields_245_a:
            subfield_245_a = subfields_245_a[0]
        if subfields_245_b:
            subfield_245_b = subfields_245_b[0]
    field_245_a_end_with_equal = re.search(r'\s*=\s*$', subfield_245_a)

    fields_246 = marc21.get_fields(tag='246')
    subfield_246_a = ''
    if fields_246:
        subfields_246_a = marc21.get_subfields(fields_246[0], 'a')
        if subfields_246_a:
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
                elif not subfield_246_a and value_data:
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
        new_responsibility = data.get('responsibilityStatement', [])
        for resp in responsibility:
            new_responsibility.append(resp)
        data['responsibilityStatement'] = new_responsibility
    return title_list or None


def do_contribution(data, marc21, key, value):
    """Get contribution."""

    def build_agent():
        agent_data = {}
        if value.get('a'):
            name = not_repetitive(
                marc21.bib_id, marc21.bib_id, key, value, 'a')
            agent_data['preferred_name'] = remove_trailing_punctuation(
                name)
        # 100|700 Person
        if key[:3] in ['100', '700']:
            agent_data['type'] = 'bf:Person'
            if value.get('a'):
                name = not_repetitive(
                    marc21.bib_id, marc21.bib_id, key, value, 'a')
                agent_data['preferred_name'] = remove_trailing_punctuation(
                    name)  # name.rstrip('.')
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
                try:
                    date_of_birth = dates[0].strip()
                    if date_of_birth:
                        agent_data['date_of_birth'] = date_of_birth
                except Exception:
                    pass
                try:
                    date_of_death = dates[1].strip()
                    if date_of_death:
                        agent_data['date_of_death'] = date_of_death
                except Exception:
                    pass
            if value.get('q'):
                fuller_form_of_name = not_repetitive(
                    marc21.bib_id, marc21.bib_id, key, value, 'q')
                agent_data[
                    'fuller_form_of_name'] = remove_trailing_punctuation(
                    fuller_form_of_name
                ).lstrip('(').rstrip(')')

        # 710|711 Organisation
        if key[:3] in ['710', '711']:
            agent_data['type'] = 'bf:Organisation'
            if key[:3] == '711':
                agent_data['conference'] = True
            else:
                agent_data['conference'] = False
            if value.get('b'):
                subordinate_units = []
                for subordinate_unit in utils.force_list(
                        value.get('b')):
                    subordinate_units.append(
                        subordinate_unit.rstrip('.'))
                agent_data['subordinate_unit'] = subordinate_units
            if value.get('n'):
                numbering = not_repetitive(
                    marc21.bib_id, marc21.bib_id, key, value, 'n')

                numbering = remove_trailing_punctuation(
                    numbering).lstrip('(').rstrip(')')
                if numbering:
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

        return agent_data or None

    # exclude work access points
    if key[:3] in ['700', '710'] and value.get('t'):
        return None

    agent = {}

    if value.get('0'):
        ref = get_contribution_link(marc21.bib_id, marc21.rero_id,
                                    value.get('0'), key)
        if ref:
            agent['$ref'] = ref
            if key[:3] in ['100', '700']:
                agent['type'] = 'bf:Person'
            elif key[:3] in ['710', '711']:
                agent['type'] = 'bf:Organisation'

    # we do not have a $ref
    if not agent.get('$ref') and value.get('a'):
        agent = build_agent()

    if value.get('4'):
        roles = []
        for role in utils.force_list(value.get('4')):
            if len(role) != 3 and 'http' not in role:
                error_print('WARNING CONTRIBUTION ROLE LENGTH:',
                            marc21.bib_id, marc21.rero_id, role)
                role = role[:3]
            if role == 'sce':
                error_print('WARNING CONTRIBUTION ROLE SCE:',
                            marc21.bib_id, marc21.rero_id,
                            'sce --> aus')
                role = 'aus'
            role = role.lower()
            if role not in _CONTRIBUTION_ROLE and 'http' not in role:
                error_print('WARNING CONTRIBUTION ROLE DEFINITION:',
                            marc21.bib_id, marc21.rero_id, role)
                role = 'ctb'
            roles.append(role)
    else:
        if key[:3] == '100':
            roles = ['cre']
        elif key[:3] == '711':
            roles = ['aut']
        else:
            roles = ['ctb']
    if agent:
        return {
            'agent': agent,
            'role': list(set(roles))
        }
    return None


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
    else:
        subfield_w = not_repetitive(marc21.bib_id,  marc21.rero_id,
                                    key, value, 'w', default='').strip()
        if subfield_w:
            pid = None
            match = re_reroils.match(subfield_w)
            if match:
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

    def build_statement(field_value, ind2):

        def build_agent_data(code, label, index, link):
            type_per_code = {
                'a': 'bf:Place',
                'b': 'bf:Agent'
            }
            label = remove_trailing_punctuation(label)
            if not label:
                return None
            agent_data = {
                'type': type_per_code[code],
                'label': [{'value': label}]
            }
            try:
                alt_gr = marc21.alternate_graphic[tag][link]
                subfield = \
                    marc21.get_subfields(alt_gr['field'])[index]
                subfield = remove_trailing_punctuation(subfield)
                if subfield:
                    agent_data['label'].append({
                        'value': subfield,
                        'language': marc21.get_language_script(
                            alt_gr['script'])
                    })
            except Exception as err:
                pass

            identifier = build_identifier(value)
            if identifier:
                agent_data['identifiedBy'] = identifier

            return agent_data

        # function build_statement start here
        _, link = get_field_link_data(field_value)
        items = get_field_items(field_value)
        statement = []
        index = 1
        for blob_key, blob_value in items:
            if blob_key in ('a', 'b'):
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
    publication = {'type': type_per_ind2[ind2]}

    if ind2 in ('_', ' ', '1'):
        publication['startDate'] = marc21.date['start_date']
        if 'end_date' in marc21.date:
            publication['endDate'] = marc21.date['end_date']
        if 'note' in marc21.date:
            publication['note'] = marc21.date['note']
        publication['startDate'] = marc21.date['start_date']

        places = []
        place = marc21.build_place()
        if place and place.get('country') != 'xx':
            places.append(place)
        # parce le link skipping the fist (already used by build_place)
        for i in range(1, len(marc21.links_from_752)):
            place = {
                'country': 'xx',
                'type': 'bf:Place',
                'identifyBy': marc21.links_from_752[i]
            }
            places.append(place)
        if places:
            publication['place'] = places
    subfield_3 = not_repetitive(marc21.bib_id, marc21.rero_id,
                                key, value, '3')
    if subfield_3:
        notes = publication.get('note')
        if notes:
            notes = [notes]
        else:
            notes = []
        notes.append(subfield_3)
        publication['note'] = ', '.join(notes)

    statement = build_statement(value, ind2)
    if statement:
        publication['statement'] = build_statement(value, ind2)

    subfields_c = utils.force_list(value.get('c', []))
    if subfields_c:
        subfield_c = subfields_c[0]
        date = {
            'label': [{'value': subfield_c}],
            'type': 'Date'
        }

        _, link = get_field_link_data(value)
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
        publication.setdefault('statement', [])
        publication['statement'].append(date)
    return publication or None


def do_table_of_contents(data, value):
    """Get tableOfContents from repetitive field 505."""
    table_of_contents = build_string_from_subfields(value, 'agtr')
    if table_of_contents:
        table_of_contents_list = data.get('tableOfContents', [])
        table_of_contents_list.append(table_of_contents)
        data['tableOfContents'] = table_of_contents_list


def do_usage_and_access_policy_from_field_506_540(marc21, key, value):
    """Get usageAndAccessPolicy from fields: 506, 540."""
    subfield_a = not_repetitive(marc21.bib_id, marc21.rero_id,
                                key, value, 'a', default='').strip()
    if subfield_a:
        policy = {'type': 'bf:UsageAndAccessPolicy',
                  'label': subfield_a}
        return policy


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
        subfield_a = not_repetitive(marc21.bib_id, marc21.rero_id,
                                    key, value, 'a', default='').strip()
        if subfield_a:
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
                identified_by.append(identifier)
    if identified_by:
        data['identifiedBy'] = identified_by


def do_identified_by_from_field_024(data, marc21, key, value):
    """Get identifier from field 024."""
    def populate_acquisitionTerms_note_qualifier(identifier):
        subfield_c = not_repetitive(marc21.bib_id,  marc21.rero_id,
                                    key, value, 'c', default='').strip()
        if subfield_c:
            acquisition_terms = data.get('acquisitionTerms', [])
            acquisition_terms.append(subfield_c)
            data['acquisitionTerms'] = acquisition_terms
        subfield_d = not_repetitive(marc21.bib_id, marc21.rero_id,
                                    key, value, 'd', default='').strip()
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
    identified_by = data.get('identifiedBy', [])
    subfield_a = not_repetitive(marc21.bib_id, marc21.rero_id,
                                key, value, 'a', default='').strip()
    if subfield_a:
        identifier['value'] = subfield_a
        if value.get('q'):  # $q is repetitive
            identifier['qualifier'] = \
                ', '.join(utils.force_list(value.get('q')))
        subfield_b = not_repetitive(marc21.bib_id, marc21.rero_id,
                                    key, value, 'b', default='').strip()
        if subfield_b:
            identifier['source'] = subfield_b
        # key[3] is the indicateur_1
        identifier['type'] = type_for_ind1.get(key[3], 'bf:Identifier')
        identified_by.append(identifier)
        data['identifiedBy'] = identified_by


def do_identified_by_from_field_035(data, marc21, key, value, source=None):
    """Get identifier from field 035."""
    identified_by = data.get('identifiedBy', [])
    subfield_a = not_repetitive(marc21.bib_id, marc21.rero_id,
                                key, value, 'a', default='').strip()
    if subfield_a:
        value = subfield_a
        # search source between parenthesis
        match = re_identified.match(subfield_a)
        if match:
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
    subfields_c = utils.force_list(value.get('c'))
    if subfields_c:
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
        content = None
        if value.get('3'):
            content = utils.force_list(value.get('3'))[0]
        public_note = []
        if content and content not in electronic_locator_content:
            public_note.append(content)
        if value.get('y'):
            for subfield_y in utils.force_list(value.get('y')):
                public_note.append(subfield_y)
        if value.get('z'):
            for subfield_z in utils.force_list(value.get('z')):
                public_note.append(subfield_z)

        for url in utils.force_list(value.get('u')):
            electronic_locator = {
                'url': url,
                'type': electronic_locator_type.get(indicator2, 'noInfo')
            }
            if content:
                if content in electronic_locator_content:
                    electronic_locator['content'] = content
            if public_note:
                electronic_locator['publicNote'] = public_note
            validate_url = re_electonic_locator.match(url)
            if validate_url:
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
            note_str = ''
            subfield_selection = {'a', 'c', 'x'}
            for blob_key, blob_value in items:
                if blob_key in subfield_selection:
                    note_str += blob_value + ' '
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
            subfield_a = 'Participants ou interprètes: ' + subfield_a
        return subfield_a


def do_sequence_numbering(data, value):
    """Get notes and original title."""
    if value.get('a'):
        subfield_a = utils.force_list(value.get('a'))[0]
        sequence_numbering = data.get('sequence_numbering', '')
        if sequence_numbering:
            sequence_numbering += ' ; ' + subfield_a
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
    subfields_a = utils.force_list(value.get('a', []))
    subfields_2 = utils.force_list(value.get('2'))
    subfield_2 = None
    if subfields_2:
        subfield_2 = subfields_2[0]
    for subfield_a in subfields_a:
        classification = {}
        classification['classificationPortion'] = subfield_a
        classification['type'] = classification_type_per_tag[tag]
        if tag == '050' and indicator2 == '0':
            classification['assigner'] = 'LOC'
        if tag == '060' and indicator2 == '0':
            classification['assigner'] = 'NLM'
        if tag == '080':
            subfields_x = utils.force_list(value.get('x'))
            if subfields_x:
                classification['subdivision'] = []
                for subfield_x in subfields_x:
                    classification['subdivision'].append(subfield_x)
            edition = None
            if indicator1 == '0':
                edition = 'Full edition'
            elif indicator1 == '1':
                edition = 'Abridged edition'
            if subfield_2:
                if edition:
                    edition += ', ' + subfield_2
                else:
                    edition = subfield_2
            if edition:
                classification['edition'] = edition
        elif tag == '082':
            subfields_q = utils.force_list(value.get('q'))
            subfield_q = None
            edition = None
            if subfields_q:
                subfield_q = subfields_q[0]
            if indicator2 == '0':
                classification['assigner'] = 'LOC'
            elif subfield_q:
                classification['assigner'] = subfield_q
            if indicator1 == '0':
                edition = 'Full edition'
            elif indicator1 == '1':
                edition = 'Abridged edition'
            if subfield_2:
                if edition:
                    edition += ', ' + subfield_2
                else:
                    edition = subfield_2
            if edition:
                classification['edition'] = edition
        classification_list = data.get('classification', [])
        if classification:
            classification_list.append(classification)
            data['classification'] = classification_list


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
            self._integer_regexp = re.compile(r'^\d+$')
            self._pages_regexp = re.compile(r'^\d+(-\d+)?$')
            self._pattern_per_key = {
                'year': self._year_regexp,
                'pages': self._pages_regexp,
                'issue': self._integer_regexp,
                'volume': self._integer_regexp
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
                if key in ('issue', 'volume'):
                    value = int(value)
                    if value > 0:
                        self._numbering[key] = value
                else:
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
                        subfield_t += ' / ' + author
                    new_data.append(('t', subfield_t))
                elif blob_key == 'g':
                    pending_g_values.append(blob_value)
                elif blob_key == 'v':
                    pending_v_values.append(blob_value)
        for g_value in pending_g_values:
            new_data.append(('g', g_value))
        for v_value in pending_v_values:
            new_data.append(('v', v_value))
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
            marc21.extract_series_statement_from_marc_field(
                key, value, data
            )


def do_work_access_point(marc21, key, value):
    """Get work access point."""
    """
    * "agent": {
    *   "type": "bf:Person", (700.2)
    *   "preferred_name": "700.2$a",
    *   "numeration": "700.2$b",
    *   "date_of_birth": "700.2$d - 1ère date",
    *   "date_of_death": "700.2$d - 2e date",
    *   "qualifier": ["700.2$c"]
    *   "type": "bf:Organization", (710.2)
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
    agent = {}
    work_access_point = {}
    # subfield_0 = not_repetitive(
    #     marc21.bib_id, marc21.bib_id, key, value, '0')
    # if subfield_0:
    #     ref = get_contribution_link(marc21.bib_id, marc21.rero_id,
    #                                 subfield_0, key)
    # if ref:
    #     agent['$ref'] = ref
    #     if tag == '700':
    #         agent['type'] = 'bf:Person'
    #     elif tag == '710':
    #         agent['type'] = 'bf:Organisation'
    # else:
    if tag == '700' and value.get('t'):
        title_tag = 't'
        agent['type'] = 'bf:Person'
        if value.get('a'):
            agent['preferred_name'] = remove_trailing_punctuation(
                not_repetitive(marc21.bib_id, marc21.bib_id, key, value, 'a'))
        if value.get('b'):
            agent['numeration'] = remove_trailing_punctuation(
                not_repetitive(marc21.bib_id, marc21.bib_id, key, value, 'b'))
        dates = not_repetitive(marc21.bib_id, marc21.bib_id, key, value, 'd')
        if dates:
            dates = dates.rstrip(',')
            dates = remove_trailing_punctuation(dates).split('-')
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
        if value.get('c'):
            agent['qualifier'] = remove_trailing_punctuation(
                not_repetitive(marc21.bib_id, marc21.bib_id, key, value, 'c'))
    elif tag == '710':
        title_tag = 't'
        agent['type'] = 'bf:Organisation'
        agent['conference'] = False
        if value.get('a'):
            agent['preferred_name'] = not_repetitive(
                marc21.bib_id, marc21.bib_id, key, value, 'a')
        if value.get('b'):
            agent['subordinate_unit'] = not_repetitive(
                marc21.bib_id, marc21.bib_id, key, value, 'b')
    if agent:
        work_access_point['agent'] = agent
    if value.get(title_tag):
        work_access_point['title'] = not_repetitive(
            marc21.bib_id, marc21.bib_id, key, value, title_tag)
    if value.get('f'):
        work_access_point['date_of_work'] = not_repetitive(
            marc21.bib_id, marc21.bib_id, key, value, 'f')
    if value.get('g'):
        work_access_point['miscellaneous_information'] = not_repetitive(
            marc21.bib_id, marc21.bib_id, key, value, 'g')
    if value.get('l'):
        language = not_repetitive(
            marc21.bib_id, marc21.bib_id, key, value, 'l')
        lang = language
        if lang not in _LANGUAGES:
            # try to get alpha3 language:
            iso_language = find(language)
            if iso_language:
                lang = iso_language.get('iso639_2_b')
        if lang in _LANGUAGES:
            work_access_point['language'] = lang
        else:
            error_print('WARNING WORK ACCESS POINT LANGUAGE:', marc21.bib_id,
                        marc21.rero_id, language)
    part_list = TitlePartList(part_number_code='n', part_name_code='p')
    items = get_field_items(value)
    index = 1
    for blob_key, blob_value in items:
        if blob_key in ['n', 'p']:
            part_list.update_part(blob_value, blob_key, blob_value)
        if blob_key != '__order__':
            index += 1
    the_part_list = part_list.get_part_list()
    if the_part_list:
        work_access_point['part'] = the_part_list
    if value.get('k'):
        work_access_point['form_subdivision'] = list(
            utils.force_list(value.get('k')))
    if value.get('m'):
        work_access_point['medium_of_performance_for_music'] = list(
            utils.force_list(value.get('m')))
    if value.get('o'):
        work_access_point['arranged_statement_for_music'] = not_repetitive(
            marc21.bib_id, marc21.bib_id, key, value, 'o')
    if value.get('r'):
        work_access_point['key_for_music'] = not_repetitive(
            marc21.bib_id, marc21.bib_id, key, value, 'r')
    identifier = build_identifier(value)
    if identifier:
        agent['identifiedBy'] = identifier

    if not work_access_point.get('title'):
        error_print('WARNING WORK ACCESS POINT:', marc21.bib_id,
                    marc21.rero_id, 'no title')
        return None
    agent = work_access_point.get('agent', {})
    if agent and not agent.get('preferred_name'):
        error_print('WARNING WORK ACCESS POINT:', marc21.bib_id,
                    marc21.rero_id, 'no agent preferred_name')
        return None
    return work_access_point or None
