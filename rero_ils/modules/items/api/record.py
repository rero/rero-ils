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

"""API for manipulating item records."""
from contextlib import suppress
from datetime import datetime, timezone

import pytz
from elasticsearch_dsl.query import Q
from flask_babel import gettext as _

from rero_ils.modules.api import IlsRecord
from rero_ils.modules.holdings.models import HoldingTypes
from rero_ils.modules.item_types.api import ItemType
from rero_ils.modules.local_fields.extensions import \
    DeleteRelatedLocalFieldExtension
from rero_ils.modules.operation_logs.extensions import \
    UntrackedFieldsOperationLogObserverExtension
from rero_ils.modules.organisations.api import Organisation
from rero_ils.modules.record_extensions import OrgLibRecordExtension
from rero_ils.modules.utils import date_string_to_utc, \
    extracted_data_from_ref, generate_item_barcode, get_ref_for_pid, \
    trim_item_barcode_for_record

from ..extensions import IssueSortDateExtension, IssueStatusExtension
from ..models import TypeOfItem
from ..utils import item_pid_to_object


class ItemRecord(IlsRecord):
    """Item record class."""

    _extensions = [
        IssueSortDateExtension(),
        IssueStatusExtension(),
        OrgLibRecordExtension(),
        UntrackedFieldsOperationLogObserverExtension(['status']),
        DeleteRelatedLocalFieldExtension()
    ]

    def extended_validation(self, **kwargs):
        """Add additional record validation.

        Ensures that barcode field is unique.

        Ensures that item of type issue is created only on
        holdings of type serials.

        Ensures that item of type issue has the issue field.
        Ensures that item of type issue has the enumAndChrono field required.

        Ensures that standard item has no issue field.

        Ensures that only one note of each type is present.

        :return: Error message if
            - barcode already exists
            - holdings type is not journal and item type is issue.
            - item type is journal and field issue exists.
            - item type is standard and field issue does not exists.
            - if notes array has multiple notes with same type
            - `temporary_item_type` has same value than `item_type`
            - temporary_item_type isn't in the future (if specified)

        """
        from . import ItemsSearch
        if barcode := self.get('barcode'):
            if (
                ItemsSearch()
                .exclude('term', pid=self.pid)
                .filter('term', barcode=barcode)
                .source('pid')
                .count()
            ):
                return _(f'Barcode {barcode} is already taken.')

        from ...holdings.api import Holding
        holding_pid = extracted_data_from_ref(self.get('holding').get('$ref'))
        holding = Holding.get_record_by_pid(holding_pid)
        if not holding:
            return _(f'Holding does not exist: {holding_pid}')

        if self.get('issue') and self.get('type') == TypeOfItem.STANDARD:
            return _('Standard item can not have a issue field.')
        if self.get('type') == TypeOfItem.ISSUE:
            if not self.get('issue', {}):
                return _('Issue item must have an issue field.')
            if not self.get('enumerationAndChronology'):
                return _('enumerationAndChronology field is required '
                         'for an issue item')
        note_types = [note.get('type') for note in self.get('notes', [])]
        if len(note_types) != len(set(note_types)):
            return _('Can not have multiple notes of the same type.')

        # check temporary item type data
        if tmp_itty := self.get('temporary_item_type'):
            if tmp_itty['$ref'] == self['item_type']['$ref']:
                return _('Temporary circulation category cannot be the same '
                         'than default circulation category.')
            if tmp_itty.get('end_date'):
                end_date = date_string_to_utc(tmp_itty.get('end_date'))
                if end_date <= pytz.utc.localize(datetime.now()):
                    return _('Temporary circulation category end date must be '
                             'a date in the future.')

        return True

    @classmethod
    def create(cls, data, id_=None, delete_pid=False,
               dbcommit=False, reindex=False, **kwargs):
        """Create item record."""
        data = cls._prepare_item_record(data=data, mode='create')
        data = cls._set_issue_status_date(data=data)
        record = super().create(
            data, id_, delete_pid, dbcommit, reindex, **kwargs)
        holding = cls._increment_next_prediction_for_holding(
            record, dbcommit=dbcommit, reindex=reindex)
        # As we potentially update the parent holding when we create an issue
        # item, we need to commit this holding even if `dbcommit` iss set to
        # false. Without this commit, only the current (Item) resource will be
        # committed by `invenio-records` and the holding changes will be lost.
        #
        # If `dbcommit` is already set to True, this commit is already done by
        # the `IlsRecord.update()` function.
        #
        # /!\ if we write some other operation after _increment_next_prediction
        #     we need to manage ourself the `rollback()`.
        #
        # TODO :: best solution will be to create an invenio `post_create`
        #         extension for the Item resource.
        # https://invenio-records.readthedocs.io/en/latest/api.html#module-invenio_records.extensions
        if not dbcommit and holding:
            holding.commit()
        return record

    def update(self, data, commit=True, dbcommit=False, reindex=False):
        """Update an item record.

        :param data: The record to update.
        :param dbcommit: boolean to   the record to the database or not.
        :param reindex: boolean to reindex the record or not.
        :return: The updated item record.
        """
        data = self._set_issue_status_date(data)
        data = self._prepare_item_record(data=data, mode='update')
        super().update(data, commit, dbcommit, reindex)
        # TODO: some item updates do not require holding re-linking
        return self

    def replace(self, data, commit=True, dbcommit=False, reindex=False):
        """Replace an item record.

        :param data: The record to replace.
        :param dbcommit: boolean to commit the record to the database or not.
        :param reindex: boolean to reindex the record or not.
        :return: The replaced item record.
        """
        # update item record with a generated barcode if does not exist
        data = generate_item_barcode(data=data)
        super().replace(data, commit, dbcommit, reindex)
        return self

    @classmethod
    def _set_issue_status_date(cls, data):
        """Set the status date to current timestamp for an issue.

        :param data: The record to update.
        :return: The updated record.
        """
        if data.get('type') != TypeOfItem.ISSUE:
            return data

        status = data.get('issue', {}).get('status')
        item = cls.get_record_by_pid(data.get('pid'))
        now = datetime.now(timezone.utc).isoformat()

        if item:  # item already exists
            if status and status != item.issue_status:
                data['issue']['status_date'] = now
        else:  # item creation
            if status:
                data['issue']['status_date'] = now
        return data

    @classmethod
    def _increment_next_prediction_for_holding(
            cls, item, dbcommit=False, reindex=False):
        """Increment next issue for items with regular frequencies."""
        from ...holdings.api import Holding
        holding = Holding.get_record_by_pid(item.holding_pid)
        if item.get('type') == 'issue' and \
                item.get('issue', {}).get('regular') and \
                holding.holdings_type == 'serial' and \
                holding.get('patterns') and \
                holding.get('patterns', {}).get('frequency') != 'rdafr:1016':
            updated_holding = holding.increment_next_prediction()
            return holding.update(
                data=updated_holding,
                dbcommit=dbcommit,
                reindex=reindex
            )

    @classmethod
    def link_item_to_holding(cls, record, mode):
        """Complete the item record.

        Link an item to a standard holding record.
        Only holdings check is made at the update mode.

        :param record: the item record.
        :param mode: update or create mode.
        :return: the updated record with matched holdings record
        """
        from ...holdings.api import Holding, create_holding, \
            get_holding_pid_by_doc_location_item_type

        old_holding_pid = None
        old_holding_type = None
        if record.get('holding'):
            old_holding_pid = extracted_data_from_ref(
                record['holding'], data='pid')
            old_holding_type = Holding.get_holdings_type_by_holding_pid(
                old_holding_pid)

        if (
            mode == 'create' and record.get('holding')) or (
            old_holding_type in [HoldingTypes.SERIAL, HoldingTypes.ELECTRONIC]
        ):
            return record

        # item type is important for linking to the correct holdings type.
        item_record_type = record.get('type', 'standard')

        # get pids from $ref
        document_pid = extracted_data_from_ref(record['document'], data='pid')
        location_pid = extracted_data_from_ref(record['location'], data='pid')
        item_type_pid = extracted_data_from_ref(
            record['item_type'], data='pid')

        holding_pid = get_holding_pid_by_doc_location_item_type(
            document_pid, location_pid, item_type_pid, item_record_type)

        # we will NOT create serial holdings for items
        if not holding_pid and item_record_type != 'serial':
            holdings_record = create_holding(
                document_pid=document_pid,
                location_pid=location_pid,
                item_type_pid=item_type_pid)
            holding_pid = holdings_record.pid

        # update item record with the parent holding record if different
        # from the old holding pid
        if not old_holding_pid or holding_pid != old_holding_pid:
            record['holding'] = {'$ref': get_ref_for_pid(
                'hold',
                holding_pid
            )}
        return record

    @classmethod
    def _prepare_item_record(cls, data, mode):
        """Prepare item data before the creation.

        Trims the barcode.
        Relinks to the correct holdings record.
        Generates a barcode if not given.

        :param data: the item record.
        :param mode: update or create mode.
        :return: the modified record.
        """
        data = trim_item_barcode_for_record(data=data)
        # Since the barcode is a mandatory field, we set it to current
        # timestamp if not given
        data = generate_item_barcode(data=data)
        data = cls.link_item_to_holding(data, mode)
        return data

    @classmethod
    def get_items_pid_by_holding_pid(cls, holding_pid, with_masked=True):
        """Returns item pids from holding pid."""
        from . import ItemsSearch
        es_query = ItemsSearch() \
            .params(preserve_order=True)\
            .filter('term', holding__pid=holding_pid) \
            .sort({'pid': {"order": "asc"}}) \
            .source(['pid'])
        if not with_masked:
            es_query = es_query.filter(
                'bool', must_not=[Q('term', _masked=True)])
        for item in es_query.scan():
            yield item.pid

    @property
    def holding_pid(self):
        """Shortcut for item holding pid."""
        return extracted_data_from_ref(self.get('holding'))

    @property
    def holding(self):
        """Shortcut for item holding."""
        return extracted_data_from_ref(self.get('holding'), data='record')

    @property
    def holding_location_pid(self):
        """Shortcut for holding location pid of an item."""
        if holding := self.holding:
            return holding.location_pid

    @property
    def holding_library_pid(self):
        """Shortcut for holding library pid of an item."""
        if holding := self.holding:
            return holding.library_pid

    @property
    def document_pid(self):
        """Shortcut for item document pid."""
        return extracted_data_from_ref(self['document'])

    @classmethod
    def get_document_pid_by_item_pid(cls, item_pid):
        """Returns document pid from item pid."""
        item = cls.get_record_by_pid(item_pid)
        return extracted_data_from_ref(item['document'])

    @classmethod
    def get_document_pid_by_item_pid_object(cls, item_pid):
        """Returns document pid from item pid.

        :param item_pid: the item_pid object
        :type item_pid: object
        :return: the document pid
        :rtype: str
        """
        item = cls.get_record_by_pid(item_pid.get('value'))
        return extracted_data_from_ref(item['document'])

    @classmethod
    def get_items_pid_by_document_pid(cls, document_pid):
        """Returns item pids related to a document pid.

        :param document_pid: the parent document pid.
        :return a generator of related item pid.
        :rtype generator<str>
        """
        from . import ItemsSearch
        results = ItemsSearch()\
            .filter('term', document__pid=document_pid)\
            .source(['pid']).scan()
        for item in results:
            yield item_pid_to_object(item.pid)

    @classmethod
    def get_item_by_barcode(cls, barcode, organisation_pid=None):
        """Get item by barcode.

        :param barcode: the item barcode.
        :param organisation_pid: the organisation pid. As barcode could be
            shared between items from multiple organisations we need to filter
            result by organisation.pid
        :return The item corresponding to the barcode if exists or None.
        :rtype `rero_ils.modules.items.api.api.Item`
        """
        from . import ItemsSearch
        filters = Q('term', barcode=barcode)
        if organisation_pid:
            filters &= Q('term', organisation__pid=organisation_pid)
        results = ItemsSearch()\
            .filter(filters)\
            .source(includes='pid')\
            .scan()
        with suppress(StopIteration):
            return cls.get_record_by_pid(next(results).pid)

    def get_organisation(self):
        """Shortcut to the organisation of the item location."""
        return Organisation.get_record_by_pid(self.organisation_pid)

    def get_library(self):
        """Shortcut to the library of the item location."""
        return self.get_location().get_library()

    def get_location(self):
        """Shortcut to the location of the item."""
        return extracted_data_from_ref(self['location'], data='record')

    def get_circulation_location(self):
        """Get the location to used for circulation operation."""
        # By default, the location used for circulation operations is the main
        # item location except if this item has a `temporary_location` and this
        # location isn't yet over.
        if tmp_location := self.get('temporary_location'):
            if end_date := tmp_location.get('end_date'):
                now_date = pytz.utc.localize(datetime.now())
                end_date = date_string_to_utc(end_date)
                if now_date > end_date:
                    return self.get_location()
            return extracted_data_from_ref(tmp_location['$ref'], data='record')
        return self.get_location()

    @property
    def status(self):
        """Shortcut for item status."""
        return self.get('status', '')

    @property
    def enumerationAndChronology(self):
        """Shortcut for item enumerationAndChronology."""
        return self.get('enumerationAndChronology', '')

    @property
    def item_type_pid(self):
        """Shortcut for item type pid."""
        if self.get('item_type'):
            return extracted_data_from_ref(self.get('item_type'))

    @property
    def temporary_item_type_pid(self):
        """Shortcut for temporary item type pid."""
        if tmp_item_type := self.get('temporary_item_type', {}):
            # if the temporary_item_type end_date is over : return none
            if end_date := tmp_item_type.get('end_date'):
                now_date = pytz.utc.localize(datetime.now())
                end_date = date_string_to_utc(end_date)
                if now_date > end_date:
                    return None
            return extracted_data_from_ref(tmp_item_type.get('$ref'))

    @property
    def item_type_circulation_category_pid(self):
        """Shortcut to find the best item_type to use for circulation."""
        return self.temporary_item_type_pid or self.item_type_pid

    @property
    def circulation_category(self):
        """Shortcut to find the used circulation category for this item.

        :return the in-used circulation category for this item.
        :rtype rero_ils.modules.item_types.api.ItemType
        """
        return ItemType.get_record_by_pid(
            self.item_type_circulation_category_pid
        )

    @property
    def item_record_type(self):
        """Shortcut for item type, whether a standard or an issue record."""
        return self.get('type')

    @property
    def holding_circulation_category_pid(self):
        """Shortcut for holding circulation category pid of an item."""
        from ...holdings.api import Holding
        if self.holding_pid:
            return Holding.get_record_by_pid(
                    self.holding_pid).circulation_category_pid

    @property
    def call_numbers(self):
        """Return an array with item call_numbers.

        Inherit call numbers where applicable.
        """
        from ...holdings.api import Holding
        if self.get('type') == 'standard':
            data = [self.get(key) for key in ['call_number',
                                              'second_call_number']]
        else:
            data = []
            holding = Holding.get_record_by_pid(
                extracted_data_from_ref(self.get('holding')))

            for key in ['call_number', 'second_call_number']:
                if self.get(key):
                    data.append(self.get(key))
                elif holding.get(key):
                    data.append(holding.get(key))
        return [call_number for call_number in data if call_number]

    @property
    def location_pid(self):
        """Shortcut for item location pid."""
        if self.get('location'):
            return extracted_data_from_ref(self.get('location'))

    @property
    def location(self):
        """Shortcut to get item related location resource."""
        if self.get('location'):
            return extracted_data_from_ref(self.get('location'), data='record')

    @property
    def library_pid(self):
        """Shortcut for item library pid."""
        if location := self.location:
            return location.library_pid

    @property
    def library(self):
        """Shortcut for item library resource."""
        if location := self.location:
            return location.library

    @property
    def organisation_pid(self):
        """Get organisation pid for item."""
        if self.get('organisation'):
            return extracted_data_from_ref(self.get('organisation'))
        return self.get_library().organisation_pid

    @property
    def organisation_view(self):
        """Get Organisation view for item."""
        organisation = Organisation.get_record_by_pid(self.organisation_pid)
        return organisation['view_code']

    def get_owning_pickup_location_pid(self):
        """Returns the pickup location pid for the item owning location.

        case when library has no pickup location defined, we return the item
        owning location pid.

        :return location pid.
        """
        library = self.get_library()
        return library.get_pickup_location_pid() or self.location_pid

    @property
    def notes(self):
        """Return notes related to this item.

        :return an array of all notes related to the item. Each note should
                have two keys : `type` and `content`.
        """
        return self.get('notes', [])

    def get_note(self, note_type):
        """Return an item note by its type.

        :param note_type: the type of note (see ``ItemNoteTypes``)
        :return the content of the note, None if note type is not found
        """
        notes = [note.get('content') for note in self.notes
                 if note.get('type') == note_type]
        return next(iter(notes), None)

    @property
    def is_new_acquisition(self):
        """Is this item should be considered as a new acquisition.

        :return True if Item is a new acquisition, False otherwise
        """
        if acquisition_date := self.get('acquisition_date'):
            return datetime.strptime(
                acquisition_date, '%Y-%m-%d') < datetime.now()
        return False

    @classmethod
    def get_number_masked_items_by_holdings_pid(cls, holding_pid):
        """Returns the number of unmasked items and attached to a holding.

        :param holding_pid: the pid of the holdings.
        :return number of un masked items.
        """
        from . import ItemsSearch
        query = ItemsSearch().filter('term', holding__pid=holding_pid)
        return query.filter('bool', must_not=[Q('term', _masked=True)]) \
            .source(['pid']).count()
