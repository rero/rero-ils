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

"""Blueprint used for loading templates."""

from __future__ import absolute_import, print_function

from .dojson.contrib.marc21tojson.model import remove_trailing_punctuation


def localized_data_name(data, language):
    """Get localized name."""
    return data.get(
        'name_{language}'.format(language=language),
        data.get('name', '')
    )


def clean_text(data):
    """Delete all _text from data."""
    if isinstance(data, list):
        new_val = []
        for val in data:
            new_val.append(clean_text(val))
        data = new_val
    elif isinstance(data, dict):
        if '_text' in data:
            del data['_text']
        new_data = {}
        for key, val in data.items():
            new_data[key] = clean_text(val)
        data = new_data
    return data


def publication_statement_text(provision_activity):
    """Create publication statement from place, agent and date values."""
    punctuation = {
        'bf:Place': ' ; ',
        'bf:Agent': ', '
    }

    statement_with_language = {'default': ''}
    statement_type = None

    for statement in provision_activity['statement']:
        labels = statement['label']

        for label in labels:
            language = label.get('language', 'default')

            if not statement_with_language.get(language):
                statement_with_language[language] = ''

            if statement_with_language[language]:
                if statement_type == statement['type']:
                    statement_with_language[language] += punctuation[
                        statement_type
                    ]
                else:
                    if statement['type'] == 'bf:Place':
                        statement_with_language[language] += ' ; '
                    elif statement['type'] == 'Date':
                        statement_with_language[language] += ', '
                    else:
                        statement_with_language[language] += ' : '

            statement_with_language[language] += label['value']
        statement_type = statement['type']

    # date field: remove ';' and append
    for key, value in statement_with_language.items():
        value = remove_trailing_punctuation(value)
        statement_with_language[key] = value
    return statement_with_language


def series_format_text(serie):
    """Format series for template."""
    output = []
    if serie.get('name'):
        output.append(serie.get('name'))
    if serie.get('number'):
        output.append(', ' + serie.get('number'))
    return ''.join(str(x) for x in output)


def edition_format_text(edition):
    """Format edition for _text."""
    edition_with_language = {'default': ''}
    designations = edition.get('editionDesignation', [])
    responsibilities = edition.get('responsibility', [])
    designation_output = {}
    for designation in designations:
        language = designation.get('language', 'default')
        value = designation.get('value', '')
        designation_output[language] = value
    responsibility_output = {}
    for responsibility in responsibilities:
        language = responsibility.get('language', 'default')
        value = responsibility.get('value', '')
        responsibility_output[language] = value

    for key, value in designation_output.items():
        output_value = remove_trailing_punctuation(
            '{designation} / {responsibility}'.format(
                designation=value,
                responsibility=responsibility_output.get(key, ''),
            )
        )
        edition_with_language[key] = output_value

    return edition_with_language
