# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Blueprint used for loading templates."""

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_babel import lazy_gettext as _

from rero_ils.modules.documents.api import Document
from rero_ils.modules.documents.views import create_title_text

from ...permissions import check_user_is_authenticated
from ..commons.identifiers import IdentifierType
from ..decorators import check_logged_as_patron
from ..locations.api import Location
from ..patrons.api import current_patrons
from ..utils import extracted_data_from_ref, get_ref_for_pid
from .api import ILLRequest
from .forms import ILLRequestForm
from .models import ILLRequestStatus
from .utils import (
    get_document_identifiers,
    get_pickup_location_options,
    get_production_activity,
    get_production_activity_statement,
)

blueprint = Blueprint(
    "ill_requests",
    __name__,
    url_prefix="/<string:viewcode>",
    template_folder="templates",
)


@blueprint.route("/ill_requests/new", methods=["GET", "POST"])
@check_user_is_authenticated(redirect_to="security.login")
@check_logged_as_patron
def ill_request_form(viewcode):
    """Return professional view."""
    form = ILLRequestForm(request.form)
    # pickup locations selection are based on app context then the choices
    # can't be "calculated" on the form creation (context free).
    form.pickup_location.choices = [
        *form.pickup_location.choices,
        *sorted(get_pickup_location_options(), key=lambda pickup: pickup[1]),
    ]

    # Extraction of the pids organizations from the connected patron
    org_pids = ",".join([patron.organisation_pid for patron in current_patrons])

    # Populate data only if we are on the global view
    # and that the function is allowed in the configuration
    if (
        request.method == "GET"
        and "record_pid" in request.args
        and current_app.config.get("RERO_ILS_ILL_REQUEST_ON_GLOBAL_VIEW")
        and viewcode == current_app.config.get("RERO_ILS_SEARCH_GLOBAL_VIEW_CODE")
    ):
        _populate_document_data_form(request.args["record_pid"], form)

    if request.method == "POST" and form.validate_on_submit():
        ill_request_data = form.get_data()
        # get the pickup location pid
        loc_pid = extracted_data_from_ref(ill_request_data["pickup_location"])

        # get the patron account of the same org of the location pid
        def get_patron(loc_pid):
            loc = Location.get_record_by_pid(loc_pid)
            for ptrn in current_patrons:
                if ptrn.organisation_pid == loc.organisation_pid:
                    return ptrn
            return None

        ill_request_data["patron"] = {"$ref": get_ref_for_pid("patrons", get_patron(loc_pid).pid)}
        ill_request_data["status"] = ILLRequestStatus.PENDING
        ILLRequest.create(ill_request_data, dbcommit=True, reindex=True)
        flash(_("The request has been transmitted to your library."), "success")
        return redirect(url_for("patrons.profile", viewcode=viewcode, org_pids=org_pids))

    return render_template(
        "rero_ils/ill_request_form.html",
        form=form,
        viewcode=viewcode,
        org_pids=org_pids,
    )


def _populate_document_data_form(doc_pid, form):
    """Populate document data in the form.

    :param: doc_pid: Document PID.
    :param: form: The ill form.
    """
    doc = Document.get_record_by_pid(doc_pid)
    if not doc:
        return
    # Document title
    form.document.title.data = create_title_text(doc.get("title"))
    # Document authors (only first three)
    statements = doc.get("responsibilityStatement", [])
    authors = []
    for statement in statements:
        authors.extend(author.get("value") for author in statement)
    if authors:
        form.document.authors.data = "; ".join(authors[:3])
    # Document publisher and year
    if production_activity := next(get_production_activity(doc, ["bf:Publication"]), None):
        # Document date
        if date := production_activity.get("startDate"):
            form.document.year.data = date
        # Document publisher
        if statement := next(
            get_production_activity_statement(production_activity, ["bf:Agent"]),
            None,
        ):
            if label := statement.get("label"):
                form.document.publisher.data = label[0].get("value")
    # Document identifier
    types = [
        IdentifierType.ISBN,
        IdentifierType.EAN,
        IdentifierType.ISSN,
        IdentifierType.L_ISSN,
    ]
    if identifier := next(get_document_identifiers(doc, types), None):
        identifier_type = _(identifier.get("type"))
        value = identifier.get("value")
        form.document.identifier.data = f"{value} ({identifier_type})"
    # Document source
    form.source.origin.data = current_app.config.get("RERO_ILS_ILL_DEFAULT_SOURCE")
    form.source.url.data = url_for(
        "invenio_records_ui.doc",
        viewcode=current_app.config.get("RERO_ILS_SEARCH_GLOBAL_VIEW_CODE"),
        pid_value=doc_pid,
        _external=True,
    )
