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

"""Marshmallow schema for JSON representation of `Template` resources."""
from functools import partial

from flask_babel import gettext as _
from invenio_records_rest.schemas import StrictKeysMixin
from invenio_records_rest.schemas.fields import GenFunction, SanitizedUnicode
from marshmallow import ValidationError, fields, validates, validates_schema
from marshmallow.validate import OneOf

from rero_ils.modules.commons.schemas import RefSchema, http_applicable_method
from rero_ils.modules.patrons.api import current_librarian
from rero_ils.modules.serializers.base import schema_from_context
from rero_ils.modules.users.models import UserRole

from ..api import Template
from ..models import TemplateVisibility

schema_from_template = partial(schema_from_context, schema=Template.schema)


class TemplateMetadataSchemaV1(StrictKeysMixin):
    """Marshmallow schema for the `Template` metadata."""

    pid = SanitizedUnicode()
    template_type = SanitizedUnicode(required=True)
    name = SanitizedUnicode(required=True)
    description = SanitizedUnicode()
    visibility = SanitizedUnicode(
        required=True,
        validate=OneOf([TemplateVisibility.PUBLIC, TemplateVisibility.PRIVATE])
    )
    data = fields.Dict()
    creator = fields.Nested(RefSchema)
    organisation = fields.Nested(RefSchema)
    schema = GenFunction(
        load_only=True,
        attribute="$schema",
        data_key="$schema",
        deserialize=schema_from_template
    )

    # DEV NOTES : Why using marshmallow validation process
    #   We use marshmallow validation decorators to restrict some changes on
    #   record fields instead of using permissions workflow. We use this
    #   procedure to allow custom error message transmission ; permissions
    #   procedure only send an HTTP 403 status, without any message, this isn't
    #   enough relevant for end user.

    @validates('visibility')
    @http_applicable_method('POST')
    def validate_visibility(self, data, **kwargs):
        """Validate the visibility field through REST API request.

        Through the API, a template could only be created with `private`
        visibility. To set a template in `public` visibility, an authorized
        user must update an existing template.

        :param data: the visibility field value.
        :param kwargs: any additional named arguments.
        :raises ValidationError: if error has detected on visibility attribute
        """
        if data == TemplateVisibility.PUBLIC:
            raise ValidationError(
                _('Template can be created only with `private` visibility')
            )

    @validates_schema()
    @http_applicable_method('PUT')
    def validate_visibility_changes(self, data, **kwargs):
        """Validate `visibility` changes through REST API request.

        Updates on `visibility` attribute is subject to restriction depending
        on current connected user ; only FULL_PERMISSIONS and
        LIBRARY_ADMINISTRATOR users could change `visibility` attribute.

        :param data: the json data to validate.
        :param kwargs: additional named arguments.
        :raises ValidationError: if error has detected on visibility attribute
        """
        # Load DB record
        db_record = Template.get_record_by_pid(data.get('pid'))
        if not db_record:
            raise ValidationError(f'Unable to load Template#{data.get("pid")}')

        # Check if visibility of the template changed. If not, we can stop
        # the validation process.
        if db_record.get('visibility') == data.get('visibility'):
            return

        # Only lib_admin and full_permission roles can change visibility field
        allowed_roles = [
            UserRole.FULL_PERMISSIONS,
            UserRole.LIBRARY_ADMINISTRATOR
        ]
        user_roles = set()
        if current_librarian:
            user_roles = set(current_librarian.get('roles', []))
        if not user_roles.intersection(allowed_roles):
            raise ValidationError(
                _('You are not allowed to change template visibility')
            )
