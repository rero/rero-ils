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

"""Notification utils."""
from datetime import timezone

import ciso8601
from flask_security.utils import config_value
from invenio_mail.api import TemplatedMessage
from invenio_mail.tasks import send_email

from rero_ils.modules.documents.api import Document
from rero_ils.modules.documents.views import create_title_responsibilites
from rero_ils.modules.item_types.api import ItemType
from rero_ils.modules.items.api import Item
from rero_ils.modules.locations.api import Location
from rero_ils.modules.patrons.api import Patron


def _build_notification_email_context(loan, item, location):
    """Build the context used by the send_notification_to_location function.

    :param loan : the loan for which build context
    :param item : the item for which build context
    :param location : the item location
    """
    document_pid = Item.get_document_pid_by_item_pid(loan.item_pid)
    document = Document.get_record_by_pid(document_pid)
    pickup_location = Location.get_record_by_pid(
        loan.get('pickup_location_pid')
    )
    patron = Patron.get_record_by_pid(loan.patron_pid)

    # inherit holdings call number when possible
    issue_call_number = item.issue_inherited_first_call_number
    if issue_call_number:
        item['call_number'] = issue_call_number

    ctx = {
        'loan': loan.replace_refs().dumps(),
        'item': item.replace_refs().dumps(),
        'document': document.replace_refs().dumps(),
        'pickup_location': pickup_location,
        'item_location': location.dumps(),
        'patron': patron
    }
    library = pickup_location.get_library()
    ctx['pickup_location']['library'] = library
    ctx['item']['item_type'] = \
        ItemType.get_record_by_pid(item.item_type_pid)
    titles = [title for title in ctx['document'].get('title', [])
              if title['type'] == 'bf:Title']
    ctx['document']['title_text'] = \
        next(iter(titles or []), {}).get('_text')
    responsibility_statement = create_title_responsibilites(
        document.get('responsibilityStatement', [])
    )
    ctx['document']['responsibility_statement'] = \
        next(iter(responsibility_statement or []), '')
    trans_date = ciso8601.parse_datetime(loan.get('transaction_date'))
    trans_date = trans_date\
        .replace(tzinfo=timezone.utc)\
        .astimezone(tz=library.get_timezone())
    ctx['loan']['transaction_date'] = \
        trans_date.strftime("%d.%m.%Y - %H:%M:%S")
    return ctx


def send_notification_to_location(loan, item, location):
    """Send a notification to the location defined email.

    :param loan: the loan to be parsed
    :param item: the requested item
    :param location: the location to inform
    """
    if not location.get('send_notification', False) \
            or not location.get('notification_email'):
        return
    template = 'email/others/location_notification.txt'
    recipient = location.get('notification_email')
    msg = TemplatedMessage(
        template_body=template,
        sender=config_value('EMAIL_SENDER'),
        recipients=[recipient],
        ctx=_build_notification_email_context(loan, item, location)
    )
    text = msg.body.split('\n')
    msg.subject = text[0]
    msg.body = '\n'.join(text[1:])
    send_email.run(msg.__dict__)
