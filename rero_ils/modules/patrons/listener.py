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

"""Signals connector for patron."""

from flask_babelex import gettext as _

from .api import Patron, PatronsSearch
from ..documents.api import Document
from ...utils import send_mail


def listener_item_at_desk(sender, *args, **kwargs):
    """Listener for signal item_at_desk."""
    func_item_at_desk(sender, *args, **kwargs)


def func_item_at_desk(sender, *args, **kwargs):
    """Function for signal item_at_desk."""
    item = kwargs['item']

    requests = item.number_of_requests()
    if requests:
        for request in item.get_requests():
            if request.get('state') == 'ITEM_AT_DESK':
                patron = Patron.get_record_by_pid(request.get('patron_pid'))
                if patron:
                    # Send at desk mail
                    subject = _('Document at desk')
                    document_pid = request.get('document_pid')
                    email = patron.get('email')
                    recipients = [email]
                    template = 'patron_request_at_desk'
                    send_mail(
                        subject=subject,
                        recipients=recipients,
                        template=template,
                        language='eng',
                        document=Document.get_record_by_pid(document_pid),
                        holding=request
                    )


def enrich_patron_data(sender, json=None, record=None, index=None,
                       **dummy_kwargs):
    """Signal sent before a record is indexed.

    :params: json: The dumped record dictionary which can be modified.
    :params: record: The record being indexed.
    :params: index: The index in which the record will be indexed.
    :params: doc_type: The doc_type for the record.
    """
    patron_index_name = PatronsSearch.Meta.index
    if index.startswith(patron_index_name):
        org_pid = record.get_organisation()['pid']
        if org_pid:
            json['organisation'] = {
                'pid': org_pid
            }
