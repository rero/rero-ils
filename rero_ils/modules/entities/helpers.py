# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

"""Helpers for entities."""
from rero_ils.modules.commons.exceptions import RecordNotFound
from rero_ils.modules.entities.local_entities.api import LocalEntity
from rero_ils.modules.entities.remote_entities.api import RemoteEntity
from rero_ils.modules.utils import extracted_data_from_ref


def str_builder(field_values, prefix='', suffix='', delimiter=''):
    """String builder method.

    This builder is used to format string depending on given arguments
    First, it joins all values with the delimiter and add a prefix or suffix.

    :param field_values: values to format.
    :type field_values: str or an array of str
    :param prefix: value to add before field_values.
    :type prefix: str
    :param suffix: value to add after field_values.
    :type suffix: str
    :param delimiter: delimiter used to concatenate multiple field_values.
    :type field_values: str
    :return: formatted string or an empty string.
    :rtype: str
    """
    if not isinstance(field_values, list):
        field_values = [field_values]

    # DEV NOTES:
    #  We use any() instead bool() because we can have a list of empty string.
    #  => see OrganisationLocalEntity subclass
    #  If all values in list are empty we don't want to process field.
    #  Ex:
    #    any(field_values['','']) == False
    #    bool(field_values['','']) == True
    if any(field_values):
        return f'{prefix}{delimiter.join(field_values)}{suffix}'
    return ''


def get_entity_record_from_data(data):
    """Retrieve entity record from data.

    # todo: Add comments
    """
    # try to get entity record
    if pid := data.get('pid'):
        # remote entities have a pid in data
        if entity := RemoteEntity.get_record_by_pid(pid):
            return entity
        raise RecordNotFound(RemoteEntity, data.get('pid'))
    if ref := data.get('$ref'):
        entity = extracted_data_from_ref(ref, 'record')
        # check if local entity
        if entity and isinstance(entity, LocalEntity):
            return entity
