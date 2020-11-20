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
from dojson.utils import GroupableOrderedDict

from rero_ils.dojson.utils import ReroIlsMarc21Overdo, TitlePartList, \
    add_note, build_responsibility_data, error_print, \
    extract_subtitle_and_parallel_titles_from_field_245_b, get_field_items, \
    get_field_link_data, make_year, not_repetitive, \
    remove_trailing_punctuation

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

IDREF_REF_REGEX = re.compile(r'^\(IDREF\)(.*)?')

marc21 = ReroIlsMarc21Overdo()


def get_contribution_link(bibid, reroid, id, key, value):
    """Get MEF contribution link."""
    # https://mef.test.rero.ch/api/mef/?q=rero.rero_pid:A012327677
    prod_host = 'mef.rero.ch'
    test_host = os.environ.get('RERO_ILS_MEF_HOST', 'mef.rero.ch')
    mef_url = 'https://{host}/api/'.format(host=test_host)

    match = IDREF_REF_REGEX.search(id)
    if match:
        pid = match.group(1)
        if key[:3] in ['100', '600', '610', '611', '700', '710', '711']:
            # contribution
            url = "{mef}idref/{pid}".format(mef=mef_url, pid=pid)
            try:
                request = requests.get(url=url)
            except requests.exceptions.RequestException as err:
                error_print('ERROR MEF ACCESS:', bibid, reroid, url, err)
                return None
            if request.status_code == requests.codes.ok:
                return url.replace(test_host, prod_host)
            else:
                subfiels = []
                for v, k in value.items():
                    if v != '__order__':
                        subfiels.append('${v} {k}'.format(v=v, k=k))
                subfiels = ' '.join(subfiels)
                field = '{key} {subfiels}'.format(key=key, subfiels=subfiels)
                error_print('WARNING MEF CONTRIBUTION IDREF NOT FOUND:',
                            bibid, reroid, field, url,
                            request.status_code)


@marc21.over('type_and_issuance', 'leader')
@utils.ignore_value
def marc21_to_type_and_issuance(self, key, value):
    """
    Get document type and the mode of issuance.

    Books: LDR/6-7: am
    Journals: LDR/6-7: as
    Articles: LDR/6-7: aa
    Scores: LDR/6: c|d
    Videos: LDR/6: g + 007/0: m|v
    Sounds: LDR/6: i|j
    E-books (imported from Cantook)
    """
    # get the document type
    type = 'other'
    if marc21.record_type == 'a':
        if marc21.bib_level == 'm':
            type = 'book'
        elif marc21.bib_level == 's':
            type = 'journal'
        elif marc21.bib_level == 'a':
            type = 'article'
    elif marc21.record_type in ['c', 'd']:
        type = 'score'
    elif marc21.record_type in ['i', 'j']:
        type = 'sound'
    elif marc21.record_type == 'g':
        type = 'video'
        # Todo 007
    self['type'] = type

    # get the mode of issuance
    self['issuance'] = {}
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
    self['issuance'] = {'main_type': main_type, 'subtype': sub_type}


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
    # default provisionActivity if we have no 264
    fields_264 = marc21.get_fields(tag='264')
    valid_264 = False
    for field_264 in fields_264:
        valid_264 = valid_264 or field_264['ind2'] in ['0', '1', '2', '3']
    if not valid_264:
        if fields_264:
            error_print('WARNING INVALID 264', marc21.bib_id, marc21.rero_id,
                        fields_264)
        self['provisionActivity'] = [{'type': 'bf:Publication'}]
        if (marc21.date_type_from_008 == 'q' or
                marc21.date_type_from_008 == 'n'):
            self['provisionActivity'][0][
                'note'
            ] = 'Date(s) uncertain or unknown'
        start_date = make_year(marc21.date1_from_008)
        if not start_date or start_date > 2050:
            error_print('WARNING START DATE 008:', marc21.bib_id,
                        marc21.rero_id, marc21.date1_from_008)
            start_date = 2050
            self['provisionActivity'][0][
                'note'
            ] = 'Date not available and automatically set to 2050'
        self['provisionActivity'][0]['startDate'] = start_date
        end_date = make_year(marc21.date2_from_008)
        if end_date:
            if end_date > 2050:
                error_print('WARNING END DATE 008:', marc21.bib_id,
                            marc21.rero_id, marc21.date1_from_008)
            else:
                self['provisionActivity'][0]['endDate'] = end_date

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
                if value_data:
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
    return not_repetitive(marc21.bib_id, marc21.rero_id, key, value, 'a')


