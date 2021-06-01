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

"""Shared extensions about RERO-ILS resources."""

from elasticsearch_dsl import Q
from invenio_records.extensions import RecordExtension
from jsonschema import ValidationError


class UniqueFieldsExtension(RecordExtension):
    """Extension to check the uniqueness of fields value.

    CONCEPT:
        For some resources, we would to ensure that some values are unique.
        By example, two libraries can't have the same name into the same
        organisation.

        To allow to check, we will check into an ElasticSearch index based
        on some fields define into extension configuration.

    USAGE:
        Into the resource class, add this extension into the `_extensions`
        class attribute. This extension require 2 parameters :
          * a list of tuple. Each tuple could provide 2 data :
            - the record attribute to check (required).
            - the corresponding field into ES index (optional).
            if no ES field is provided, the same key should be used to search
            into ES.
          * the search class allowing to search into the ES index.

    EXAMPLE:
        _extensions = UniqueFieldsExtension(
          [('name',), ('number', 'number_sort')],
          IlsRecordsSearchChildClass
        )

    NOTE FOR DEVELOPERS:
        Avoid to use search on ES `text` analyzed field. It will generate
        strange result (see https://www.elastic.co/guide/en/elasticsearch/
        reference/current/query-dsl-term-query.html#avoid-term-query-text-
        fields). Use a ES `keyword` analyzed field.
    """

    def __init__(self, fields, record_search_class):
        """Class initialization.

        :param fields: the list of fields to check.
        :param record_search_class: the record search class to search.
        """
        self.fields = []
        for field_tuple in fields or []:
            if len(field_tuple) == 1:
                field_tuple = (field_tuple[0], field_tuple[0])
            self.fields.append(field_tuple)
        self.search_class = record_search_class

    def _check_fields(self, record):
        """Check fields uniqueness.

        For each fields, check if this field is present into the record. If it
        is present, the value cannot already taken (for this organisation).

        :param record: the record to check.
        """
        attrs_to_check = [attr for attr, _ in self.fields if attr in record]
        if not attrs_to_check:
            # None attributes to check exists into the record.
            # Nothing to check, just return
            return

        # Create an `OR` query with all fields to check and exclude the current
        # record from the result. If one hit matches, raise a ValidationError,
        # otherwise, all should be fine. Enjoy !
        terms = []
        for attr, es_field in self.fields:  # each tuple field are unpacked
            if attr in record:
                terms.append(Q('term', **{es_field: record[attr]}))

        es_query = self.search_class()\
            .query('bool', should=terms, minimum_should_match=1)\
            .exclude('term', pid=record.pid)\
            .source().scan()

        _exhausted = object()
        matching_hit = next(es_query, _exhausted)
        if matching_hit != _exhausted:
            pid = matching_hit.pid
            field_keys = ' and/or '.join(attrs_to_check)
            msg = f'{field_keys} value(s) already taken by pid={pid}'
            raise ValidationError(msg)

    pre_commit = _check_fields
    pre_create = _check_fields
