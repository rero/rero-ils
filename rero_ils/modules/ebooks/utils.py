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

"""Utilities."""

from flask import current_app
from invenio_db import db
from invenio_oaiharvester.models import OAIHarvestConfig

from rero_ils.modules.locations.api import Location

from ..documents.api import Document
from ..holdings.api import Holding, HoldingsSearch, create_holding, \
    get_holding_pid_by_doc_location_item_type
from ..organisations.api import Organisation


def add_oai_source(name, baseurl, metadataprefix='marc21',
                   setspecs='', comment='', update=False):
    """Add OAIHarvestConfig."""
    with current_app.app_context():
        source = OAIHarvestConfig.query.filter_by(name=name).first()
        if not source:
            source = OAIHarvestConfig(
                name=name,
                baseurl=baseurl,
                metadataprefix=metadataprefix,
                setspecs=setspecs,
                comment=comment
            )
            source.save()
            db.session.commit()
            return 'Added'
        elif update:
            source.name = name
            source.baseurl = baseurl
            source.metadataprefix = metadataprefix
            if setspecs != '':
                source.setspecs = setspecs
            if comment != '':
                source.comment = comment
            db.session.commit()
            return 'Updated'
        return 'Not Updated'


def get_harvested_sources(record):
    """Get the harvested sources from electronicLocator."""
    harvested_sources = []
    new_electronic_locators = []
    electronic_locators = record.get('electronicLocator', [])
    for electronic_locator in electronic_locators:
        if source := electronic_locator.get('source'):
            harvested_sources.append({
                'source': source,
                'uri': electronic_locator.get('url')
            })
        else:
            new_electronic_locators.append(electronic_locator)
    if new_electronic_locators:
        record['electronicLocator'] = new_electronic_locators
    return harvested_sources


def create_document_holding(record):
    """Create a document and a holding for a harvested ebook."""
    harvested_sources = get_harvested_sources(record)
    new_record = None
    holdings = []
    for harvested_source in harvested_sources:
        if org := Organisation.get_record_by_online_harvested_source(
                source=harvested_source['source']):
            if not new_record:
                new_record = Document.create(
                    data=record,
                    dbcommit=False,
                    reindex=False
                )
            if new_record:
                item_type_pid = org.online_circulation_category()
                location_pids = org.get_online_locations()
                for location_pid in location_pids:
                    location = Location.get_record_by_pid(location_pid)
                    library = location.get_library()
                    if url := library.get_online_harvested_source_url(
                            source=harvested_source['source']):
                        uri_split = harvested_source['uri'].split('/')[3:]
                        uri_split.insert(0, url.rstrip('/'))
                        harvested_source['uri'] = '/'.join(uri_split)
                    hold = create_holding(
                        document_pid=new_record.pid,
                        location_pid=location_pid,
                        item_type_pid=item_type_pid,
                        electronic_location=harvested_source,
                        holdings_type='electronic')
                    holdings.append(hold)
        else:
            current_app.logger.warning(
                f"create document holding no org: {harvested_source['source']}"
            )
    db.session.commit()
    for hold in holdings:
        hold.reindex()
    # the document has been reindexed by the holdings
    if not holdings and new_record:
        new_record.reindex()
    return new_record


def update_document_holding(record, pid):
    """Update a document and a holding for a harvested ebook."""
    harvested_sources = get_harvested_sources(record)
    new_record = None
    existing_record = Document.get_record_by_pid(pid)
    new_record = existing_record.replace(
        data=record,
        dbcommit=False,
        reindex=False
    )
    # Save all source uris to find holdings we can delete later
    source_uris = []
    holdings = []
    for harvested_source in harvested_sources:
        if org := Organisation.get_record_by_online_harvested_source(
                source=harvested_source['source']):
            # add the organisation source uri
            source_uris.append(harvested_source['uri'])
            item_type_pid = org.online_circulation_category()
            for location_pid in org.get_online_locations():
                location = Location.get_record_by_pid(location_pid)
                library = location.get_library()
                # replace "https://some.uri" from ebooks with library uri
                if url := library.get_online_harvested_source_url(
                        source=harvested_source['source']):
                    uri_split = harvested_source['uri'].split('/')[3:]
                    uri_split.insert(0, url.rstrip('/'))
                    new_uri = '/'.join(uri_split)
                    harvested_source['uri'] = new_uri
                    # add the library source uri
                    source_uris.append(new_uri)
                if not get_holding_pid_by_doc_location_item_type(
                    new_record.pid, location_pid, item_type_pid, 'electronic'
                ):
                    hold = create_holding(
                        document_pid=new_record.pid,
                        location_pid=location_pid,
                        item_type_pid=item_type_pid,
                        electronic_location=harvested_source,
                        holdings_type='electronic'
                    )
                    holdings.append(hold)
    db.session.commit()
    for hold in holdings:
        hold.reindex()
    # the document has been reindexed by the holdings
    if not holdings and new_record:
        new_record.reindex()
    HoldingsSearch.flush_and_refresh()
    # delete all double holdings and holdings without valid source uri
    seen_uris = []
    for holding_pid in Holding.get_holdings_pid_by_document_pid(pid):
        holding = Holding.get_record_by_pid(holding_pid)
        to_delete = True
        for electronic_location in holding.get('electronic_location', []):
            uri = electronic_location.get('uri')
            if electronic_location.get('source') and uri not in seen_uris:
                seen_uris.append(uri)
                if uri in source_uris:
                    to_delete = False
        if to_delete:
            current_app.logger.info(
                'Delete harvested holding | '
                f'document: {pid} '
                f'holding: {holding.pid} {holding.get("electronic_location")}'
            )
            holding.delete(force=False, dbcommit=True, delindex=True)
    return new_record
