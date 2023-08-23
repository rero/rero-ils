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

"""Item utils."""
from datetime import datetime, timedelta, timezone

from rero_ils.modules.items.models import ItemIssueStatus, ItemStatus, \
    TypeOfItem
from rero_ils.modules.locations.api import LocationsSearch
from rero_ils.modules.notifications.models import RecipientType
from rero_ils.modules.patron_transactions.api import PatronTransactionsSearch
from rero_ils.modules.patrons.api import current_librarian


def item_pid_to_object(item_pid):
    """Build an item_pid object from a given item pid.

    :param item_pid: the item pid value
    :return: the item_pid object
    :rtype: object
    """
    return {'value': item_pid, 'type': 'item'}


def item_location_retriever(item_pid):
    """Returns the item shelflocation pid for the given item_pid.

    :param item_pid: the item_pid object
    :type item_pid: object
    :return: the location pid of the item
    :rtype: str
    """
    from .api import Item

    # TODO: for requests we probably need the transation_location_pid
    #       to deal with multiple pickup locations for a library
    item = Item.get_record_by_pid(item_pid.get('value'))
    if item:
        # TODO: this will be useful for the very specific rero use cases

        # last_location = item.get_last_location()
        # if last_location:
        #     return last_location.pid
        return item.get_owning_pickup_location_pid()


def same_location_validator(item_pid, input_location_pid):
    """Validate that item and transaction location are in same library.

    :param item_pid: the item_pid object
    :type input_location_pid: object
    :return: true if in same library otherwise false
    :rtype: boolean
    """
    from rero_ils.modules.items.api import ItemsSearch
    lib_from_loc = LocationsSearch().get_record_by_pid(
        input_location_pid).library.pid
    lib_from_item = ItemsSearch().get_record_by_pid(
        item_pid.get('value')).library.pid
    return lib_from_loc == lib_from_item


def exists_available_item(items=None):
    """Check if at least one item of the list are available.

    Caution: `items` param couldn't be a generator otherwise the
    :param items: the items to check. Either as a list of item pids, either as
                  a list of item resources.
    :return True if one item is available; false otherwise.
    """
    from rero_ils.modules.items.api import Item
    items = items or []
    for item in items:
        if isinstance(item, str):  # `item` seems to be an item pid
            item = Item.get_record_by_pid(item)
        if not isinstance(item, Item):
            raise ValueError('All items should be Item resource.')
        if item.is_available():
            return True
    return False


def get_provisional_items_candidate_to_delete():
    """Returns checked-in provisional items pids.

    Returns list of candidate provisional items pids to delete, based on the
    status of the item. Filtering by the status `ItemStatus.ON_SHELF` removes
    items with active loans. in addition, remove items with active fees.
    :return an item pid generator.
    """
    from rero_ils.modules.items.api import Item, ItemsSearch

    # query ES index for open fees
    query_fees = PatronTransactionsSearch()\
        .filter('term', status='open')\
        .filter('exists', field='item')\
        .filter('range', total_amount={'gt': 0})\
        .source('item')
    # list of item pids with open fees
    item_pids_with_fees = [hit.item.pid for hit in query_fees.scan()]
    query = ItemsSearch()\
        .filter('term', type=TypeOfItem.PROVISIONAL) \
        .filter('terms', status=[ItemStatus.ON_SHELF]) \
        .exclude('terms', pid=item_pids_with_fees)\
        .source(False)
    for hit in query.scan():
        yield Item.get_record(hit.meta.id)


def update_late_expected_issue(dbcommit=False, reindex=False):
    """Update status of issues with a passed `expected_date` to late status.

    :param reindex: reindex record by record.
    :param dbcommit: commit record to database.
    :return: the number of updated issues.
    """
    from rero_ils.modules.items.api import Item, ItemsSearch

    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    yesterday = yesterday.strftime('%Y-%m-%d')
    query = ItemsSearch() \
        .filter('term', type=TypeOfItem.ISSUE) \
        .filter('term', issue__status=ItemIssueStatus.EXPECTED) \
        .filter('range', issue__expected_date={'lte': yesterday}) \
        .source(False)
    counter = 0
    for counter, hit in enumerate(query.scan(), 1):
        item = Item.get_record(hit.meta.id)
        item.issue_status = ItemIssueStatus.LATE
        item.update(item, dbcommit=dbcommit, reindex=reindex)
    return counter


def get_recipient_suggestions(issue):
    """Get the recipient email suggestions for an issue.

    :param issue: the issue item to analyze.
    :return: the list of suggested emails.
    :rtype list<{type: list<str>, address: str}>
    """
    # Build suggestions email :
    #   1) related vendor issue (default TO recipient type)
    #   2) related library serial acquisition settings information
    #   3) current logged user
    suggestions = {}
    if (vendor := issue.vendor) and (email := vendor.serial_email):
        suggestions.setdefault(email, set()).update([RecipientType.TO])
    if settings := (issue.library or {}).get('serial_acquisition_settings'):
        if email := settings.get('shipping_informations', {}).get('email'):
            suggestions.setdefault(email, set())\
                .update([RecipientType.CC, RecipientType.REPLY_TO])
        if email := settings.get('billing_informations', {}).get('email'):
            suggestions.setdefault(email, set())
    if email := current_librarian.user.email:
        suggestions.setdefault(email, set())

    # sometimes, the recipient types could be an empty set. In this case, we
    # don't need to return this key --> clean the build suggestions dict and
    # return a recipient suggestion array.
    cleaned_suggestions = []
    for recipient_address, recipient_types in suggestions.items():
        suggestion = {'address': recipient_address}
        if recipient_types:
            suggestion['type'] = list(recipient_types)
        cleaned_suggestions.append(suggestion)
    return cleaned_suggestions
