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

"""API for manipulating Fees."""

from __future__ import absolute_import, print_function

from datetime import datetime, timezone
from functools import partial

from flask import current_app
from invenio_search.api import RecordsSearch

from .models import FeeIdentifier, FeeMetadata
from ..api import IlsRecord
from ..circ_policies.api import CircPolicy
from ..fetchers import id_fetcher
from ..locations.api import Location
from ..minters import id_minter
from ..providers import Provider

# fee provider
feeProvider = type(
    'FeeProvider',
    (Provider,),
    dict(identifier=FeeIdentifier, pid_type='fee')
)
# fee minter
fee_id_minter = partial(id_minter, provider=feeProvider)
# fee fetcher
fee_id_fetcher = partial(id_fetcher, provider=feeProvider)


class FeesSearch(RecordsSearch):
    """RecordsSearch for Fees."""

    class Meta:
        """Search only on Fees index."""

        index = 'fees'


class Fee(IlsRecord):
    """Fees class."""

    minter = fee_id_minter
    fetcher = fee_id_fetcher
    provider = feeProvider
    model_cls = FeeMetadata

    @property
    def organisation_pid(self):
        """Return organisation pid."""
        location = Location.get_record_by_pid(self.transaction_location_pid)
        return location.organisation_pid

    @property
    def transaction_location_pid(self):
        """Return transaction location pid."""
        return self.replace_refs().get('location').get('pid')

    @classmethod
    def create_fee_from_notification(cls, notification):
        """Create a new fee."""
        record = {}
        if notification.get('notification_type') == 'overdue':
            data = {}
            schemas = current_app.config.get('RECORDS_JSON_SCHEMA')
            data_schema = {
                'base_url': current_app.config.get(
                    'RERO_ILS_APP_BASE_URL'
                ),
                'schema_endpoint': current_app.config.get(
                    'JSONSCHEMAS_ENDPOINT'
                ),
                'schema': schemas['fee']
            }
            data['$schema'] = '{base_url}{schema_endpoint}{schema}'\
                .format(**data_schema)
            base_url = current_app.config.get('RERO_ILS_APP_BASE_URL')
            url_api = '{base_url}/api/{doc_type}/{pid}'
            data['creation_date'] = datetime.now(timezone.utc).isoformat()
            data['fee_type'] = 'overdue'
            data['notification'] = {
                '$ref': url_api.format(
                    base_url=base_url,
                    doc_type='notifications',
                    pid=notification.pid)
            }
            location_pid = notification.transaction_location_pid
            data['location'] = {
                '$ref': url_api.format(
                    base_url=base_url,
                    doc_type='locations',
                    pid=location_pid)
            }
            library_pid = Location.get_record_by_pid(location_pid).library_pid
            patron_type_pid = notification.patron.patron_type_pid
            holding_circulation_category_pid = notification\
                .item.holding_circulation_category_pid
            cipo = CircPolicy.provide_circ_policy(
                library_pid,
                patron_type_pid,
                holding_circulation_category_pid
            )
            data['amount'] = cipo.get('reminder_fee_amount')
            currency = current_app.config.get('RERO_ILS_DEFAULT_CURRENCY')
            if notification.organisation:
                currency = notification.organisation.get('default_currency')
            data['currency'] = currency
            data['status'] = 'open'
            record = cls.create(
                data,
                dbcommit=True,
                reindex=True,
                delete_pid=True
            )
        return record
