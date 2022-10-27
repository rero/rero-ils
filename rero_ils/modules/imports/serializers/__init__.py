# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

"""Import serialization."""

from rero_ils.modules.serializers import search_responsify

from .response import record_responsify
from .serializers import ImportSchemaJSONV1, ImportsMarcSearchSerializer, \
    ImportsSearchSerializer, UIImportsSearchSerializer


def json_record_serializer_factory(import_class, serializer_type='record'):
    """JSON record factory.

    create json serializer for the given import class.
    :param import_class: import class
    :param serializer_type: type of serializer (record, uirecord)
    :return: Records-REST response serializer
    """
    if serializer_type == 'record':
        return record_responsify(
            ImportsSearchSerializer(
                ImportSchemaJSONV1,
                record_processor=import_class.to_json_processor),
            'application/json'
        )
    if serializer_type == 'uirecord':
        return record_responsify(
            UIImportsSearchSerializer(
                ImportSchemaJSONV1,
                record_processor=import_class.to_json_processor),
            'application/rero+json'
        )


json_v1_search = ImportsSearchSerializer(ImportSchemaJSONV1)
json_v1_uisearch = UIImportsSearchSerializer(ImportSchemaJSONV1)
json_v1_record_marc = ImportsMarcSearchSerializer(ImportSchemaJSONV1)

json_v1_import_search = search_responsify(json_v1_search,
                                          'application/json')
json_v1_import_uisearch = search_responsify(json_v1_uisearch,
                                            'application/rero+json')
json_v1_import_record_marc = record_responsify(json_v1_record_marc,
                                               'application/json+marc')
