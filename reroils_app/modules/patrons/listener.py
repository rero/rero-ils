# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 CERN.
# Copyright (C) 2017 RERO.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Record module listener."""

from flask_babelex import gettext as _

from ...utils import send_mail
from ..documents_items.api import DocumentsWithItems
from ..patrons.api import Patron


def listener_item_at_desk(sender, *args, **kwargs):
    """Listener for signal item_at_desk."""
    func_item_at_desk(sender, *args, **kwargs)


def func_item_at_desk(sender, *args, **kwargs):
    """Function for signal item_at_desk."""
    item = kwargs['item']

    # Get patron for holding.
    holdings = item.get('_circulation', {}).get('holdings', [])
    if holdings:
        patron_barcode = holdings[0].get('patron_barcode')
        patron = Patron.get_patron_by_barcode(patron_barcode)

        if patron:
            # Send at desk mail
            subject = _('Document at desk')
            email = patron.get('email')
            recipients = [email]
            template = 'patron_request_at_desk'
            send_mail(
                subject=subject,
                recipients=recipients,
                template=template,
                language='eng',
                document=DocumentsWithItems.get_document_by_itemid(item.id),
                holding=item.dumps().get('_circulation').get('holdings')[0]
            )
