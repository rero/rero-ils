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

"""API for manipulating Circulation policies."""
from __future__ import absolute_import, print_function

import math
import sys
from functools import partial

from elasticsearch_dsl import Q

from rero_ils.modules.api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from rero_ils.modules.fetchers import id_fetcher
from rero_ils.modules.libraries.api import Library
from rero_ils.modules.minters import id_minter
from rero_ils.modules.providers import Provider
from rero_ils.modules.utils import extracted_data_from_ref, \
    get_patron_from_arguments

from .extensions import CircPolicyFieldsExtension
from .models import CircPolicyIdentifier, CircPolicyMetadata

DUE_SOON_REMINDER_TYPE = 'due_soon'
OVERDUE_REMINDER_TYPE = 'overdue'

# cipo provider
CircPolicyProvider = type(
    'CircPolicyProvider',
    (Provider,),
    dict(identifier=CircPolicyIdentifier, pid_type='cipo')
)
# cipo minter
circ_policy_id_minter = partial(id_minter, provider=CircPolicyProvider)
# cipo fetcher
circ_policy_id_fetcher = partial(id_fetcher, provider=CircPolicyProvider)


class CircPoliciesSearch(IlsRecordsSearch):
    """RecordsSearch for Circulation policies."""

    class Meta:
        """Search only on Circulation policies index."""

        index = 'circ_policies'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class CircPolicy(IlsRecord):
    """Circulation policies class."""

    minter = circ_policy_id_minter
    fetcher = circ_policy_id_fetcher
    provider = CircPolicyProvider
    model_cls = CircPolicyMetadata
    pids_exist_check = {
        'required': {
            'org': 'organisation',
        },
        'not_required': {
            # TODO: this is in list of settings
            # 'lib': 'library', # list
            # 'ptty': 'patron_type', # settings list
            # 'itty': 'item_type' # setings list
        }
    }

    _extensions = [
        CircPolicyFieldsExtension()
    ]

    def extended_validation(self, **kwargs):
        """Validate record against schema.

        and extended validation to check that patron types and item types are
        part of the correct organisation.
        """
        from ..item_types.api import ItemType
        from ..patron_types.api import PatronType

        # Only one default policy by organisation
        if self.get('is_default', False):
            default_cipo = CircPolicy.get_default_circ_policy(
                self.organisation_pid)
            if default_cipo and default_cipo.pid != self.pid:
                return 'CircPolicy: already a default policy for this org'

        for library in self.get('libraries', []):
            library_pid = extracted_data_from_ref(library)
            if not Library.get_record_by_pid(library_pid):
                return f"CircPolicy: no library:  {library.get('pid')}"

        # check all patron_types & item_types from settings belongs to the
        # same organisation than the cipo
        org = self.get('organisation')
        for setting in self.get('settings', []):
            patron_type_pid = extracted_data_from_ref(setting.get(
                'patron_type'
            ))
            patron_type = PatronType.get_record_by_pid(patron_type_pid)
            patron_type_org = patron_type.get('organisation')
            item_type_pid = extracted_data_from_ref(setting.get('item_type'))
            item_type = ItemType.get_record_by_pid(item_type_pid)
            item_type_org = item_type.get('organisation')
            if patron_type_org != org or item_type_org != org:
                return 'CircPolicy: PatronType ItemType Org diff'

        # check reminders ::
        #   1) only one "before" reminder can be defined.
        #   2) each delay of "after" reminder must be unique.
        reminders = self.get('reminders', [])
        due_soon_reminders = [r for r in reminders
                              if r.get('type') == DUE_SOON_REMINDER_TYPE]
        if len(due_soon_reminders) > 1:
            return 'Only one "due soon" reminder can be defined by CircPolicy'
        overdue_reminder_delays = [r.get('days_delay') for r in reminders
                                   if r.get('type') == OVERDUE_REMINDER_TYPE]
        unique_delays = set(overdue_reminder_delays)
        if len(unique_delays) != len(overdue_reminder_delays):
            return 'Delay for "overdue" reminder should be unique.'

        # check fees intervals :
        #  1) None interval can overlap other one.
        #  2) Only the last interval can omit an upper limit.
        intervals = sorted(
            self.get('overdue_fees', {}).get('intervals', []),
            key=lambda interval: interval.get('from')
        )
        last_lower_limit = -1
        last_upper_limit = 0
        for interval in intervals:
            lower_limit = interval.get('from', 0)
            upper_limit = interval.get('to')
            if upper_limit is None and interval != intervals[-1]:
                return 'Only the last interval can omit the upper limit.'
            if lower_limit <= last_upper_limit:
                return 'Another interval covers this lower limit interval ' \
                       f':: [{lower_limit}-{upper_limit}]'
            if upper_limit and upper_limit <= last_lower_limit:
                return 'Another interval covers this upper limit interval ' \
                       f':: [{lower_limit}-{upper_limit}]'
            last_lower_limit = lower_limit
            last_upper_limit = upper_limit

        return True

    @classmethod
    def create(cls, data, id_=None, delete_pid=False,
               dbcommit=True, reindex=True, pidcheck=True, **kwargs):
        """Create a new circulation policy record."""
        # default behavior is to reindex the record. Needed to check that there
        # is only one default policy by organisation
        return super().create(
            data, id_, delete_pid, dbcommit, reindex, **kwargs)

    @classmethod
    def exist_name_and_organisation_pid(cls, name, organisation_pid):
        """Check if the policy name is unique on organisation.

        :param name: the name to check if unique.
        :param organisation_pid: the organisation pid.
        :return `True` if name already exists, `False` otherwise.
        """
        result = CircPoliciesSearch()\
            .filter('term', circ_policy_name=name)\
            .filter('term', organisation__pid=organisation_pid)\
            .source().scan()
        try:
            return next(result)
        except StopIteration:
            return None

    @classmethod
    def get_circ_policy_by_LPI(cls, org_pid, lib_pid, ptty_pid, itty_pid):
        """Check if there is a policy for library/location/item types.

        :param org_pid: the organisation pid
        :param lib_pid: the library pid
        :param ptty_pid: the patron type pid
        :param itty_pid: the item type pid
        :return the first circulation policy corresponding to criteria ; `None`
                if no policy found.
        """
        result = CircPoliciesSearch()\
            .filter('term', policy_library_level=True)\
            .filter('term', organisation__pid=org_pid)\
            .filter('term', libraries__pid=lib_pid)\
            .filter('nested',
                    path='settings',
                    query=Q(
                        'bool',
                        must=[
                            Q('match', settings__patron_type__pid=ptty_pid),
                            Q('match', settings__item_type__pid=itty_pid)
                        ]
                    ))\
            .source('pid').scan()
        try:
            return CircPolicy.get_record_by_pid(next(result).pid)
        except StopIteration:
            return None

    @classmethod
    def get_circ_policy_by_OPI(cls, org_pid, ptty_pid, itty_pid):
        """Check if there is a policy for location/item types.

        :param org_pid: the organisation pid
        :param ptty_pid: the patron type pid
        :param itty_pid: the item type pid
        :return the first circulation policy corresponding to criteria ; `None`
                if no policy found.
        """
        result = CircPoliciesSearch()\
            .filter('term', policy_library_level=False)\
            .filter('term', organisation__pid=org_pid)\
            .filter('nested',
                    path='settings',
                    query=Q(
                        'bool',
                        must=[
                            Q('match', settings__patron_type__pid=ptty_pid),
                            Q('match', settings__item_type__pid=itty_pid)
                        ]
                    ))\
            .source('pid').scan()
        try:
            return CircPolicy.get_record_by_pid(next(result).pid)
        except StopIteration:
            return None

    @classmethod
    def get_default_circ_policy(cls, organisation_pid):
        """Return the default circulation policy for an organisation.

        :param organisation_pid: the organisation pid.
        :return the first circulation policy corresponding to criteria ; `None`
                if no policy found.
        """
        result = CircPoliciesSearch()\
            .filter('term', organisation__pid=organisation_pid)\
            .filter('term', is_default=True)\
            .source('pid').scan()
        try:
            return CircPolicy.get_record_by_pid(next(result).pid)
        except StopIteration:
            return None

    @classmethod
    def provide_circ_policy(cls, organisation_pid, library_pid,
                            patron_type_pid, item_type_pid):
        """Return a circ policy for library/patron/item.

        :param organisation_pid: the organisation_pid.
        :param library_pid: the library pid.
        :param patron_type_pid: the patron type_pid.
        :param item_type_pid: the item_type pid.
        :return the best circulation policy corresponding to criteria.
        """
        LPI_policy = CircPolicy.get_circ_policy_by_LPI(
            organisation_pid,
            library_pid,
            patron_type_pid,
            item_type_pid
        )
        if LPI_policy:
            return LPI_policy
        PI_policy = CircPolicy.get_circ_policy_by_OPI(
            organisation_pid,
            patron_type_pid,
            item_type_pid
        )
        if PI_policy:
            return PI_policy
        return CircPolicy.get_default_circ_policy(organisation_pid)

    def reasons_to_keep(self):
        """Reasons aside from record_links to keep a circ policy."""
        others = {}
        is_default = self.get('is_default')
        if is_default:
            others['is_default'] = is_default
        return others

    def reasons_not_to_delete(self):
        """Get reasons not to delete policy."""
        cannot_delete = {}
        others = self.reasons_to_keep()
        links = self.get_links_to_me()
        if others:
            cannot_delete['others'] = others
        if links:
            cannot_delete['links'] = links
        return cannot_delete

    @property
    def can_checkout(self):
        """Shortcut to know if circulation policy allow checkout."""
        return 'checkout_duration' in self

    @property
    def due_soon_interval_days(self):
        """Get number of days to check if loan is considered as due_soon."""
        reminder = [r for r in self.get('reminders', [])
                    if r.get('type') == DUE_SOON_REMINDER_TYPE]
        return reminder[0].get('days_delay') if reminder else 1

    @property
    def initial_overdue_days(self):
        """Get number of days after which loan is considered as overdue.

        To complete this request, we need to find the minimum day where a
        notification OR an incremental fees is placed.
        """
        intervals = self.get_overdue_intervals()
        reminder = self.get_reminder(reminder_type=OVERDUE_REMINDER_TYPE)
        if intervals or reminder:
            return min([
                intervals[0].get('from') if intervals else sys.maxsize,
                reminder.get('days_delay') if reminder else sys.maxsize
            ])

    def get_overdue_intervals(self):
        """Return sorted overdue intervals for this circulation policy."""
        intervals = self.get('overdue_fees', {}).get('intervals', [])
        if intervals:
            intervals = sorted(
                intervals,
                key=lambda interval: interval.get('from')
            )
            if 'to' not in intervals[-1]:
                intervals[-1]['to'] = float('+inf')
        return intervals

    def get_reminders(self, reminder_type=DUE_SOON_REMINDER_TYPE, limit=None):
        """Get reminders corresponding to arguments.

        :param reminder_type: the type of reminder to search.
        :param limit: the number of day limit. All reminders defined after
                      these limit will not be returned
        """
        if limit is None:
            limit = math.inf
        for reminder in self.get('reminders', []):
            if reminder.get('type') == reminder_type \
               and reminder.get('days_delay') <= limit:
                yield reminder

    def get_reminder(self, reminder_type=DUE_SOON_REMINDER_TYPE, idx=0):
        """Get the best possible reminder based on argument criteria.

        :param reminder_type: the type of reminder to search.
        :param idx: the reminder index to search. First reminder has 0 index.
        """
        reminders = list(self.get_reminders(reminder_type=reminder_type))
        if reminders and idx < len(reminders):
            return reminders[idx]

    @classmethod
    def can_request(cls, record, **kwargs):
        """Check if the cipo corresponding to record/patron allow request.

        :param record : the record to check (Item or Holding)
        :param kwargs : To be relevant, additional arguments should contains
                        'patron' argument.
        :return a tuple with True|False and reasons to disallow if False.
        """
        from ..holdings.api import Holding
        from ..items.api import Item

        patron = get_patron_from_arguments(**kwargs)
        if not patron:
            # none patron get be load from kwargs argument. This check can't
            # be relevant --> return True by default
            return True, []
        if 'patron' not in patron.get('roles', []):
            # without 'patron' role, we can't find any patron_type and so we
            # can't find any corresponding cipo --> return False
            return False, ["Patron doesn't have the correct role"]
        library_pid = kwargs['library'].pid if kwargs.get('library') \
            else record.library_pid

        if isinstance(record, Item):
            record_circulation_category_pid = \
                record.item_type_circulation_category_pid
        elif isinstance(record, Holding):
            record_circulation_category_pid = \
                record.circulation_category_pid
        else:
            raise Exception(f'This resource cannot be \
                requested : {record.__class__.__name__}')

        cipo = cls.provide_circ_policy(
                record.organisation_pid,
                library_pid,
                patron.patron_type_pid,
                record_circulation_category_pid
            )
        if not cipo.get('allow_requests', False):
            return False, ["Circulation policy disallows the operation."]
        return True, []

    @classmethod
    def allow_checkout(cls, item, **kwargs):
        """Check if the cipo corresponding to item/patron allow request.

        :param item : the item to check
        :param kwargs : To be relevant, additional arguments should contains
                        'patron' argument.
        :return a tuple with True|False and reasons to disallow if False.
        """
        patron = get_patron_from_arguments(**kwargs)
        if not patron:
            # none patron get be load from kwargs argument. This check can't
            # be relevant --> return True by default
            return True, []
        if 'patron' not in patron.get('roles', []):
            # without 'patron' role, we can't find any patron_type and so we
            # can't find any corresponding cipo --> return False
            return False, ["Patron doesn't have the correct role"]
        library_pid = kwargs['library'].pid if kwargs.get('library') \
            else item.library_pid
        cipo = cls.provide_circ_policy(
            item.organisation_pid,
            library_pid,
            patron.patron_type_pid,
            item.item_type_circulation_category_pid
        )
        if not cipo.can_checkout:
            return False, ["Circulation policy disallows the operation."]
        return True, []


class CircPoliciesIndexer(IlsRecordsIndexer):
    """Indexing documents in Elasticsearch."""

    record_cls = CircPolicy

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='cipo')
