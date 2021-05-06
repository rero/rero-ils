# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""Blueprint used for loading templates."""

from __future__ import absolute_import, print_function

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_babelex import gettext as _

from .api import ILLRequest
from .forms import ILLRequestForm
from .models import ILLRequestStatus
from .utils import get_pickup_location_options
from ..decorators import check_logged_as_patron
from ..locations.api import Location
from ..patrons.api import current_patrons
from ..utils import extracted_data_from_ref, get_ref_for_pid
from ...permissions import check_user_is_authenticated

blueprint = Blueprint(
    'ill_requests',
    __name__,
    url_prefix='/ill_requests',
    template_folder='templates',
    static_folder='static',
)


@blueprint.route('/create/', methods=['GET', 'POST'])
@check_user_is_authenticated(redirect_to='security.login')
@check_logged_as_patron
def ill_request_form():
    """Return professional view."""
    form = ILLRequestForm(request.form)
    # pickup locations selection are based on app context then the choices
    # can't be "calculated" on the form creation (context free).
    form.pickup_location.choices = list(get_pickup_location_options())

    if request.method == 'POST' and form.validate_on_submit():
        ill_request_data = form.get_data()
        # get the pickup location pid
        loc_pid = extracted_data_from_ref(
            ill_request_data['pickup_location'])

        # get the patron account of the same org of the location pid
        def get_patron(location_pid):
            loc = Location.get_record_by_pid(loc_pid)
            for ptrn in current_patrons:
                if ptrn.organisation_pid == loc.organisation_pid:
                    return ptrn

        ill_request_data['patron'] = {
            '$ref': get_ref_for_pid('patrons', get_patron(loc_pid).pid)
        }
        ill_request_data['status'] = ILLRequestStatus.PENDING
        ILLRequest.create(ill_request_data, dbcommit=True, reindex=True)
        flash(
            _('The request has been transmitted to your library.'),
            'success'
        )
        return redirect(url_for('patrons.profile', tab='ill_request'))

    return render_template('rero_ils/ill_request_form.html', form=form)
