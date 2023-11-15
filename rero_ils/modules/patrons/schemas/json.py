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

"""Marshmallow schema for JSON representation of `Patron` resources."""
from functools import partial

from flask import abort
from flask_login import current_user
from invenio_records_rest.schemas import StrictKeysMixin
from invenio_records_rest.schemas.fields import GenFunction, SanitizedUnicode
from marshmallow import Schema, fields, pre_load, validates, validates_schema
from marshmallow.validate import OneOf

from rero_ils.modules.commons.models import NoteTypes
from rero_ils.modules.commons.schemas import NoteSchema, RefSchema, \
    http_applicable_method
from rero_ils.modules.serializers.base import schema_from_context
from rero_ils.modules.users.api import User
from rero_ils.modules.users.models import UserRole

from ..api import Patron
from ..utils import validate_role_changes

schema_from_template = partial(schema_from_context, schema=Patron.schema)


class PatronAddressSchema(Schema):
    """Marshmallow schema for patron address."""

    street = SanitizedUnicode()
    postal_code = SanitizedUnicode()
    city = SanitizedUnicode()
    country = SanitizedUnicode()


class PatronNoteSchema(NoteSchema):
    """Marshmallow schema for `notes` on Patron."""

    ttype = SanitizedUnicode(
        validate=OneOf([NoteTypes.PUBLIC_NOTE, NoteTypes.STAFF_NOTE])
    )


class PatronMetadataSchemaV1(StrictKeysMixin):
    """Marshmallow schema for the `Template` metadata."""

    pid = SanitizedUnicode()
    schema = GenFunction(
        load_only=True,
        attribute='$schema',
        data_key='$schema',
        deserialize=schema_from_template
    )
    source = SanitizedUnicode()
    local_codes = fields.List(SanitizedUnicode())
    user_id = fields.Integer()
    second_address = fields.Nested(PatronAddressSchema())
    patron = fields.Dict()  # TODO : stricter implementation
    libraries = fields.Nested(RefSchema, many=True)
    roles = fields.List(SanitizedUnicode(validate=OneOf(UserRole.ALL_ROLES)))
    notes = fields.Nested(PatronNoteSchema, many=True)

    @pre_load
    def remove_user_data(self, data, many, **kwargs):
        """Removed data concerning User not Patron.

        :param data: the data received from request.
        :param many: is the `data` represent an array of schema object.
        :param kwargs: any additional named arguments.
        :return Data cleared from user profile information.
        """
        data = data if many else [data]
        profile_fields = set(
            User.profile_fields + ['username', 'email',  'password'])
        for record in data:
            for field in profile_fields:
                record.pop(field, None)
        return data if many else data[0]

    @validates('roles')
    @http_applicable_method('POST')
    def validate_role(self, data, **kwargs):
        """Validate `roles` attribute through API request.

        The `roles` attribute must be controlled to restrict some role
        attribution/modification depending on the current logged user.

        :param data: the `roles` attribute value.
        :param kwargs: any additional named arguments.
        :raises ValidationError: if error has detected on `roles` attribute
        """
        validate_role_changes(current_user, set(data))

    @validates_schema
    @http_applicable_method('PUT')
    def validate_roles_changes(self, data, **kwargs):
        """Validate `roles` changes through REST API request.

        Updates on `roles` attribute is subject to restriction depending
        on current connected user. Determine if `roles` field changes and if
        these changes are allowed or not.

        :param data: the json data to validate.
        :param kwargs: additional named arguments.
        :raises abort: if corresponding record is not found.
        :raises ValidationError: if error has detected on role field
        """
        # Load DB record
        db_record = Patron.get_record_by_pid(data.get('pid'))
        if not db_record:
            abort(404)

        # Check if `roles` of the patron changed. If not, we can stop
        # the validation process.
        original_roles = set(db_record.get('roles', []))
        data_roles = set(data.get('roles', []))
        role_changes = original_roles.symmetric_difference(data_roles)
        if not role_changes:
            return

        # `roles` field changes, we need to validate this change.
        validate_role_changes(current_user, role_changes)
