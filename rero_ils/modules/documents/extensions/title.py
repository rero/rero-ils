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

"""Document record extension to enrich the title."""


from elasticsearch_dsl.utils import AttrDict
from invenio_records.extensions import RecordExtension

from ..utils import display_alternate_graphic_first, title_format_text


class TitleExtension(RecordExtension):
    """Adds textual information for the title."""

    @classmethod
    def format_text(cls, titles, responsabilities=None, with_subtitle=True):
        """Format title head for display purpose.

        :param titles: titles object list
        :type titles: JSON object list
        :param with_subtitle: `True` for including the subtitle in the output
        :type with_subtitle: bool, optional
        :return: a title string formatted for display purpose
        :rtype: str
        """
        head_titles = []
        parallel_titles = []
        for title in titles:
            if isinstance(title, AttrDict):
                # force title to dict because ES gives AttrDict
                title = title.to_dict()
            title = dict(title)
            if title.get('type') == 'bf:Title':
                title_texts = \
                    title_format_text(title=title, with_subtitle=with_subtitle)
                if len(title_texts) == 1:
                    head_titles.append(title_texts[0].get('value'))
                else:
                    languages = [
                        title.get('language') for title in title_texts]

                    def filter_list(value):
                        """Check if a value should be removed from languages.

                        :returns: True if the language type is latin and a
                                  vernacular from exits
                        """
                        # keep simple language such as `default`
                        if '-' not in value:
                            return True
                        lang, _ = value.split('-')
                        # remove the latin form if a vernacular form exists
                        return (
                            not value.endswith('-latn')
                            or sum(v.startswith(f'{lang}-') for v in languages)
                            <= 1
                        )

                    # list of selected language
                    filtered_languages = list(filter(filter_list, languages))

                    for title_text in title_texts:
                        language = title_text.get('language')
                        if language not in filtered_languages:
                            continue
                        if display_alternate_graphic_first(language):
                            head_titles.append(title_text.get('value'))
                    # If I don't have a title available,
                    # I get the last value of the array
                    if not len(head_titles):
                        head_titles.append(title_texts[-1].get('value'))
            elif title.get('type') == 'bf:ParallelTitle':
                parallel_title_texts = title_format_text(
                    title=title, with_subtitle=with_subtitle)
                if len(parallel_title_texts) == 1:
                    parallel_titles.append(
                        parallel_title_texts[0].get('value'))
                else:
                    for parallel_title_text in parallel_title_texts:
                        language = parallel_title_text.get('language')
                        if display_alternate_graphic_first(language):
                            parallel_titles.append(
                                parallel_title_text.get('value')
                            )
        output_value = '. '.join(head_titles)
        for parallel_title in parallel_titles:
            output_value += f' = {str(parallel_title)}'
        responsabilities = responsabilities or []
        for responsibility in responsabilities:
            if len(responsibility) == 1:
                output_value += ' / ' + responsibility[0].get('value')
            else:
                for responsibility_language in responsibility:
                    value = responsibility_language.get('value')
                    language = responsibility_language.get(
                        'language', 'default')
                    if display_alternate_graphic_first(language):
                        output_value += f' / {value}'
        return output_value

    def post_dump(self, record, data, dumper=None):
        """Called before a record is dumped.

        :param record: invenio record - the original record.
        :param data: dict - the data.
        :param dumper: record dumper - dumper helper.
        """
        titles = data.get('title', [])
        bf_titles = list(filter(lambda t: t['type'] == 'bf:Title', titles))
        for title in bf_titles:
            title['_text'] = self.format_text(titles, with_subtitle=True)
