# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
# Copyright (C) 2020 UCLouvain
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

"""API for manipulating patron types."""

from __future__ import absolute_import, print_function

from functools import partial

from elasticsearch_dsl import Q
from flask_babelex import gettext as _

from .models import PatronTypeIdentifier, PatronTypeMetadata
from ..api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from ..circ_policies.api import CircPoliciesSearch
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..patrons.api import Patron, PatronsSearch
from ..providers import Provider

# provider
PatronTypeProvider = type(
    'PatronTypeProvider',
    (Provider,),
    dict(identifier=PatronTypeIdentifier, pid_type='ptty')
)
# minter
patron_type_id_minter = partial(id_minter, provider=PatronTypeProvider)
# fetcher
patron_type_id_fetcher = partial(id_fetcher, provider=PatronTypeProvider)


class PatronTypesSearch(IlsRecordsSearch):
    """PatronTypeSearch."""

    class Meta:
        """Search only on patrons index."""

        index = 'patron_types'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class PatronType(IlsRecord):
    """PatronType class."""

    minter = patron_type_id_minter
    fetcher = patron_type_id_fetcher
    provider = PatronTypeProvider
    model_cls = PatronTypeMetadata
    pids_exist_check = {
        'required': {
            'org': 'organisation',
        }
    }

    def extended_validation(self, **kwargs):
        """Add additional record validation.

        Ensure than checkout limits are coherent.
        Ensure than library limit exceptions are coherent.

        """
        # validate checkout limits
        checkout_limits_data = self.get('limits', {}).get('checkout_limits')
        if checkout_limits_data:
            global_limit = checkout_limits_data.get('global_limit')
            library_limit = checkout_limits_data.get('library_limit')
            if library_limit:
                # Library limit cannot be higher than global limit
                if library_limit > global_limit:
                    return _('Library limit cannot be higher than global '
                             'limit.')
                # Exception limit cannot have same value than library limit
                # Only one exception per library
                exceptions_lib = []
                exceptions = checkout_limits_data.get('library_exceptions', [])
                for exception in exceptions:
                    if exception.get('value') == library_limit:
                        return _('Exception limit cannot have same value than '
                                 'library limit')
                    ref = exception.get('library').get('$ref')
                    if ref in exceptions_lib:
                        return _('Only one specific limit by library if '
                                 'allowed.')
                    exceptions_lib.append(ref)
        return True

    @classmethod
    def exist_name_and_organisation_pid(cls, name, organisation_pid):
        """Check if the name is unique within organisation."""
        patron_type = PatronTypesSearch()\
            .filter('term', patron_type_name=name)\
            .filter('term', organisation__pid=organisation_pid).source().scan()
        try:
            return next(patron_type)
        except StopIteration:
            return None

    @classmethod
    def get_yearly_subscription_patron_types(cls):
        """Get PatronType with an active yearly subscription."""
        results = PatronTypesSearch()\
            .filter('range', subscription_amount={'gt': 0})\
            .source('pid')\
            .scan()
        for result in results:
            yield cls.get_record_by_pid(result.pid)

    def get_linked_patron(self):
        """Get patron linked to this patron type."""
        results = PatronsSearch()\
            .filter('term', patron__type__pid=self.pid).source('pid').scan()
        for result in results:
            yield Patron.get_record_by_pid(result.pid)

    def get_number_of_patrons(self):
        """Get number of patrons."""
        return PatronsSearch()\
            .filter('term', patron__type__pid=self.pid).source().count()

    def get_number_of_circ_policies(self):
        """Get number of circulation policies."""
        return CircPoliciesSearch().filter(
            'nested',
            path='settings',
            query=Q(
                'bool',
                must=[
                    Q(
                        'match',
                        settings__patron_type__pid=self.pid
                    )
                ]
            )
        ).source().count()

    @property
    def is_subscription_required(self):
        """Check if a subscription is required for this patron type."""
        return self.get('subscription_amount', 0) > 0

    def get_links_to_me(self):
        """Get number of links."""
        links = {}
        patrons = self.get_number_of_patrons()
        if patrons:
            links['patrons'] = patrons
        circ_policies = self.get_number_of_circ_policies()
        if circ_policies:
            links['circ_policies'] = circ_policies
        return links

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        cannot_delete = {}
        links = self.get_links_to_me()
        if links:
            cannot_delete['links'] = links
        return cannot_delete


class PatronTypesIndexer(IlsRecordsIndexer):
    """Holdings indexing class."""

    record_cls = PatronType

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super(PatronTypesIndexer, self).bulk_index(record_id_iterator,
                                                   doc_type='ptty')
