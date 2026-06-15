# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""RERO ILS common record extensions."""

from invenio_records.extensions import RecordExtension

from .locations.api import Location, LocationsSearch
from .utils import extracted_data_from_ref, get_base_url


def _add_org_and_lib(record):
    """Build $ref for the organisation and library of the item.

    :param record: the record metadata.
    """
    location_pid = extracted_data_from_ref(record.get("location"))
    # try on the search index location index
    try:
        search_loc = next(LocationsSearch().filter("term", pid=location_pid).source(["organisation", "library"]).scan())
        organisation_pid = search_loc.organisation.pid
        library_pid = search_loc.library.pid
    except StopIteration:
        # ok go to the db
        library = Location.get_record_by_pid(location_pid).get_library()
        library_pid = library.pid
        organisation_pid = library.organisation_pid
    base_url = get_base_url()
    record["organisation"] = {"$ref": f"{base_url}/api/organisations/{organisation_pid}"}
    record["library"] = {"$ref": f"{base_url}/api/libraries/{library_pid}"}


class OrgLibRecordExtension(RecordExtension):
    """Defines the methods needed by an extension."""

    def pre_create(self, record):
        """Called before a record is created.

        :param record: the record metadata.
        """
        # do nothing if already exists
        if record.get("organisation") and record.get("library"):
            return
        _add_org_and_lib(record)
        # required for validation
        if record.model:
            record.model.data = record

    def pre_commit(self, record):
        """Called before a record is committed.

        :param record: the record metadata.
        """
        _add_org_and_lib(record)
