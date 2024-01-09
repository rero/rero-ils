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

from dojson import utils
from dojson.utils import GroupableOrderedDict

from rero_ils.dojson.utils import ReroIlsMarc21Overdo, build_identifier, \
    build_string_from_subfields, error_print, get_field_items, get_mef_link, \
    not_repetitive, re_identified, remove_trailing_punctuation
from rero_ils.modules.documents.utils import create_authorized_access_point
from rero_ils.modules.entities.models import EntityType

from ..utils import _CONTRIBUTION_ROLE, do_abbreviated_title, \
    do_acquisition_terms_from_field_037, do_copyright_date, do_credits, \
    do_dissertation, do_edition_statement, \
    do_electronic_locator_from_field_856, do_frequency_field_310_321, \
    do_identified_by_from_field_020, do_identified_by_from_field_022, \
    do_identified_by_from_field_024, do_identified_by_from_field_028, \
    do_identified_by_from_field_035, do_intended_audience, do_issuance, \
    do_notes_and_original_title, do_provision_activity, \
    do_scale_and_cartographic, do_sequence_numbering, \
    do_specific_document_relation, do_summary, do_table_of_contents, \
    do_temporal_coverage, do_title, \
    do_usage_and_access_policy_from_field_506_540, do_work_access_point, \
    perform_subdivisions

marc21 = ReroIlsMarc21Overdo()

_CONTAINS_FACTUM_REGEXP = re.compile(r'factum')


@marc21.over('issuance', 'leader')
@utils.ignore_value
def marc21_to_type_and_issuance(self, key, value):
    """Get document type, content/Media/Carrier type and mode of issuance."""
    do_issuance(self, marc21)


@marc21.over('pid', '^001')
@utils.ignore_value
def marc21_to_pid(self, key, value):
    """Get pid.

    If 001 starts with 'REROILS:' save as pid.
    """
    value = value.strip().split(':')
    return value[1] if value[0] == 'REROILS' else None


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
    # language note
    if fields_546 := marc21.get_fields(tag='546'):
        subfields_546_a = marc21.get_subfields(fields_546[0], 'a')
        if subfields_546_a and language:
            language[0]['note'] = subfields_546_a[0]
    # if not language:
    #     error_print('ERROR LANGUAGE:', marc21.bib_id, 'set to "und"')
    #     language = [{'value': 'und', 'type': 'bf:Language'}]
    return language or None


@marc21.over('title', '^245..')
@utils.ignore_value
def marc21_to_title(self, key, value):
    """Get title data."""
    # extraction and initialization of data for further processing
    title_list = do_title(self, marc21, value)
    return title_list or None


