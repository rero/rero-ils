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
