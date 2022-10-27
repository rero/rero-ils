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

"""Admin views for selfcheck user."""

from flask_admin.contrib.sqla import ModelView
from flask_admin.form.fields import DateTimeField
from flask_babelex import gettext as _
from werkzeug.local import LocalProxy
from wtforms.fields import SelectField
from wtforms.validators import DataRequired

from .models import SelfcheckTerminal
from ..locations.api import search_location_by_pid, search_locations_by_pid
from ..organisations.api import Organisation


class SelfcheckTerminalView(ModelView):
    """Flask-Admin view to manage selfcheck terminals."""

    can_view_details = True
    can_create = True
    can_delete = True

    list_all = (
        'id', 'name', 'access_token', 'organisation_pid', 'library_pid',
        'location_pid', 'active', 'last_login_at', 'last_login_ip',
    )

    column_list = \
        column_searchable_list = \
        column_sortable_list = \
        column_details_list = \
        list_all

    form_columns = ('name', 'access_token', 'location_pid', 'active')

    form_args = dict(
        name=dict(label='Name', validators=[DataRequired()]),
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

    column_filters = ('id', 'name', 'active', 'organisation_pid',
                      'library_pid', 'location_pid', 'last_login_at')

    column_default_sort = ('last_login_at', True)

    form_overrides = {
        'location_pid': SelectField,
        'last_login_at': DateTimeField
    }

    def on_model_change(self, form, model, is_created):
        """Fill organisation_pid when saving.

        :param form:
            Form used to create/update model
        :param model:
            Model that was created/updated
        :param is_created:
            True if model was created, False if model was updated
        """
        location_pid = form.location_pid.data
        location = search_location_by_pid(location_pid)
        model.organisation_pid = location.organisation['pid']
        model.library_pid = location.library['pid']


def locations_form_options():
    """Get locations form options."""
    location_opts = []
    for org in Organisation.get_all():
        search = search_locations_by_pid(organisation_pid=org.pid,
                                         sort_by_field='code',
                                         preserve_order=True)
        search = search.exclude('term', is_online=True)
        for location in search.scan():
            location_opts.append({
                'location_pid': location.pid,
                'location_name': '{org} - {loc_code} ({loc_name})'.format(
                    org=org.get('name'),
                    loc_code=location.code,
                    loc_name=location.name
                )
            })
    return location_opts


selfcheck_terminal_adminview = {
    'model': SelfcheckTerminal,
    'modelview': SelfcheckTerminalView,
    'category': _('Selfcheck Terminal Management'),
}

__all__ = (
    'selfcheck_terminal_adminview',
    'SelfcheckTerminalView'
)