@marc21.over('contribution', '[17][01][01]..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_contribution(self, key, value):
    """Get contribution."""
    if not key[4] == '2' and key[:3] in ['100', '700', '710', '711']:
        agent = {}
        if value.get('0'):
            refs = utils.force_list(value.get('0'))
            for ref in refs:
                ref = get_contribution_link(
                    marc21.bib_id, marc21.rero_id, ref, key, value)
                if ref:
                    agent['$ref'] = ref
                    if key[:3] in ['100', '700']:
                        agent['type'] = 'bf:Person'
                    elif key[:3] in ['710', '711']:
                        agent['type'] = 'bf:Organisation'

        # we do not have a $ref
        if not agent.get('$ref') and value.get('a'):
            agent = {'type': 'bf:Person'}
            if value.get('a'):
                name = not_repetitive(
                    marc21.bib_id, marc21.rero_id, key, value, 'a').rstrip('.')
                if name:
                    agent['preferred_name'] = name

            # 100|700 Person
            if key[:3] in ['100', '700']:
                agent['type'] = 'bf:Person'
                if value.get('b'):
                    numeration = not_repetitive(
                        marc21.bib_id, marc21.rero_id, key, value, 'b')
                    numeration = remove_trailing_punctuation(numeration)
                    if numeration:
                        agent['numeration'] = numeration
                if value.get('c'):
                    qualifier = not_repetitive(
                        marc21.bib_id, marc21.rero_id, key, value, 'c')
                    agent['qualifier'] = remove_trailing_punctuation(qualifier)
                if value.get('d'):
                    date = not_repetitive(
                        marc21.bib_id, marc21.rero_id, key, value, 'd')
                    date = date.rstrip(',')
                    dates = remove_trailing_punctuation(date).split('-')
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
                if value.get('q'):
                    fuller_form_of_name = not_repetitive(
                        marc21.bib_id, marc21.rero_id, key, value, 'q')
                    fuller_form_of_name = remove_trailing_punctuation(
                        fuller_form_of_name
                    ).lstrip('(').rstrip(')')
                    if fuller_form_of_name:
                        agent['fuller_form_of_name'] = fuller_form_of_name

            # 710|711 Organisation
            elif key[:3] in ['710', '711']:
                agent['type'] = 'bf:Organisation'
                if key[:3] == '711':
                    agent['conference'] = True
                else:
                    agent['conference'] = False
                if value.get('b'):
                    subordinate_units = []
                    for subordinate_unit in utils.force_list(value.get('b')):
                        subordinate_units.append(subordinate_unit.rstrip('.'))
                    agent['subordinate_unit'] = subordinate_units
                if value.get('e'):
                    subordinate_units = agent.get('subordinate_unit', [])
                    for subordinate_unit in utils.force_list(value.get('e')):
                        subordinate_units.append(subordinate_unit.rstrip('.'))
                    agent['subordinate_unit'] = subordinate_units
                if value.get('n'):
                    numbering = not_repetitive(
                        marc21.bib_id, marc21.rero_id, key, value, 'n')
                    numbering = remove_trailing_punctuation(
                        numbering
                    ).lstrip('(').rstrip(')')
                    if numbering:
                        agent['numbering'] = numbering
                if value.get('d'):
                    conference_date = not_repetitive(
                        marc21.bib_id, marc21.rero_id, key, value, 'd')
                    conference_date = remove_trailing_punctuation(
                        conference_date
                    ).lstrip('(').rstrip(')')
                    if conference_date:
                        agent['conference_date'] = conference_date
                if value.get('c'):
                    place = not_repetitive(
                        marc21.bib_id, marc21.rero_id, key, value, 'c')
                    place = remove_trailing_punctuation(
                        place
                    ).lstrip('(').rstrip(')')
                    if place:
                        agent['place'] = place

        if value.get('4'):
            roles = []
            for role in utils.force_list(value.get('4')):
                if len(role) != 3:
                    error_print('WARNING CONTRIBUTION ROLE LENGTH:',
                                marc21.bib_id, marc21.rero_id, role)
                    role = role[:3]
                if role == 'sce':
                    error_print('WARNING CONTRIBUTION ROLE SCE:',
                                marc21.bib_id, marc21.rero_id,
                                'sce --> aus')
                    role = 'aus'
                role = role.lower()
                if role not in _CONTRIBUTION_ROLE:
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


@marc21.over('copyrightDate', '^264.4')
@utils.ignore_value
def marc21_to_copyright_date(self, key, value):
    """Get Copyright Date."""
    copyright_dates = self.get('copyrightDate', [])
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
            edition_designation = marc21.build_value_with_alternate_graphic(
                '250', blob_key, blob_value, index, link, ',.', ':;/-=')
            if edition_designation:
                edition_data[key_per_code[blob_key]] = edition_designation
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

    subfields_c = utils.force_list(value.get('c', []))
    if ind2 in (' ', '1'):
        publication['startDate'] = marc21.date['start_date']
        if 'end_date' in marc21.date:
            publication['endDate'] = marc21.date['end_date']
        if 'note' in marc21.date:
            publication['note'] = marc21.date['note']
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


@marc21.over('seriesStatement', '^490..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_series_statement(self, key, value):
    """Get seriesStatement.

    series.name: [490$a repetitive]
    series.number: [490$v repetitive]
    """
    marc21.extract_series_statement_from_marc_field(key, value, self)
    return None


@marc21.over('abstracts', '^520..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_abstracts(self, key, value):
    """Get abstracts.

    abstract: [520$a repetitive]
    """
    abstracts = ', '.join(utils.force_list(value.get('a', [])))
    return abstracts


@marc21.over('identifiedBy', '^020..')
@utils.ignore_value
def marc21_to_identifiedBy_from_field_020(self, key, value):
    """Get identifier from field 020."""
    def build_identifier_from(subfield_data, status=None):
        subfield_data = subfield_data.strip()
        identifier = {'value': subfield_data}
        subfield_c = not_repetitive(marc21.bib_id, marc21.rero_id,
                                    key, value, 'c', default='').strip()
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
    subfield_a = not_repetitive(marc21.bib_id, marc21.rero_id, key, value, 'a')
    if subfield_a:
        build_identifier_from(subfield_a)
    for subfield_z in utils.force_list(value.get('z', [])):
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
        subfield_c = not_repetitive(marc21.bib_id,  marc21.rero_id,
                                    key, value, 'c', default='').strip()
        if subfield_c:
            identifier['acquisitionTerms'] = subfield_c
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
    identifiedBy = None
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
        identifiedBy = self.get('identifiedBy', [])
        identifiedBy.append(identifier)
    return identifiedBy or None


@marc21.over('identifiedBy', '^035..')
@utils.ignore_value
def marc21_to_identifiedBy_from_field_035(self, key, value):
    """Get identifier from field 035."""
    subfield_a = not_repetitive(marc21.bib_id, marc21.rero_id,
                                key, value, 'a', default='').strip()
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
@utils.ignore_value
def marc21_to_electronicLocator_from_field_856(self, key, value):
    """Get electronicLocator from field 856."""
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
        electronic_locators = self.get('electronicLocator', [])
        indicator2 = key[4]
        content = None
        if value.get('3'):
            content = utils.force_list(value.get('3'))[0]
        public_note = []
        if content and content not in electronic_locator_content:
            public_note.append(content)
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
            if len(electronic_locator['url']) >= 7:
                electronic_locators.append(electronic_locator)
            else:
                error_print('WARNING ELECTRONICLOCATOR:', marc21.bib_id,
                            marc21.rero_id, electronic_locator['url'])
        return electronic_locators or None


@marc21.over('identifiedBy', '^930..')
@utils.ignore_value
def marc21_to_identifiedBy_from_field_930(self, key, value):
    """Get identifier from field 930."""
    subfield_a = not_repetitive(marc21.bib_id, marc21.rero_id,
                                key, value, 'a', default='').strip()
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
            label=not_repetitive(marc21.bib_id, marc21.rero_id,
                                 key, value, 'a')
        ),
        self)
    return None


@marc21.over('part_of', '^(773|800|830)..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_part_of(self, key, value):
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

    part_of = {}
    numbering_list = []
    subfield_w = not_repetitive(marc21.bib_id,  marc21.rero_id,
                                key, value, 'w', default='').strip()
    if subfield_w:
        match = re.compile(r'^REROILS:')
        pid = match.sub('', subfield_w)
        part_of['document'] = {
            '$ref':
                'https://ils.rero.ch/api/documents/{pid}'.format(pid=pid)
        }
        if key[:3] == '773':
            discard_numbering = False
            for subfield_g in utils.force_list(value.get('g', [])):
                numbering = Numbering()
                values = subfield_g.strip().split('/')
                numbering.add_numbering_value('year', values[0][:4])
                if len(values) == 1 and not numbering.has_year():
                    if values[0]:
                        numbering.add_numbering_value('pages', values[0])
                elif len(values) == 2:
                    if numbering.has_year():
                        if values[1]:
                            numbering.add_numbering_value('pages', values[1])
                    else:
                        if values[0]:
                            numbering.add_numbering_value('volume', values[0])
                        if values[1]:
                            numbering.add_numbering_value('issue', values[1])
                elif len(values) == 3:
                    if not numbering.has_year() and values[0]:
                        numbering.add_numbering_value('volume', values[0])
                    if values[1]:
                        numbering.add_numbering_value('issue', values[1])
                    if values[2]:
                        numbering.add_numbering_value('pages', values[2])
                elif len(values) == 4:
                    if numbering.has_year():
                        if values[1]:
                            numbering.add_numbering_value('volume', values[1])
                        if values[2]:
                            numbering.add_numbering_value('issue', values[2])
                        if values[3]:
                            numbering.add_numbering_value('pages', values[3])
                    else:
                        discard_numbering = True
                if not discard_numbering and numbering.is_valid():
                    numbering_list.append(numbering.get())
        else:  # 800, 830
            for subfield_v in utils.force_list(value.get('v', [])):
                numbering = Numbering()
                if subfield_v:
                    numbering.add_numbering_value('volume', subfield_v)
                if numbering.is_valid():
                    numbering_list.append(numbering.get())
        if 'document' in part_of:
            if numbering_list:
                part_of['numbering'] = numbering_list
            self['partOf'] = self.get('partOf', [])
            self['partOf'].append(part_of)
    else:  # no link found
        if key[:3] == '773':
            if not marc21.has_field_580:
                # the author in subfield $a is appended to subfield $t
                value = add_author_to_subfield_t(value)
                # create a seriesStatement instead of a partOf
                marc21.extract_series_statement_from_marc_field(
                    key, value, self
                )
        else:  # 800, 830
            if not marc21.has_field_490:
                # create a seriesStatement instead of a partOf
                if key[:3] == '800':
                    # the author in subfield $a is appended to subfield $t
                    value = add_author_to_subfield_t(value)
                marc21.extract_series_statement_from_marc_field(
                    key, value, self
                )


@marc21.over('subjects', '^6....')
@utils.for_each_value
@utils.ignore_value
def marc21_to_subjects(self, key, value):
    """Get subjects.

    subjects: 6xx [duplicates could exist between several vocabularies,
        if possible deduplicate]
    """
    subjects = self.get('subjects', [])
    subfields_a = utils.force_list(value.get('a'))
    if subfields_a:
        for subfield_a in subfields_a:
            if subfield_a not in subjects:
                subjects.append(subfield_a)
        if subjects:
            self['subjects'] = subjects
    # we will return None because we have set subjects directly in self
