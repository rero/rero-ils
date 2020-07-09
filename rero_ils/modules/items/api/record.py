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

"""API for manipulating item records."""
from ..utils import item_pid_to_object
from ...api import IlsRecord
from ...libraries.api import Library
from ...locations.api import Location
from ...organisations.api import Organisation
from ...utils import extracted_data_from_ref, generate_item_barcode, \
    get_base_url, get_ref_for_pid, trim_barcode_for_record


class ItemRecord(IlsRecord):
    """Item record class."""

    def extended_validation(self, **kwargs):
        """Add additional record validation.

        Ensures that item of type issue is created only on
        holdings of type serials.

        Ensures that item of type issue has the issue field.

        Ensures that standard item has no issue field.

        Ensures that only one note of each type is present.

        :return: False if
            - holdings type is not journal and item type is issue.
            - item type is journal and field issue exists.
            - item type is standard and field issue does not exists.
            - if notes array has multiple notes with same type
        """
        from ...holdings.api import Holding
        holding = Holding.get_record_by_pid(self.holding_pid)
        is_serial = holding.holdings_type == 'serial'
        if is_serial and self.get('type') == 'standard':
            return False
        issue = self.get('issue', {})
        if issue and self.get('type') == 'standard':
            return False
        if self.get('type') == 'issue' and not issue:
            return False
        note_types = [note.get('type') for note in self.get('notes', [])]
        if len(note_types) != len(set(note_types)):
            return False

        return True

    @classmethod
    def create(cls, data, id_=None, delete_pid=False,
               dbcommit=False, reindex=False, **kwargs):
        """Create item record."""
        cls._item_build_org_ref(data)
        data = cls._prepare_item_record(data=data, mode='create')
        record = super(ItemRecord, cls).create(
            data, id_, delete_pid, dbcommit, reindex, **kwargs)
        cls._increment_next_prediction_for_holding(
            record, dbcommit=dbcommit, reindex=reindex)
        return record

    def update(self, data, dbcommit=False, reindex=False):
        """Update an item record.

        :param data: The record to update.
        :param dbcommit: boolean to commit the record to the database or not.
        :param reindex: boolean to reindex the record or not.
        :return: The updated item record.
        """
        data = self._prepare_item_record(data=data, mode='update')
        super(ItemRecord, self).update(data, dbcommit, reindex)
        # TODO: some item updates do not require holding re-linking

        return self

    def replace(self, data, dbcommit=False, reindex=False):
        """Replace an item record.

        :param data: The record to replace.
        :param dbcommit: boolean to commit the record to the database or not.
        :param reindex: boolean to reindex the record or not.
        :return: The replaced item record.
        """
        # update item record with a generated barcode if does not exist
        data = generate_item_barcode(data=data)
        super(ItemRecord, self).replace(data, dbcommit, reindex)
        return self

    @classmethod
    def _increment_next_prediction_for_holding(
            cls, item, dbcommit=False, reindex=False):
        """Increment next issue for items with regular frequencies."""
        from ...holdings.api import Holding
        holding = Holding.get_record_by_pid(item.holding_pid)
        if item.get('type') == 'issue' and \
            item.get('issue', {}).get('regular') and \
                holding.holdings_type == 'serial' and \
                holding.get('patterns', {}).get('frequency') != 'rdafr:1016':
            updated_holding = holding.increment_next_prediction()
            holding = Holding.get_record_by_pid(item.holding_pid)
            holding.update(data=updated_holding,
                           dbcommit=dbcommit, reindex=reindex)
            holding.commit()

    @classmethod
    def _item_build_org_ref(cls, data):
        """Build $ref for the organisation of the item."""
        loc_pid = data.get('location', {}).get('pid')
        if not loc_pid:
            loc_pid = data.get('location').get('$ref').split('locations/')[1]
            org_pid = Location.get_record_by_pid(loc_pid).organisation_pid
        url_api = '{base_url}/api/{doc_type}/{pid}'
        org_ref = {
            '$ref': url_api.format(
                base_url=get_base_url(),
                doc_type='organisations',
                pid=org_pid or cls.organisation_pid)
        }
        data['organisation'] = org_ref

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
            old_holding_type in ['serial', 'electronic']
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

        # we will NOT create serials holdings for items
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
        data = trim_barcode_for_record(data=data)
        # Since the barcode is a mandatory field, we set it to current
        # timestamp if not given
        data = generate_item_barcode(data=data)
        data = cls.link_item_to_holding(data, mode)
        return data

    @classmethod
    def get_items_pid_by_holding_pid(cls, holding_pid):
        """Returns item pids from holding pid."""
        from . import ItemsSearch
        results = ItemsSearch()\
            .filter('term', holding__pid=holding_pid)\
            .source(['pid']).scan()
        for item in results:
            yield item.pid

    @property
    def holding_pid(self):
        """Shortcut for item holding pid."""
        if self.replace_refs().get('holding'):
            return self.replace_refs()['holding']['pid']
        return None

    @property
    def document_pid(self):
        """Shortcut for item document pid."""
        if self.replace_refs().get('document'):
            return self.replace_refs()['document']['pid']
        return None

    @classmethod
    def get_document_pid_by_item_pid(cls, item_pid):
        """Returns document pid from item pid."""
        item = cls.get_record_by_pid(item_pid).replace_refs()
        return item.get('document', {}).get('pid')

    @classmethod
    def get_document_pid_by_item_pid_object(cls, item_pid):
        """Returns document pid from item pid.

        :param item_pid: the item_pid object
        :type item_pid: object
        :return: the document pid
        :rtype: str
        """
        item = cls.get_record_by_pid(item_pid.get('value')).replace_refs()
        return item.get('document', {}).get('pid')

    @classmethod
    def get_items_pid_by_document_pid(cls, document_pid):
        """Returns item pisd from document pid."""
        from . import ItemsSearch
        results = ItemsSearch()\
            .filter('term', document__pid=document_pid)\
            .source(['pid']).scan()
        for item in results:
            yield item_pid_to_object(item.pid)

    @classmethod
    def get_item_by_barcode(cls, barcode=None):
        """Get item by barcode."""
        from . import ItemsSearch
        results = ItemsSearch().filter(
            'term', barcode=barcode).source(includes='pid').scan()
        try:
            return cls.get_record_by_pid(next(results).pid)
        except StopIteration:
            return None

    def get_organisation(self):
        """Shortcut to the organisation of the item location."""
        return self.get_library().get_organisation()

    def get_library(self):
        """Shortcut to the library of the item location."""
        return self.get_location().get_library()

    def get_location(self):
        """Shortcut to the location of the item."""
        location_pid = self.replace_refs()['location']['pid']
        return Location.get_record_by_pid(location_pid)

    @property
    def status(self):
        """Shortcut for item status."""
        return self.get('status', '')

    @property
    def item_type_pid(self):
        """Shortcut for item type pid."""
        item_type_pid = None
        item_type = self.replace_refs().get('item_type')
        if item_type:
            item_type_pid = item_type.get('pid')
        return item_type_pid

    @property
    def item_record_type(self):
        """Shortcut for item type, whether a standard or an issue record."""
        return self.get('type')

    @property
    def holding_circulation_category_pid(self):
        """Shortcut for holding circulation category pid of an item."""
        from ...holdings.api import Holding
        circulation_category_pid = None
        if self.holding_pid:
            circulation_category_pid = \
                Holding.get_record_by_pid(
                    self.holding_pid).circulation_category_pid
        return circulation_category_pid

    @property
    def location_pid(self):
        """Shortcut for item location pid."""
        location_pid = None
        location = self.replace_refs().get('location')
        if location:
            location_pid = location.get('pid')
        return location_pid

    @property
    def holding_location_pid(self):
        """Shortcut for holding location pid of an item."""
        from ...holdings.api import Holding
        location_pid = None
        if self.holding_pid:
            location_pid = Holding.get_record_by_pid(
                self.holding_pid).location_pid
        return location_pid

    @property
    def library_pid(self):
        """Shortcut for item library pid."""
        location = Location.get_record_by_pid(self.location_pid).replace_refs()
        return location.get('library').get('pid')

    @property
    def holding_library_pid(self):
        """Shortcut for holding library pid of an item."""
        library_pid = None
        if self.holding_location_pid:
            location = Location.get_record_by_pid(
                self.holding_location_pid).replace_refs()
            library_pid = location.get('library').get('pid')
        return library_pid

    @property
    def organisation_pid(self):
        """Get organisation pid for item."""
        library = Library.get_record_by_pid(self.library_pid)
        return library.organisation_pid

    @property
    def organisation_view(self):
        """Get Organisation view for item."""
        organisation = Organisation.get_record_by_pid(self.organisation_pid)
        return organisation['view_code']

    def get_owning_pickup_location_pid(self):
        """Returns the pickup location for the item owning location.

        :return the pid of the item owning item location.
        """
        library = self.get_library()
        return library.get_pickup_location_pid()

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
