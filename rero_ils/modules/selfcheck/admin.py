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

"""Admin views for selfcheck user."""

from flask_admin.contrib.sqla import ModelView
from flask_admin.form.fields import DateTimeField
from flask_babelex import gettext as _
from werkzeug.local import LocalProxy
from wtforms.fields import SelectField
from wtforms.validators import DataRequired

from .models import SelfcheckUser
from ..locations.api import get_organisation_pid_by_location_pid, \
    search_locations_by_pid
from ..organisations.api import Organisation


class SelfcheckUserView(ModelView):
    """Flask-Admin view to manage selfcheck user accounts."""

    can_view_details = True
    can_create = True
    can_delete = True

    list_all = (
        'id', 'username', 'access_token', 'organisation_pid', 'location_pid',
        'active', 'last_login_at',
    )

    column_list = \
        column_searchable_list = \
        column_sortable_list = \
        column_details_list = \
        list_all

    form_columns = ('username', 'access_token', 'location_pid', 'active',
                    'roles')

    form_args = dict(
        username=dict(label='Username', validators=[DataRequired()]),
        access_token=dict(label='Access token', validators=[DataRequired()]),
        location_pid=dict(
            label='Location',
            validators=[DataRequired()],
            choices=LocalProxy(lambda: [
                (opts.get('location_pid'), opts.get('location_name')) for opts
                in locations_form_options()
            ]),
        ),
    )

    column_filters = ('id', 'username', 'active', 'organisation_pid',
                      'location_pid', 'last_login_at')

    column_default_sort = ('last_login_at', True)

    form_overrides = {
        'location_pid': SelectField,
        'last_login_at': DateTimeField
    }

    def on_model_change(self, form, model, is_created):
        """Fill organisation_pid when saving."""
        location_pid = form.location_pid.data
        org_pid = get_organisation_pid_by_location_pid(location_pid)
        model.organisation_pid = org_pid


def locations_form_options():
    """Get locations form options."""
    location_opts = []
    for org in Organisation.get_all():
        search = search_locations_by_pid(organisation_pid=org.pid)
        for location in search.scan():
            location_opts.append({
                'organisation_pid': org.pid,
                'organisation_name': org.get('name'),
                'location_pid': location.pid,
                'location_name': '{organisation} : {location}'.format(
                    organisation=org.get('name'),
                    location=location.name
                )
            })
    return location_opts


selfcheck_user_adminview = {
    'model': SelfcheckUser,
    'modelview': SelfcheckUserView,
    'category': _('Selfcheck User Management'),
}

__all__ = (
    'selfcheck_user_adminview',
    'SelfcheckUserView'
)
