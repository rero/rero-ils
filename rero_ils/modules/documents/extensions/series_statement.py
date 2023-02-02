# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
# Copyright (C) 2021 UCLouvain
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

"""Document record extension to enrich the series statement."""


from invenio_records.extensions import RecordExtension

from ..utils import display_alternate_graphic_first


class SeriesStatementExtension(RecordExtension):
    """Adds textual information for seriesStatement."""

    @classmethod
    def format_text(cls, serie_statement):
        """Format series statement for template."""
        def get_title_language(data):
            """Get title and language."""
            output = {}
            for value in data:
                language = value.get('language', 'default')
                title = value.get('value', '')
                language_title = output.get(language, [])
                language_title.append(title)
                output[language] = language_title
            return output

        serie_title = get_title_language(
            serie_statement.get('seriesTitle', []))
        serie_enum = get_title_language(
            serie_statement.get('seriesEnumeration', [])
        )
        subserie_data = []
        for subserie in serie_statement.get('subseriesStatement', []):
            subserie_title = get_title_language(
                subserie.get('subseriesTitle', []))
            subserie_enum = get_title_language(
                subserie.get('subseriesEnumeration', [])
            )
            subserie_data.append({
                'title': subserie_title, 'enum': subserie_enum})

        intermediate_output = {}
        for key, value in serie_title.items():
            intermediate_output[key] = ', '.join(value)
        for key, value in serie_enum.items():
            value = ', '.join(value)
            intermediate_value = intermediate_output.get(key, '')
            intermediate_value = f'{intermediate_value}; {value}'
            intermediate_output[key] = intermediate_value
        for intermediate_subserie in subserie_data:
            for key, value in intermediate_subserie.get('title', {}).items():
                value = ', '.join(value)
                intermediate_value = intermediate_output.get(key, '')
                intermediate_value = f'{intermediate_value}. {value}'
                intermediate_output[key] = intermediate_value
            for key, value in subserie_enum.items():
                value = ', '.join(value)
                intermediate_value = intermediate_output.get(key, '')
                intermediate_value = f'{intermediate_value}; {value}'
                intermediate_output[key] = intermediate_value

        serie_statement_text = []
        for key, value in intermediate_output.items():
            if display_alternate_graphic_first(key):
                serie_statement_text.insert(
                    0, {'value': value, 'language': key})
            else:
                serie_statement_text.append({'value': value, 'language': key})

        return serie_statement_text

    def post_dump(self, record, data, dumper=None):
        """Called before a record is dumped.

        :param record: invenio record - the original record.
        :param data: dict - the data.
        :param dumper: record dumper - dumper helper.
        """
        series = data.get('seriesStatement', [])
        for series_element in series:
            series_element["_text"] = self.format_text(
                series_element
            )
