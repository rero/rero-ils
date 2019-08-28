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

"""Dojson utils."""

import click
from dojson import Overdo, utils


class ReroIlsMarc21Overdo(Overdo):
    """Specialized Overdo.

    The purpose of this class is to store the blob record in order to
    have access to all the record fields during the Overdo processing.
    This class provide also record field manipulation functions.
    """

    blob_record = None
    field_008_data = ''
    lang_from_008 = None
    date1_from_008 = None
    date2_from_008 = None
    date_type_from_008 = ''
    langs_from_041_a = []
    langs_from_041_h = []
    alternate_graphic = {}

    def __init__(self, bases=None, entry_point_group=None):
        """ReroIlsMarc21Overdo init."""
        super(ReroIlsMarc21Overdo, self).__init__(
            bases=bases, entry_point_group=entry_point_group)

    def do(self, blob, ignore_missing=True, exception_handlers=None):
        """Translate blob values and instantiate new model instance."""
        self.blob_record = blob
        self.field_008_data = ''
        self.date1_from_008 = None
        self.date2_from_008 = None
        self.date_type_from_008 = ''
        fields_008 = self.get_fields(tag='008')
        if fields_008:
            self.field_008_data = self.get_control_field_data(
                fields_008[0]).replace('\n', '')
            self.date1_from_008 = self.field_008_data[7:11]
            self.date2_from_008 = self.field_008_data[11:15]
            self.date_type_from_008 = self.field_008_data[6]
        self.init_lang()
        self.init_country()
        self.init_alternate_graphic()
        result = super(ReroIlsMarc21Overdo, self).do(
            blob,
            ignore_missing=ignore_missing,
            exception_handlers=exception_handlers
        )
        return result

    def get_fields(self, tag=None):
        """Get all fields having the given tag value."""
        fields = []
        if isinstance(self.blob_record, utils.GroupableOrderedDict):
            items = self.blob_record.iteritems(repeated=True)
        else:
            items = utils.iteritems(self.blob_record)
        for blob_key, blob_value in items:
            field_data = {}
            tag_value = blob_key[0:3]
            if (tag_value == tag) or not tag:
                field_data['tag'] = tag_value
                if len(blob_key) == 3:  # if control field
                    field_data['data'] = blob_value.strip()
                else:
                    field_data['ind1'] = blob_key[3:4]
                    field_data['ind2'] = blob_key[4:5]
                    field_data['subfields'] = blob_value
                fields.append(field_data)
        return fields

    def get_control_field_data(self, field):
        """Get control fields data."""
        field_data = None
        if int(field['tag']) < 10:
            field_data = field['data']
        else:
            raise ValueError('control field expected (tag < 01x)')
        return field_data

    def get_subfields(self, field, code=None):
        """Get all subfields having the given subfield code value."""
        subfields = []

        if int(field['tag']) >= 10:
            if isinstance(field['subfields'], utils.GroupableOrderedDict):
                items = field['subfields'].iteritems(repeated=True)
            else:
                items = utils.iteritems(field['subfields'])
            for subfield_code, subfield_data in items:
                if (subfield_code == code) or not code:
                    subfields.append(subfield_data)
        else:
            raise ValueError('data field expected (tag >= 01x)')
        return subfields

    def get_link_data(self, subfields_6_data):
        """Extract link and script data from subfields $6 data."""
        link = None
        tag, extra_data = subfields_6_data.split('-')
        if extra_data:
            link_and_script_data = extra_data.split('/')
            link = link_and_script_data[0]
            try:
                script_code = link_and_script_data[1]
            except Exception:
                script_code = 'latn'
            try:
                script_dir = link_and_script_data[2]
            except Exception:
                script_dir = ''
        return tag, link, script_code, script_dir

    def init_country(self):
        """Initialization country (008 and 044)."""
        self.country = None
        self.cantons = []
        fields_044 = self.get_fields(tag='044')
        if fields_044:
            field_044 = fields_044[0]
            cantons_codes = self.get_subfields(field_044, 'c')
            for cantons_codes in self.get_subfields(field_044, 'c'):
                self.cantons.append(cantons_codes.split('-')[1])
            if self.cantons:
                self.country = 'sz'
        else:
            if len(self.field_008_data) > 18:
                self.country = self.field_008_data[15:18].rstrip()

    def init_lang(self):
        """Initialization languages (008 and 041)."""
        def init_lang_from(fields_041, code):
            """Construct list of language codes from data."""
            langs_from_041 = []
            for field_041 in fields_041:
                lang_codes = self.get_subfields(field_041, code)
                for lang_from_041 in lang_codes:
                    if lang_from_041 not in langs_from_041:
                        langs_from_041.append(lang_from_041)
            return langs_from_041

        # check len(value) to avoid getting char[35:38] if data is invalid
        self.lang_from_008 = ''
        self.langs_from_041_a = []
        self.langs_from_041_h = []
        if len(self.field_008_data) > 38:
            self.lang_from_008 = self.field_008_data[35:38]
        fields_041 = self.get_fields(tag='041')
        self.langs_from_041_a = init_lang_from(fields_041, code='a')
        self.langs_from_041_h = init_lang_from(fields_041, code='h')

    def init_alternate_graphic(self):
        """Initialization of alternate graphic representation.

        Parse all the 880 fields and populate a dictionary having as first
        level keys the tag of the linked field and as secound level key the
        link code (from $6) of the linked field. The language script is
        extracted from $6 and used to qualify the alternate graphic value.
        """
        def get_script_from_lang(asian=False):
            """Initialization of alternate graphic representation."""
            script_per_lang_asia = {
                'jpn': 'jpan',
                'kor': 'kore',
                'chi': 'hani'
            }
            script_per_lang_not_asian = {
                'gre': 'grek',
                'grc': 'grek',
                'ara': 'arab',
                'per': 'arab',
                'bel': 'cyrl',
                'rus': 'cyrl',
                'mac': 'cyrl',
                'srp': 'cyrl',
                'ukr': 'cyrl',
                'chu': 'cyrl',
                'yid': 'hebr',
                'heb': 'hebr',
                'lad': 'hebr',
                'chi': 'hani'
            }
            script = None
            default_script = 'zyyy'
            script_per_lang = script_per_lang_not_asian
            if asian:
                default_script = 'hani'
                script_per_lang = script_per_lang_asia
            script = script_per_lang.get(self.lang_from_008, None)
            if not script:
                for lang in self.langs_from_041_a:
                    if lang in script_per_lang:
                        script = script_per_lang[lang]
                        break
                if not script:
                    script = default_script
            return script

        # function init_alternate_graphic start here
        self.alternate_graphic = {}
        script_per_code = {
            '(S': 'grek',
            '(3': 'arab',
            '(B': 'latn',
            '(N': 'cyrl',
            '(2': 'hebr'
        }
        fields_880 = self.get_fields(tag='880')
        for field_880 in fields_880:
            try:
                subfields_6 = self.get_subfields(field_880, code='6')
                for subfield_6 in subfields_6:
                    tag, link, script_code, script_dir = self.get_link_data(
                        subfield_6)
                    tag_data = self.alternate_graphic.get(tag, {})
                    link_data = tag_data.get(link, {})
                    if script_code == '$1':
                        script = get_script_from_lang(asian=True)
                    elif script_code in script_per_code:
                        script = script_per_code[script_code]
                    else:
                        script = get_script_from_lang()
                    link_data['script'] = script
                    link_data['field'] = field_880
                    if script_dir == 'r':
                        link_data['right_to_left'] = True
                    tag_data[link] = link_data
                    self.alternate_graphic[tag] = tag_data
            except Exception as exp:
                click.secho(
                    'Error in init_alternate_graphic: {error}'.format(
                        error=exp
                    ),
                    fg='red'
                )
