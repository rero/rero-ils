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

import re
import sys
import traceback

import click
from dojson import Overdo, utils

LANGUAGES_SCRIPTS = {
    'arab': ('ara', 'per'),
    'cyrl': ('bel', 'chu', 'mac', 'rus', 'srp', 'ukr'),
    'grek': ('grc', 'gre'),
    'hani': ('chi', 'jpn'),
    'hebr': ('heb', 'lad', 'yid'),
    'jpan': ('jpn', ),
    'kore': ('kor', ),
    'zyyy': ('chi', )
}

SCRIPT_PER_LANG_ASIA = {
    'jpn': 'jpan',
    'kor': 'kore',
    'chi': 'hani'
}
SCRIPT_PER_LANG_NOT_ASIA = {
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

SCRIPT_PER_CODE = {
    '(S': 'grek',
    '(3': 'arab',
    '(B': 'latn',
    '(N': 'cyrl',
    '(2': 'hebr'
}


def error_print(*args):
    """Error printing to sdterr."""
    msg = ''
    for arg in args:
        msg += str(arg) + '\t'
    msg.strip()
    click.echo(msg, err=True)
    sys.stderr.flush()


def make_year(date):
    """Test if string is integer and between -9999 to 9999."""
    try:
        int_date = int(date)
        if int_date >= -9999 and int_date < 9999:
            return int_date
    except:
        pass
    return None


def not_repetitive(bibid, key, value, subfield, default=None):
    """Get the first value if the value is a list or tuple."""
    if default is None:
        data = value.get(subfield)
    else:
        data = value.get(subfield, default)
    if isinstance(data, (list, tuple)):
        error_print('WARNING NOT REPETITIVE:', bibid, key, subfield, value)
        data = data[0]
    return data


def get_field_link_data(value):
    """Get field link data from subfield $6."""
    subfield_6 = value.get('6', '')
    tag_link = subfield_6.split('-')
    link = ''
    if len(tag_link) == 2:
        link = tag_link[1]
    return tag_link, link


def get_field_items(value):
    """Get field items."""
    if isinstance(value, utils.GroupableOrderedDict):
        return value.iteritems(repeated=True)
    else:
        return utils.iteritems(value)


def remove_trailing_punctuation(
        data,
        punctuation=',',
        spaced_punctuation=':;/-'):
    """Remove trailing punctuation from data.

    :param data: string to process
    :type data: str
    :param punctuation: punctuation characters to be removed
        (preceded by a space or not)
    :type punctuation: str
    :param spaced_punctuation: punctuation characters needing
        one or more preceding space(s) in order to be removed.
    :type spaced_punctuation: str

    :return: the data string with specific trailing punctuation removed
    :rtype: list
    """
    # escape chars: .[]^-
    if punctuation:
        punctuation = re.sub(r'([\.\[\]\^\\-])', r'\\\1', punctuation)
    if spaced_punctuation:
        spaced_punctuation = \
            re.sub(r'([\.\[\]\^\\-])', r'\\\1', spaced_punctuation)

    return re.sub(
        r'([{0}]|\s+[{1}])$'.format(punctuation, spaced_punctuation),
        '',
        data.rstrip()).rstrip()


class ReroIlsOverdo(Overdo):
    """Specialized Overdo.

    The purpose of this class is to store the blob record in order to
    have access to all the record fields during the Overdo processing.
    This class provide also record field manipulation functions.
    """

    blob_record = None

    def __init__(self, bases=None, entry_point_group=None):
        """Reroilsoverdo init."""
        super(ReroIlsOverdo, self).__init__(
            bases=bases, entry_point_group=entry_point_group)

    def do(self, blob, ignore_missing=True, exception_handlers=None):
        """Translate blob values and instantiate new model instance."""
        self.blob_record = blob
        result = super(ReroIlsOverdo, self).do(
            blob,
            ignore_missing=ignore_missing,
            exception_handlers=exception_handlers
        )
        return result

    def get_fields(self, tag=None):
        """Get all fields having the given tag value."""
        fields = []
        items = get_field_items(self.blob_record)
        for blob_key, blob_value in items:
            field_data = {}
            tag_value = blob_key[0:3]
            if (tag_value == tag) or not tag:
                field_data['tag'] = tag_value
                if len(blob_key) == 3:  # if control field
                    field_data['data'] = blob_value.rstrip()
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
            items = get_field_items(field['subfields'])
            for subfield_code, subfield_data in items:
                if (subfield_code == code) or not code:
                    subfields.append(subfield_data)
        else:
            raise ValueError('data field expected (tag >= 01x)')
        return subfields


class ReroIlsMarc21Overdo(ReroIlsOverdo):
    """Specialized Overdo.

    This class adds RERO Marc21 properties and functions to the ReroIlsOverdo.
    """

    bib_id = ''
    field_008_data = ''
    lang_from_008 = None
    date1_from_008 = None
    date2_from_008 = None
    date_type_from_008 = ''
    langs_from_041_a = []
    langs_from_041_h = []
    alternate_graphic = {}

    def __init__(self, bases=None, entry_point_group=None):
        """Reroilsmarc21overdo init."""
        super(ReroIlsMarc21Overdo, self).__init__(
            bases=bases, entry_point_group=entry_point_group)
        self.count = 0

    def do(self, blob, ignore_missing=True, exception_handlers=None):
        """Translate blob values and instantiate new model instance."""
        self.count += 1
        result = None
        try:
            self.blob_record = blob
            try:
                self.bib_id = self.get_fields(tag='001')[0]['data']
            except Exception as err:
                self.bib_id = '???'
            self.field_008_data = ''
            self.date1_from_008 = None
            self.date2_from_008 = None
            self.date_type_from_008 = ''
            fields_008 = self.get_fields(tag='008')
            if fields_008:
                self.field_008_data = self.get_control_field_data(
                    fields_008[0]).rstrip()
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
        except Exception as err:
            error_print('ERROR:', self.bib_id, self.count, err)
            traceback.print_exc()
        return result

    def get_link_data(self, subfields_6_data):
        """Extract link and script data from subfields $6 data."""
        link = None
        tag, extra_data = subfields_6_data.split('-')
        if extra_data:
            link_and_script_data = extra_data.split('/')
            link = link_and_script_data[0]
            try:
                script_code = link_and_script_data[1]
            except Exception as err:
                script_code = 'latn'
            try:
                script_dir = link_and_script_data[2]
            except Exception as err:
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
                try:
                    canton = cantons_codes.split('-')[1].strip()
                    self.cantons.append(canton)
                except Exception as err:
                    error_print('ERROR INIT CANTONS:', self.bib_id,
                                cantons_codes)
            if self.cantons:
                self.country = 'sz'
        else:
            try:
                self.country = self.field_008_data[15:18].rstrip()
            except Exception as err:
                pass

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

        self.lang_from_008 = ''
        self.langs_from_041_a = []
        self.langs_from_041_h = []
        try:
            self.lang_from_008 = self.field_008_data[35:38]
        except Exception as err:
            self.lang_from_008 = 'und'
            error_print('WARNING:', "set 008 language to 'und'")

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
            script = None
            default_script = 'zyyy'
            script_per_lang = SCRIPT_PER_LANG_NOT_ASIA
            if asian:
                default_script = 'hani'
                script_per_lang = SCRIPT_PER_LANG_ASIA
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
                    elif script_code in SCRIPT_PER_CODE:
                        script = SCRIPT_PER_CODE[script_code]
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

    def get_language_script(self, script_code):
        """Build the `language-script` code.

        This code is built according to the format
        <lang_code>-<script_code> for example: chi-hani;
        the <lang_code> is retrived from field 008 and 041
        the <script_code> is received as parameter

        :param script_code: the script code
        :param script_code: str
        :return: language script code in the format `<lang_code>-<script_code>`
        :rtype: str
        """
        if script_code in LANGUAGES_SCRIPTS:
            languages = (
                [self.lang_from_008] +
                self.langs_from_041_a +
                self.langs_from_041_h)
            for lang in languages:
                if lang in LANGUAGES_SCRIPTS[script_code]:
                    return '-'.join([lang, script_code])
            error_print('WARNING LANGUAGE SCRIPTS:', self.bib_id,
                        script_code,  '008:', self.lang_from_008,
                        '041$a:', self.langs_from_041_a,
                        '041$h:', self.langs_from_041_h)
        return '-'.join(['und', script_code])

    def build_value_with_alternate_graphic(
            self, tag, code, label, index, link,
            punct=None, spaced_punct=None):
        """
        Build the data structure for alternate graphical representation.

        :param tag: the marc field tag
        :param code: contains the subfield code. Used for debug only
        :param label: the subfield data value
        :param index: the subfield index position in the field
        :param link: the link code to the alternate graphic field 880
        :param punct: punctuation chars to remove i.e. ',.'
        :param spaced_punct: punctuation chars preceded by a space to remove
        :return: a list of 1 value, or 2 values if alternate graphical exists
        :rtype: list

        Example of return value:
        [
            {
                "value": "B.I. Bursov"
            },
            {
                "value": "Б.И. Бурсов",
                "language": "rus-cyrl"
            }
        ]
        """
        def clean_punctuation(value, punct, spaced_punct):
            return remove_trailing_punctuation(
                value,
                punctuation=punct,
                spaced_punctuation=spaced_punct)

        # build_value_with_alternate_graphic starts here

        data = [{
            'value': clean_punctuation(label, punct, spaced_punct).strip()
        }]
        try:
            alt_gr = self.alternate_graphic[tag][link]
            subfield = self.get_subfields(alt_gr['field'])[index]
            data.append({
                'value': clean_punctuation(subfield, punct, spaced_punct),
                'language': self.get_language_script(alt_gr['script'])
            })
        except Exception as err:
            pass
        return data

    def build_variant_title_data(self, string_set):
        """Build variant title data form fields 246.

        :param string_set: the marc field tag
        :type string_set: set
        :return: a list of variant_title object
        :rtype: list
        """
        variant_list = []
        fields_246 = self.get_fields(tag='246')
        for field_246 in fields_246:
            variant_data = {}
            subfield_246_a = ''
            subfields_246_a = self.get_subfields(field_246, 'a')
            if subfields_246_a:
                subfield_246_a = subfields_246_a[0]
            subfield_246_a_cleaned = remove_trailing_punctuation(
                                        subfield_246_a, ',.', ':;/-=')
            if subfield_246_a_cleaned not in string_set:
                # parse all subfields in order
                index = 1
                items = get_field_items(field_246['subfields'])
                tag_link, link = get_field_link_data(field_246)
                part_list = TitlePartList(
                    part_number_code='n',
                    part_name_code='p'
                )

                subfield_selection = {'a', 'n', 'p'}
                for blob_key, blob_value in items:
                    if blob_key in subfield_selection:
                        if blob_key == 'a':
                            subfield_a_parts = blob_value.split(':')
                            part_index = 0
                            for subfield_a_part in subfield_a_parts:
                                value_data = self. \
                                    build_value_with_alternate_graphic(
                                        '246', blob_key, subfield_a_part,
                                        index, link, ',.', ':;/-=')
                                if part_index == 0:
                                    variant_data['type'] = 'bf:VariantTitle'
                                    variant_data['mainTitle'] = value_data
                                else:
                                    variant_data['subtitle'] = value_data
                                part_index += 1
                        elif blob_key in ['n', 'p']:
                            value_data = self. \
                                build_value_with_alternate_graphic(
                                    '246', blob_key, blob_value,
                                    index, link, ',.', ':;/-=')
                            part_list.update_part(
                                value_data, blob_key, blob_value)
                    if blob_key != '__order__':
                        index += 1
                the_part_list = part_list.get_part_list()
                if the_part_list:
                    variant_data['part'] = the_part_list
                variant_list.append(variant_data)
            else:
                pass
                # for showing the variant title skipped for debugging purpose
                # print('variant skipped', subfield_246_a_cleaned)
        return variant_list


class TitlePartList(object):
    """The purpose of this class is to build the title part list.

    The title part list is build parsing the subfields $n, $p of fields 245
    or 246. Each title part is build for a couple of consecutive $n, $p.
    As some $n or $p can be missing, some part are build only form a $p or $n.

    To build a list of parts, you must create an instance of this class for
    a given field 245 or 246. Then you have to parse the subfields $n and $p
    in the order of appearance in the field (245 or 246) and call the "update"
    method for each of these subfields. At the end of the parsing, the method
    "get_part_list" provides the list of constructed parts.

    :param part_number_code: the specific subfield code
    :type part_number_code: char
    :param part_name_code: the specific subfield code
    :type part_name_code: char
    """

    def __init__(self, part_number_code, part_name_code):
        """Constructor method."""
        self.part_number_waiting_name = {}
        self.part_list = []
        self.part_number_code = part_number_code
        self.part_name_code = part_name_code

    def update_part(self, value_data, subfield_code, subfield_data):
        """Update part data.

        The part object is progressively build with the data collected by
        the succesive calls of the method `update_part`.

        :param subfield_code: specific subfield code for part number or name
        :type subfield_code: char
        :param subfield_data: part number or name depending of `subfield_code`
        :type subfield_data: str
        """
        if self.part_number_waiting_name:
            if subfield_code == self.part_name_code:
                self.part_list.append(
                    dict(partNumber=self.part_number_waiting_name,
                         partName=value_data)
                )
                self.part_number_waiting_name = {}
            else:
                self.part_list.append(
                    dict(partNumber=self.part_number_waiting_name)
                )
                self.part_number_waiting_name = value_data
        else:
            if subfield_code == self.part_number_code:
                self.part_number_waiting_name = value_data
            else:
                self.part_list.append(dict(partName=value_data))

    def get_part_list(self):
        """Get the part list.

        This method return a list of part object build by succesive call of
        the method `update_part`. If a part with only the `part_number` is
        pending, it is appended to the list because it will never receive a
        `part_name`.

        :return: an part list object
        :rtype: list
        """
        if self.part_number_waiting_name:
            self.part_list.append(
                dict(partNumber=self.part_number_waiting_name)
                )
        return self.part_list


def extract_subtitle_and_parallel_titles_from_field_245_b(
        parallel_title_data, field_245_a_end_with_equal):
    """Extracts subtitle and parallel titles from field 245 $b.

    This function retrieves the subtitle and the parallel title list
    from field 245 $b. It also constructs a set containing the parallel title
    and these same title without the initial article.
    This set can be used to process the fields 246 to discard those fields
    that match one of the elements in the set.
    It should be noted that the deletion of the article is achieved simply
    by deleting the first word (max 4 chars) of the parallel title.
    It is not a problem if this word is not a real article because the chain
    produced will not correspond to one of the 246 fields to be discarded.

    :param parallel_title_data: list of parallel_title objects
    :param field_245_a_end_with_equal: boolean flag
    :return: a tuple
        - the main subtitle
        - a list of parallel titles
        - a set of pararalel title strings
    :rtype: tuple

    """

    def remove_leading_article(string, max_article_len=4):
        """Remove the leading article.

        - Any leading word up to 'max_article_len' chars is considered
          as an article to remove.
        - The separateur is an APOSTROPHE or a SPACE.
        :param string: the string to process
        :param max_article_len: the length of article to remove (default: 4)
        :return: the given string without the first word,
            with the given 'max_article_len' chars.
            An empty string is returned if no leading word is removed.
        """
        last_rest = ''
        for sep in ("'", ' '):
            first, sep, rest = string.partition(sep)
            len_rest = len(rest)
            if len(first) <= max_article_len \
                    and len_rest > 0 and len_rest > len(last_rest):
                last_rest = rest
        return last_rest

    data_std = ''
    data_lang = ''
    lang = ''
    main_subtitle = []
    parallel_titles = []
    pararalel_title_string_set = set()
    for parallel_title_value in parallel_title_data:
        value = parallel_title_value.get('value', '')
        lang = parallel_title_value.get('language', '')
        if lang:
            data_lang = value
        else:
            data_std = value

    data_std_items = data_std.split('=')
    data_lang_items = []
    if data_lang:
        data_lang_items = data_lang.split('=')
    index = 0
    out_data_dict = {}

    for data_std in data_std_items:
        if index == 0 and not field_245_a_end_with_equal:
            main_subtitle.append({'value': data_std.rstrip()})
            if lang and index < len(data_lang_items):
                main_subtitle.append({
                    'value': data_lang_items[index].rstrip(),
                    'language': lang
                })
        else:
            out_data_dict = {'type': 'bf:ParallelTitle'}
            main_title = []
            subtitle = []
            data_value = \
                remove_trailing_punctuation(data_std.lstrip(), ',.', ':;/-=')
            pararalel_title_str, sep, subtitle_str = data_value.partition(':')
            pararalel_title_str = pararalel_title_str.strip()
            subtitle_str = subtitle_str.strip()
            data_lang_value = ''
            pararalel_title_altgr_str = ''
            subtitle_altgr_str = ''
            main_title.append({'value': pararalel_title_str})
            if lang:
                try:
                    data_lang_value = remove_trailing_punctuation(
                            data_lang_items[index].lstrip(), ',.', ':;/-=')
                except Exception as err:
                    data_lang_value = '[missing data]'
                pararalel_title_altgr_str, sep, subtitle_altgr_str = \
                    data_lang_value.partition(':')
                if pararalel_title_altgr_str:
                    main_title.append({
                        'value': pararalel_title_altgr_str.strip(),
                        'language': lang,
                    })
            pararalel_title_without_article = \
                remove_leading_article(pararalel_title_str)
            if pararalel_title_without_article:
                pararalel_title_string_set.add(pararalel_title_without_article)
            pararalel_title_string_set.add(pararalel_title_str)

            if subtitle_str:
                subtitle.append({'value': subtitle_str})
                if lang and subtitle_altgr_str:
                    subtitle.append({
                        'value': subtitle_altgr_str.strip(),
                        'language': lang,
                    })
            if main_title:
                out_data_dict['mainTitle'] = main_title
            if subtitle:
                out_data_dict['subtitle'] = subtitle
        index += 1
        if out_data_dict:
            parallel_titles.append(out_data_dict)
    return main_subtitle, parallel_titles, pararalel_title_string_set


def build_responsibility_data(responsibility_data):
    """Build the responsibility data form subfield $c of field 245.

    :param responsibility_data: list of responsibility_data
    :return: a list of responsibility
    :rtype: list
    """
    data_std = ''
    data_lang = ''
    lang = ''
    responsibilities = []
    for responsibility_value in responsibility_data:
        value = responsibility_value.get('value', '')
        lang = responsibility_value.get('language', '')
        if lang:
            data_lang = value
        else:
            data_std = value

    data_std_items = data_std.split(';')
    data_lang_items = []
    if data_lang:
        data_lang_items = data_lang.split(';')
    index = 0
    for data_std in data_std_items:
        out_data = []
        data_value = remove_trailing_punctuation(
                        data_std.lstrip(), ',.[]', ':;/-=')
        out_data.append({'value': data_value})
        if lang:
            try:
                data_lang_value = \
                    remove_trailing_punctuation(
                        data_lang_items[index].lstrip(), ',.[]', ':;/-=')
            except Exception as err:
                data_lang_value = '[missing data]'
            out_data.append({'value': data_lang_value, 'language': lang})
        index += 1
        responsibilities.append(out_data)
    return responsibilities