@marc21.over('contribution', '(^100|^700|^710|^711)..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_contribution(self, key, value):
    """Get contribution."""
    # exclude work access points
    if key[:3] in ['700', '710'] and value.get('t'):
        if work_access_point := do_work_access_point(marc21, key, value):
            self.setdefault('work_access_point', [])
            self['work_access_point'].append(work_access_point)
        return None
    agent = {}
    if ref := get_mef_link(
        bibid=marc21.bib_id,
        reroid=marc21.rero_id,
        entity_type=EntityType.PERSON,
        ids=utils.force_list(value.get('0')),
        key=key
    ):
        agent['$ref'] = ref

    # we do not have a $ref
    agent_data = {}
    if not agent.get('$ref') and value.get('a'):
        if value.get('a'):
            if name := not_repetitive(
                    marc21.bib_id,
                    marc21.rero_id,
                    key, value, 'a').rstrip('.'):
                agent_data['preferred_name'] = name

        # 100|700 Person
        if key[:3] in ['100', '700']:
            agent_data['type'] = EntityType.PERSON
            if value.get('b'):
                numeration = not_repetitive(
                    marc21.bib_id, marc21.rero_id, key, value, 'b')
                if numeration := remove_trailing_punctuation(numeration):
                    agent_data['numeration'] = numeration
            if value.get('c'):
                qualifier = not_repetitive(
                    marc21.bib_id, marc21.rero_id, key, value, 'c')
                agent_data['qualifier'] = \
                    remove_trailing_punctuation(qualifier)
            if value.get('d'):
                date = not_repetitive(
                    marc21.bib_id, marc21.rero_id, key, value, 'd')
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
                    marc21.bib_id, marc21.rero_id, key, value, 'q')
                if fuller_form_of_name := remove_trailing_punctuation(
                        fuller_form_of_name).lstrip('(').rstrip(')'):
                    agent_data['fuller_form_of_name'] = fuller_form_of_name
            if identifier := build_identifier(value):
                agent_data['identifiedBy'] = identifier

        elif key[:3] in ['710', '711']:
            agent_data['type'] = EntityType.ORGANISATION
            agent_data['conference'] = key[:3] == '711'
            if value.get('b'):
                subordinate_units = [
                    subordinate_unit.rstrip('.') for subordinate_unit
                    in utils.force_list(value.get('b'))
                ]

                agent_data['subordinate_unit'] = subordinate_units
            if value.get('e'):
                subordinate_units = agent_data.get('subordinate_unit', [])
                for subordinate_unit in utils.force_list(value.get('e')):
                    subordinate_units.append(subordinate_unit.rstrip('.'))
                agent_data['subordinate_unit'] = subordinate_units
            if value.get('n'):
                numbering = not_repetitive(
                    marc21.bib_id, marc21.rero_id, key, value, 'n')
                if numbering := remove_trailing_punctuation(
                        numbering).lstrip('(').rstrip(')'):
                    agent_data['numbering'] = numbering
            if value.get('d'):
                conference_date = not_repetitive(
                    marc21.bib_id, marc21.rero_id, key, value, 'd')
                if conference_date := remove_trailing_punctuation(
                        conference_date).lstrip('(').rstrip(')'):
                    agent_data['conference_date'] = conference_date
            if value.get('c'):
                place = not_repetitive(
                    marc21.bib_id, marc21.rero_id, key, value, 'c')
                if place := remove_trailing_punctuation(
                        place).lstrip('(').rstrip(')'):
                    agent_data['place'] = place
            if identifier := build_identifier(value):
                agent_data['identifiedBy'] = identifier

    if agent_data:
        agent['type'] = agent_data['type']
        agent['authorized_access_point'] = \
            create_authorized_access_point(agent_data)
        if agent_data.get('identifiedBy'):
            agent['identifiedBy'] = agent_data['identifiedBy']
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
    elif key[:3] == '100':
        roles = ['cre']
    elif key[:3] == '711':
        roles = ['aut']
    else:
        roles = ['ctb']
    if agent:
        return {
            'entity': agent,
            'role': list(set(roles))
        }


