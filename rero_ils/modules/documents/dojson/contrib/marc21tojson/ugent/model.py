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

from dojson import utils
from flask import current_app

from rero_ils.dojson.utils import ReroIlsMarc21Overdo, \
    build_string_from_subfields
from rero_ils.modules.entities.models import EntityType

from ..utils import do_abbreviated_title, \
    do_acquisition_terms_from_field_037, do_classification, do_contribution, \
    do_copyright_date, do_dissertation, do_edition_statement, \
    do_electronic_locator_from_field_856, do_frequency_field_310_321, \
    do_identified_by_from_field_010, do_identified_by_from_field_020, \
    do_identified_by_from_field_022, do_identified_by_from_field_024, \
    do_identified_by_from_field_028, do_identified_by_from_field_035, \
    do_intended_audience, do_issuance, do_language, \
    do_notes_and_original_title, do_part_of, do_provision_activity, \
    do_scale_and_cartographic, do_sequence_numbering, \
    do_specific_document_relation, do_summary, do_table_of_contents, \
    do_temporal_coverage, do_title, do_type, \
    do_usage_and_access_policy_from_field_506_540, do_work_access_point, \
    do_work_access_point_240, perform_subdivisions

marc21 = ReroIlsMarc21Overdo()


@marc21.over('issuance', 'leader')
@utils.ignore_value
def marc21_to_type_and_issuance(self, key, value):
    """Get document type, content/Media/Carrier type and mode of issuance."""
    do_issuance(self, marc21)
    do_type(self, marc21)


@marc21.over('language', '^008')
@utils.ignore_value
def marc21_to_language(self, key, value):
    """Get languages.

    languages: 008 and 041 [$a, repetitive]
    """
    language = do_language(self, marc21)
    return language or None


@marc21.over('title', '(^210|^222)....')
@utils.ignore_value
def marc21_to_abbreviated_title(self, key, value):
    """Get abbreviated title data."""
    title_list = do_abbreviated_title(self, marc21, key, value)
    return title_list or None


@marc21.over('title', '^245..')
@utils.ignore_value
def marc21_to_title(self, key, value):
    """Get title data."""
    title_list = do_title(self, marc21, value)
    return title_list or None


@marc21.over('contribution', '(^100|^700|^710|^711)..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_contribution(self, key, value):
    """Get contribution."""
    return do_contribution(self, marc21, key, value)


@marc21.over('relation', '(770|772|775|776|777|780|785|787|533|534)..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_specific_document_relation(self, key, value):
    """Get contribution."""
    do_specific_document_relation(self, marc21, key, value)


@marc21.over('copyrightDate', '^26[04].4')
@utils.ignore_value
def marc21_to_copyright_date(self, key, value):
    """Get Copyright Date."""
    copyright_dates = do_copyright_date(self, value)
    return copyright_dates or None


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


@marc21.over('provisionActivity', '^26[04].[_0-3]')
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
    300 [$a non repetitive]: colorContent, productionMethod,
        illustrativeContent, note of type otherPhysicalDetails
    300 [$c repetitive]: dimensions, book_formats
    """
    marc21.extract_description_from_marc_field(key, value, self)


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
def marc21_to_abstract(self, key, value):
    """Get summary from repetitive field 520."""
    return do_summary(marc21, value)


@marc21.over('intendedAudience', '^521..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_intended_audience(self, key, value):
    """Get intendedAudience from field 521."""
    do_intended_audience(self, value)


@marc21.over('identifiedBy', '^010..')
@utils.ignore_value
def marc21_to_identified_by_from_field_010(self, key, value):
    """Get identifier from field 010."""
    do_identified_by_from_field_010(self, marc21, key, value)


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
    do_identified_by_from_field_035(self, marc21, key, value)


@marc21.over('acquisitionTerms', '^037..')
@utils.ignore_value
def marc21_to_acquisition_terms_from_field_037(self, key, value):
    """Get acquisition terms field 037."""
    do_acquisition_terms_from_field_037(self, value)


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
    subfield_a = None
    if value.get('a'):
        subfield_a = utils.force_list(value.get('a'))[0]
        if key[:3] == '511':
            subfield_a = f'Participants ou interprètes: {subfield_a}'
        credits = self.get('credits', [])
        credits.append(subfield_a)
        self['credits'] = credits


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
def marc21_to_subjects_6XX(self, key, value):
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

    conference_per_tag = {
        '610': False,
        '611': True
    }
    source_per_indicator_2 = {
        '7': 'LCSH',
        '2': 'MeSH'
    }

    indicator_2 = key[4]
    tag_key = key[:3]
    subfields_2 = utils.force_list(value.get('2'))
    subfield_2 = subfields_2[0] if subfields_2 else None

    config_field_key = \
        current_app.config.get(
            'RERO_ILS_IMPORT_6XX_TARGET_ATTRIBUTE',
            'subjects_imported'
        )

    if subfield_2 == 'lcsh' or indicator_2 in ['0', '2', '7']:
        term_string = build_string_from_subfields(
            value, 'abcdefghijklmnopqrstuw', ' - ')
        if term_string:
            source = 'LCSH' if subfield_2 == 'lcsh' else \
                source_per_indicator_2[indicator_2]
            data = {
                'type': type_per_tag[tag_key],
                'source': source,
                'authorized_access_point': term_string.rstrip('.')
            }
            perform_subdivisions(data, value)
            if data:
                self.setdefault(config_field_key, []).append(
                    dict(entity=data))


@marc21.over('sequence_numbering', '^362..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_sequence_numbering(self, key, value):
    """Get notes and original title."""
    do_sequence_numbering(self, value)


@marc21.over('classification', '^(050|060|080|082)..')
@utils.for_each_value
@utils.ignore_value
def marc21_to_classification(self, key, value):
    """Get classification and subject."""
    do_classification(self, key, value)


@marc21.over('electronicLocator', '^856..')
@utils.ignore_value
def marc21_to_electronicLocator_from_field_856(self, key, value):
    """Get electronicLocator from field 856."""
    electronic_locators = do_electronic_locator_from_field_856(
        self, marc21, key, value)
    return electronic_locators or None


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
    do_part_of(self, marc21, key, value)


@marc21.over('work_access_point', '(^130..|^700.2|^710.2|^730..)')
@utils.for_each_value
@utils.ignore_value
def marc21_to_work_access_point(self, key, value):
    """Get work access point."""
    return do_work_access_point(marc21, key, value)


@marc21.over('work_access_point', '(^240..)')
@utils.for_each_value
@utils.ignore_value
def marc21_to_work_access_point_240(self, key, value):
    """Get work access point for 240 tag."""
    return do_work_access_point_240(marc21, key, value)


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
