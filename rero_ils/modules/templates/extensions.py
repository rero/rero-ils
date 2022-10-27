# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
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

"""Template record extensions."""
from flask_login import current_user
from invenio_records.extensions import RecordExtension
from jsonschema.exceptions import ValidationError

from rero_ils.modules.users.models import UserRole


class CleanDataDictExtension(RecordExtension):
    """Defines the methods needed by an extension."""

    def post_init(self, record, data, model=None, **kwargs):
        """Called after a record is initialized.

        Remove fields that can have a link to other records in the database.

        :param record: the record to analyze
        :param data: The dict passed to the record's constructor
        :param model: The model class used for initialization.
        """
        fields = ['pid']
        if record.get('template_type') == 'items':
            fields += ['barcode', 'status', 'document', 'holding',
                       'organisation', 'library']

        elif record.get('template_type') == 'holdings':
            fields += ['organisation', 'library', 'document']
        elif record.get('template_type') == 'patrons':
            fields += ['user_id', 'patron.subscriptions', 'patron.barcode']

        for field in fields:
            if '.' in field:
                level_1, level_2 = field.split('.')
                record.get('data', {}).get(level_1, {}).pop(level_2, None)
            else:
                record.get('data', {}).pop(field, None)


class TemplateVisibilityChangesExtension(RecordExtension):
    """Disable template visibility changes depending on connected user."""

    def pre_commit(self, record):
        """Called before a record is committed.

        :param record: the record containing data to validate.
        :raises ValidationError: If an error is detected during the validation
            check. This error could be serialized to get the error message.
        """
        # First, determine if a user is connected. If not, no check must be
        # done about any changes (probably it's a console script/user).
        from rero_ils.modules.patrons.api import current_librarian
        if not current_user:
            return

        # Check if visibility of the template changed. If not, we can stop
        # the validation process.
        original_record = record.db_record() or {}
        if record.get('visibility') == original_record.get('visibility'):
            return

        # Only lib_admin and full_permission roles can change visibility field
        error_message = "You are not allowed to change template visibility"
        allowed_roles = [
            UserRole.FULL_PERMISSIONS,
            UserRole.LIBRARY_ADMINISTRATOR
        ]
        user_roles = set()
        if current_librarian:
            user_roles = set(current_librarian.get('roles'))
        if not user_roles.intersection(allowed_roles):
            raise ValidationError(error_message)