@marc21.over('relation', '(770|772|775|776|777|780|785|787|533|534)..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_specific_document_relation(self, key, value):
    """Get contribution."""
    do_specific_document_relation(self, marc21, key, value)


@marc21.over('copyrightDate', '^264.4')
@utils.ignore_value
def marc21_to_copyright_date(self, key, value):
    """Get Copyright Date."""
    copyright_dates = do_copyright_date(self, value)
    return copyright_dates or None


@marc21.over('title', '(^210|^222)..')
@utils.ignore_value
def marc21_to_abbreviated_title(self, key, value):
    """Get abbreviated title data."""
    title_list = do_abbreviated_title(self, marc21, key, value)
    return title_list or None


@marc21.over('editionStatement', '^250..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_edition_statement(self, key, value):
    """Get edition statement data.

    editionDesignation: 250 [$a non repetitive] (without trailing /)
    responsibility: 250 [$b non repetitive]
    """
    edition_data = do_edition_statement(marc21, value)
    return edition_data or None


@marc21.over('provisionActivity', '^(260..|264.[_0-3])')
@utils.for_each_value
@utils.ignore_value
def marc21_to_provision_activity(self, key, value):
    """Get publisher data.

    publisher.name: 264 [$b repetitive] (without the , but keep the ;)
    publisher.place: 264 [$a repetitive] (without the : but keep the ;)
    publicationDate: 264 [$c repetitive] (but take only the first one)
    """
    publication = do_provision_activity(self, marc21, key, value)
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
    300 [$b non repetitive]: colorContent, productionMethod,
        illustrativeContent, note of type otherPhysicalDetails
    300 [$c repetitive]: dimensions, book_formats
    """
    marc21.extract_description_from_marc_field(key, value, self)


@marc21.over('type', '^339..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_type(self, key, value):
    """Get document type."""
    document_type = {}
    if main_type := value.get('a'):
        document_type["main_type"] = main_type
    if sub_type := value.get('b'):
        document_type["subtype"] = sub_type
    return document_type or None


@marc21.over('seriesStatement', '^490..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_series_statement(self, key, value):
    """Get seriesStatement.

    series.name: [490$a repetitive]
    series.number: [490$v repetitive]
    """
    marc21.extract_series_statement_from_marc_field(key, value, self)


@marc21.over('tableOfContents', '^505..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_table_of_contents(self, key, value):
    """Get tableOfContents from repetitive field 505."""
    do_table_of_contents(self, value)


@marc21.over('usageAndAccessPolicy', '^(506|540)..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_usage_and_access_policy_from_field_506_540(self, key, value):
    """Get usageAndAccessPolicy from fields: 506, 540."""
    return do_usage_and_access_policy_from_field_506_540(marc21, key, value)


@marc21.over('frequency', '^(310|321)..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_frequency_field_310_321(self, key, value):
    """Get frequency from fields: 310, 321."""
    return do_frequency_field_310_321(marc21, key, value)


@marc21.over('dissertation', '^502..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_dissertation(self, key, value):
    """Get dissertation from repetitive field 502."""
    # parse field 502 subfields for extracting dissertation
    return do_dissertation(marc21, value)


@marc21.over('summary', '^520..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_summary(self, key, value):
    """Get summary from repetitive field 520."""
    return do_summary(marc21, value)


@marc21.over('intendedAudience', '^521..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_intended_audience(self, key, value):
    """Get intendedAudience from field 521."""
    do_intended_audience(self, value)


@marc21.over('identifiedBy', '^020..')
@utils.ignore_value
def marc21_to_identified_by_from_field_020(self, key, value):
    """Get identifier from field 020."""
    do_identified_by_from_field_020(self, marc21, key, value)


@marc21.over('identifiedBy', '^022..')
@utils.ignore_value
def marc21_to_identified_by_from_field_022(self, key, value):
    """Get identifier from field 022."""
    do_identified_by_from_field_022(self, value)


@marc21.over('identifiedBy', '^024..')
@utils.ignore_value
def marc21_to_identified_by_from_field_024(self, key, value):
    """Get identifier from field 024."""
    do_identified_by_from_field_024(self, marc21, key, value)


@marc21.over('identifiedBy', '^028..')
@utils.ignore_value
def marc21_to_identified_by_from_field_028(self, key, value):
    """Get identifier from field 028."""
    do_identified_by_from_field_028(self, marc21, key, value)


@marc21.over('identifiedBy', '^035..')
@utils.ignore_value
def marc21_to_identified_by_from_field_035(self, key, value):
    """Get identifier from field 035."""
    do_identified_by_from_field_035(self, marc21, key, value, source='RERO')


@marc21.over('identifiedBy', '^930..')
@utils.ignore_value
def marc21_to_identified_by_from_field_930(self, key, value):
    """Get identifier from field 930."""
    if subfield_a := not_repetitive(marc21.bib_id, marc21.rero_id, key, value,
                                    'a', default='').strip():
        identifier = {}
        if match := re_identified.match(subfield_a):
            # match.group(1) : parentheses content
            identifier['source'] = match.group(1)
            # value without parenthesis and parentheses content
            identifier['value'] = match.group(2)
        else:
            identifier['value'] = subfield_a
        identifier['type'] = 'bf:Local'
        identified_by = self.get('identifiedBy', [])
        identified_by.append(identifier)
        self['identifiedBy'] = identified_by


@marc21.over('acquisitionTerms', '^037..')
@utils.ignore_value
def marc21_to_acquisition_terms_from_field_037(self, key, value):
    """Get acquisition terms field 037."""
    do_acquisition_terms_from_field_037(self, value)


@marc21.over('electronicLocator', '^856..')
@utils.ignore_value
def marc21_to_electronicLocator_from_field_856(self, key, value):
    """Get electronicLocator from field 856."""
    electronic_locators = do_electronic_locator_from_field_856(
        self, marc21, key, value)
    return electronic_locators or None


@marc21.over('note', '^(500|510|530|545|555|580)..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_notes_and_original_title(self, key, value):
    """Get notes and original title."""
    do_notes_and_original_title(self, key, value)


@marc21.over('credits', '^(508|511)..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_credits(self, key, value):
    """Get notes and original title."""
    return do_credits(key, value)


@marc21.over('supplementaryContent', '^504..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_supplementary_content(self, key, value):
    """Get notes and original title."""
    if value.get('a'):
        return utils.force_list(value.get('a'))[0]


@marc21.over('subjects', '^(600|610|611|630|650|651|655)..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_subjects(self, key, value):
    """Get subjects.

    - create an object :
        genreForm : for the field 655
        subjects :  for 6xx with $2 rero
        subjects_imported : for 6xx having indicator 2 '0' or '2'
    """
    type_per_tag = {
        '600': EntityType.PERSON,
        '610': EntityType.ORGANISATION,
        '611': EntityType.ORGANISATION,
        '600t': EntityType.WORK,
        '610t': EntityType.WORK,
        '611t': EntityType.WORK,
        '630': EntityType.WORK,
        '650': EntityType.TOPIC,  # or bf:Temporal, changed by code
        '651': EntityType.PLACE,
        '655': EntityType.TOPIC
    }

    source_per_indicator_2 = {
        '0': 'LCSH',
        '2': 'MeSH'
    }

    indicator_2 = key[4]
    tag_key = key[:3]
    subfields_2 = utils.force_list(value.get('2'))
    subfield_2 = subfields_2[0] if subfields_2 else None
    subfields_a = utils.force_list(value.get('a', []))

    if subfield_2 == 'rero':
        if tag_key in ['600', '610', '611'] and value.get('t'):
            tag_key += 't'
        data_type = type_per_tag[tag_key]

        # `data_type` is Temporal if tag is 650 and a $a start with digit.
        if tag_key == '650':
            for subfield_a in subfields_a:
                if subfield_a[0].isdigit():
                    data_type = EntityType.TEMPORAL
                    break

        subject = {
            'type': data_type,
            'source': subfield_2
        }

        subfield_code_per_tag = {
            '600': 'abcd',
            '610': 'ab',
            '611': 'acden',
            '600t': 'tpn',
            '610t': 'tpn',
            '611t': 't',
            '630': 'apn',
            '650': 'a',
            '651': 'a',
            '655': 'a'
        }

        string_build = build_string_from_subfields(
            value, subfield_code_per_tag[tag_key])
        if tag_key == '655':
            # remove the square brackets
            string_build = re.sub(r'^\[(.*)\]$', r'\1', string_build)
        subject['authorized_access_point'] = string_build

        if tag_key in ['600t', '610t', '611t']:
            creator_tag_key = tag_key[:3]  # to keep only tag:  600, 610, 611
            subject['authorized_access_point'] = remove_trailing_punctuation(
                build_string_from_subfields(
                    value,
                    subfield_code_per_tag[creator_tag_key]),
                '.', '.'
            ) + '. ' + subject['authorized_access_point']
        field_key = 'genreForm' if tag_key == '655' else 'subjects'
        subfields_0 = utils.force_list(value.get('0'))
        if field_key != 'subjects_imported' and (ref := get_mef_link(
            bibid=marc21.bib_id,
            reroid=marc21.rero_id,
            entity_type=data_type,
            ids=utils.force_list(subfields_0),
            key=key
        )):
            subject = {
                '$ref': ref,
            }
        else:
            if identifier := build_identifier(value):
                subject['identifiedBy'] = identifier
            if field_key != 'genreForm':
                perform_subdivisions(subject, value)

        if subject.get('$ref') or subject.get('authorized_access_point'):
            subjects = self.get(field_key, [])
            subjects.append(dict(entity=subject))
            self[field_key] = subjects

    elif subfield_2 == 'rerovoc' or indicator_2 in ['0', '2']:
        if term_string := build_string_from_subfields(
           value, 'abcdefghijklmnopqrstuw', ' - '):
            source = 'rerovoc' if subfield_2 == 'rerovoc' \
                else source_per_indicator_2[indicator_2]
            subject_imported = {
                'type': type_per_tag[tag_key],
                'source': source,
                'authorized_access_point': term_string
            }
            perform_subdivisions(subject_imported, value)

            subjects_imported = self.get('subjects_imported', [])
            if subject_imported:
                subjects_imported.append(dict(entity=subject_imported))
                self['subjects_imported'] = subjects_imported


@marc21.over('subjects_imported', '^919..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_subjects_imported(self, key, value):
    """Get subject and genreForm_imported imported from 919 (L53, L54)."""
    specific_contains_regexp = \
        re.compile(r'\[(carte postale|affiche|document photographique)\]')
    contains_specific_voc_regexp = re.compile(
            r'^(chrero|rerovoc|ram|rameau|gnd|rerovoc|gatbegr|gnd-content)$')

    subfields_2 = utils.force_list(value.get('2'))
    term_string = ''
    data_imported = None
    field_key = 'subjects_imported'
    if subfields_2:
        subfield_2 = subfields_2[0]
        if contains_specific_voc_regexp.search(subfield_2):
            add_data_imported = False
            if subfield_2 == 'chrero':
                subfields_9 = utils.force_list(value.get('9'))
                subfield_9 = subfields_9[0]
                if subfields_v := utils.force_list(value.get('v')):
                    subfield_v = subfields_v[0]
                    match = specific_contains_regexp.search(subfield_v)
                    if match:
                        contains_655_regexp = re.compile(r'655')
                        match = contains_655_regexp.search(subfield_9)
                        add_data_imported = True
                    if match:
                        field_key = 'genreForm_imported'
            else:
                add_data_imported = True
                if subfield_2 in ['gatbegr', 'gnd-content']:
                    field_key = 'genreForm_imported'
            if add_data_imported:
                term_string = build_string_from_subfields(
                    value,
                    'abcdefghijklmnopqrstuvwxyz', ' - ')
                data_imported = {
                    'type': EntityType.TOPIC,
                    'source': subfield_2,
                    'authorized_access_point': term_string
                }
    elif term_string := build_string_from_subfields(
            value, 'abcdefghijklmnopqrstuvwxyz', ' - '):
        data_imported = {
            'type': EntityType.TOPIC,
            'authorized_access_point': term_string
        }
    if data_imported:
        subjects_or_genre_form_imported_imported = self.get(field_key, [])
        subjects_or_genre_form_imported_imported.append(
            dict(entity=data_imported))
        self[field_key] = subjects_or_genre_form_imported_imported


@marc21.over('sequence_numbering', '^362..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_sequence_numbering(self, key, value):
    """Get notes and original title."""
    do_sequence_numbering(self, value)


@marc21.over('classification', '^(050|060|080|082|980)..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_classification(self, key, value):
    """Get classification and subject from 980."""
    classification_type_per_tag = {
        '050': 'bf:ClassificationLcc',
        '060': 'bf:ClassificationNlm',
        '080': 'bf:ClassificationUdc',
        '082': 'bf:ClassificationDdc',
    }

    def get_classif_type_and_subdivision_codes_from_980_2(subfield_2):
        if not subfield_2:
            return None, None
        classification_type_per_tag_980_2 = {
            'brp': 'classification_brunetparguez',
            'dr-sys': 'classification_droit',
            'musi': 'classification_musicale_instruments',
            'musg': 'classification_musicale_genres'
        }
        subdivision_subfield_codes_per_tag_980_2 = {
            'brp': {'d'},
            'musg': {'d', 'e'}
        }
        classification_type = None
        subdivision_subfield_codes = None
        for key in classification_type_per_tag_980_2:
            regexp = re.compile(fr'{key}', re.IGNORECASE)
            if regexp.search(subfield_2):
                classification_type = classification_type_per_tag_980_2[key]
                if key in subdivision_subfield_codes_per_tag_980_2:
                    subdivision_subfield_codes = \
                        subdivision_subfield_codes_per_tag_980_2[key]
                break
        return classification_type, subdivision_subfield_codes

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
        if tag == '980':
            if subfield_2 and _CONTAINS_FACTUM_REGEXP.search(subfield_2):
                subject = {
                    'type': EntityType.PERSON,
                    'authorized_access_point': subfield_a,
                    'source': 'Factum'
                }
                subjects = self.get('subjects', [])
                subjects.append(dict(entity=subject))
                self['subjects'] = subjects

            classif_type, subdivision_subfield_codes = \
                get_classif_type_and_subdivision_codes_from_980_2(subfield_2)
            if classif_type:
                classification['type'] = classif_type
                if subdivision_subfield_codes:
                    items = get_field_items(value)
                    subdivision = []
                    for blob_key, blob_value in items:
                        if blob_key in subdivision_subfield_codes:
                            subdivision.append(blob_value)
                    if subdivision:
                        classification['subdivision'] = subdivision
            else:  # avoid classification if type not found
                classification = None

        else:
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
        classification_list = self.get('classification', [])
        if classification:
            classification_list.append(classification)
            self['classification'] = classification_list


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

    if key[:3] == '800' and value.get('t'):
        if work_access_point := do_work_access_point(marc21, key, value):
            self.setdefault('work_access_point', [])
            self['work_access_point'].append(work_access_point)

    part_of = {}
    numbering_list = []
    subfield_w = not_repetitive(marc21.bib_id,  marc21.rero_id,
                                key, value, 'w', default='').strip()
    if subfield_w:
        match = re.compile(r'^REROILS:')
        pid = match.sub('', subfield_w)
        part_of['document'] = {
            '$ref': f'https://bib.rero.ch/api/documents/{pid}'
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
                    numbering.add_numbering_value('volume', str(subfield_v))
                if numbering.is_valid():
                    numbering_list.append(numbering.get())
        if 'document' in part_of:
            if numbering_list:
                part_of['numbering'] = numbering_list
            self['partOf'] = self.get('partOf', [])
            if part_of not in self['partOf']:
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


@marc21.over('_masked', '^099..')
def marc21_to_masked(self, key, value):
    """Get masked.

    masked: [099$a masked]
    """
    return value.get('a') == 'masked'


@marc21.over('work_access_point', '(^130..|^730..)')
@utils.for_each_value
@utils.ignore_value
def marc21_to_work_access_point(self, key, value):
    """Get work access point."""
    return do_work_access_point(marc21, key, value)


@marc21.over('scale_cartographicAttributes', '^255..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_scale_cartographic_attributes(self, key, value):
    """Get scale and/or cartographicAttributes."""
    do_scale_and_cartographic(self, marc21, key, value)


@marc21.over('temporalCoverage', '^045..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_temporal_coverage(self, key, value):
    """Get temporal coverage."""
    return do_temporal_coverage(marc21, key, value)
