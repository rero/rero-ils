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

"""Document record extension to enrich the provision activity."""


from invenio_records.extensions import RecordExtension

from rero_ils.dojson.utils import remove_trailing_punctuation
from rero_ils.modules.entities.models import EntityType

from ..utils import display_alternate_graphic_first


class ProvisionActivitiesExtension(RecordExtension):
    """Adds textual information for ProvisionActivities."""

    @classmethod
    def format_text(cls, provision_activity):
        """Create publication statement from place, agent and date values.

        :param provision_activity: dict - a provision activity document field.
        :returns: a text representation of the input dictionary
        :rtype: string
        """
        punctuation = {
            EntityType.PLACE: ' ; ',
            EntityType.AGENT: ' ; ',
            'Date': ', '
        }
        statement_with_language = {'default': ''}
        last_statement_type = None
        # Perform each statement entries to build the best possible string
        for statement in provision_activity.get('statement', []):
            for label in statement['label']:
                language = label.get('language', 'default')
                statement_with_language.setdefault(language, '')
                if statement_with_language[language]:
                    if last_statement_type == statement['type']:
                        statement_with_language[language] += punctuation[
                            last_statement_type
                        ]
                    elif statement['type'] == EntityType.PLACE:
                        statement_with_language[language] += ' ; '
                    elif statement['type'] == 'Date':
                        statement_with_language[language] += ', '
                    else:
                        statement_with_language[language] += ' : '

                statement_with_language[language] += label['value']
            last_statement_type = statement['type']
        # date field: remove ';' and append
        statement_text = []
        for key, value in statement_with_language.items():
            value = remove_trailing_punctuation(value)
            if display_alternate_graphic_first(key):
                statement_text.insert(0, {'value': value, 'language': key})
            else:
                statement_text.append({'value': value, 'language': key})
        return statement_text

    def post_dump(self, record, data, dumper=None):
        """Called before a record is dumped.

        :param record: invenio record - the original record.
        :param data: dict - the data.
        :param dumper: record dumper - dumper helper.
        """
        for provision_activity in data.get('provisionActivity', []):
            if pub_state_text := self.format_text(
                    provision_activity):
                provision_activity['_text'] = pub_state_text
